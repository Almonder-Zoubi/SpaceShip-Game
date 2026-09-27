"""Small helpers for building pixel art in code."""
import math

import pygame

# 4x4 ordered-dither matrix (classic Bayer) used for retro shading.
BAYER4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def sprite_from_rows(rows, colors):
    """Build a Surface from equal-length strings; '.' is transparent."""
    width = len(rows[0])
    assert all(len(r) == width for r in rows), "sprite rows must be equal length"
    surf = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), colors[ch])
    return surf


def dither(value, x, y, levels, spread=1.0):
    """Quantise value (0..1) to 0..levels-1 using ordered dithering at pixel (x, y).

    spread < 1 keeps flat colour bands and only dithers near the band edges.
    """
    value = min(1.0, max(0.0, value)) * (levels - 1)
    base = int(value)
    threshold = 0.5 + ((BAYER4[y & 3][x & 3] + 0.5) / 16 - 0.5) * spread
    return min(levels - 1, base + (1 if value - base > threshold else 0))


def lerp(a, b, t):
    return a + (b - a) * t


def normalise(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v)


def ramp(colors, t):
    """Pick a colour from a list by t in 0..1 (no blending — keeps the palette)."""
    return colors[min(len(colors) - 1, max(0, int(t * len(colors))))]


class ValueNoise:
    """Smooth 2D value noise. With a period it tiles seamlessly."""

    def __init__(self, rng, cell, period_x=16, period_y=16):
        self.cell = cell
        self.px, self.py = period_x, period_y
        self.grid = [[rng.random() for _ in range(period_x)] for _ in range(period_y)]

    def sample(self, x, y):
        fx, fy = x / self.cell, y / self.cell
        ix, iy = math.floor(fx), math.floor(fy)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        g = self.grid
        x0, x1 = ix % self.px, (ix + 1) % self.px
        y0, y1 = iy % self.py, (iy + 1) % self.py
        top = lerp(g[y0][x0], g[y0][x1], tx)
        bottom = lerp(g[y1][x0], g[y1][x1], tx)
        return lerp(top, bottom, ty)


def make_glow(radius, color, strength=1.0):
    """Radial glow for additive blending (black = no contribution)."""
    size = radius * 2 + 1
    surf = pygame.Surface((size, size))
    surf.fill((0, 0, 0))
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - radius, y - radius) / radius
            if d < 1:
                k = (1 - d) ** 2 * strength
                surf.set_at((x, y), tuple(int(c * k) for c in color))
    return surf


def shaded_sphere(radius, palette, rng, bands=0.0):
    """Dithered sphere lit from the upper left; optional horizontal bands (gas giant)."""
    from .settings import LIGHT_DIR
    lx, ly, lz = normalise(LIGHT_DIR)
    size = radius * 2 + 1
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    noise = ValueNoise(rng, cell=max(3, radius // 3))
    phase = rng.uniform(0, math.tau)
    levels = len(palette)
    for y in range(size):
        for x in range(size):
            nx, ny = (x - radius) / radius, (y - radius) / radius
            d2 = nx * nx + ny * ny
            if d2 > 1:
                continue
            nz = math.sqrt(1 - d2)
            b = max(0.0, nx * lx + ny * ly + nz * lz)
            if bands:
                b += bands * math.sin(ny * 9 + noise.sample(x, y) * 3 + phase)
            surf.set_at((x, y), palette[dither(b * 0.95, x, y, levels)])
    return surf
