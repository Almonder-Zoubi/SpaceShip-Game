"""The full backdrop: nebula, planet and stars drawn back to front."""
import random

from ..config.palette import NEBULA
from .nebula import Nebula
from .planet import Planet
from .starfield import Starfield


class Background:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self._nebulas = {}                 # built once per colour set, levels switch between them
        self.set_nebula(NEBULA)
        self.planet = Planet(self.rng)
        self.stars = Starfield(self.rng)
        self._events = {}                  # event layer per class, built once
        self.event = None

    def set_nebula(self, colors):
        colors = tuple(colors)
        if colors not in self._nebulas:
            self._nebulas[colors] = Nebula(self.rng, colors)
        self.nebula = self._nebulas[colors]

    def set_event(self, event_class):
        """A level's event layer (sun corona, lightning ...) or None."""
        if event_class and event_class not in self._events:
            self._events[event_class] = event_class(self.rng)
        self.event = self._events.get(event_class)

    def update(self, dt, world_speed):
        self.nebula.update(dt, world_speed)
        self.planet.update(dt, world_speed)
        if self.event:
            self.event.update(dt, world_speed)
        self.stars.update(dt, world_speed)

    def draw(self, surf):
        self.nebula.draw(surf)
        self.planet.draw(surf)
        if self.event:
            self.event.draw(surf)
        self.stars.draw(surf)
