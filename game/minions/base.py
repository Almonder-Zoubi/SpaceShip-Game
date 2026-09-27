"""Base class for small enemy ships."""
import pygame

from ..config.display import LOW_H, LOW_W


class Enemy:
    """Base for small enemy ships. Same target interface as asteroids and bosses:
    x, y, bound, contains(), damage(). Subclasses implement move() and attack()."""

    hit_flash = 0.06
    points = 0
    contact_damage = 0

    def __init__(self, image, x, y, hp):
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.w, self.h = image.get_size()
        self.x, self.y = float(x), float(y)
        self.max_hp = self.hp = hp
        self.flash = 0.0
        self.time = 0.0

    @property
    def bound(self):
        return max(self.w, self.h) / 2 + 1

    @property
    def topleft(self):
        return int(self.x - self.w / 2), int(self.y - self.h / 2)

    @property
    def destroyed(self):
        return self.hp <= 0

    @property
    def offscreen(self):
        return self.y - self.h > LOW_H or not -40 < self.x < LOW_W + 40

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        return 0 <= mx < self.w and 0 <= my < self.h and self.mask.get_at((mx, my))

    def collides_with(self, ship):
        sx, sy = ship.topleft
        ex, ey = self.topleft
        return ship.mask.overlap(self.mask, (ex - sx, ey - sy)) is not None

    def damage(self, amount, flash=True):
        self.hp -= amount
        if flash:
            self.flash = self.hit_flash

    def update(self, dt, world):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        self.move(dt, world)
        if 0 < self.y < LOW_H * 0.7:          # only shoot while well on screen
            self.attack(dt, world)

    def move(self, dt, world):
        raise NotImplementedError

    def attack(self, dt, world):
        raise NotImplementedError

    def draw(self, surf):
        surf.blit(self.white if self.flash > 0 else self.image, self.topleft)
