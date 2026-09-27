"""Machine gun: rapid tracer rounds from the ship's barrels."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import POWER, SPARK, TRACER
from ..config.tuning import (GUN_INTERVAL, GUN_PUSH, GUN_SIDE_ANGLE, GUN_SPEED, GUN_SPREAD,
                             SLINGSHOT_SHOT)
from .base import Hit, Weapon


class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "life", "boost")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = 1.5
        self.boost = False          # flew through the black hole's SLINGSHOT ring


class MachineGun(Weapon):
    """Rapid tracer rounds from alternating wing barrels. No overheating, some spread.
    Barrel positions come from the ship's hull (ship-local, x right, y down)."""

    name = "GUN"
    colors = TRACER             # tracer skin

    def __init__(self):
        self.bullets = []
        self.reset()

    def reset(self):
        self.bullets.clear()
        self.cooldown = 0.0
        self.barrel = 0
        self.shots = 0
        self.power = 0

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = GUN_INTERVAL / self.rate
            self._volley(ship, fire)
        return self._move_bullets(dt, targets, fire)

    def _volley(self, ship, fire):
        """Power 0: alternating wing barrels. Power 1: + nose round every other shot.
        Power 2: + nose round every shot and angled side rounds every other shot."""
        barrels = ship.hull.barrels
        self.shots += 1
        self._shoot(ship, fire, barrels[self.barrel], 0.0)
        self.barrel = 1 - self.barrel
        if self.power >= 2 or (self.power == 1 and self.shots % 2 == 0):
            self._shoot(ship, fire, (0.0, ship.hull.nose_y + 0.5), 0.0)
        if self.power >= 2 and self.shots % 2 == 1:
            for side, barrel in ((-1, barrels[0]), (1, barrels[1])):
                self._shoot(ship, fire, barrel, side * GUN_SIDE_ANGLE)

    def _shoot(self, ship, fire, barrel, offset):
        bx, by = ship.to_world(*barrel)
        a = ship.angle + offset + random.uniform(-GUN_SPREAD, GUN_SPREAD)   # 0 = straight up
        dx, dy = math.sin(a), -math.cos(a)
        self.bullets.append(Bullet(bx, by, dx * GUN_SPEED + ship.vx, dy * GUN_SPEED + ship.vy))
        for _ in range(3):   # muzzle flash
            fire.emit(bx + dx * 2, by + dy * 2, dx * random.uniform(20, 60) + ship.vx,
                      dy * random.uniform(20, 60) + ship.vy, random.uniform(0.03, 0.07), SPARK)

    def _move_bullets(self, dt, targets, fire):
        hits, alive = [], []
        for b in self.bullets:
            b.life -= dt
            hit = None
            for step in (0.5, 1.0):        # two sub-steps so fast bullets can't skip small rocks
                x, y = b.x + b.vx * dt * step, b.y + b.vy * dt * step
                for t in targets:
                    if abs(x - t.x) < t.bound and abs(y - t.y) < t.bound and t.contains(x, y):
                        speed = math.hypot(b.vx, b.vy) or 1.0
                        damage = self.loadout.gun_damage * (SLINGSHOT_SHOT if b.boost else 1)
                        hit = Hit(t, damage, x, y, b.vx / speed, b.vy / speed, GUN_PUSH)
                        break
                if hit:
                    break
            if hit:
                hits.append(hit)
                continue
            b.x += b.vx * dt
            b.y += b.vy * dt
            if b.life > 0 and -8 < b.x < LOW_W + 8 and -8 < b.y < LOW_H + 8:
                alive.append(b)
        self.bullets = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        colors = self.colors
        head = POWER[1] if self.power else colors[0]
        for b in self.bullets:
            speed = math.hypot(b.vx, b.vy) or 1
            dx, dy = b.vx / speed, b.vy / speed
            surf.fill(head, (int(b.x) - 1, int(b.y) - 1, 2, 2), special_flags=add)        # hot head
            for i in range(1, 5):                                                          # fading tail
                color = colors[min(len(colors) - 1, i // 2 + 1)]
                surf.fill(color, (int(b.x - dx * i * 1.2), int(b.y - dy * i * 1.2), 1, 1),
                          special_flags=add)
