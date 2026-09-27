"""SCATTER: a shotgun fan of short-lived pellets, strongest up close."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import SPARK
from ..config.tuning import (GUN_PUSH, SCATTER_INTERVAL, SCATTER_PELLETS, SCATTER_RANGE,
                             SCATTER_SPEED, SCATTER_SPREAD)
from .base import Hit, Weapon

PELLET = [(255, 255, 255), (255, 214, 120), (255, 140, 60)]


class Scatter(Weapon):
    name = "SCATTER"
    sound = "scatter"

    def __init__(self):
        self.pellets = []            # [x, y, vx, vy, life]
        self.reset()

    def reset(self):
        self.pellets.clear()
        self.cooldown = 0.0
        self.shots = 0
        self.power = 0

    @property
    def pellet_damage(self):
        """One shot of 5 pellets = the gun's damage over the same time."""
        return self.loadout.gun_dps * SCATTER_INTERVAL / SCATTER_PELLETS

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = SCATTER_INTERVAL / self.rate
            self._blast(ship, fire)
        return self._move(dt, targets)

    def _blast(self, ship, fire):
        self.shots += 1
        count = SCATTER_PELLETS + 2 * self.power
        ox, oy = ship.nose()
        for i in range(count):
            off = (i / (count - 1) - 0.5) * SCATTER_SPREAD + random.uniform(-0.03, 0.03)
            a = ship.angle + off
            speed = SCATTER_SPEED * random.uniform(0.9, 1.1)
            self.pellets.append([ox, oy, math.sin(a) * speed + ship.vx,
                                 -math.cos(a) * speed + ship.vy, SCATTER_RANGE])
        fx, fy = ship.forward
        fire.burst(ox + fx * 2, oy + fy * 2, 6, 60, 0.08, SPARK, size=(1, 1))

    def _move(self, dt, targets):
        hits, alive = [], []
        for p in self.pellets:
            p[4] -= dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            target = next((t for t in targets if abs(p[0] - t.x) < t.bound
                           and abs(p[1] - t.y) < t.bound and t.contains(p[0], p[1])), None)
            if target:
                speed = math.hypot(p[2], p[3]) or 1
                hits.append(Hit(target, self.pellet_damage, p[0], p[1], p[2] / speed,
                                p[3] / speed, GUN_PUSH))
            elif p[4] > 0 and -4 < p[0] < LOW_W + 4 and -4 < p[1] < LOW_H + 4:
                alive.append(p)
        self.pellets = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for x, y, vx, vy, life in self.pellets:
            color = PELLET[0 if life > SCATTER_RANGE * 0.6 else 1 if life > 0.1 else 2]
            surf.fill(color, (int(x), int(y), 2, 2), special_flags=add)
