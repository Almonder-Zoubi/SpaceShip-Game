"""Enemy bullets, shared by minions and bosses."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import ENEMY_SHOT, SPARK


class EnemyBullet:
    __slots__ = ("x", "y", "vx", "vy", "damage")

    def __init__(self, x, y, vx, vy, damage):
        self.x, self.y, self.vx, self.vy, self.damage = x, y, vx, vy, damage

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def offscreen(self):
        return not (-6 < self.x < LOW_W + 6 and -6 < self.y < LOW_H + 6)

    def draw(self, surf, blink):
        """Glowing orb: red rim, orange body, white-hot core (additive)."""
        x, y = int(self.x), int(self.y)
        add = pygame.BLEND_ADD
        surf.fill(ENEMY_SHOT[3], (x - 2, y - 1, 5, 3), special_flags=add)
        surf.fill(ENEMY_SHOT[3], (x - 1, y - 2, 3, 5), special_flags=add)
        surf.fill(ENEMY_SHOT[2 if blink else 1], (x - 1, y - 1, 3, 3), special_flags=add)
        surf.fill(ENEMY_SHOT[0], (x, y, 1, 1), special_flags=add)


def shoot(world, x, y, angle, speed, damage):
    """Fire one enemy bullet with a small muzzle flash."""
    dx, dy = math.cos(angle), math.sin(angle)
    world.enemy_bullets.append(EnemyBullet(x, y, dx * speed, dy * speed, damage))
    world.fire.emit(x, y, dx * 30, dy * 30, 0.08, SPARK, size=2)
    world.audio.play("enemy_shot")


def bullet(x, y, angle, speed, damage):
    """Enemy bullet without a muzzle flash (spirals and walls fire too many for flashes)."""
    return EnemyBullet(x, y, math.cos(angle) * speed, math.sin(angle) * speed, damage)


class CurvedBullet(EnemyBullet):
    """An enemy bullet whose path bends (turn = rad/s, + = clockwise)."""
    __slots__ = ("turn",)

    def __init__(self, x, y, vx, vy, damage, turn):
        super().__init__(x, y, vx, vy, damage)
        self.turn = turn

    def update(self, dt):
        a = self.turn * dt
        c, s = math.cos(a), math.sin(a)
        self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c
        super().update(dt)


class ColoredBullet(EnemyBullet):
    """An enemy bullet in another hot colour (Kaleidos's prism spirals). colors: rim, body,
    core — always in the hot range with a white core, so it still reads as dangerous."""
    __slots__ = ("colors",)

    def __init__(self, x, y, vx, vy, damage, colors):
        super().__init__(x, y, vx, vy, damage)
        self.colors = colors

    def draw(self, surf, blink):
        x, y = int(self.x), int(self.y)
        add = pygame.BLEND_ADD
        rim, body = self.colors
        surf.fill(rim, (x - 2, y - 1, 5, 3), special_flags=add)
        surf.fill(rim, (x - 1, y - 2, 3, 5), special_flags=add)
        surf.fill(body, (x - 1, y - 1, 3, 3), special_flags=add)
        surf.fill((255, 255, 255), (x, y, 1, 1), special_flags=add)
