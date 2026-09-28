"""Galaxy 2 boss 5: THE MIMIC (G2 level 5, MIRROR SEA). It copies you: your position
(mirrored), your equipped weapon, and at last your own path, replayed as a trail of traps.
A learning boss."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, VEIL_GLOW
from ..core.pixelart import CharCanvas
from ..minions.mirror import echo_ghost
from ..minions.veil_bullets import LeadShot, RuneMark, VeilBullet, aimed
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

HALF_W, H = 30, 46
COLORS = {"K": (10, 12, 20), "S": (196, 204, 220), "s": (130, 140, 158), "D": (70, 78, 96),
          "M": (250, 252, 255), "E": (120, 170, 255), "e": (60, 90, 170), "R": (228, 44, 64)}


def _half(phase):
    """A chrome ship, like yours but upside down and too big, with a mirror for a face."""
    c = CharCanvas(HALF_W, H)
    c.poly([(29, 45), (24, 36), (14, 24), (4, 8), (10, 2), (20, 8), (29, 10)], "s")
    c.poly([(29, 42), (24, 34), (16, 24), (8, 10), (12, 6), (21, 11), (29, 13)], "S")
    c.line(29, 14, 18, 26, "D")
    c.rect(6, 2, 10, 6, "D")                                 # engine pods (it flies "down")
    c.circle(29, 28, 7, "K")
    c.circle(29, 28, 5, "E" if phase < 3 else "R")           # the mirror face
    c.set(27, 26, "M")
    c.set(28, 26, "M")
    if phase >= 2:
        c.line(20, 16, 26, 22, "K")                          # cracked chrome
    return c.rows()


class Mimic(Learner, Boss):
    """Galaxy 2, level 5. Four phases; attacks chosen by the bandit.

    COPY    -- your equipped weapon, turned on you: GUN = twin tracer streams, LASER = a
               beam column (with a warning line), SCATTER = pellet bursts, PLASMA = slow big
               orbs, ARC = a lightning strike on the spot where you were
    MIRROR  -- it jumps to your mirrored position and fires fans from there
    ECHOES  -- (phase 2+) two echo ghosts retrace your path
    REPLAY  -- (phase 3+) rune traps bloom along the path you flew over the last 10 s
    """

    EPITHET = "YOUR OWN WORST ENEMY"
    PHASES = 4
    RAGE = (1.0, 1.15, 1.3, 1.45)
    OPTIONS = (("copy", "mirror"),
               ("copy", "mirror", "echoes"),
               ("copy", "mirror", "echoes", "replay"),
               ("copy", "mirror", "replay"))
    SLOT, REST = 3.0, 0.8
    GUN_INTERVAL, SCATTER_INTERVAL, PLASMA_INTERVAL, ARC_INTERVAL = 0.2, 0.7, 0.6, 1.0
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.8, 120, 0.22
    BEAM_WARN, BEAM_HALF, BEAM_X = 0.9, 5, 0.1
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 1.0

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(4)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {}, [(8, 2), (52, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 30 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.copying = "GUN"
        self.beam = 0
        self.strikes = []                                  # ARC: (x, y, seconds left)

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer, self.beam = "rest", 0.0, 0.6, 0

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.learn_tick(dt)
        self._strikes(dt, world)
        ship = world.ship
        slow = 0.4 if self.beam == 2 else 1.0
        self.x += (LOW_W - ship.x - self.x) * min(1.0, 1.4 * slow * dt)     # it mirrors you
        self.y = self.home_y + math.sin(self.move_time) * 5
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer, self.beam = 0.0, 0.3, 0
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                self.copying = world.weapon.name
                world.telegraph()
                if self.attack == "mirror":
                    self._jump(world)
            else:
                self.attack = "rest"
            return
        if self.attack == "copy" and self.copying == "LASER":
            self._beam(dt, world)
            return
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    # --- attacks ------------------------------------------------------------------------
    def _copy(self, world):
        weapon = self.copying
        if weapon == "SCATTER":
            self.fire_timer = self.SCATTER_INTERVAL
            aim = self.lead_aim(world, self.x, self.y, 130)
            for i in range(5):
                a = aim + (i - 2) * 0.13
                world.enemy_bullets.append(VeilBullet(self.x, self.y + 8, math.cos(a) * 130,
                                                      math.sin(a) * 130, self.bullet_damage * 0.6))
        elif weapon == "PLASMA":
            self.fire_timer = self.PLASMA_INTERVAL
            aim = self.lead_aim(world, self.x, self.y, 70)
            world.enemy_bullets.append(aimed(PlasmaCopy, self.x, self.y + 8, aim, 70,
                                             self.bullet_damage * 1.3))
        elif weapon == "ARC":
            self.fire_timer = self.ARC_INTERVAL
            target = world.aim_target()
            self.strikes.append([target.x, target.y, 0.7])          # strikes where you were
            world.audio.play("lock_on")
        else:                                                        # GUN (and anything else)
            self.fire_timer = self.GUN_INTERVAL
            for dx in (-9, 9):
                world.enemy_bullets.append(VeilBullet(self.x + dx, self.y + 10, 0, 190,
                                                      self.bullet_damage * 0.45))

    def _beam(self, dt, world):
        """LASER copied: a warning line, then a column straight down."""
        if self.attack_time < self.BEAM_WARN:
            self.beam = 1
            return
        if self.beam != 2:
            world.audio.play("beam")
            world.shake.add(0.3)
        self.beam = 2
        ship = world.ship
        if ship.alive and ship.y > self.y and abs(ship.x - self.x) < self.BEAM_HALF + ship.w * 0.35:
            world.hurt_ship(self.bullet_damage * self.BEAM_X, self.x, ship.y)

    def _strikes(self, dt, world):
        for s in self.strikes:
            s[2] -= dt
        for x, y, t in [s for s in self.strikes if s[2] <= 0]:
            ship = world.ship
            world.fire.burst(x, y, 12, 90, 0.25, VEIL_GLOW, size=(1, 1))
            world.audio.play("switch")
            if ship.alive and math.hypot(ship.x - x, ship.y - y) < 14:
                world.hurt_ship(self.bullet_damage * 1.6, x, y)
        self.strikes = [s for s in self.strikes if s[2] > 0]

    def _jump(self, world):
        """A flash, and it stands where your reflection would be."""
        ship = world.ship
        world.fire.burst(self.x, self.y, 16, 80, 0.3, VEIL_GLOW, size=(1, 2))
        self.x = LOW_W - ship.x
        world.audio.play("teleport")

    def _mirror(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 8, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _echoes(self, world):
        self.fire_timer = 99
        world.spawn_enemies(echo_ghost(world) + echo_ghost(world))

    def _replay(self, world):
        """Your last 10 seconds, turned into traps: a rune every second of the path."""
        self.fire_timer = 99
        for seconds in range(1, 11):
            at = world.ship_at(seconds)
            if at:
                x, y = at
                world.enemy_bullets.append(RuneMark(x, max(40, y), self.bullet_damage * 0.8,
                                                    speed=55))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        super().draw(surf)
        if self.state != "fight":
            return
        for x, y, t in self.strikes:                                  # ARC warnings
            if int(t * 14) % 2 == 0:
                pygame.draw.circle(surf, DANGER, (int(x), int(y)), 14, 1)
        if self.beam and self.roar <= 0:
            x, y = int(self.x), int(self.y + self.h / 2)
            if self.beam == 1:
                if int(self.attack_time * 12) % 2 == 0:
                    pygame.draw.line(surf, DANGER, (x, y), (x, LOW_H))
            else:
                h = LOW_H - y
                surf.fill(VEIL_GLOW[3], (x - self.BEAM_HALF - 1, y, 2 * self.BEAM_HALF + 3, h))
                surf.fill(VEIL_GLOW[1], (x - 1, y, 3, h))
                surf.fill(VEIL_GLOW[0], (x, y, 1, h))


class PlasmaCopy(VeilBullet):
    """The Mimic's copy of a plasma orb: big, slow, pulsing."""
    __slots__ = ()

    def draw(self, surf, blink):
        r = 4 + (1 if blink else 0)
        pygame.draw.circle(surf, VEIL_GLOW[2], (int(self.x), int(self.y)), r)
        pygame.draw.circle(surf, VEIL_GLOW[0], (int(self.x), int(self.y)), r - 2)
