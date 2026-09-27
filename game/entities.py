"""Asteroids: falling, spinning, destructible rocks."""
import math
import random

from .settings import LOW_H, LOW_W, ROCK_HP_BASE, ROCK_HP_PER_AREA, ROCK_MIN_FALL

HIT_FLASH = 0.06   # seconds a rock shows white after being hit


class Asteroid:
    """A rock drawn from pre-rendered AsteroidArt frames. Bigger rocks have more hp."""

    def __init__(self, art, x, y, vx, vy, spin):
        self.art = art
        self.x, self.y = float(x), float(y)       # centre
        self.vx, self.vy = vx, vy
        self.angle = random.uniform(0, math.tau)
        self.spin = spin
        self.max_hp = ROCK_HP_BASE + ROCK_HP_PER_AREA * art.radius ** 2
        self.hp = self.max_hp
        self.flash = 0.0

    @property
    def radius(self):
        return self.art.radius

    @property
    def bound(self):
        """Radius of a circle that surely contains the rock (for quick rejects)."""
        return self.art.max_r + 1

    @property
    def frame_index(self):
        return int(self.angle / math.tau * self.art.FRAMES) % self.art.FRAMES

    @property
    def topleft(self):
        half = self.art.size // 2
        return int(self.x) - half, int(self.y) - half

    @property
    def mask(self):
        return self.art.masks[self.frame_index]

    @property
    def offscreen(self):
        size = self.art.size
        return self.y - size > LOW_H or self.x < -size or self.x > LOW_W + size

    @property
    def destroyed(self):
        return self.hp <= 0

    def update(self, dt, world_speed):
        self.x += self.vx * dt
        self.y += self.vy * world_speed * dt
        self.angle = (self.angle + self.spin * dt) % math.tau
        self.flash = max(0.0, self.flash - dt)

    def damage(self, amount, flash=True):
        """Continuous damage (laser) passes flash=False, or the rock would stay white."""
        self.hp -= amount
        if flash:
            self.flash = HIT_FLASH

    def push(self, dx, dy, amount):
        """Knock the rock along (dx, dy); bigger rocks are heavier and move less.

        Shots from below slow the fall, but a rock never stops or flies back up.
        """
        k = amount * 4 / self.radius
        self.vx += dx * k
        self.vy = max(ROCK_MIN_FALL, self.vy + dy * k)

    def contains(self, px, py):
        """Pixel-exact point test (used by bullets and the laser)."""
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        size = self.art.size
        return 0 <= mx < size and 0 <= my < size and self.mask.get_at((mx, my))

    def collides_with(self, ship):
        sx, sy = ship.topleft
        ax, ay = self.topleft
        return ship.mask.overlap(self.mask, (ax - sx, ay - sy)) is not None

    def draw(self, surf):
        if self.flash > 0:
            white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
            surf.blit(white, self.topleft)
        else:
            surf.blit(self.art.frames[self.frame_index], self.topleft)
