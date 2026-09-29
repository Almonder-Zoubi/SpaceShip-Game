"""Galaxy 2 boss 6: TEMPO (G2 level 6, PULSE NEBULA). A metronome the size of a cruiser.
Its pendulum swings on the beat and every attack lands on the beat; each phase it plays
faster notes (quarters, eighths, triplets). A learning boss."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.tuning import PULSE_BPM
from ..core.pixelart import CharCanvas
from ..minions.veil_bullets import LeadShot, VeilBullet, aimed, cage
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

BEAT = 60.0 / PULSE_BPM
HALF_W, H = 26, 44
ROD = 62                                   # px from the pivot to the weight
COLORS = {"K": (18, 6, 20), "P": (140, 40, 130), "p": (80, 20, 80), "B": (226, 206, 186),
          "b": (176, 140, 124), "G": (255, 204, 64), "W": (255, 255, 255), "E": (255, 90, 190)}


def _half(phase):
    """A tall wedge (a metronome's case) with a scale on its face and a glowing eye."""
    c = CharCanvas(HALF_W, H)
    c.poly([(25, 0), (18, 2), (4, 43), (25, 43)], "p")
    c.poly([(25, 3), (19, 5), (7, 40), (25, 40)], "P")
    for y in range(10, 38, 5):                               # the tempo scale
        c.line(25 - (y - 4) // 4, y, 25, y, "b")
    c.rect(22, 38, 25, 43, "B")                              # the pivot housing
    eye = 2 + phase
    c.circle(25, 14, eye + 1, "K")
    c.circle(25, 14, eye, "E")
    c.set(24, 13, "W")
    return c.rows()


class Weight:
    """The pendulum's weight: a part of the boss (hits count), and where its shots start."""

    RADIUS = 7

    def __init__(self):
        self.x = self.y = 0.0
        self.flash = 0.0

    @property
    def bound(self):
        return self.RADIUS + 1

    def contains(self, px, py):
        return (px - self.x) ** 2 + (py - self.y) ** 2 <= self.RADIUS ** 2

    def draw(self, surf):
        color = (255, 255, 255) if self.flash > 0 else COLORS["G"]
        pygame.draw.circle(surf, COLORS["K"], (int(self.x), int(self.y)), self.RADIUS + 1)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.RADIUS)
        pygame.draw.circle(surf, COLORS["W"], (int(self.x) - 2, int(self.y) - 2), 2)


class Tempo(Learner, Boss):
    """Galaxy 2, level 6. Four phases = four note values; attacks chosen by the bandit.

    TICK     -- lead shots from the weight on every note
    TOCK     -- rings from the case on every other note
    CAGE     -- cage walls on the bar's first beat
    ARPEGGIO -- (phase 2+) a spiral that climbs note by note
    SWING    -- (phase 3+) the weight leaves a trail of bullets along its arc
    """

    EPITHET = "THE BEAT THAT KILLS"
    PHASES = 4
    RAGE = (1.0, 1.1, 1.2, 1.3)
    NOTES = (1, 2, 2, 3)                   # notes per beat in each phase
    OPTIONS = (("tick", "tock", "cage"),
               ("tick", "tock", "cage", "arpeggio"),
               ("tick", "tock", "arpeggio", "swing"),
               ("tick", "cage", "arpeggio", "swing"))
    SLOT, REST = BEAT * 8, BEAT * 2        # attacks last two bars, a bar's rest between
    AMP = 1.0                              # the pendulum's swing (radians each side)
    RING_SHOTS, RING_SPEED = 10, 70
    TICK_SPEED = 115
    # Aimed damage per second: one lead shot per note on average (phase 1: a beat).
    AIMED_RATE = 1 / BEAT * SLOT / (SLOT + REST) * 0.8

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(4)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {}, [(10, 2), (42, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 28 + self.h / 2
        self.weight = Weight()
        self.attack, self.attack_time = "rest", 0.0
        self.last_note = -1
        self.spiral = 0.0
        self.clock = 0.0
        self._layout()

    def parts(self):
        return [self, self.weight]

    def hit_part(self, part, amount, flash=True, source=None):
        if part is self.weight:
            part.flash = 0.05 if flash else part.flash
        self.damage(amount, flash)

    def collides_with(self, ship):
        w = self.weight
        return (super().collides_with(ship)
                or math.hypot(ship.x - w.x, ship.y - w.y) < w.RADIUS + ship.w * 0.3)

    def pivot(self):
        return self.x, self.y + self.h / 2 - 2

    def swing(self):
        """The rod's angle: one swing from side to side per beat."""
        return self.AMP * math.sin(math.pi * self.clock / BEAT)

    def _layout(self):
        px, py = self.pivot()
        a = self.swing()
        self.weight.x = px + math.sin(a) * ROD
        self.weight.y = py + math.cos(a) * ROD

    def on_phase(self):
        self.attack, self.attack_time = "rest", 0.0

    def update(self, dt, world):
        self.weight.flash = max(0.0, self.weight.flash - dt)
        pulse = getattr(world.hazard, "clock", None)          # the level's beat clock
        self.clock = pulse if pulse is not None else self.clock + dt
        result = super().update(dt, world)
        self._layout()
        return result

    def enter(self, k):
        super().enter(k)
        self._layout()

    def fight(self, dt, world):
        self.learn_tick(dt)
        self.x += (LOW_W / 2 + math.sin(self.clock * 0.25) * 60 - self.x) * min(1.0, dt)
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time = 0.0
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                world.telegraph()
            else:
                self.attack = "rest"
        notes = self.NOTES[self.phase]
        note = int(self.clock / BEAT * notes)
        if note == self.last_note:
            return
        self.last_note = note
        if self.attack != "rest":
            getattr(self, "_" + self.attack)(world, note, notes)

    # --- attacks (called once per note) -------------------------------------------------
    def _tick(self, world, note, notes):
        w = self.weight
        aim = self.lead_aim(world, w.x, w.y, self.TICK_SPEED)
        world.enemy_bullets.append(aimed(LeadShot, w.x, w.y, aim, self.TICK_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _tock(self, world, note, notes):
        if note % 2:
            return
        off = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            a = off + math.tau * i / self.RING_SHOTS
            world.enemy_bullets.append(VeilBullet(self.x, self.y, math.cos(a) * self.RING_SPEED,
                                                  math.sin(a) * self.RING_SPEED, self.bullet_damage))

    def _cage(self, world, note, notes):
        if note % (4 * notes) == 0:                       # the bar's first beat
            cage(world, self.bullet_damage)
            world.audio.play("warning")

    def _arpeggio(self, world, note, notes):
        self.spiral += 0.55
        for i in range(3):
            a = self.spiral + math.tau * i / 3
            world.enemy_bullets.append(VeilBullet(self.x, self.y, math.cos(a) * 85,
                                                  math.sin(a) * 85, self.bullet_damage))

    def _swing(self, world, note, notes):
        w = self.weight
        world.enemy_bullets.append(VeilBullet(w.x, w.y, 0, 60, self.bullet_damage))
        if note % notes == 0:
            self._tick(world, note, notes)

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        px, py = self.pivot()
        w = self.weight
        pygame.draw.line(surf, COLORS["K"], (int(px) + 1, int(py)), (int(w.x) + 1, int(w.y)), 3)
        pygame.draw.line(surf, COLORS["b"], (int(px), int(py)), (int(w.x), int(w.y)), 2)
        super().draw(surf)
        w.draw(surf)
        if self.state == "fight":                          # a spark on the beat at the pivot
            k = 1 - (self.clock % BEAT) / BEAT
            if k > 0.85:
                pygame.draw.circle(surf, COLORS["E"], (int(px), int(py)), 3 + int(k * 3), 1)

