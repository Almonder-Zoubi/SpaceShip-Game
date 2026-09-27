"""PLASMA: slow, big orbs that pierce several targets (a boss stops them)."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import (PLASMA_INTERVAL, PLASMA_PIERCE, PLASMA_POWER_BONUS, PLASMA_SPEED)
from .base import Hit, Weapon, is_boss_part

PLASMA = [(255, 255, 255), (220, 170, 255), (160, 90, 255), (80, 40, 170)]


class Orb:
    __slots__ = ("x", "y", "vx", "vy", "left", "hit", "time")

    def __init__(self, x, y, vx, vy, pierce):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.left = pierce          # targets it can still go through
        self.hit = set()            # ids of targets already hit
        self.time = random.uniform(0, 5)


class Plasma(Weapon):
    name = "PLASMA"
    sound = "plasma"

    def __init__(self):
        self.orbs = []
        self.reset()

    def reset(self):
        self.orbs.clear()
        self.cooldown = 0.0
        self.shots = 0
        self.power = 0

    @property
    def orb_damage(self):
        return (self.loadout.gun_dps * PLASMA_INTERVAL * (1 + PLASMA_POWER_BONUS * self.power))

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = PLASMA_INTERVAL / self.rate
            self.shots += 1
            ox, oy = ship.nose()
            fx, fy = ship.forward
            self.orbs.append(Orb(ox, oy, fx * PLASMA_SPEED + ship.vx * 0.3,
                                 fy * PLASMA_SPEED + ship.vy * 0.3, PLASMA_PIERCE))
            fire.burst(ox, oy, 5, 40, 0.12, PLASMA, size=(1, 1))
        return self._move(dt, targets, fire)

    def _move(self, dt, targets, fire):
        hits, alive = [], []
        for o in self.orbs:
            o.time += dt
            o.x += o.vx * dt
            o.y += o.vy * dt
            for t in targets:
                if id(t) in o.hit or abs(o.x - t.x) > t.bound + 2 or abs(o.y - t.y) > t.bound + 2:
                    continue
                if t.contains(o.x, o.y):
                    o.hit.add(id(t))
                    speed = math.hypot(o.vx, o.vy) or 1
                    hits.append(Hit(t, self.orb_damage, o.x, o.y, o.vx / speed, o.vy / speed, 90))
                    fire.burst(o.x, o.y, 6, 50, 0.2, PLASMA, size=(1, 1))
                    o.left = 0 if is_boss_part(t) else o.left - 1   # a boss soaks it up
                    if o.left <= 0:
                        break
            if o.left > 0 and -8 < o.x < LOW_W + 8 and -8 < o.y < LOW_H + 8:
                alive.append(o)
        self.orbs = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for o in self.orbs:
            r = 3 + (self.power > 0) + (int(o.time * 20) % 2)
            pygame.draw.circle(surf, PLASMA[3], (int(o.x), int(o.y)), r + 1)
            pygame.draw.circle(surf, PLASMA[2], (int(o.x), int(o.y)), r)
            surf.fill(PLASMA[0], (int(o.x) - 1, int(o.y) - 1, 2, 2), special_flags=add)
