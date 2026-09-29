"""MIRROR SEA's enemies (galaxy 2, level 5).

Reflection -- your own ship, upside down, mirrored across the screen's centre. It fires
              down when you fire. Shoot it and it breaks; it re-forms a while later.
EchoGhost  -- flies exactly where you were ECHO_DELAY seconds ago, and leaves a mine there
              now and then: don't fly back where you have been.
"""
import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import (ECHO_DELAY, ECHO_DROP, ECHO_HP, POINTS_ECHO, REFLECTION_FIRE,
                             REFLECTION_HP, WISP_BULLET_DAMAGE)
from .base import Enemy
from .veil_bullets import VeilBullet


class Reflection(Enemy):
    """Mirrored across both axes (upper half of the screen): x' = W - x, y' = H - y."""

    points = 300
    contact_damage = 20
    drops_coins = True
    stat = False

    def __init__(self, ship_image):
        image = pygame.transform.flip(ship_image, False, True)
        image = image.copy()
        image.fill((140, 150, 190, 255), special_flags=pygame.BLEND_RGBA_MULT)
        super().__init__(image, LOW_W / 2, 40, REFLECTION_HP)
        self.fire_timer = 0.0

    @property
    def offscreen(self):
        return False

    def move(self, dt, world):
        ship = world.ship
        tx, ty = LOW_W - ship.x, max(20, min(LOW_H * 0.42, LOW_H - ship.y))
        self.x += (tx - self.x) * min(1.0, 10 * dt)
        self.y += (ty - self.y) * min(1.0, 10 * dt)

    def attack(self, dt, world):
        self.fire_timer -= dt
        if world.firing_now and self.fire_timer <= 0:          # it fires when you fire
            self.fire_timer = REFLECTION_FIRE
            for dx in (-3, 3):
                world.enemy_bullets.append(VeilBullet(self.x + dx, self.y + self.h / 2, 0, 170,
                                                      WISP_BULLET_DAMAGE * 0.6))


class EchoMine(VeilBullet):
    """A mine an echo leaves behind: it sits still for a few seconds."""
    __slots__ = ()

    def __init__(self, x, y, damage):
        super().__init__(x, y, 0.0, 0.0, damage)

    @property
    def offscreen(self):
        return self.age > 4.0 or self.done

    def draw(self, surf, blink):
        x, y = int(self.x), int(self.y)
        pygame.draw.circle(surf, (150, 200, 255) if blink else (80, 120, 200), (x, y), 3, 1)
        surf.fill((255, 255, 255), (x, y, 1, 1))


class EchoGhost(Enemy):
    points = POINTS_ECHO
    contact_damage = 12
    _image = None

    def __init__(self, ship_image):
        image = ship_image.copy()
        image.fill((120, 170, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
        super().__init__(image, -40, -40, ECHO_HP)
        self.drop = ECHO_DROP

    @property
    def offscreen(self):
        return self.time > 14

    def move(self, dt, world):
        at = world.ship_at(ECHO_DELAY)
        if at:
            self.x, self.y = at

    def attack(self, dt, world):
        self.drop -= dt
        if self.drop <= 0 and world.ship_at(ECHO_DELAY):
            self.drop = ECHO_DROP
            world.enemy_bullets.append(EchoMine(self.x, self.y, WISP_BULLET_DAMAGE * 0.8))


def echo_ghost(game):
    return [EchoGhost(game.ship.frames[0])]
