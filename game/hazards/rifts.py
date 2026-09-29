"""Rift portals (galaxy 2, VEIL GATE): pairs of tears in space. Rocks, minions, enemy bullets
and the rocket's own shots that enter one portal come out of the other, keeping their
velocity. Portals shimmer for RIFT_OPEN seconds before they carry anything."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import VEIL_GLOW
from ..config.tuning import RIFT_INTERVAL, RIFT_LIFE, RIFT_OPEN, RIFT_RADIUS
from ..flow.states import Phase
from .base import Hazard

PAIR_COLORS = ((170, 110, 255), (80, 220, 230))       # one colour per pair


class Rift:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.other = None
        self.age = 0.0

    @property
    def open(self):
        return RIFT_OPEN <= self.age < RIFT_LIFE

    def contains(self, x, y):
        return (x - self.x) ** 2 + (y - self.y) ** 2 < RIFT_RADIUS ** 2


class RiftPortals(Hazard):
    """At most two pairs at a time; things teleport once, then need a moment before the next
    jump (so nothing ping-pongs)."""

    def __init__(self):
        self.rifts = []
        self.timer = 2.5
        self.time = 0.0
        self.recent = {}                  # id(obj) -> seconds until it may jump again
        self.jumps = 0                    # how many things went through (tests, fun)

    def open_pair(self):
        color = PAIR_COLORS[len(self.rifts) // 2 % len(PAIR_COLORS)]
        a = Rift(random.uniform(40, LOW_W - 40), random.uniform(50, LOW_H * 0.55), color)
        for _ in range(20):                               # the exit well away from the entry
            b = Rift(random.uniform(40, LOW_W - 40), random.uniform(50, LOW_H * 0.6), color)
            if math.hypot(a.x - b.x, a.y - b.y) > 110:
                break
        a.other, b.other = b, a
        self.rifts += [a, b]
        return a, b

    def update(self, dt, game):
        self.time += dt
        for rift in self.rifts:
            rift.age += dt
        self.rifts = [r for r in self.rifts if r.age < RIFT_LIFE + 0.4]
        self.recent = {k: v - dt for k, v in self.recent.items() if v - dt > 0}
        self.timer -= dt
        if self.timer <= 0 and len(self.rifts) < 4 and game.phase in (Phase.FIELD, Phase.BOSS):
            self.timer = random.uniform(*RIFT_INTERVAL)
            self.open_pair()
            game.audio.play("teleport")
        things = list(game.asteroids) + list(game.enemies) + list(game.enemy_bullets)
        for weapon in game.weapons:                       # the rocket's shots go through too
            things += getattr(weapon, "bullets", [])
            things += getattr(weapon, "orbs", [])
        for rift in self.rifts:
            if not rift.open:
                continue
            for obj in things:
                if id(obj) in self.recent or not rift.contains(obj.x, obj.y):
                    continue
                self._jump(obj, rift, game)

    def _jump(self, obj, rift, game):
        out = rift.other
        dx, dy = obj.x - rift.x, obj.y - rift.y
        obj.x, obj.y = out.x + dx, out.y + dy
        if hasattr(obj, "cx"):                            # orbiting pairs move their centre
            obj.cx, obj.cy = obj.cx + out.x - rift.x, obj.cy + out.y - rift.y
        self.recent[id(obj)] = 0.6
        self.jumps += 1
        game.fire.burst(out.x, out.y, 5, 40, 0.25, VEIL_GLOW, size=(1, 1))

    def draw_back(self, surf):
        for rift in self.rifts:
            k = min(1.0, rift.age / RIFT_OPEN)
            fade = max(0.0, min(1.0, (RIFT_LIFE + 0.4 - rift.age) / 0.4))
            r = int(RIFT_RADIUS * k * fade) + 1
            x, y = int(rift.x), int(rift.y)
            if not rift.open:                             # the shimmer: it is about to open
                if int(self.time * 12) % 2:
                    pygame.draw.circle(surf, rift.color, (x, y), RIFT_RADIUS, 1)
                continue
            pygame.draw.ellipse(surf, (8, 4, 16), (x - r, y - int(r * 1.3), 2 * r, int(r * 2.6)))
            for i in range(10):                           # swirling rim
                a = self.time * 4 + i * math.tau / 10
                surf.fill(rift.color, (x + int(math.cos(a) * r), y + int(math.sin(a) * r * 1.3),
                                       1, 1), special_flags=pygame.BLEND_ADD)
            pygame.draw.ellipse(surf, rift.color, (x - r, y - int(r * 1.3), 2 * r, int(r * 2.6)), 1)
