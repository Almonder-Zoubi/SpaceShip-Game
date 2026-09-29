"""DARKNESS (galaxy 2, THE DARK VEIL): the screen goes black. Light comes from the rocket,
from every tracer it fires, from explosions, and from a FLARE (ability). Enemy bullets, pickups
and the rims of dark things are drawn on top of the dark (fair: you always see what can hurt
you). Rocks and lurkers show only where there is light."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import DARK_ALPHA, LIGHT_BOOM, LIGHT_SHIP, LIGHT_SHOT
from .base import Hazard

FLARE_LIGHT = 230                          # px: the rocket's light during a FLARE


def _hole(radius):
    """A soft round hole: how much of the dark it takes away, fading at the edge."""
    size = radius * 2 + 1
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - radius, y - radius) / radius
            if d < 1:
                k = 1.0 if d < 0.55 else (1 - d) / 0.45
                a = int(DARK_ALPHA * k)
                if 0.55 <= d and (x + y) % 2:                 # a dithered edge
                    a = a * 3 // 4
                surf.set_at((x, y), (0, 0, 0, a))
    return surf


class Darkness(Hazard):
    def __init__(self):
        self.dark = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
        self._holes = {}
        self.game = None
        self.dim = 0.0                    # > 0: the Eclipse has put the rocket's light out
        self.light = LIGHT_SHIP

    _base = None

    def hole(self, radius):
        """A hole of about this radius (steps of 4 px), scaled from one drawn base hole."""
        radius = max(4, int(round(radius / 4)) * 4)
        if radius not in self._holes:
            if Darkness._base is None:
                Darkness._base = _hole(48)
            size = radius * 2 + 1
            self._holes[radius] = pygame.transform.scale(Darkness._base, (size, size))
        return self._holes[radius]

    def update(self, dt, game):
        self.game = game
        self.dim = max(0.0, self.dim - dt)
        want = FLARE_LIGHT if game.flare > 0 else (LIGHT_SHIP * 0.4 if self.dim > 0 else LIGHT_SHIP)
        self.light += (want - self.light) * min(1.0, 4 * dt)

    def lights(self):
        """(x, y, radius) of everything that shines this frame."""
        game = self.game
        out = []
        if game.ship.alive:
            out.append((game.ship.x, game.ship.y, self.light))
        for weapon in game.weapons:
            for b in getattr(weapon, "bullets", [])[::2]:
                out.append((b.x, b.y, LIGHT_SHOT))
            for orb in getattr(weapon, "orbs", []):
                out.append((orb.x, orb.y, LIGHT_SHOT * 2))
            if weapon.name in ("LASER",) and getattr(weapon, "active", False):
                for y in range(int(game.ship.y) - 20, 0, -24):
                    out.append((game.ship.x, y, LIGHT_SHOT * 1.5))
        for wave in game.shockwaves:
            out.append((wave.x, wave.y, LIGHT_BOOM))
        glow = getattr(game.boss, "light", None)
        if glow:
            out += glow()
        return out

    def draw_front(self, surf):
        if self.game is None:
            return
        game = self.game
        self.dark.fill((0, 0, 0, DARK_ALPHA))
        for x, y, r in self.lights():
            hole = self.hole(r)
            self.dark.blit(hole, (int(x) - hole.get_width() // 2, int(y) - hole.get_height() // 2),
                           special_flags=pygame.BLEND_RGBA_SUB)
        surf.blit(self.dark, (0, 0))
        blink = int(game.time * 12) % 2 == 0
        for pickup in game.pickups:                       # what matters shows through
            pickup.draw(surf)
        rim = getattr(game.boss, "draw_rim", None)
        if rim and game.boss.state != "dead":
            rim(surf)
        for enemy in game.enemies:                        # eyes in the dark, now and then
            if int(game.time * 3 + enemy.x) % 4 == 0:
                surf.fill((255, 60, 80), (int(enemy.x) - 2, int(enemy.y), 1, 1))
                surf.fill((255, 60, 80), (int(enemy.x) + 2, int(enemy.y), 1, 1))
        for bullet in game.enemy_bullets:
            bullet.draw(surf, blink)
