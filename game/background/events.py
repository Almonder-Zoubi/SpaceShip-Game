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


class Lightning(EventLayer):
    """Level 6: lightning flickers deep in the nebula now and then."""

    def __init__(self, rng):
        super().__init__(rng)
        self.timer = 2.0
        self.bolt = []                # points of the current bolt
        self.flash = 0.0

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.flash = max(0.0, self.flash - dt)
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.rng.uniform(2.5, 7.0)
            self.flash = 0.25
            x, y = self.rng.uniform(30, LOW_W - 30), 0
            self.bolt = [(x, y)]
            while y < LOW_H * 0.7:
                x += self.rng.uniform(-14, 14)
                y += self.rng.uniform(8, 18)
                self.bolt.append((x, y))

    def draw(self, surf):
        if self.flash <= 0:
            return
        k = self.flash / 0.25
        glow = (int(18 * k), int(30 * k), int(26 * k))
        surf.fill(glow, special_flags=pygame.BLEND_ADD)
        if int(self.flash * 40) % 2 == 0 and len(self.bolt) > 1:
            pygame.draw.lines(surf, (int(90 * k), int(120 * k), int(110 * k)), False, self.bolt, 1)


class CrystalSparkle(EventLayer):
    """Level 7: a faceted crystal moon and glittering star crosses."""

    def __init__(self, rng):
        super().__init__(rng)
        self.moon = pygame.Surface((70, 70), pygame.SRCALPHA)
        facets = [(34, 0), (66, 20), (60, 58), (30, 69), (4, 50), (2, 16)]
        center = (34, 34)
        tones = ((30, 26, 60), (22, 38, 60), (40, 32, 74), (20, 22, 46), (26, 44, 66),
                 (36, 30, 68))
        for i, color in enumerate(tones):
            pygame.draw.polygon(self.moon, color, [center, facets[i], facets[(i + 1) % 6]])
        pygame.draw.polygon(self.moon, (54, 50, 100), facets, 1)
        self.y = 40.0
        self.glints = [[rng.uniform(0, LOW_W), rng.uniform(0, LOW_H), rng.uniform(0, 3)]
                       for _ in range(14)]

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.y += 3 * world_speed * dt
        if self.y > LOW_H + 40:
            self.y = -80.0
        for g in self.glints:
            g[2] += dt
            g[1] += 12 * world_speed * dt
            if g[2] > 3 or g[1] > LOW_H:
                g[:] = [self.rng.uniform(0, LOW_W), self.rng.uniform(0, LOW_H), 0.0]

    def draw(self, surf):
        surf.blit(self.moon, (26, int(self.y)))
        for x, y, t in self.glints:
            k = max(0.0, 1 - abs(t - 1.5) / 1.5)
            if k <= 0:
                continue
            c = (int(120 * k), int(110 * k), int(160 * k))
            size = 1 + int(k * 2)
            surf.fill(c, (int(x) - size, int(y), 2 * size + 1, 1), special_flags=pygame.BLEND_ADD)
            surf.fill(c, (int(x), int(y) - size, 1, 2 * size + 1), special_flags=pygame.BLEND_ADD)


class Wrecks(EventLayer):
    """Level 8: silhouettes of dead battleships drifting past (very dark, two depths)."""

    def __init__(self, rng):
        super().__init__(rng)
        self.shapes = [self._ship(rng, 150, (22, 16, 14)), self._ship(rng, 100, (30, 22, 18)),
                       self._ship(rng, 190, (18, 13, 12))]
        self.wrecks = [[rng.choice(self.shapes), rng.uniform(-60, LOW_W - 40),
                        rng.uniform(-LOW_H, LOW_H), rng.uniform(4, 9)] for _ in range(3)]

    @staticmethod
    def _ship(rng, length, color):
        """A long hull with towers and a broken end, lying at an angle."""
        surf = pygame.Surface((length + 10, length // 2), pygame.SRCALPHA)
        h = length // 7
        y0 = length // 4
        pygame.draw.polygon(surf, color, [(0, y0), (length * 0.15, y0 - h), (length, y0 - h // 2),
                                          (length - 12, y0 + h // 2), (length * 0.2, y0 + h)])
        for i in range(rng.randint(2, 4)):          # towers
            x = rng.uniform(length * 0.3, length * 0.8)
            surf.fill(color, (int(x), y0 - h - rng.randint(4, 12), rng.randint(5, 10), h))
        for i in range(rng.randint(3, 6)):          # holes
            surf.fill((0, 0, 0, 0), (int(rng.uniform(10, length - 10)), y0, 3, 2))
        return pygame.transform.rotate(surf, rng.uniform(-25, 25))

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        for w in self.wrecks:
            w[2] += w[3] * world_speed * dt
            if w[2] > LOW_H:
                w[0] = self.rng.choice(self.shapes)
                w[1], w[2] = self.rng.uniform(-60, LOW_W - 40), -w[0].get_height()

    def draw(self, surf):
        for image, x, y, speed in self.wrecks:
            surf.blit(image, (int(x), int(y)))
