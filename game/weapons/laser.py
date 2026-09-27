"""Laser: continuous beam from the nose that overheats."""
import math
import random

import pygame

from ..config.palette import LASER
from ..config.tuning import (LASER_COOL_RATE, LASER_POWER_BONUS, LASER_POWER_COOL, LASER_PUSH,
                             LASER_RANGE, LASER_RESUME)
from .base import Hit, Weapon, raycast


class Laser(Weapon):
    """Continuous beam from the nose: instant, precise, but it overheats."""

    name = "LASER"
    colors = LASER              # beam skin

    def __init__(self):
        self.reset()

    def reset(self):
        self.power = 0
        self.heat = 0.0
        self.overheated = False
        self.active = False
        self.start = self.end = (0, 0)
        self.time = 0.0

    def update(self, dt, firing, ship, targets, fire):
        self.time += dt
        self.active = firing and not self.overheated
        if self.active:
            rate = self.loadout.laser_heat_rate * (1 - LASER_POWER_COOL * self.power)
            self.heat = min(1.0, self.heat + rate * dt)
            if self.heat >= 1.0:
                self.overheated = True
        else:
            self.heat = max(0.0, self.heat - LASER_COOL_RATE * dt)
            if self.overheated and self.heat <= LASER_RESUME:
                self.overheated = False
        if not self.active:
            return []

        ox, oy = ship.nose()
        dx, dy = ship.forward
        dist, target = raycast(ox, oy, dx, dy, LASER_RANGE, targets)
        self.start, self.end = (ox, oy), (ox + dx * dist, oy + dy * dist)
        if target is None:
            return []
        ex, ey = self.end
        for _ in range(2):   # sparks spray back from the impact point
            a = math.atan2(-dy, -dx) + random.uniform(-1.1, 1.1)
            s = random.uniform(30, 110)
            fire.emit(ex, ey, math.cos(a) * s, math.sin(a) * s, random.uniform(0.08, 0.2),
                      self.colors)
        dps = self.loadout.laser_dps * (1 + LASER_POWER_BONUS * self.power) * self.rate
        return [Hit(target, dps * dt, ex, ey, dx, dy, LASER_PUSH * dt, continuous=True)]

    def draw(self, surf):
        if not self.active:
            return
        (sx, sy), (ex, ey) = self.start, self.end
        length = max(1, int(math.hypot(ex - sx, ey - sy)))
        dx, dy = (ex - sx) / length, (ey - sy) / length
        px, py = -dy, dx
        wobble = 1 if int(self.time * 30) % 2 else 0
        add = pygame.BLEND_ADD
        for i in range(length):
            x, y = sx + dx * i, sy + dy * i
            surf.fill(self.colors[0], (int(x), int(y), 1, 1), special_flags=add)
            for side in (-1, 1):
                surf.fill(self.colors[2], (int(x + px * side), int(y + py * side), 1, 1), special_flags=add)
                if self.power:                                 # powered beam is wider
                    surf.fill(self.colors[1 + (self.power == 1)],
                              (int(x + px * side * 2), int(y + py * side * 2), 1, 1),
                              special_flags=add)
                if wobble and i % 3 == 0:
                    surf.fill(self.colors[3], (int(x + px * side * 2), int(y + py * side * 2), 1, 1),
                              special_flags=add)
        pygame.draw.circle(surf, self.colors[1], (int(sx), int(sy)), 1)               # muzzle
        pygame.draw.circle(surf, self.colors[1], (int(ex), int(ey)), 2 + wobble, 1)   # impact ring
