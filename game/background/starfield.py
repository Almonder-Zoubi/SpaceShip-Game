"""Parallax starfield."""
import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import STAR_COLORS


class Starfield:
    """Three parallax layers; the nearest layer stretches into streaks when boosting."""

    LAYERS = (  # (count, speed px/s, brightness, streaks)
        (55, 8, 0.45, False),
        (32, 22, 0.75, False),
        (14, 56, 1.0, True),
    )

    def __init__(self, rng):
        self.rng = rng
        self.stars = []   # [x, y, speed, color, streaks, twinkle_phase]
        for count, speed, bright, streaks in self.LAYERS:
            for _ in range(count):
                base = rng.choice(STAR_COLORS)
                color = tuple(int(c * bright) for c in base)
                self.stars.append([rng.uniform(0, LOW_W), rng.uniform(0, LOW_H),
                                   speed * rng.uniform(0.85, 1.15), color, streaks,
                                   rng.uniform(0, 6.28)])
        self.time = 0.0
        self.world_speed = 1.0

    def update(self, dt, world_speed):
        self.time += dt
        self.world_speed = world_speed
        for s in self.stars:
            s[1] += s[2] * world_speed * dt
            if s[1] >= LOW_H:
                s[0], s[1] = self.rng.uniform(0, LOW_W), -2

    def draw(self, surf):
        streak = max(0, int((self.world_speed - 1.05) * 18))
        for x, y, speed, color, streaks, phase in self.stars:
            ix, iy = int(x), int(y)
            if streaks and streak:
                pygame.draw.line(surf, color, (ix, iy - streak), (ix, iy))
            elif not streaks and int(self.time * 3 + phase) % 7 == 0:
                surf.set_at((ix, iy), tuple(c // 2 for c in color))   # twinkle
            else:
                surf.set_at((ix, iy), color)
