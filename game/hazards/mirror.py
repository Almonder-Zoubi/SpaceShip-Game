"""MIRROR (galaxy 2, MIRROR SEA): a calm silver sea where the rocket has a reflection. It
flies mirrored across the screen and fires when you fire; broken, it re-forms after a while.
The water line shimmers across the middle of the screen."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import REFLECTION_BACK
from ..flow.states import Phase
from ..minions.mirror import Reflection
from .base import Hazard


class MirrorSea(Hazard):
    def __init__(self):
        self.reflection = None
        self.back = 2.0                  # seconds until the reflection (re-)forms
        self.time = 0.0

    def update(self, dt, game):
        self.time += dt
        if self.reflection is not None and self.reflection not in game.enemies:
            self.reflection = None       # broken
            self.back = REFLECTION_BACK
        if self.reflection is None and game.phase == Phase.FIELD and game.ship.alive:
            self.back -= dt
            if self.back <= 0:
                self.reflection = Reflection(game.ship.image)
                game.spawn_enemies([self.reflection])
                game.fire.burst(self.reflection.x, self.reflection.y, 12, 50, 0.4,
                                [(220, 230, 255), (120, 140, 200)], size=(1, 2))

    def draw_back(self, surf):
        y = LOW_H // 2
        for x in range(0, LOW_W, 2):                    # the water line
            dy = int(math.sin(self.time * 2 + x * 0.08) * 2)
            if (x // 2 + int(self.time * 10)) % 5:
                surf.fill((60, 70, 100), (x, y + dy, 1, 1))
        for i in range(12):                             # glints on the silver sea
            x = int((i * 53 + self.time * 12) % LOW_W)
            if int(self.time * 3 + i) % 4 == 0:
                surf.fill((170, 180, 210), (x, y + 6 + (i % 5) * 9, 2, 1),
                          special_flags=pygame.BLEND_ADD)
