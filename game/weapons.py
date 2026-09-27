"""Player weapons. Each weapon moves its own projectiles and reports hits to the game."""
import math
import random

import pygame

from .settings import (GUN_DAMAGE, GUN_INTERVAL, GUN_PUSH, GUN_SPEED, GUN_SPREAD, LASER,
                       LASER_COOL_RATE, LASER_DPS, LASER_HEAT_RATE, LASER_PUSH, LASER_RANGE,
                       LASER_RESUME, LOW_H, LOW_W, SPARK, TRACER)


class Hit:
    """One weapon impact: the game applies damage, push and effects.

    (dx, dy) is the shot's direction; push is px/s applied to a radius-4 rock.
    """
    __slots__ = ("target", "damage", "x", "y", "dx", "dy", "push", "continuous")

    def __init__(self, target, damage, x, y, dx, dy, push, continuous=False):
        self.target, self.damage, self.x, self.y = target, damage, x, y
        self.dx, self.dy, self.push = dx, dy, push
        self.continuous = continuous


class Weapon:
    """Base class. Subclasses implement update() and draw()."""

    name = "WEAPON"
    heat = 0.0          # 0..1, shown in the HUD for weapons that can overheat
    overheated = False

    def update(self, dt, firing, ship, targets, fire):
        """Advance the weapon; returns a list of Hit."""
        raise NotImplementedError

    def draw(self, surf):
        raise NotImplementedError

    def reset(self):
        pass


class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "life")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = 1.5


class MachineGun(Weapon):
    """Rapid tracer rounds from alternating wing barrels. No overheating, some spread."""

    name = "GUN"
    BARRELS = ((-5.0, 1.0), (5.0, 1.0))      # ship-local positions (x right, y down)

    def __init__(self):
        self.bullets = []
        self.reset()

    def reset(self):
        self.bullets.clear()
        self.cooldown = 0.0
        self.barrel = 0

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = GUN_INTERVAL
            self._shoot(ship, fire)
        return self._move_bullets(dt, targets, fire)

    def _shoot(self, ship, fire):
        bx, by = ship.to_world(*self.BARRELS[self.barrel])
        self.barrel = 1 - self.barrel
        a = ship.angle + random.uniform(-GUN_SPREAD, GUN_SPREAD)   # 0 = straight up
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
                        hit = Hit(t, GUN_DAMAGE, x, y, b.vx / speed, b.vy / speed, GUN_PUSH)
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
        for b in self.bullets:
            speed = math.hypot(b.vx, b.vy) or 1
            dx, dy = b.vx / speed, b.vy / speed
            surf.fill(TRACER[0], (int(b.x) - 1, int(b.y) - 1, 2, 2), special_flags=add)   # hot head
            for i in range(1, 5):                                                          # fading tail
                color = TRACER[min(len(TRACER) - 1, i // 2 + 1)]
                surf.fill(color, (int(b.x - dx * i * 1.2), int(b.y - dy * i * 1.2), 1, 1),
                          special_flags=add)


class Laser(Weapon):
    """Continuous beam from the nose: instant, precise, but it overheats."""

    name = "LASER"

    def __init__(self):
        self.reset()

    def reset(self):
        self.heat = 0.0
        self.overheated = False
        self.active = False
        self.start = self.end = (0, 0)
        self.time = 0.0

    def update(self, dt, firing, ship, targets, fire):
        self.time += dt
        self.active = firing and not self.overheated
        if self.active:
            self.heat = min(1.0, self.heat + LASER_HEAT_RATE * dt)
            if self.heat >= 1.0:
                self.overheated = True
        else:
            self.heat = max(0.0, self.heat - LASER_COOL_RATE * dt)
            if self.overheated and self.heat <= LASER_RESUME:
                self.overheated = False
        if not self.active:
            return []

        ox, oy = ship.nose()
        dx, dy = ship.forward
        dist, target = raycast(ox, oy, dx, dy, LASER_RANGE, targets)
        self.start, self.end = (ox, oy), (ox + dx * dist, oy + dy * dist)
        if target is None:
            return []
        ex, ey = self.end
        for _ in range(2):   # sparks spray back from the impact point
            a = math.atan2(-dy, -dx) + random.uniform(-1.1, 1.1)
            s = random.uniform(30, 110)
            fire.emit(ex, ey, math.cos(a) * s, math.sin(a) * s, random.uniform(0.08, 0.2), LASER)
        return [Hit(target, LASER_DPS * dt, ex, ey, dx, dy, LASER_PUSH * dt, continuous=True)]

    def draw(self, surf):
        if not self.active:
            return
        (sx, sy), (ex, ey) = self.start, self.end
        length = max(1, int(math.hypot(ex - sx, ey - sy)))
        dx, dy = (ex - sx) / length, (ey - sy) / length
        px, py = -dy, dx
        wobble = 1 if int(self.time * 30) % 2 else 0
        add = pygame.BLEND_ADD
        for i in range(length):
            x, y = sx + dx * i, sy + dy * i
            surf.fill(LASER[0], (int(x), int(y), 1, 1), special_flags=add)
            for side in (-1, 1):
                surf.fill(LASER[2], (int(x + px * side), int(y + py * side), 1, 1), special_flags=add)
                if wobble and i % 3 == 0:
                    surf.fill(LASER[3], (int(x + px * side * 2), int(y + py * side * 2), 1, 1),
                              special_flags=add)
        pygame.draw.circle(surf, LASER[1], (int(sx), int(sy)), 1)               # muzzle
        pygame.draw.circle(surf, LASER[1], (int(ex), int(ey)), 2 + wobble, 1)   # impact ring


def raycast(ox, oy, dx, dy, max_dist, targets):
    """Distance to the first target pixel along a ray, and that target (or None)."""
    best, hit = max_dist, None
    for t in targets:
        rx, ry = t.x - ox, t.y - oy
        along = rx * dx + ry * dy
        if along < -t.bound or along - t.bound > best:
            continue
        if abs(rx * dy - ry * dx) > t.bound:          # perpendicular distance
            continue
        s = max(0.0, along - t.bound)
        stop = min(best, along + t.bound)
        while s < stop:
            if t.contains(ox + dx * s, oy + dy * s):
                best, hit = s, t
                break
            s += 1.0
    return best, hit
