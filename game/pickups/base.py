"""Pickup base class: falls, sways, drifts to the ship, gets collected."""
import math
import random

import pygame

from ..config.display import LOW_H
from ..config.palette import HEAL
from ..config.tuning import PICKUP_FALL, PICKUP_MAGNET, PICKUP_RADIUS
from .art import KIT_SMALL_ROWS, build_pickup


class Pickup:
    """Base class: falls with a gentle sway, drifts to a nearby ship, gets collected.

    Subclasses set `rows`, `glow` and implement apply(game) -> popup text (or None).
    """

    rows = KIT_SMALL_ROWS
    glow = HEAL
    sound = "pickup"
    fanfare = True                # popup text + shockwave when collected (coins: just a sparkle)
    magnet = PICKUP_MAGNET        # px; closer than this and the pickup flies to the ship
    _images = {}                  # sprite cache per subclass

    def __init__(self, x, y, vx=0.0, vy=PICKUP_FALL):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.time = random.uniform(0, math.tau)
        self.collected = False
        cls = type(self)
        if cls not in Pickup._images:
            Pickup._images[cls] = build_pickup(cls.rows)
        self.image = Pickup._images[cls]

    @property
    def offscreen(self):
        return self.y > LOW_H + 10

    def update(self, dt, ship):
        self.time += dt
        dx, dy = ship.x - self.x, ship.y - self.y
        dist = math.hypot(dx, dy) or 1.0
        if ship.alive and dist < self.magnet:
            pull = 160 * (1 - dist / self.magnet) + 40
            self.x += dx / dist * pull * dt
            self.y += dy / dist * pull * dt
        else:
            self.vx *= max(0.0, 1 - 2 * dt)       # launch speed (from a boss) fades
            self.vy += (PICKUP_FALL - self.vy) * min(1.0, 2 * dt)
            self.x += (self.vx + math.sin(self.time * 2.2) * 10) * dt
            self.y += self.vy * dt
        if ship.alive and dist < PICKUP_RADIUS:
            self.collected = True

    def apply(self, game):
        raise NotImplementedError

    def draw(self, surf):
        x = int(self.x) - self.image.get_width() // 2
        y = int(self.y) - self.image.get_height() // 2 + int(math.sin(self.time * 4))
        # Pulsing halo (additive) so pickups stand out against rocks and bullets.
        r = 6 + int(2 * (1 + math.sin(self.time * 6)))
        pygame.draw.circle(surf, self.glow[3], (int(self.x), int(self.y)), r, 1)
        surf.blit(self.image, (x, y))
        if int(self.time * 3) % 3 == 0:                     # twinkle
            surf.fill(self.glow[0], (x + 1, y + 2, 1, 1), special_flags=pygame.BLEND_ADD)
