"""Base class for small enemy ships (and the ELITE version any of them can be)."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import ELITE_GOLD
from ..config.tuning import ELITE_GUARD, ELITE_HP, ELITE_SPEED


class Enemy:
    """Base for small enemy ships. Same target interface as asteroids and bosses:
    x, y, bound, contains(), damage(). Subclasses implement move() and attack()."""

    hit_flash = 0.06
    points = 0
    contact_damage = 0
    drops_coins = True
    stat = True                  # counts in the level's "destroyed" rating
    elite = False                # galaxy 2: golden, tougher, faster, x3 coins, shrugs off hits

    def __init__(self, image, x, y, hp):
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.w, self.h = image.get_size()
        self.x, self.y = float(x), float(y)
        self.max_hp = self.hp = hp
        self.flash = 0.0
        self.time = 0.0
        self.guard = 0.0                 # elite: seconds until it can shrug off a hit again

    def make_elite(self):
        """The golden version: x3 hull, faster, and every ELITE_GUARD seconds one hit bounces."""
        self.elite = True
        self.max_hp = self.hp = self.hp * ELITE_HP
        self._outline = self.mask.outline()
        return self

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

    def armour(self, hit):
        """Damage multiplier for a weapon Hit (e.g. a shield that faces one way)."""
        return 1.0

    def on_death(self, world, scored):
        """Hook: it was destroyed (scored = by the player)."""

    def damage(self, amount, flash=True):
        if self.elite and self.guard <= 0:        # the golden shell takes this one
            self.guard = ELITE_GUARD
            self.flash = self.hit_flash
            return
        self.hp -= amount
        if flash:
            self.flash = self.hit_flash

    def update(self, dt, world):
        if self.elite:
            self.guard = max(0.0, self.guard - dt)
            dt *= ELITE_SPEED
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
        if self.elite:                            # golden aura (brighter while the guard is up)
            left, top = self.topleft
            k = 0.5 + 0.5 * math.sin(self.time * 8)
            color = ELITE_GOLD[0 if self.guard <= 0 and k > 0.5 else 1 if self.guard <= 0 else 2]
            for i, (x, y) in enumerate(self._outline):
                if (i + int(self.time * 20)) % 3:
                    surf.fill(color, (left + x - 1, top + y - 1, 1, 1),
                              special_flags=pygame.BLEND_ADD)
                    surf.fill(color, (left + x + 1, top + y + 1, 1, 1),
                              special_flags=pygame.BLEND_ADD)
        surf.blit(self.white if self.flash > 0 else self.image, self.topleft)
