"""PURSUIT (galaxy 2, BONE REEF): the Leech Maw hunts the rocket from below. Its jaws creep
up the screen; boosting (UP) makes them fall back. Get caught and it bites. The world rushes
past while it chases. In the boss wave the maw overtakes the rocket and turns to fight."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import MAW_FLESH
from ..config.tuning import (PURSUIT_BITE, PURSUIT_FALL, PURSUIT_RISE, PURSUIT_SATED,
                             PURSUIT_SPEED, PURSUIT_START)
from ..flow.states import Phase
from .base import Hazard

TOP = LOW_H * 0.45                       # the jaws never come higher than this


class MawPursuit(Hazard):
    def __init__(self):
        self.bite_y = LOW_H - PURSUIT_START
        self.time = 0.0
        self.chomp = 0.0                 # > 0 right after a bite (the jaws snap shut)
        self.active = False
        self.world_speed = 1.0
        self.bites = 0

    def update(self, dt, game):
        self.time += dt
        self.chomp = max(0.0, self.chomp - dt)
        self.active = bool(getattr(game.wave, "pursuit", False)) and game.phase == Phase.FIELD
        self.world_speed = PURSUIT_SPEED if self.active else 1.0
        if not self.active:
            self.bite_y = min(LOW_H + 30, self.bite_y + 60 * dt)     # it sinks away
            return
        ship = game.ship
        boosting = ship.throttle > 0.75
        rate = -PURSUIT_FALL if boosting else PURSUIT_RISE
        self.bite_y = min(LOW_H + 10, max(TOP, self.bite_y - rate * dt))
        if ship.alive and ship.y + ship.h / 2 > self.bite_y and self.chomp <= 0:
            self.chomp = 0.8
            self.bites += 1
            game.hurt_ship(ship.max_hp * PURSUIT_BITE, ship.x, self.bite_y)
            ship.y = self.bite_y - ship.h / 2 - 18
            self.bite_y = min(LOW_H + 10, self.bite_y + PURSUIT_SATED)   # it swallows first
            ship.vy = -140
            game.shake.add(0.4)
            game.audio.play("dive")
            game.fire.burst(ship.x, self.bite_y, 14, 80, 0.4, MAW_FLESH[::-1], size=(1, 2))

    def draw_front(self, surf):
        if self.bite_y >= LOW_H + 8:
            return
        y = int(self.bite_y) + (6 if self.chomp > 0.5 else 0)
        surf.fill(MAW_FLESH[0], (0, y + 6, LOW_W, LOW_H - y))
        for x in range(0, LOW_W, 3):                        # the gullet: dark, wet, ribbed
            if (x // 3) % 4 == 0:
                surf.fill((30, 6, 12), (x, y + 10, 2, LOW_H - y))
        for i, x in enumerate(range(-6, LOW_W + 12, 12)):   # a row of teeth
            h = 9 + (i % 2) * 4 + int(math.sin(self.time * 6 + i) * 1.5)
            points = [(x, y + 7), (x + 6, y + 7 - h), (x + 12, y + 7)]
            pygame.draw.polygon(surf, (230, 220, 200), points)
            pygame.draw.polygon(surf, (40, 20, 24), points, 1)
        for ex in (LOW_W * 0.3, LOW_W * 0.7):               # eyes in the dark below
            if int(self.time * 2 + ex) % 7:
                pygame.draw.circle(surf, (255, 60, 70), (int(ex), y + 22), 3)
                surf.fill((255, 255, 255), (int(ex) - 1, y + 21, 1, 1))
        if self.active and random.random() < 0.3:
            surf.fill(MAW_FLESH[2], (random.randrange(LOW_W), y + 8, 2, 1))
