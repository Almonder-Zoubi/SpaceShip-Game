"""Small homing rockets shared by the HUNTER wingman and the ROCKET POD secondary."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import FLAME
from .base import Hit


class Rocket:
    __slots__ = ("x", "y", "vx", "vy", "target", "damage", "life")

    def __init__(self, x, y, vx, vy, target, damage):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.target, self.damage = target, damage
        self.life = 2.5


class RocketSwarm:
    """A group of homing rockets. launch() adds one; update() moves them and returns Hits.
    A rocket whose target is gone picks the nearest target on screen."""

    def __init__(self, speed=200, turn=6.0, colors=FLAME):
        self.speed, self.turn, self.colors = speed, turn, colors
        self.rockets = []

    def launch(self, x, y, vx, vy, target, damage):
        self.rockets.append(Rocket(x, y, vx, vy, target, damage))

    def clear(self):
        self.rockets.clear()

    @staticmethod
    def on_screen(targets):
        return [t for t in targets if -t.bound < t.y < LOW_H and -t.bound < t.x < LOW_W + t.bound]

    def update(self, dt, targets, fire, source=None):
        visible = self.on_screen(targets)
        ids = {id(t) for t in visible}
        hits, alive = [], []
        for r in self.rockets:
            r.life -= dt
            if r.target is None or id(r.target) not in ids:
                r.target = min(visible, key=lambda t: (t.x - r.x) ** 2 + (t.y - r.y) ** 2,
                               default=None)
            angle = math.atan2(r.vy, r.vx)
            if r.target is not None:
                want = math.atan2(r.target.y - r.y, r.target.x - r.x)
                turn = (want - angle + math.pi) % math.tau - math.pi
                angle += max(-self.turn * dt, min(self.turn * dt, turn))
            speed = min(self.speed, math.hypot(r.vx, r.vy) + 350 * dt)
            r.vx, r.vy = math.cos(angle) * speed, math.sin(angle) * speed
            r.x += r.vx * dt
            r.y += r.vy * dt
            if random.random() < 0.7:
                fire.emit(r.x - r.vx * 0.02, r.y - r.vy * 0.02, -r.vx * 0.15, -r.vy * 0.15,
                          0.12, self.colors[1:])
            hit = None
            for t in visible:
                if abs(r.x - t.x) < t.bound and abs(r.y - t.y) < t.bound and t.contains(r.x, r.y):
                    hit = Hit(t, r.damage, r.x, r.y, math.cos(angle), math.sin(angle), 20,
                              source=source)
                    break
            if hit:
                hits.append(hit)
                fire.burst(r.x, r.y, 6, 60, 0.25, self.colors, size=(1, 1))
            elif r.life > 0 and -20 < r.x < LOW_W + 20 and -20 < r.y < LOW_H + 20:
                alive.append(r)
        self.rockets = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for r in self.rockets:
            speed = math.hypot(r.vx, r.vy) or 1
            dx, dy = r.vx / speed, r.vy / speed
            for i in range(1, 4):
                surf.fill(self.colors[min(i, len(self.colors) - 1)],
                          (int(r.x - dx * i), int(r.y - dy * i), 1, 1), special_flags=add)
            surf.fill((255, 255, 255), (int(r.x), int(r.y), 2, 1), special_flags=add)
