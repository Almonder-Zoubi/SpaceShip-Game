"""Fog banks (level 6): dithered grey-green fog drifting down. It covers rocks, minions and
pickups, but never the ship or enemy bullets (the fairness rule)."""
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import FOG_INTERVAL, FOG_SPEED
from ..core.pixelart import ValueNoise
from .base import Hazard

FOG = ((72, 92, 84, 210), (54, 72, 66, 190), (40, 54, 50, 150))


def fog_blob(w, h, rng):
    """An irregular fog cloud: noise threshold shaped by an ellipse, 3 dithered tones."""
    noise = ValueNoise(rng, cell=9)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            ex, ey = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
            d = ex * ex + ey * ey
            v = noise.sample(x, y) * 0.7 + (1 - d) * 0.8
            if v > 0.62:
                tone = 0 if v > 0.95 else 1 if v > 0.78 else 2
                if tone == 2 and (x + y) % 2:
                    continue
                surf.set_at((x, y), FOG[tone])
    return surf


class FogBanks(Hazard):
    _library = None               # fog images, built once

    def __init__(self):
        if FogBanks._library is None:
            rng = random.Random(7)
            FogBanks._library = [fog_blob(rng.randint(90, 150), rng.randint(46, 80), rng)
                                 for _ in range(4)]
        self.library = FogBanks._library
        self.banks = []                           # [image, x, y]
        self.timer = 1.5

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = random.uniform(*FOG_INTERVAL)
            image = random.choice(self.library)
            self.banks.append([image, random.uniform(-40, LOW_W - image.get_width() + 40),
                               -image.get_height()])
        speed = FOG_SPEED * game._world_speed()
        for bank in self.banks:
            bank[2] += speed * dt
        self.banks = [b for b in self.banks if b[2] < LOW_H]

    def covers(self, x, y):
        """True if a point is inside a fog bank (for tests / hidden things)."""
        for image, bx, by in self.banks:
            px, py = int(x - bx), int(y - by)
            if 0 <= px < image.get_width() and 0 <= py < image.get_height():
                if image.get_at((px, py)).a > 0:
                    return True
        return False

    def draw_mid(self, surf):
        for image, x, y in self.banks:
            surf.blit(image, (int(x), int(y)))
