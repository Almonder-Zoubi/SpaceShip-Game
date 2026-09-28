"""The Swarm's small fry (level 10).

SporePod -- drifts down; at mid-screen it swells (a telegraph ring) and bursts into a ring
            of slow bullets. Shot before that, it pops harmlessly.
Larva    -- tiny and fast, hunts in flocks (boids: separation, alignment, cohesion, plus a
            pull towards the rocket), then swarms off after a while.
"""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import HEAL
from ..config.tuning import (LARVA_DAMAGE, LARVA_HP, LARVA_SPEED, LARVA_TIME, POINTS_LARVA,
                             POINTS_SPORE, SPORE_BULLET_DAMAGE, SPORE_BULLET_SPEED, SPORE_FALL,
                             SPORE_HP, SPORE_RIPEN, SPORE_SHOTS, SPORE_SWELL)
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .bullets import bullet

SPORE_ROWS = (
    "...KKKKK...",
    "..KGGgGGK..",
    ".KGgLLLgGK.",
    "KGgLYYYLgGK",
    "KGLYWYYYLGK",
    "KGLYYYYYLGK",
    "KGgLYYYLgGK",
    ".KGgLLLgGK.",
    "..KGGgGGK..",
    "...KKKKK...",
)
LARVA_ROWS = (
    ".KKK.",
    "KGYGK",
    "KYWYK",
    ".KGK.",
    "..K..",
)
COLORS = {"K": (18, 10, 20), "G": (90, 40, 80), "g": (60, 24, 56), "L": (140, 70, 110),
          "Y": (140, 230, 90), "W": (230, 255, 210)}


class SporePod(Enemy):
    points = POINTS_SPORE
    contact_damage = 14
    _image = None

    def __init__(self, x):
        if SporePod._image is None:
            SporePod._image = sprite_from_rows(SPORE_ROWS, COLORS)
        super().__init__(SporePod._image, x, -8, SPORE_HP)
        self.swell = -1.0                 # < 0 not yet; then seconds swelling
        self.phase = random.uniform(0, math.tau)

    def move(self, dt, world):
        if self.swell < 0:
            self.y += SPORE_FALL * dt
            self.x += math.sin(self.time * 1.2 + self.phase) * 10 * dt
            if self.y > SPORE_RIPEN:
                self.swell = 0.0
                world.audio.play("lock_on")

    def attack(self, dt, world):
        if self.swell < 0:
            return
        self.swell += dt
        if self.swell >= SPORE_SWELL:            # burst: a ring of slow bullets
            offset = random.uniform(0, math.tau)
            for i in range(SPORE_SHOTS):
                world.enemy_bullets.append(bullet(self.x, self.y, offset + math.tau * i / SPORE_SHOTS,
                                                  SPORE_BULLET_SPEED, SPORE_BULLET_DAMAGE))
            world.fire.burst(self.x, self.y, 14, 70, 0.4, HEAL, size=(1, 2))
            world.audio.play("spore")
            self.hp = 0                           # gone (the world removes it, no score)
            self.burst = True

    @property
    def offscreen(self):
        return getattr(self, "burst", False) or super().offscreen

    def draw(self, surf):
        if self.swell >= 0:                       # the telegraph: swelling + a closing ring
            k = self.swell / SPORE_SWELL
            r = int(22 - 16 * k)
            if int(self.swell * 14) % 2 == 0:
                pygame.draw.circle(surf, (220, 60, 90), (int(self.x), int(self.y)), r, 1)
            image = pygame.transform.scale(self.image, (int(self.w * (1 + 0.4 * k)),
                                                        int(self.h * (1 + 0.4 * k))))
            surf.blit(image, image.get_rect(center=(int(self.x), int(self.y))))
            return
        super().draw(surf)


class Larva(Enemy):
    points = POINTS_LARVA
    contact_damage = LARVA_DAMAGE
    drops_coins = False
    _image = None

    def __init__(self, x, y, flock):
        if Larva._image is None:
            Larva._image = sprite_from_rows(LARVA_ROWS, COLORS)
        super().__init__(Larva._image, x, y, LARVA_HP)
        self.flock = flock                # the list this larva flies with
        self.vx, self.vy = random.uniform(-30, 30), random.uniform(40, 70)

    @property
    def offscreen(self):
        return (self.time > LARVA_TIME and (self.y > LOW_H + 6 or self.y < -30
                                            or not -20 < self.x < LOW_W + 20))

    def move(self, dt, world):
        mates = [m for m in self.flock if m is not self and m.hp > 0]
        ax = ay = 0.0
        if mates:
            cx = sum(m.x for m in mates) / len(mates)
            cy = sum(m.y for m in mates) / len(mates)
            ax += (cx - self.x) * 0.8                             # cohesion
            ay += (cy - self.y) * 0.8
            ax += (sum(m.vx for m in mates) / len(mates) - self.vx) * 1.2   # alignment
            ay += (sum(m.vy for m in mates) / len(mates) - self.vy) * 1.2
            for m in mates:                                       # separation
                dx, dy = self.x - m.x, self.y - m.y
                d2 = dx * dx + dy * dy
                if 0 < d2 < 100:
                    ax += dx / d2 * 900
                    ay += dy / d2 * 900
        ship = world.ship
        if self.time < LARVA_TIME and ship.alive:                 # hunt the rocket
            ax += (ship.x - self.x) * 1.4
            ay += (ship.y - self.y) * 1.4
        else:                                                     # swarm off
            ay += 260
        ax += random.uniform(-80, 80)
        self.vx += ax * dt
        self.vy += ay * dt
        speed = math.hypot(self.vx, self.vy) or 1.0
        if speed > LARVA_SPEED:
            self.vx, self.vy = self.vx / speed * LARVA_SPEED, self.vy / speed * LARVA_SPEED
        self.x += self.vx * dt
        self.y += self.vy * dt

    def attack(self, dt, world):
        pass

    def draw(self, surf):
        if int(self.time * 10 + id(self) % 7) % 2 == 0 and self.flash <= 0:
            surf.fill((40, 90, 30), (int(self.x) - int(self.vx * 0.04), int(self.y) - int(self.vy * 0.04),
                                     1, 1), special_flags=pygame.BLEND_ADD)
        super().draw(surf)


def spore_cluster(game):
    return [SporePod(random.uniform(40, LOW_W - 40)) for _ in range(random.choice((2, 3)))]


def larva_flock(game, size=None):
    flock = []
    cx = random.uniform(60, LOW_W - 60)
    for _ in range(size or random.randint(8, 14)):
        flock.append(Larva(cx + random.uniform(-20, 20), random.uniform(-40, -8), flock))
    return flock
