"""The hive tunnel (level 10): living walls on both sides that breathe and bulge inwards.
Touching them hurts. During the escape wave the hive collapses: the walls close in, debris
rains down and the world rushes past."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import HIVE_FLESH, HIVE_VEIN
from ..config.tuning import (ESCAPE_SPEED, ESCAPE_WALL, HIVE_WALL, HIVE_WALL_DAMAGE)
from ..core.pixelart import dither
from ..flow.states import Phase
from ..obstacles.asteroid import rock_class
from .base import Hazard


class HiveTunnel(Hazard):
    def __init__(self):
        self.scroll = 0.0                # how far the tunnel has scrolled (px)
        self.time = 0.0
        self.collapse = 0.0              # 0..1 during the escape
        self.world_speed = 1.0           # read by Game._world_speed()
        self.debris_timer = 0.0

    def width(self, side, y):
        """Wall width (px) at screen row y; side -1 = left, 1 = right."""
        v = self.scroll - y
        lo, hi = HIVE_WALL
        wave = (math.sin(v * 0.021 + side) * 0.5 + math.sin(v * 0.053 + side * 2.1) * 0.3
                + math.sin(self.time * 1.7 + v * 0.01) * 0.1)
        w = lo + (hi - lo) * (0.5 + 0.5 * wave)
        return w + (ESCAPE_WALL - lo) * self.collapse

    def update(self, dt, game):
        self.time += dt
        self.scroll += 55 * game._world_speed() * dt
        escape = game.wave.escape and game.phase == Phase.FIELD
        if escape:
            k = min(1.0, game.distance / max(1.0, game.wave.length))
            self.collapse = k
            self.world_speed = ESCAPE_SPEED
            self._debris(dt, game, k)
            if random.random() < 3 * dt:
                game.shake.add(0.08)
        else:
            self.world_speed = 1.0
        ship = game.ship
        if not ship.alive:
            return
        for side in (-1, 1):
            w = self.width(side, ship.y)
            edge = w if side < 0 else LOW_W - w
            if (ship.x - edge) * -side < ship.w / 2 - 2:       # touching the wall
                ship.x = edge - side * (ship.w / 2 + 1)
                ship.vx = -side * 60
                game.hurt_ship(ship.max_hp * HIVE_WALL_DAMAGE, edge, ship.y)

    def _debris(self, dt, game, k):
        """The hive collapses: chitin chunks rain down, faster and faster."""
        self.debris_timer -= dt
        if self.debris_timer <= 0:
            self.debris_timer = 0.45 - 0.3 * k
            art = game.library.pick(5, 11, ("chitin",))
            game.asteroids.append(rock_class("chitin")(
                art, random.uniform(40, LOW_W - 40), -art.size / 2, random.uniform(-20, 20),
                random.uniform(120, 180), random.uniform(-2, 2),
                hp_scale=game.level.difficulty.rock_hp))

    def draw_mid(self, surf):
        """Flesh walls with dithered shading and glowing veins (over rocks, under the ship)."""
        tones = len(HIVE_FLESH)
        for y in range(0, LOW_H, 2):
            for side in (-1, 1):
                w = int(self.width(side, y))
                if w <= 0:
                    continue
                x0 = 0 if side < 0 else LOW_W - w
                surf.fill(HIVE_FLESH[1], (x0, y, w, 2))
                # the inner rim: lighter, pulsing
                pulse = 0.5 + 0.5 * math.sin(self.time * 3 + y * 0.05)
                rim = x0 + w - 3 if side < 0 else x0
                surf.fill(HIVE_FLESH[dither(0.6 + 0.4 * pulse, rim, y, tones)], (rim, y, 3, 2))
                surf.fill(HIVE_FLESH[0], (x0 + w - 1 if side < 0 else x0, y, 1, 2))
                vein = (self.scroll - y) * 0.08 + side
                vx = x0 + int((0.5 + 0.35 * math.sin(vein)) * (w - 4))
                if int(self.scroll - y) % 9 < 6:
                    glow = int(60 + 60 * pulse)
                    surf.fill((glow // 3, glow, glow // 4), (vx, y, 1, 2),
                              special_flags=pygame.BLEND_ADD)
                if (int(self.scroll - y) // 2) % 23 == 0:            # a pore
                    surf.fill(HIVE_FLESH[0], (x0 + w // 2, y, 2, 2))
        if self.collapse > 0:
            for i in range(3):
                x = random.randint(0, LOW_W)
                surf.fill(HIVE_VEIN, (x, random.randint(0, LOW_H), 1, 1),
                          special_flags=pygame.BLEND_ADD)
