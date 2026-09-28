"""Galaxy 2 boss 7b: SPINNER (G2 level 7, HOLLOW MAZE, the BLUE route). A star-shaped turret
that never stops turning: spiral arms of twinned bullets, lead fans, and in the end three
rotating beams that sweep the whole screen. A learning boss."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER
from ..core.pixelart import CharCanvas
from ..minions.veil_bullets import LeadShot, RuneMark, aimed, twinned
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

R = 22
COLORS = {"K": (6, 10, 20), "B": (60, 120, 230), "b": (30, 60, 130), "W": (220, 240, 255),
          "C": (120, 220, 255), "R": (255, 80, 110)}


def _half(phase):
    c = CharCanvas(R + 1, R * 2 + 1)
    for k in range(4):                                    # the star's points (left half)
        a = math.pi / 2 + k * math.pi / 4 + math.pi / 8
        tip = (R + math.cos(a) * R, R + math.sin(a) * R)
        c.poly([(R, R), (int(tip[0]), int(tip[1])),
                (int(R + math.cos(a + 0.35) * 9), int(R + math.sin(a + 0.35) * 9))], "b")
    c.circle(R, R, 11, "b")
    c.circle(R, R, 9, "B")
    c.circle(R, R, 5, "K")
    c.circle(R, R, 3, "C" if phase < 2 else "R")
    c.set(R - 1, R - 1, "W")
    return c.rows()


class Spinner(Learner, Boss):
    """Galaxy 2, level 7 (BLUE). Three phases; attacks chosen by the bandit.

    SPIRAL   -- four arms of twinned bullets, turning
    FANS     -- lead-shot fans
    BEAMS    -- (phase 2+) three beams: thin warning lines, then they burn and turn
    RUNES    -- (phase 3) rune marks round the rocket bloom into rings
    """

    EPITHET = "IT NEVER STOPS TURNING"
    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    OPTIONS = (("spiral", "fans"),
               ("spiral", "fans", "beams"),
               ("spiral", "fans", "beams", "runes"))
    SLOT, REST = 3.2, 0.8
    SPIRAL_INTERVAL, SPIRAL_SPEED = 0.34, 75
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.8, 120, 0.2
    BEAM_WARN, BEAM_TURN, BEAM_X, BEAM_WIDTH = 0.9, 0.55, 0.12, 5
    RUNE_INTERVAL = 0.8
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 1.0

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(3)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {}, [(R, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 40 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.spin = 0.0
        self.beam_angle = 0.0

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.6

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.spin += dt * rate * 1.6
        self.learn_tick(dt)
        slow = 0.25 if self.attack == "beams" else 1.0
        self.x += (LOW_W / 2 + math.sin(self.move_time * 0.35) * 80 - self.x) * min(1.0, 1.5 * slow * dt)
        self.y = self.home_y + math.sin(self.move_time * 0.8) * 6
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer = 0.0, 0.3
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                world.telegraph()
                if self.attack == "beams":
                    target = world.aim_target()                  # no beam starts on you
                    self.beam_angle = math.atan2(target.y - self.y, target.x - self.x) + math.pi / 3
            else:
                self.attack = "rest"
            return
        if self.attack == "beams":
            self._beams(dt, world, rate)
            return
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    def beam_angles(self):
        return [self.beam_angle + i * math.tau / 3 for i in range(3)]

    def _beams(self, dt, world, rate):
        if self.attack_time < self.BEAM_WARN:
            return
        if self.attack_time - dt < self.BEAM_WARN:
            world.audio.play("beam")
        self.beam_angle += self.BEAM_TURN * rate * dt
        ship = world.ship
        if not ship.alive:
            return
        for a in self.beam_angles():
            dx, dy = ship.x - self.x, ship.y - self.y
            along = dx * math.cos(a) + dy * math.sin(a)
            off = abs(-dx * math.sin(a) + dy * math.cos(a))
            if along > 0 and off < self.BEAM_WIDTH + ship.w * 0.3:
                world.hurt_ship(self.bullet_damage * self.BEAM_X, ship.x, ship.y)

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        for k in range(4):
            a = self.spin + k * math.tau / 4
            world.enemy_bullets += twinned(self.x, self.y, a, self.SPIRAL_SPEED,
                                           self.bullet_damage * 0.5)

    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 10, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _runes(self, world):
        self.fire_timer = self.RUNE_INTERVAL
        ship = world.aim_target()
        a = random.uniform(0, math.tau)
        x = min(LOW_W - 10, max(10, ship.x + math.cos(a) * 30))
        y = min(LOW_H - 10, max(70, ship.y + math.sin(a) * 30))
        world.enemy_bullets.append(RuneMark(x, y, self.bullet_damage * 0.7))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        if self.attack == "beams" and self.state == "fight" and self.roar <= 0:
            warn = self.attack_time < self.BEAM_WARN
            for a in self.beam_angles():
                end = (int(self.x + math.cos(a) * 400), int(self.y + math.sin(a) * 400))
                start = (int(self.x), int(self.y))
                if warn:
                    if int(self.attack_time * 12) % 2 == 0:
                        pygame.draw.line(surf, DANGER, start, end)
                else:
                    pygame.draw.line(surf, COLORS["b"], start, end, self.BEAM_WIDTH * 2 + 1)
                    pygame.draw.line(surf, COLORS["C"], start, end, 3)
                    pygame.draw.line(surf, COLORS["W"], start, end, 1)
        super().draw(surf)
        if self.state == "fight":
            for k in range(4):                                # the rotating arms' tips
                a = self.spin + k * math.tau / 4
                surf.fill(COLORS["C"], (int(self.x + math.cos(a) * (R + 3)),
                                        int(self.y + math.sin(a) * (R + 3)), 2, 2))
