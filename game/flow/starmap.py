"""The STAR MAP state: fly the rocket between the level planets, find hidden data caches,
land on a planet to open its hangar."""
import math

import pygame

from ..core.input import pressed
from ..levels.data import GALAXIES, LEVELS, galaxy_of
from ..starmap.model import CACHES, MAPS, StarMap
from .states import State


class StarMapMixin:
    """Game mixin: open the map, move the rocket, cache rewards, landing."""

    def open_star_map(self, index=None, at_gate=False):
        """The map of the galaxy that holds level `index` (default: the level the title has
        selected), the rocket parked at that planet (or at the gate after a warp)."""
        index = self.start_level if index is None else index
        galaxy = galaxy_of(LEVELS[min(index, len(LEVELS) - 1)])
        offset = LEVELS.index(galaxy.levels[0])
        ranks = {i: self.save.cleared[galaxy.key(level)] for i, level in enumerate(galaxy.levels)
                 if galaxy.key(level) in self.save.cleared}
        gmap = MAPS[galaxy.number]
        target = next((g for g in GALAXIES if g.number == gmap.gate_to), None)
        if gmap.gate_to > galaxy.number:                  # forward: the galaxy's medal opens it
            gate_open = galaxy.number in self.save.medals and target is not None
        else:
            gate_open = target is not None                # the way back is always open
        self.star_map = StarMap(galaxy.levels, max(0, self.selectable_levels - offset),
                                self.save.caches, galaxy.number in self.save.medals, ranks,
                                gmap, gate_open)
        self.star_map_offset = offset
        if at_gate:
            self.star_map.place_at_gate()
        else:
            self.star_map.place_at(min(max(0, index - offset), len(galaxy.levels) - 1))
        self.star_map_view.set_rocket(self.ship.frames[0])
        self.map_ping = 0.0
        self.set_state(State.STAR_MAP)

    @property
    def star_map_view(self):
        return self.star_map_views[self.star_map.gmap.galaxy]

    def _update_star_map(self, dt, keys, mouse):
        m = self.star_map
        ax = pressed(keys, pygame.K_RIGHT, pygame.K_d) - pressed(keys, pygame.K_LEFT, pygame.K_a)
        ay = pressed(keys, pygame.K_DOWN, pygame.K_s) - pressed(keys, pygame.K_UP, pygame.K_w)
        if mouse and mouse.aim and not (ax or ay):         # fly towards the pointer
            cx, cy = self.star_map_view.camera(m)
            dx, dy = mouse.aim[0] + cx - m.ship.x, mouse.aim[1] + cy - m.ship.y
            d = math.hypot(dx, dy)
            if d > 4:
                k = min(1.0, d / 40) / d
                ax, ay = dx * k, dy * k
        cache = m.update(dt, ax, ay)
        self.star_map_view.update(dt, m)
        if cache:
            self._open_cache(cache)
        signal = m.signal()                                # the scanner beeps faster nearby
        self.map_ping -= dt
        if signal > 0.05 and self.map_ping <= 0 and not m.card:
            self.map_ping = 1.4 - signal
            self.audio.play("select")

    def _open_cache(self, cache):
        """A data cache: its coins go straight to the bank (once), its story on a card."""
        if self.save.find_cache(cache.id):
            self.save.coins += cache.coins
            self.save.save()
        self.audio.play("data_cache")
        self.screen_flash(0.06)
        if len(self.save.caches) >= len(CACHES) and not self.dev:
            self.achieve("EXPLORER")

    def star_map_enter(self):
        """ENTER: close a story card, or land on the planet the rocket is at."""
        m = self.star_map
        if m.card:
            m.card = None
            return
        node = m.near_node()
        if node is None:
            if m.near_gate() and m.gate_open:            # warp to the other galaxy's map
                target = next(g for g in GALAXIES if g.number == m.gmap.gate_to)
                self.audio.play("warp")
                self.screen_flash(0.15)
                self.open_star_map(LEVELS.index(target.levels[0]), at_gate=True)
            return
        if not m.is_open(node):
            self.audio.play("denied")
            return
        self.audio.play("confirm")
        self.start_level = self.star_map_offset + node
        self.open_hangar(self.start_level)
