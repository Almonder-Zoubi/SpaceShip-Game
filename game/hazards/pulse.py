"""PULSE (galaxy 2, PULSE NEBULA): the enemy side moves on the beat of the music. Rocks,
minions, the boss and every enemy bullet lurch forward on each beat and nearly stop between
beats - listen, and the gaps open on the off-beat. The speed averages about normal."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import PULSE_BPM, PULSE_HIGH, PULSE_LOW
from ..flow.states import Phase
from .base import Hazard

BEAT = 60.0 / PULSE_BPM
PINK = (255, 90, 190)


class PulseField(Hazard):
    def __init__(self):
        self.clock = 0.0                  # seconds on the music's clock (restarts with it)
        self.start = None                 # game time when the music (re)started
        self.phase = None
        self.time_scale = 1.0             # read by Game.enemy_dt()

    @property
    def beat_phase(self):
        """0..1 through the current beat (0 = on the beat)."""
        return (self.clock % BEAT) / BEAT

    @property
    def beat_index(self):
        return int(self.clock / BEAT)

    def update(self, dt, game):
        if game.phase != self.phase or self.start is None:
            if self.start is None or game.phase in (Phase.FIELD, Phase.BOSS):
                self.start = game.time    # the music restarts with a new phase (boss track)
            self.phase = game.phase
        self.clock = game.time - self.start               # real time, like the music
        pulse = max(0.0, math.cos(self.beat_phase * math.tau)) ** 2
        self.time_scale = PULSE_LOW + (PULSE_HIGH - PULSE_LOW) * pulse

    def draw_back(self, surf):
        k = self.beat_phase
        r = int(20 + k * 200)             # a ring of light spreads from the centre on every beat
        c = int(90 * (1 - k))
        if c > 8:
            pygame.draw.circle(surf, (c, c // 4, c * 2 // 3), (LOW_W // 2, LOW_H // 2), r, 1)

    def draw_front(self, surf):
        k = 1 - self.beat_phase
        if k > 0.8:                        # the border flashes on the beat
            v = int(255 * (k - 0.8) * 5)
            color = (min(255, v), v // 3, min(255, v * 3 // 4))
            surf.fill(color, (0, 0, LOW_W, 2), special_flags=pygame.BLEND_ADD)
            surf.fill(color, (0, LOW_H - 2, LOW_W, 2), special_flags=pygame.BLEND_ADD)
            surf.fill(color, (0, 0, 2, LOW_H), special_flags=pygame.BLEND_ADD)
            surf.fill(color, (LOW_W - 2, 0, 2, LOW_H), special_flags=pygame.BLEND_ADD)
