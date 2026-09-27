"""ARC: continuous lightning from the nose to the nearest target ahead, jumping on to more
targets nearby (each jump weaker). One boss counts once: it never chains along a boss."""
import math
import random

import pygame

from ..config.tuning import (ARC_CHAIN, ARC_CONE, ARC_JUMP, ARC_JUMPS, ARC_RANGE, ARC_SHARE)
from .base import Hit, Weapon, is_boss_part

ARC = [(255, 255, 255), (200, 240, 255), (120, 200, 255), (60, 110, 230)]


class Arc(Weapon):
    name = "ARC"

    def __init__(self):
        self.reset()

    def reset(self):
        self.power = 0
        self.active = False
        self.chain = []              # points of the bolt: nose, target, target, ...
        self.time = 0.0
        self.shots = 0

    def _first(self, ship, targets):
        ox, oy = ship.nose()
        fx, fy = ship.forward
        best, pick = ARC_RANGE, None
        for t in targets:
            dx, dy = t.x - ox, t.y - oy
            dist = math.hypot(dx, dy)
            if dist - t.bound > ARC_RANGE or dist < 1:
                continue
            if math.acos(max(-1.0, min(1.0, (dx * fx + dy * fy) / dist))) > ARC_CONE:
                continue
            if dist < best:
                best, pick = dist, t
        return pick

    def update(self, dt, firing, ship, targets, fire):
        self.time += dt
        self.active = firing
        self.chain = []
        if not firing:
            return []
        ox, oy = ship.nose()
        target = self._first(ship, targets)
        self.chain = [(ox, oy)]
        if target is None:                       # fizzles forward
            fx, fy = ship.forward
            self.chain.append((ox + fx * 26, oy + fy * 26))
            return []
        dps = self.loadout.gun_dps * ARC_SHARE * self.rate
        hits, seen, boss_hit = [], set(), False
        for _ in range(1 + ARC_JUMPS + self.power):
            seen.add(id(target))
            boss_hit = boss_hit or is_boss_part(target)
            self.chain.append((target.x, target.y))
            hits.append(Hit(target, dps * dt, target.x, target.y, 0, -1, 10 * dt,
                            continuous=True))
            if random.random() < 0.3:
                fire.emit(target.x, target.y, random.uniform(-50, 50), random.uniform(-50, 50),
                          0.12, ARC)
            dps *= ARC_JUMP
            target = min((t for t in targets if id(t) not in seen
                          and not (boss_hit and is_boss_part(t))
                          and math.hypot(t.x - target.x, t.y - target.y) < ARC_CHAIN + t.bound),
                         key=lambda t: math.hypot(t.x - target.x, t.y - target.y), default=None)
            if target is None:
                break
        return hits

    def draw(self, surf):
        if len(self.chain) < 2:
            return
        add = pygame.BLEND_ADD
        for (x0, y0), (x1, y1) in zip(self.chain, self.chain[1:]):
            points = [(x0, y0)]
            steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / 7))
            for i in range(1, steps):
                k = i / steps
                points.append((x0 + (x1 - x0) * k + random.uniform(-3, 3),
                               y0 + (y1 - y0) * k + random.uniform(-3, 3)))
            points.append((x1, y1))
            pygame.draw.lines(surf, ARC[3], False, points, 3)
            pygame.draw.lines(surf, ARC[1], False, points, 1)
            for x, y in points[1:-1:2]:
                surf.fill(ARC[0], (int(x), int(y), 1, 1), special_flags=add)
