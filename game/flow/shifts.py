"""VEIL SHIFTS on the game side: roll one per attempt, show it, and apply its effect where
the game reads it (spawn rates, kits, coins, elites, damage, the blind spots)."""
import random

from ..config.tuning import SHIFT_BONUS, SHIFT_GLASS, SHIFT_ROCK_SPEED
from ..hazards.blindspots import BlindSpots
from ..levels.shifts import SHIFTS


class ShiftsMixin:
    """Game mixin: self.shift is the Shift of this attempt (or None)."""

    def roll_shift(self, shift=None):
        """A level attempt starts: the Veil shifts (levels with `shifts`)."""
        self.shift = shift or (random.choice(SHIFTS) if self.level.shifts else None)
        self.overlay = BlindSpots() if self.shift_is("BLIND SPOTS") else None
        self.spawner.speed_scale = SHIFT_ROCK_SPEED if self.shift_is("ROCKS FAST") else 1.0
        if self.shift:
            self.shift_card = 6.5                 # seconds the start card shows (after the title)

    def _reset_shift(self):
        self.shift = None
        self.overlay = None
        self.shift_card = 0.0

    def shift_is(self, shift_id):
        return bool(self.shift) and self.shift.id == shift_id

    @property
    def minion_rate(self):
        return 2.0 if self.shift_is("DOUBLE MINIONS") else 1.0

    @property
    def kits_allowed(self):
        return not self.shift_is("NO KITS")

    @property
    def shift_coins(self):
        return 2 if self.shift_is("NO KITS") else 1

    @property
    def glass(self):
        """GLASS CANNON: damage both ways x1.5."""
        return SHIFT_GLASS if self.shift_is("GLASS CANNON") else 1.0

    def elite_chance(self):
        base = self.level.difficulty.elite_chance
        return base * 3 if self.shift_is("ELITE SQUAD") else base

    def shift_payout(self, pending):
        """Clearing a level under a shift pays more."""
        return int(round(pending * SHIFT_BONUS)) if self.shift else pending

    def _update_shift(self, dt, real_dt):
        self.shift_card = max(0.0, self.shift_card - real_dt)
        if self.overlay:
            self.overlay.update(dt, self)
