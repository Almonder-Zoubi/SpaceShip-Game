"""EGG CLUSTERS (galaxy 2, HOLLOW MAZE): a clutch of Hollow eggs drifts down; after
EGG_HATCH seconds it hatches a flock of larvae - unless you break it first. A ring round it
shows the time left."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER
from ..config.tuning import EGG_HATCH, EGG_HP, EGG_LARVAE, POINTS_EGG
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .swarm import larva_flock

ROWS = (
    "...KKK.KKK...",
    "..KeEeKeEeK..",
    ".KeEEeKeEEeK.",
    ".KeeeKKKeeeK.",
    "..KKKeEeKKK..",
    ".KeEeKeEeKeK.",
    "KeEEeKeeeKEeK",
    "KeeeK.KKK.KeK",
    ".KKK.......K.",
)
COLORS = {"K": (20, 10, 26), "e": (120, 70, 130), "E": (200, 150, 210)}


class EggCluster(Enemy):
    points = POINTS_EGG
    contact_damage = 12
    drops_coins = True
    _image = None

    def __init__(self, x, y=-8):
        if EggCluster._image is None:
            EggCluster._image = sprite_from_rows(ROWS, COLORS)
        super().__init__(EggCluster._image, x, y, EGG_HP)
        self.hatched = False

    @property
    def offscreen(self):
        return self.hatched or self.y - self.h > LOW_H

    def move(self, dt, world):
        self.y += (26 if self.y < 90 else 6) * dt
        self.x += math.sin(self.time * 1.3) * 6 * dt
        if self.time >= EGG_HATCH and not self.hatched and self.hp > 0:
            self.hatched = True
            flock = larva_flock(world, EGG_LARVAE)
            for larva in flock:
                larva.x = self.x + random.uniform(-8, 8)
                larva.y = self.y + random.uniform(-4, 4)
            world.spawn_enemies(flock)
            world.fire.burst(self.x, self.y, 14, 60, 0.4, [(200, 150, 210), (120, 70, 130)],
                             size=(1, 2))
            world.audio.play("spore")

    def attack(self, dt, world):
        pass

    def draw(self, surf):
        super().draw(surf)
        k = min(1.0, self.time / EGG_HATCH)
        steps = int(16 * (1 - k))                         # the ring runs out as it ripens
        for i in range(steps):
            a = -math.pi / 2 + math.tau * i / 16
            color = DANGER if k > 0.7 and int(self.time * 8) % 2 else (150, 110, 170)
            surf.fill(color, (int(self.x + math.cos(a) * 11), int(self.y + math.sin(a) * 11), 1, 1))
        if k > 0.7:
            pygame.draw.circle(surf, DANGER, (int(self.x), int(self.y)), 3, 1)


def egg_cluster(game):
    return [EggCluster(random.uniform(40, LOW_W - 40))]
