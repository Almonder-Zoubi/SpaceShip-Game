"""Small helpers for building pixel art in code (shared by every sprite module)."""
import math

import pygame

from ..config.display import LIGHT_DIR

# 4x4 ordered-dither matrix (classic Bayer) used for retro shading.
BAYER4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def opaque_surface(size):
    """Surface with no alpha channel at all.

    A plain pygame.Surface copies the display format, which on macOS includes an
    alpha channel. Blitting SRCALPHA sprites onto such a surface writes alpha 0 in
    their transparent areas, and the window then shows black boxes around sprites.
    """
    return pygame.Surface(size, 0, 32, (0xFF0000, 0x00FF00, 0x0000FF, 0))


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
    surf = opaque_surface((size, size))
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


class CharCanvas:
    """A grid of palette characters to draw pixel art with shapes ('.' = empty).

    Used for large sprites (bosses) where typing every row by hand gets impractical.
    """

    def __init__(self, width, height):
        self.w, self.h = width, height
        self.grid = [["."] * width for _ in range(height)]

    def set(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = ch

    def rect(self, x0, y0, x1, y1, ch):
        """Filled rectangle, corners inclusive."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, ch)

    def line(self, x0, y0, x1, y1, ch):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            self.set(round(x0 + (x1 - x0) * i / steps), round(y0 + (y1 - y0) * i / steps), ch)

    def poly(self, points, ch):
        """Filled polygon (scanline, pixel centres)."""
        ys = [p[1] for p in points]
        for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
            cy = y + 0.5
            xs = []
            for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
                if (ay <= cy < by) or (by <= cy < ay):
                    xs.append(ax + (cy - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for xa, xb in zip(xs[::2], xs[1::2]):
                for x in range(math.ceil(xa - 0.5), math.floor(xb - 0.5) + 1):
                    self.set(x, y, ch)

    def circle(self, cx, cy, r, ch):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r * 0.8:
                    self.set(x, y, ch)

    def rows(self):
        return ["".join(r) for r in self.grid]


# --- Building big sprites from character rows ----------------------------------
def mirrored(half_rows):
    """Left half -> symmetric sprite (the half's last column touches the centre line)."""
    return [row + row[::-1] for row in half_rows]


def outlined(rows, ink="K"):
    """Add a 1px outline around the silhouette (grows the sprite by 1px on every side)."""
    w, h = len(rows[0]) + 2, len(rows) + 2
    grid = [["."] * w for _ in range(h)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            grid[y + 1][x + 1] = ch
    for y in range(h):
        for x in range(w):
            if grid[y][x] != ".":
                continue
            if any(0 <= y + dy < h and 0 <= x + dx < w and grid[y + dy][x + dx] not in (".", ink)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                grid[y][x] = ink
    return ["".join(r) for r in grid]


def _scale2x(rows):
    """One pass of the Scale2x (EPX) pixel-art upscaler on character rows."""
    h, w = len(rows), len(rows[0])
    out = [[""] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            p = rows[y][x]
            a = rows[y - 1][x] if y > 0 else p
            b = rows[y][x + 1] if x < w - 1 else p
            c = rows[y][x - 1] if x > 0 else p
            d = rows[y + 1][x] if y < h - 1 else p
            out[2 * y][2 * x] = a if c == a and c != d and a != b else p
            out[2 * y][2 * x + 1] = b if a == b and a != c and b != d else p
            out[2 * y + 1][2 * x] = c if d == c and d != b and c != a else p
            out[2 * y + 1][2 * x + 1] = d if b == d and b != a and d != c else p
    return ["".join(r) for r in out]


def rotate_pixel_art(rows, colors, degrees):
    """RotSprite-style rotation (clockwise): Scale2x three times, rotate, sample back down.

    Rotating the 8x version and picking the centre of each 8x8 block keeps lines
    clean, instead of the ragged holes you get rotating pixel art directly.
    """
    big_rows = rows
    for _ in range(3):
        big_rows = _scale2x(big_rows)
    rot = pygame.transform.rotate(sprite_from_rows(big_rows, colors), -degrees)
    rw, rh = rot.get_size()
    ow, oh = math.ceil(rw / 8), math.ceil(rh / 8)
    out = pygame.Surface((ow, oh), pygame.SRCALPHA)
    for oy in range(oh):
        sy = int(rh / 2 + (oy - oh / 2 + 0.5) * 8)
        for ox in range(ow):
            sx = int(rw / 2 + (ox - ow / 2 + 0.5) * 8)
            if 0 <= sx < rw and 0 <= sy < rh:
                px = rot.get_at((sx, sy))
                if px.a > 127:
                    out.set_at((ox, oy), px)
    return out


def window_icon(sprite):
    """32x32 window icon with the sprite centred."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    icon.blit(sprite, ((32 - sprite.get_width()) // 2, (32 - sprite.get_height()) // 2))
    return icon
