"""BLIND SPOTS (a VEIL SHIFT): three patches of darkness drift over the field and hide what is
under them. The rocket and enemy bullets stay visible on top (pillar 4: fair and readable)."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from .base import Hazard

RADIUS = 30


class BlindSpots(Hazard):
    def __init__(self, count=3):
        self.spots = [[random.uniform(40, LOW_W - 40), random.uniform(40, LOW_H - 90),
                       random.uniform(-14, 14), random.uniform(-8, 8)] for _ in range(count)]
        self.time = 0.0
        self._disc = self._build()

    @staticmethod
    def _build():
        size = RADIUS * 2 + 1
        disc = pygame.Surface((size, size), pygame.SRCALPHA)
        for y in range(size):
            for x in range(size):
                d = math.hypot(x - RADIUS, y - RADIUS) / RADIUS
                if d < 1:
                    alpha = 250 if d < 0.7 else int(250 * (1 - d) / 0.3)
                    if d >= 0.7 and (x + y) % 2:            # dithered rim
                        alpha //= 2
                    disc.set_at((x, y), (4, 2, 10, alpha))
        return disc

    def update(self, dt, game):
        self.time += dt
        for s in self.spots:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            if not 30 < s[0] < LOW_W - 30:
                s[2] = -s[2]
            if not 40 < s[1] < LOW_H - 80:
                s[3] = -s[3]

    def draw_mid(self, surf):
        for x, y, _, _ in self.spots:
            surf.blit(self._disc, (int(x) - RADIUS, int(y) - RADIUS))
