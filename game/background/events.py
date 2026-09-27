"""Event layers: one memorable background effect per level (drawn between the planet and
the stars). Every layer stays dark (<= ~40% brightness) so sprites and bullets pop."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..core.pixelart import dither


class EventLayer:
    def __init__(self, rng):
        self.rng = rng
        self.time = 0.0

    def update(self, dt, world_speed):
        self.time += dt

    def draw(self, surf):
        raise NotImplementedError


class SunCorona(EventLayer):
    """Level 5: a huge dim sun at the right edge with slowly licking corona flares."""

    RADIUS = 78
    CENTER = (LOW_W + 36, 70)

    def __init__(self, rng):
        super().__init__(rng)
        r = self.RADIUS
        self.image = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        tones = [(58, 16, 10), (84, 26, 12), (110, 40, 16), (128, 56, 22)]
        for y in range(2 * r + 1):
            for x in range(2 * r + 1):
                d = math.hypot(x - r, y - r) / r
                if d <= 1:
                    b = 1 - d ** 1.6 + 0.08 * math.sin(x * 0.4 + y * 0.3)
                    self.image.set_at((x, y), tones[dither(b, x, y, len(tones))])
        self.flares = [(rng.uniform(math.pi * 0.5, math.pi * 1.5), rng.uniform(0.5, 1.4),
                        rng.uniform(0, math.tau)) for _ in range(9)]

    def draw(self, surf):
        cx, cy = self.CENTER
        r = self.RADIUS
        for angle, speed, phase in self.flares:          # corona arcs licking out and back
            k = 0.5 + 0.5 * math.sin(self.time * speed + phase)
            length = 8 + 22 * k
            for i in range(int(length)):
                d = r + i
                a = angle + math.sin(i * 0.12 + self.time * speed) * 0.05
                shade = max(0, 90 - i * 3)
                surf.fill((shade, shade // 3, 8), (int(cx + math.cos(a) * d),
                                                   int(cy + math.sin(a) * d), 2, 2))
        surf.blit(self.image, (cx - r, cy - r))
        # heat shimmer: faint moving lines across the screen
        for i in range(3):
            y = int((self.time * 14 + i * 80) % LOW_H)
            surf.fill((10, 4, 2), (0, y, LOW_W, 1), special_flags=pygame.BLEND_ADD)
