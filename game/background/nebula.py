"""Seamless tiling cloud layer."""
import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import NEBULA, SPACE
from ..core.pixelart import ValueNoise, dither, opaque_surface


class Nebula:
    """Seamless tiling cloud layer, rendered at half resolution for chunky dithering."""

    SPEED = 4  # px/s

    def __init__(self, rng, colors=NEBULA):
        w, h = LOW_W // 2, LOW_H // 2
        low = opaque_surface((w, h))
        low.fill(SPACE)
        # Noise periods divide the (4:3) tile exactly so it wraps without a seam.
        big = ValueNoise(rng, cell=w / 4, period_x=4, period_y=3)
        small = ValueNoise(rng, cell=w / 16, period_x=16, period_y=12)
        for y in range(h):
            for x in range(w):
                v = big.sample(x, y) * 0.7 + small.sample(x, y) * 0.3
                v = (v - 0.52) * 2.6          # only the dense parts show
                if v > 0:
                    low.set_at((x, y), colors[dither(v, x, y, len(colors))])
        self.tile = pygame.transform.scale(low, (LOW_W, LOW_H))
        self.offset = 0.0

    def update(self, dt, world_speed):
        self.offset = (self.offset + self.SPEED * world_speed * dt) % LOW_H

    def draw(self, surf):
        y = int(self.offset)
        surf.blit(self.tile, (0, y))
        surf.blit(self.tile, (0, y - LOW_H))
