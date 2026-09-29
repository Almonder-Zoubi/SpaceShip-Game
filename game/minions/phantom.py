"""Phantom (level 6): a cloaked fighter. Only a faint shimmer shows where it is; it fades in
for PHANTOM_FADE seconds before it fires a short burst, then cloaks again."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.tuning import (PHANTOM_BULLET_DAMAGE, PHANTOM_BULLET_SPEED, PHANTOM_BURST,
                             PHANTOM_CLOAK, PHANTOM_FADE, PHANTOM_HP, POINTS_PHANTOM)
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .bullets import shoot

PHANTOM_ROWS = (
    "K.........K",
    "KGK.....KGK",
    "KGGK...KGGK",
    ".KGGKKKGGK.",
    ".KGLLLLLGK.",
    "..KLCQCLK..",
    "..KLLCLLK..",
    "...KLLLK...",
    "....KLK....",
    ".....K.....",
)
COLORS = {"K": (20, 26, 30), "G": (70, 110, 100), "L": (150, 200, 185), "C": (200, 255, 235),
          "Q": (255, 90, 110)}
ALPHAS = 8                       # cached transparency steps


class Phantom(Enemy):
    points = POINTS_PHANTOM
    contact_damage = 20
    _frames = None

    def __init__(self, x):
        if Phantom._frames is None:
            image = sprite_from_rows(PHANTOM_ROWS, COLORS)
            Phantom._frames = []
            for i in range(ALPHAS + 1):
                frame = image.copy()
                frame.set_alpha(int(255 * i / ALPHAS))
                Phantom._frames.append(frame)
            Phantom._outline = pygame.mask.from_surface(image).outline()
        super().__init__(Phantom._frames[-1], x, -10, PHANTOM_HP)
        self.target_y = random.uniform(40, 110)
        self.cloak = random.uniform(0.6, PHANTOM_CLOAK)   # seconds hidden until the next fade-in
        self.fade = 0.0                                   # 0 hidden .. 1 fully visible
        self.bursts = 2
        self.shots = 0
        self.fire_timer = 0.0
        self.sway = random.uniform(0, math.tau)

    @property
    def visible(self):
        return self.fade

    def move(self, dt, world):
        leaving = self.bursts <= 0 and self.fade <= 0
        goal = 400 if leaving else self.target_y
        self.y += max(-40.0, min(60.0, (goal - self.y) * 1.5)) * dt
        self.x += math.sin(self.time * 1.3 + self.sway) * 22 * dt
        self.x = min(LOW_W - 10, max(10, self.x))

    def attack(self, dt, world):
        if self.shots:                                   # visible and firing
            self.fade = 1.0
            self.fire_timer -= dt
            if self.fire_timer <= 0:
                self.fire_timer = 0.14
                self.shots -= 1
                aim = math.atan2(world.ship.y - self.y, world.ship.x - self.x)
                shoot(world, self.x, self.y + 4, aim, PHANTOM_BULLET_SPEED, PHANTOM_BULLET_DAMAGE)
                if not self.shots:
                    self.cloak = PHANTOM_CLOAK
            return
        if self.cloak > 0:                               # hidden, fading out
            self.cloak -= dt
            self.fade = max(0.0, self.fade - dt / 0.3)
            return
        if self.bursts <= 0:
            return
        self.fade = min(1.0, self.fade + dt / PHANTOM_FADE)
        if self.fade >= 1.0:
            self.bursts -= 1
            self.shots = PHANTOM_BURST

    def draw(self, surf):
        if self.flash > 0:
            surf.blit(self.white, self.topleft)
            return
        step = int(self.fade * ALPHAS)
        left, top = self.topleft
        if step == 0:                                    # just a shimmer on its outline
            for i, (px, py) in enumerate(Phantom._outline):
                if (i + int(self.time * 12)) % 5 == 0:
                    surf.fill((60, 90, 80), (left + px, top + py, 1, 1),
                              special_flags=pygame.BLEND_ADD)
            return
        surf.blit(Phantom._frames[max(1, step)], (left, top))


def phantom_pair(game):
    """Two phantoms at random places across the top."""
    return [Phantom(random.uniform(30, LOW_W - 30)) for _ in range(2)]
