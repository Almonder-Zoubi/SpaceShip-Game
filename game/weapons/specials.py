"""MK III special weapons that charge from damage dealt: BLAST beam and ULTIMATE missiles."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import FLAME, SMOKE, SPARK, TRACER
from ..config.tuning import (BLAST_DPS, BLAST_PUSH, BLAST_TIME, BLAST_WIDTH, LASER_RANGE,
                             ULT_INTERVAL, ULT_MISSILE_DAMAGE, ULT_MISSILE_SPEED, ULT_TIME,
                             ULT_TURN)
from .base import Hit, Weapon


class Charged(Weapon):
    """Base for special weapons that fill a 0..1 meter from damage dealt, then fire."""

    duration = 1.0

    def __init__(self):
        self.reset()

    def reset(self):
        self.charge = 0.0
        self.active_time = 0.0
        self.time = 0.0

    @property
    def active(self):
        return self.active_time > 0

    @property
    def ready(self):
        return self.charge >= 1 and not self.active

    def add_charge(self, amount):
        """Returns True if this made the weapon ready."""
        if self.active or self.charge >= 1:
            return False
        self.charge = min(1.0, self.charge + amount)
        return self.charge >= 1

    def activate(self):
        if not self.ready:
            return False
        self.active_time = self.duration
        return True

    def _tick(self, dt):
        self.time += dt
        if self.active:
            self.active_time = max(0.0, self.active_time - dt)
            self.charge = self.active_time / self.duration      # meter drains while it fires


class Blast(Charged):
    """BLAST: when charged, holding fire unleashes a huge piercing beam from the nose for
    BLAST_TIME seconds. It destroys everything in front of the rocket, then recharges.
    Its colour follows the active weapon (golden plasma for the gun, blue for the laser)."""

    name = "BLAST"
    duration = BLAST_TIME

    def reset(self):
        super().reset()
        self.colors = TRACER
        self.start = self.end = (0, 0)

    def update(self, dt, firing, ship, targets, fire):
        self._tick(dt)
        if firing and self.charge >= 1 and not self.active:
            self.activate()
        if not self.active:
            return []
        ox, oy = ship.nose()
        dx, dy = ship.forward
        self.start, self.end = (ox, oy), (ox + dx * LASER_RANGE, oy + dy * LASER_RANGE)
        for _ in range(3):                                    # recoil sparks at the nose
            a = math.atan2(-dy, -dx) + random.uniform(-1.2, 1.2)
            fire.emit(ox, oy, math.cos(a) * 90, math.sin(a) * 90, 0.15, self.colors)
        hits = []
        for t in targets:
            rx, ry = t.x - ox, t.y - oy
            along = rx * dx + ry * dy
            if along < -t.bound or abs(rx * dy - ry * dx) > BLAST_WIDTH / 2 + t.bound * 0.8:
                continue
            hx, hy = ox + dx * along, oy + dy * along
            if random.random() < 0.5:
                fire.emit(hx, hy, random.uniform(-80, 80), random.uniform(-80, 80), 0.2, SPARK)
            hits.append(Hit(t, BLAST_DPS * dt, hx, hy, dx, dy, BLAST_PUSH * dt,
                            continuous=True, charges=False))
        return hits

    def draw(self, surf):
        if not self.active:
            return
        start, end = self.start, self.end
        grow = min(1.0, (self.duration - self.active_time) / 0.15)    # beam opens up quickly
        fade = min(1.0, self.active_time / 0.3)                       # and narrows at the end
        width = max(1, int(BLAST_WIDTH * grow * fade)) + (int(self.time * 30) % 2)
        pygame.draw.line(surf, self.colors[-1], start, end, width + 4)
        pygame.draw.line(surf, self.colors[-2], start, end, width)
        pygame.draw.line(surf, self.colors[1], start, end, max(1, width - 4))
        pygame.draw.line(surf, (255, 255, 255), start, end, max(1, width - 8))
        pygame.draw.circle(surf, self.colors[1], (int(start[0]), int(start[1])), width // 2 + 2)


class Missile:
    __slots__ = ("x", "y", "vx", "vy", "target", "life")

    def __init__(self, x, y, vx, vy, target):
        self.x, self.y, self.vx, self.vy, self.target = x, y, vx, vy, target
        self.life = 3.0


class Ultimate(Charged):
    """ULTIMATE (key T): a storm of homing missiles spread over every target on screen.
    Bigger targets (bosses) draw more missiles."""

    name = "ULTIMATE"
    duration = ULT_TIME

    def reset(self):
        super().reset()
        self.missiles = []
        self.timer = 0.0
        self.side = 1
        self.assigned = {}

    def activate(self):
        if super().activate():
            self.timer = 0.0
            self.assigned = {}
            return True
        return False

    def update(self, dt, firing, ship, targets, fire):
        self._tick(dt)
        visible = [t for t in targets if -t.bound < t.y < LOW_H and -t.bound < t.x < LOW_W + t.bound]
        if self.active and ship.alive:
            self.timer -= dt
            while self.timer <= 0:
                self.timer += ULT_INTERVAL
                self._launch(ship, visible, fire)
        return self._move(dt, visible, fire)

    def _pick(self, visible):
        """Spread missiles over all targets; each gets a share by its size."""
        if not visible:
            return None
        target = min(visible, key=lambda t: self.assigned.get(id(t), 0) / max(1.0, t.bound / 6))
        self.assigned[id(target)] = self.assigned.get(id(target), 0) + 1
        return target

    def _launch(self, ship, visible, fire):
        self.side = -self.side
        x, y = ship.to_world(self.side * (abs(ship.hull.barrels[0][0]) + 2), 2)
        rx, ry = ship.right
        fx, fy = ship.forward
        speed = random.uniform(90, 140)
        self.missiles.append(Missile(x, y, rx * self.side * speed + fx * 60,
                                     ry * self.side * speed + fy * 60, self._pick(visible)))
        fire.burst(x, y, 3, 40, 0.1, FLAME[:3], size=(1, 1))

    def _move(self, dt, visible, fire):
        hits, alive = [], []
        ids = {id(t) for t in visible}
        for m in self.missiles:
            m.life -= dt
            if m.target is None or id(m.target) not in ids:
                m.target = min(visible, key=lambda t: (t.x - m.x) ** 2 + (t.y - m.y) ** 2,
                               default=None)
            angle = math.atan2(m.vy, m.vx)
            if m.target is not None:
                want = math.atan2(m.target.y - m.y, m.target.x - m.x)
                turn = (want - angle + math.pi) % math.tau - math.pi
                angle += max(-ULT_TURN * dt, min(ULT_TURN * dt, turn))
            speed = min(ULT_MISSILE_SPEED, math.hypot(m.vx, m.vy) + 400 * dt)
            m.vx, m.vy = math.cos(angle) * speed, math.sin(angle) * speed
            m.x += m.vx * dt
            m.y += m.vy * dt
            fire.emit(m.x - m.vx * 0.02, m.y - m.vy * 0.02, -m.vx * 0.2 + random.uniform(-10, 10),
                      -m.vy * 0.2 + random.uniform(-10, 10), 0.18, FLAME[1:])
            hit = None
            for t in visible:
                if abs(m.x - t.x) < t.bound and abs(m.y - t.y) < t.bound and t.contains(m.x, m.y):
                    hit = Hit(t, ULT_MISSILE_DAMAGE, m.x, m.y, math.cos(angle), math.sin(angle),
                              25, charges=False)
                    break
            if hit:
                hits.append(hit)
                fire.burst(m.x, m.y, 12, 90, 0.35, FLAME, size=(1, 2))
                fire.burst(m.x, m.y, 4, 60, 0.6, SMOKE, size=(1, 2))
            elif m.life > 0 and -20 < m.x < LOW_W + 20 and -20 < m.y < LOW_H + 20:
                alive.append(m)
        self.missiles = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for m in self.missiles:
            speed = math.hypot(m.vx, m.vy) or 1
            dx, dy = m.vx / speed, m.vy / speed
            for i in range(1, 5):                          # hot body fading back to orange
                surf.fill(FLAME[min(i, 3)], (int(m.x - dx * i), int(m.y - dy * i), 2, 2),
                          special_flags=add)
            surf.fill((255, 255, 255), (int(m.x), int(m.y), 2, 2), special_flags=add)
