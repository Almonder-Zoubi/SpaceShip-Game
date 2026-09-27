"""Small enemies (drones), their formations, and the bullets every enemy fires."""
import math
import random

import pygame

from .settings import (DRONE_BULLET_DAMAGE, DRONE_BULLET_SPEED, DRONE_CONTACT_DAMAGE, DRONE_HP,
                       DRONE_SPEED, ENEMY_SHOT, LOW_H, LOW_W, POINTS_DRONE, SPARK)
from .sprites import build_drone


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


class Drone(Enemy):
    """Small attack drone: dives down with a sine sway, drifts towards the rocket
    and fires a couple of aimed shots before leaving the screen."""

    points = POINTS_DRONE
    contact_damage = DRONE_CONTACT_DAMAGE
    _image = None
    STEER = 0.8                 # how strongly it drifts towards the rocket's x (1/s)

    def __init__(self, x, y, vx=0.0, vy=DRONE_SPEED, sway=18.0, shots=2, bullet_damage=None,
                 steer=STEER):
        if Drone._image is None:
            Drone._image = build_drone()
        super().__init__(Drone._image, x, y, DRONE_HP)
        self.vx, self.vy = vx, vy
        self.sway, self.phase = sway, random.uniform(0, math.tau)
        self.shots, self.steer = shots, steer
        self.fire_timer = random.uniform(0.6, 1.4)
        self.bullet_damage = DRONE_BULLET_DAMAGE if bullet_damage is None else bullet_damage

    def move(self, dt, world):
        self.vx *= max(0.0, 1 - 1.5 * dt)                    # launch kick fades out
        steer = (world.ship.x - self.x) * self.steer if world.ship.alive else 0.0
        sway = math.cos(self.time * 3 + self.phase) * self.sway
        self.x += (self.vx + sway + max(-40.0, min(40.0, steer))) * dt
        self.y += self.vy * dt

    def attack(self, dt, world):
        self.fire_timer -= dt
        if self.shots and self.fire_timer <= 0 and world.ship.alive and self.y < world.ship.y - 20:
            self.shots -= 1
            self.fire_timer = random.uniform(0.9, 1.5)
            x, y = self.x, self.y + self.h / 2
            shoot(world, x, y, math.atan2(world.ship.y - y, world.ship.x - x),
                  DRONE_BULLET_SPEED, self.bullet_damage)


def drone_formation(kind=None):
    """A wave of drones entering from the top: 'v', 'line' or 'snake'."""
    kind = kind or random.choice(("v", "line", "snake"))
    cx = random.uniform(70, LOW_W - 70)
    if kind == "v":
        return [Drone(cx + i * 16, -10 - abs(i) * 12, sway=8, shots=1, steer=0.3)
                for i in range(-2, 3)]
    if kind == "line":
        return [Drone(40 + i * 60, -10, sway=24, shots=1, steer=0.1) for i in range(5)]
    return [Drone(cx, -10 - i * 16, sway=40, shots=1, steer=0.5) for i in range(5)]  # snake
