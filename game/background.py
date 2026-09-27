"""Scrolling space backdrop: dithered nebula, a drifting planet and parallax stars."""
import random

import pygame

from .pixelart import ValueNoise, dither, shaded_sphere
from .settings import LOW_H, LOW_W, NEBULA, PLANET_PALETTES, SPACE, STAR_COLORS


class Nebula:
    """Seamless tiling cloud layer, rendered at half resolution for chunky dithering."""

    SPEED = 4  # px/s

    def __init__(self, rng):
        w, h = LOW_W // 2, LOW_H // 2
        low = pygame.Surface((w, h))
        low.fill(SPACE)
        # Noise periods divide the (4:3) tile exactly so it wraps without a seam.
        big = ValueNoise(rng, cell=w / 4, period_x=4, period_y=3)
        small = ValueNoise(rng, cell=w / 16, period_x=16, period_y=12)
        for y in range(h):
            for x in range(w):
                v = big.sample(x, y) * 0.7 + small.sample(x, y) * 0.3
                v = (v - 0.52) * 2.6          # only the dense parts show
                if v > 0:
                    low.set_at((x, y), NEBULA[dither(v, x, y, len(NEBULA))])
        self.tile = pygame.transform.scale(low, (LOW_W, LOW_H))
        self.offset = 0.0

    def update(self, dt, world_speed):
        self.offset = (self.offset + self.SPEED * world_speed * dt) % LOW_H

    def draw(self, surf):
        y = int(self.offset)
        surf.blit(self.tile, (0, y))
        surf.blit(self.tile, (0, y - LOW_H))


class Planet:
    """A distant planet that drifts past slowly, then respawns with a new look."""

    SPEED = 6

    def __init__(self, rng):
        self.rng = rng
        self._spawn(initial=True)

    def _spawn(self, initial=False):
        r = self.rng.randint(10, 22)
        palette = self.rng.choice(PLANET_PALETTES)
        self.image = shaded_sphere(r, palette, self.rng, bands=self.rng.choice((0.0, 0.18, 0.28)))
        self.x = self.rng.randint(20, LOW_W - 20 - 2 * r)
        self.y = self.rng.randint(10, LOW_H // 2) if initial else -2 * r - self.rng.randint(40, 400)

    def update(self, dt, world_speed):
        self.y += self.SPEED * world_speed * dt
        if self.y > LOW_H:
            self._spawn()

    def draw(self, surf):
        surf.blit(self.image, (self.x, int(self.y)))


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


class Background:
    def __init__(self, rng=None):
        rng = rng or random.Random()
        self.nebula = Nebula(rng)
        self.planet = Planet(rng)
        self.stars = Starfield(rng)

    def update(self, dt, world_speed):
        self.nebula.update(dt, world_speed)
        self.planet.update(dt, world_speed)
        self.stars.update(dt, world_speed)

    def draw(self, surf):
        self.nebula.draw(surf)
        self.planet.draw(surf)
        self.stars.draw(surf)
