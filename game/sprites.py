"""All game art, generated in code: ship frames and procedural asteroids."""
import math

import pygame

from .pixelart import ValueNoise, dither, normalise, sprite_from_rows
from .settings import LIGHT_DIR, ROCK_PALETTES, SHIP_COLORS

# --- Ship --------------------------------------------------------------------
# 17x25 rocket, lit from the upper left: tapered red nose cone, gold band,
# porthole, hull panel seam, swept fins and twin engine bells.
SHIP_ROWS = (
    "........K........",
    ".......KPK.......",
    "......KPRrK......",
    "......KPRrK......",
    ".....KPRRRrK.....",
    ".....KPRRRrK.....",
    "....KPRRRRRrK....",
    "....KRRRRRRrK....",
    "....KYYYYYyyK....",
    "....KWLLLLLGK....",
    "....KWLKKKLGK....",
    "....KWKCBbKGK....",
    "....KWKBBbKGK....",
    "....KWKbbbKGK....",
    "....KWLKKKLGK....",
    "....KWLLLLLGK....",
    "..KRKWLLDLLGKrK..",
    ".KPRKWLLDLLGKRrK.",
    "KPRRKWLLDLLGKRRrK",
    "KPRRKWLLDLLGKRRrK",
    "KRRrKLLLDLLDKRrrK",
    "KRrrKDDDDDDDKrrrK",
    "KKKKKKKKKKKKKKKKK",
    ".....KOK.KOK.....",
    "....KOOOKOOOK....",
)
# Nozzle centres relative to the sprite's horizontal centre, and flame start row.
NOZZLE_OFFSETS = (-2, 2)
NOZZLE_ROW = len(SHIP_ROWS)


def _bank_rows(rows, direction):
    """Fake a roll: foreshorten the fin on the side we turn towards (-1 left, 1 right)."""
    out = []
    for row in rows:
        chars = list(row if direction < 0 else row[::-1])
        if chars[0] != ".":
            chars[0] = "."
            if chars[1] != ".":
                chars[1] = "K"
        # The far fin rotates into the light.
        for i in range(len(chars) - 3, len(chars)):
            if chars[i] == "r":
                chars[i] = "R"
        row = "".join(chars)
        out.append(row if direction < 0 else row[::-1])
    return out


def build_ship_frames():
    """Return {-1: bank left, 0: level, 1: bank right} surfaces."""
    return {
        -1: sprite_from_rows(_bank_rows(SHIP_ROWS, -1), SHIP_COLORS),
        0: sprite_from_rows(SHIP_ROWS, SHIP_COLORS),
        1: sprite_from_rows(_bank_rows(SHIP_ROWS, 1), SHIP_COLORS),
    }


# --- Asteroids ---------------------------------------------------------------
class AsteroidArt:
    """One procedurally generated rock, pre-rendered in several rotation steps.

    The silhouette is a circle distorted by a few sine harmonics; lighting treats
    each pixel as lying on a sphere, plus surface noise and craters. The light stays
    fixed (upper left) while the rock turns, so rotation looks correct.
    """

    FRAMES = 24

    def __init__(self, radius, palette_name, rng):
        self.radius = radius
        self.palette = ROCK_PALETTES[palette_name]
        self.harmonics = [
            (k, rng.uniform(0.02, amp), rng.uniform(0, math.tau))
            for k, amp in ((2, 0.12), (3, 0.10), (5, 0.06), (7, 0.04))
        ]
        self.max_r = radius * (1 + sum(a for _, a, _ in self.harmonics))
        self.size = 2 * math.ceil(self.max_r) + 3
        self.noise = ValueNoise(rng, cell=3.5)
        self.craters = []
        for _ in range(1 + radius // 4 + rng.randint(0, 1)):
            ang, dist = rng.uniform(0, math.tau), rng.uniform(0, 0.62) * radius
            cr = max(1.5, rng.uniform(0.18, 0.36) * radius)
            self.craters.append((math.cos(ang) * dist, math.sin(ang) * dist, cr))
        self.frames = [self._render(math.tau * i / self.FRAMES) for i in range(self.FRAMES)]
        self.masks = [pygame.mask.from_surface(f) for f in self.frames]

    def _radius_at(self, theta):
        return self.radius * (1 + sum(a * math.sin(k * theta + p) for k, a, p in self.harmonics))

    def _render(self, rot):
        size, c = self.size, self.size / 2
        lx, ly, lz = normalise(LIGHT_DIR)
        cos_r, sin_r = math.cos(-rot), math.sin(-rot)
        # Light direction expressed in the rock's own (rotating) frame, 2D only.
        llx, lly = normalise((lx * cos_r - ly * sin_r, lx * sin_r + ly * cos_r))
        tones = len(self.palette) - 1
        grid = [[None] * size for _ in range(size)]

        for py in range(size):
            dy = py + 0.5 - c
            for px in range(size):
                dx = px + 0.5 - c
                d = math.hypot(dx, dy)
                if d > self.max_r:
                    continue
                ox, oy = dx * cos_r - dy * sin_r, dx * sin_r + dy * cos_r   # local coords
                rr = self._radius_at(math.atan2(oy, ox))
                if d > rr:
                    continue
                nx, ny = dx / (rr + 0.8), dy / (rr + 0.8)
                nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
                lam = max(0.0, nx * lx + ny * ly + nz * lz)
                b = 0.02 + 1.05 * lam ** 1.4          # hard terminator, dark night side
                b += (self.noise.sample(ox + 40, oy + 40) - 0.5) * 0.18
                for cx, cy, cr in self.craters:
                    ex, ey = ox - cx, oy - cy
                    e2 = ex * ex + ey * ey
                    if e2 < cr * cr:
                        # Wall nearest the light is in shadow, far wall is lit.
                        s = (ex * llx + ey * lly) / cr
                        b += -0.22 - 0.55 * s
                    elif e2 < (cr + 1.2) ** 2 and (ex * llx + ey * lly) > 0.3 * cr:
                        b += 0.22     # outer rim slope facing the light
                grid[py][px] = 1 + dither(b, px, py, tones, spread=0.45)

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for py in range(size):
            for px in range(size):
                tone = grid[py][px]
                if tone is None:
                    continue
                edge = any(
                    not (0 <= px + ax < size and 0 <= py + ay < size) or grid[py + ay][px + ax] is None
                    for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                surf.set_at((px, py), self.palette[0] if edge else self.palette[tone])
        return surf


class AsteroidLibrary:
    """Cache of AsteroidArt variants, looked up by radius range and palette."""

    def __init__(self, rng):
        self.rng = rng
        self.variants = []   # list of AsteroidArt

    def prebuild(self, radii, palettes):
        for i, r in enumerate(radii):
            self.variants.append(AsteroidArt(r, palettes[i % len(palettes)], self.rng))

    def pick(self, radius_min, radius_max, palettes):
        matches = [v for v in self.variants
                   if radius_min <= v.radius <= radius_max
                   and any(ROCK_PALETTES[p] is v.palette for p in palettes)]
        if not matches:
            art = AsteroidArt(self.rng.randint(radius_min, radius_max),
                              self.rng.choice(palettes), self.rng)
            self.variants.append(art)
            return art
        return self.rng.choice(matches)


def ship_icon(frames):
    """32x32 window icon made from the level ship frame."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    ship = frames[0]
    icon.blit(ship, ((32 - ship.get_width()) // 2, (32 - ship.get_height()) // 2))
    return icon

