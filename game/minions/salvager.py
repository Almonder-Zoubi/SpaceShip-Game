"""Salvager (level 8): flies to coins and pickups, grabs them and flees upwards. Kill it
before it gets away and everything it stole drops twice."""
import math
import random

from ..config.display import LOW_W
from ..config.palette import COIN
from ..config.tuning import (POINTS_SALVAGER, SALVAGER_GREED, SALVAGER_HP, SALVAGER_SPEED,
                             SALVAGER_TIME)
from ..core.pixelart import sprite_from_rows
from .base import Enemy

SALVAGER_ROWS = (
    "...KKKKK...",
    "..KLLWLLK..",
    ".KLLLLLLLK.",
    "KORRLLLRROK",
    "KOKKRRRKKOK",
    ".K.KGGGK.K.",
    ".K..KYK..K.",
    "KYK.....KYK",
    "K.K.....K.K",
)
COLORS = {"K": (18, 14, 30), "L": (150, 140, 120), "W": (230, 220, 200), "R": (190, 90, 40),
          "O": (110, 60, 30), "G": (70, 60, 60), "Y": (255, 200, 80)}


class Salvager(Enemy):
    points = POINTS_SALVAGER
    contact_damage = 15
    _image = None

    def __init__(self, x):
        if Salvager._image is None:
            Salvager._image = sprite_from_rows(SALVAGER_ROWS, COLORS)
        super().__init__(Salvager._image, x, -10, SALVAGER_HP)
        self.loot = []                   # pickups it grabbed
        self.fleeing = False

    @property
    def offscreen(self):
        return (self.fleeing and self.y < -20) or super().offscreen

    def move(self, dt, world):
        if not self.fleeing and (len(self.loot) >= SALVAGER_GREED or self.time > SALVAGER_TIME):
            self.fleeing = True
        if self.fleeing:
            self.y -= SALVAGER_SPEED * 1.3 * dt
            return
        wanted = [p for p in world.pickups if p.y > 0]
        if not wanted:                                   # nothing to steal: cruise down slowly
            self.y += 25 * dt
            self.x += math.sin(self.time * 1.5) * 20 * dt
            return
        goal = min(wanted, key=lambda p: (p.x - self.x) ** 2 + (p.y - self.y) ** 2)
        dx, dy = goal.x - self.x, goal.y - self.y
        dist = math.hypot(dx, dy) or 1.0
        self.x += dx / dist * SALVAGER_SPEED * dt
        self.y += dy / dist * SALVAGER_SPEED * dt
        if dist < 8:
            world.pickups.remove(goal)
            self.loot.append(goal)
            world.fire.burst(goal.x, goal.y, 4, 30, 0.2, COIN, size=(1, 1))

    def attack(self, dt, world):
        pass

    def on_death(self, world, scored):
        """Shot down: everything it stole drops twice."""
        if not scored:
            return
        for pickup in self.loot:
            for _ in range(2):
                a = random.uniform(0, math.tau)
                world.pickups.append(type(pickup)(self.x, self.y, math.cos(a) * 50,
                                                  math.sin(a) * 50 - 20))

    def draw(self, surf):
        super().draw(surf)
        for i in range(len(self.loot)):                  # what it carries
            surf.fill(COIN[2], (int(self.x) - 3 + i * 3, int(self.y) + 5, 2, 2))


def salvager(game):
    return [Salvager(random.uniform(30, LOW_W - 30))]
