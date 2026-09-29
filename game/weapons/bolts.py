"""Small straight shots (wingmen, side cannons): a list of bolts that return Hits."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import TRACER
from .base import Hit


class Bolts:
    """Straight small shots of a wingman; hits carry the wingman as their source."""

    def __init__(self, colors=TRACER):
        self.colors = colors
        self.shots = []                 # [x, y, vx, vy, damage]

    def fire(self, x, y, angle, speed, damage):
        self.shots.append([x, y, math.sin(angle) * speed, -math.cos(angle) * speed, damage])

    def update(self, dt, targets, source):
        hits, alive = [], []
        for s in self.shots:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            hit = next((t for t in targets if abs(s[0] - t.x) < t.bound
                        and abs(s[1] - t.y) < t.bound and t.contains(s[0], s[1])), None)
            if hit:
                speed = math.hypot(s[2], s[3]) or 1
                hits.append(Hit(hit, s[4], s[0], s[1], s[2] / speed, s[3] / speed, 20,
                                source=source))
            elif -6 < s[0] < LOW_W + 6 and -6 < s[1] < LOW_H + 6:
                alive.append(s)
        self.shots = alive
        return hits

    def clear(self):
        self.shots.clear()

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for x, y, vx, vy, _ in self.shots:
            speed = math.hypot(vx, vy) or 1
            surf.fill(self.colors[0], (int(x), int(y), 1, 2), special_flags=add)
            surf.fill(self.colors[2], (int(x - vx / speed * 2), int(y - vy / speed * 2), 1, 1),
                      special_flags=add)
