"""Galaxy 2 boss 7a: GRINDER (G2 level 7, HOLLOW MAZE, the RED route). A mining crawler with
a saw for a face. It rams along a row it marks first, throws saw blades that come back, and
grinds a spray of sparks under itself. A learning boss."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER
from ..core.pixelart import CharCanvas
from ..minions.veil_bullets import Boomerang, LeadShot, VeilBullet, aimed, cage
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

HALF_W, H = 30, 36
COLORS = {"K": (14, 8, 8), "H": (150, 50, 44), "h": (96, 30, 30), "d": (60, 44, 40),
          "S": (210, 210, 220), "s": (130, 130, 150), "E": (255, 200, 60), "R": (255, 70, 60)}
SAW = (29, 26)                            # the saw's hub on the sprite (half coordinates)


def _half(phase):
    c = CharCanvas(HALF_W, H)
    c.poly([(29, 2), (14, 4), (2, 14), (4, 24), (16, 26), (29, 26)], "h")
    c.poly([(29, 5), (16, 7), (6, 15), (8, 22), (18, 23), (29, 23)], "H")
    c.rect(1, 9, 6, 27, "d")                                  # a tread
    for y in range(10, 27, 3):
        c.line(2, y, 5, y, "K")
    c.circle(SAW[0], SAW[1], 9, "K")
    c.circle(SAW[0], SAW[1], 8, "s")
    c.circle(SAW[0], SAW[1], 6, "S")
    for a in range(0, 360, 30):                               # teeth
        x = SAW[0] + math.cos(math.radians(a)) * 9.5
        y = SAW[1] + math.sin(math.radians(a)) * 9.5
        if x <= SAW[0]:
            c.set(int(x), int(y), "S")
    c.circle(SAW[0], SAW[1], 2, "K")
    c.rect(19, 11, 23, 13, "E" if phase < 2 else "R")         # eyes
    if phase >= 1:
        c.line(10, 16, 16, 20, "K")                           # dents
    return c.rows()


class Grinder(Learner, Boss):
    """Galaxy 2, level 7 (RED). Three phases; attacks chosen by the bandit.

    RAM    -- a red row marks your height, then it rams across the screen along it
    SAWS   -- saw blades (boomerangs) in a fan: they fly out, stop and come back
    GRIND  -- it tracks you and grinds a cone of sparks straight down
    WALLS  -- (phase 2+) a cage: two walls with one gap each close in from the sides
    """

    EPITHET = "IT CHEWS THROUGH ROCK"
    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    OPTIONS = (("ram", "saws", "grind"),
               ("ram", "saws", "grind", "walls"),
               ("ram", "saws", "walls", "grind"))
    SLOT, REST = 3.0, 0.8
    SAW_INTERVAL, SAW_SPEED = 1.0, 150
    GRIND_INTERVAL = 0.16
    RAM_WARN, RAM_SPEED, RAM_X = 0.9, 360, 3.0
    AIMED_RATE = 1 / SAW_INTERVAL * 3 * SLOT / (SLOT + REST) * 0.5 + 1.0

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(3)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {"saw": (SAW[0] + 1, SAW[1] + 1)},
                         [(6, 4), (54, 4)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 30 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.ram = 0                      # 0 none, 1 marking, 2 ramming, 3 returning
        self.ram_y = 0.0
        self.ram_dir = 1
        self.spin = 0.0

    @property
    def contact_damage(self):
        return self.bullet_damage * self.RAM_X if self.ram == 2 else super().contact_damage

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer, self.ram = "rest", 0.0, 0.6, 0

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.spin += dt * (14 if self.attack == "grind" or self.ram == 2 else 5)
        self.learn_tick(dt)
        if self.ram:
            self._ram(dt, world, rate)
            return
        target = world.aim_target()
        follow = 1.2 if self.attack == "grind" else 0.6
        goal = target.x if self.attack == "grind" else LOW_W / 2 + math.sin(self.move_time * 0.5) * 90
        self.x += (goal - self.x) * min(1.0, follow * dt)
        self.y += (self.home_y + math.sin(self.move_time * 1.4) * 4 - self.y) * min(1.0, 3 * dt)
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer = 0.0, 0.3
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                world.telegraph()
                if self.attack == "ram":
                    self.ram, self.ram_y = 1, max(self.home_y + 30, target.y)
                    world.audio.play("lock_on")
                elif self.attack == "walls":
                    cage(world, self.bullet_damage)
                    world.audio.play("warning")
            else:
                self.attack = "rest"
            return
        if self.attack in ("rest", "walls", "ram"):
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    def _ram(self, dt, world, rate):
        self.attack_time += dt
        if self.ram == 1:                                  # the mark: it lines up
            self.x += ((20 if self.x < LOW_W / 2 else LOW_W - 20) - self.x) * min(1.0, 4 * dt)
            if self.attack_time >= self.RAM_WARN:
                self.ram, self.ram_dir = 2, 1 if self.x < LOW_W / 2 else -1
                world.audio.play("dive")
                world.shake.add(0.3)
        elif self.ram == 2:                                # down to the row, across the screen
            self.y += (self.ram_y - self.y) * min(1.0, 8 * dt)
            self.x += self.ram_dir * self.RAM_SPEED * rate * dt
            if random.random() < 20 * dt:
                world.fire.burst(self.x, self.y + self.h / 2, 3, 60, 0.3, [(255, 220, 120)],
                                 size=(1, 1))
            if not -self.w < self.x < LOW_W + self.w:
                self.ram = 3
                self.x = LOW_W / 2
                self.y = -self.h
        else:                                              # back in from the top
            self.y += (self.home_y - self.y) * min(1.0, 3 * dt)
            if abs(self.y - self.home_y) < 3:
                self.ram, self.attack, self.attack_time = 0, "rest", 0.0

    def _saws(self, world):
        self.fire_timer = self.SAW_INTERVAL
        x, y = self.point(*self.muzzles["saw"])
        aim = self.lead_aim(world, x, y, self.SAW_SPEED * 0.5)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(Boomerang, x, y, aim + i * 0.4, self.SAW_SPEED,
                                             self.bullet_damage * 0.6))
        world.audio.play("enemy_shot")

    def _grind(self, world):
        self.fire_timer = self.GRIND_INTERVAL
        x, y = self.point(*self.muzzles["saw"])
        a = math.pi / 2 + random.uniform(-0.35, 0.35)
        world.enemy_bullets.append(VeilBullet(x, y + 8, math.cos(a) * 150, math.sin(a) * 150,
                                              self.bullet_damage * 0.35))
        if random.random() < 0.25:                         # now and then a real shot at you
            aim = self.lead_aim(world, x, y, 120)
            world.enemy_bullets.append(aimed(LeadShot, x, y, aim, 120, self.bullet_damage * 0.6))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        if self.ram == 1 and int(self.attack_time * 12) % 2 == 0 and self.roar <= 0:
            pygame.draw.line(surf, DANGER, (0, int(self.ram_y)), (LOW_W, int(self.ram_y)))
        super().draw(surf)
        if self.state in ("fight", "enter"):
            x, y = self.point(*self.muzzles["saw"])
            for i in range(6):                              # the spinning teeth
                a = self.spin + i * math.tau / 6
                surf.fill((240, 240, 250), (int(x + math.cos(a) * 7), int(y + math.sin(a) * 7), 2, 2))
