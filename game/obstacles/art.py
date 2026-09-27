"""Procedural asteroid art: lumpy silhouettes, sphere lighting, craters, rotation frames."""
import math

import pygame

from ..config.display import LIGHT_DIR
from ..config.palette import ROCK_PALETTES
from ..core.pixelart import ValueNoise, dither, normalise


class AsteroidArt:
    """One procedurally generated rock, pre-rendered in several rotation steps.

    The silhouette is a circle distorted by a few sine harmonics; lighting treats
    each pixel as lying on a sphere, plus surface noise and craters. The light stays
    fixed (upper left) while the rock turns, so rotation looks correct.
    """

    FRAMES = 24

    def __init__(self, radius, palette_name, rng, lazy=False):
        """lazy: render the rotation frames later, one per render_step() call."""
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
        self.frames, self.masks = [], []
        while not lazy and not self.ready:
            self.render_step()

    @property
    def ready(self):
        return len(self.frames) == self.FRAMES

    def render_step(self):
        """Render the next rotation frame (a few ms)."""
        frame = self._render(math.tau * len(self.frames) / self.FRAMES)
        self.frames.append(frame)
        self.masks.append(pygame.mask.from_surface(frame))

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
        self.variants = []   # list of AsteroidArt (only finished ones are picked)
        self.pending = []    # rocks queued to be built a frame at a time (see build_step)

    def prebuild(self, radii, palettes):
        for i, r in enumerate(radii):
            self.variants.append(AsteroidArt(r, palettes[i % len(palettes)], self.rng))

    def queue(self, radii, palettes):
        """Rocks to build in the background (menus call build_step every frame)."""
        for i, r in enumerate(radii):
            self.pending.append(AsteroidArt(r, palettes[i % len(palettes)], self.rng, lazy=True))

    def build_step(self, frames=1):
        """Render a few frames of the queued rocks; finished ones join the library."""
        for _ in range(frames):
            if not self.pending:
                return
            art = self.pending[0]
            art.render_step()
            if art.ready:
                self.variants.append(self.pending.pop(0))

    def finish(self):
        while self.pending:
            self.build_step()

    def pick(self, radius_min, radius_max, palettes):
        """A random prebuilt rock in the radius range and palettes; if there is none in that
        range, the closest size in those palettes (building a rock mid-game would hitch)."""
        matches = [v for v in self.variants
                   if radius_min <= v.radius <= radius_max
                   and v.palette_name in palettes]
        if not matches:
            near = [v for v in self.variants if v.palette_name in palettes]
            if near:
                mid = (radius_min + radius_max) / 2
                best = min(abs(v.radius - mid) for v in near)
                return self.rng.choice([v for v in near if abs(v.radius - mid) == best])
            art = AsteroidArt(self.rng.randint(radius_min, radius_max),
                              self.rng.choice(palettes), self.rng)
            self.variants.append(art)
            return art
        return self.rng.choice(matches)
