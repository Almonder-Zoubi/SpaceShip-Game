"""All game art, generated in code: ship frames and procedural asteroids."""
import math

import pygame

from .pixelart import CharCanvas, ValueNoise, dither, normalise, sprite_from_rows
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


def build_ship_tilts(max_degrees, steps):
    """Leaning frames for diagonal flight: index 0 = most left ('\\'), last = most right ('/')."""
    angles = [max_degrees * i / steps for i in range(-steps, steps + 1)]
    return [rotate_pixel_art(SHIP_ROWS, SHIP_COLORS, a) for a in angles]


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
        self.palette_name = palette_name
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
                   and v.palette_name in palettes]
        if not matches:
            art = AsteroidArt(self.rng.randint(radius_min, radius_max),
                              self.rng.choice(palettes), self.rng)
            self.variants.append(art)
            return art
        return self.rng.choice(matches)


def ship_icon(ship):
    """32x32 window icon made from a ship frame."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    icon.blit(ship, ((32 - ship.get_width()) // 2, (32 - ship.get_height()) // 2))
    return icon



# --- Bosses ------------------------------------------------------------------
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


# Boss 1 "GUNSHIP": heavy armoured gunship flying nose-down towards the player.
# Drawn as the left half on a CharCanvas, then mirrored and outlined (70x48 px).
GUNSHIP_HALF_W, GUNSHIP_HALF_H = 34, 46
# Muzzles in final-sprite pixels (after mirror + outline): main cannon, left & right turrets.
GUNSHIP_MUZZLES = {"main": (34, 47), "left": (8, 39), "right": (61, 39)}
# Engine vents (for exhaust particles) in final-sprite pixels.
GUNSHIP_VENTS = ((22, 1), (47, 1))


def _gunship_half():
    c = CharCanvas(GUNSHIP_HALF_W, GUNSHIP_HALF_H)
    # Swept wing with a lit leading edge, shadowed trailing edge, red stripe and panel seams.
    c.poly([(25, 12), (1, 23), (1, 28), (25, 31)], "M")
    c.line(25, 12, 1, 23, "W")
    c.line(25, 13, 1, 24, "L")
    c.line(25, 31, 1, 28, "H")
    c.line(25, 17, 3, 25, "E")
    c.line(25, 18, 3, 26, "e")
    for x in (11, 18):
        c.line(x, 13 + (25 - x) // 2 + 3, x, 28, "H")
    c.set(1, 23, "E")                                   # wing-tip light
    # Engine nacelle with intake and glowing vents on top.
    c.rect(17, 0, 25, 14, "M")
    c.line(17, 0, 17, 14, "H")
    c.line(18, 1, 18, 13, "L")
    c.rect(19, 0, 24, 0, "V")
    c.rect(19, 1, 24, 1, "y")
    c.rect(19, 4, 23, 9, "H")
    c.rect(20, 5, 22, 8, "G")
    # Fuselage: rounded top, lit centre, armour seams, rivets, red emblem.
    c.rect(26, 3, 33, 36, "L")
    c.rect(29, 2, 33, 2, "L")
    c.line(26, 3, 26, 36, "H")
    c.line(27, 3, 27, 36, "M")
    c.rect(30, 2, 33, 4, "W")
    for y in (11, 19):
        c.line(27, y, 33, y, "H")
    for y in (7, 15, 23):
        c.set(29, y, "W")
    c.rect(32, 13, 33, 16, "E")
    c.set(31, 14, "E")
    c.set(31, 15, "e")
    # Glowing cockpit near the nose.
    c.rect(29, 25, 33, 32, "G")
    c.rect(30, 26, 33, 31, "Y")
    c.line(30, 26, 30, 31, "y")
    c.rect(32, 27, 33, 27, "W")
    # Nose taper and main cannon.
    c.poly([(26, 36), (34, 36), (34, 44), (30, 44)], "M")
    c.line(27, 37, 30, 43, "H")
    c.rect(32, 37, 33, 45, "G")
    c.rect(33, 38, 33, 44, "g")
    # Wing turret with barrel.
    c.circle(7, 27, 4, "H")
    c.circle(7, 27, 3, "M")
    c.circle(7, 26, 1, "E")
    c.rect(6, 30, 8, 37, "G")
    c.line(7, 31, 7, 37, "g")
    return c.rows()


GUNSHIP_COLORS = {
    "K": (18, 14, 30),
    "H": (52, 56, 78),
    "M": (88, 94, 118),
    "L": (136, 142, 164),
    "W": (196, 202, 218),
    "E": (206, 44, 62),
    "e": (122, 22, 46),
    "Y": (255, 214, 96),
    "y": (220, 120, 36),
    "G": (40, 40, 56),
    "g": (104, 104, 126),
    "V": (255, 110, 50),
}


def build_gunship():
    return sprite_from_rows(outlined(mirrored(_gunship_half())), GUNSHIP_COLORS)
