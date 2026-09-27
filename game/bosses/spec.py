"""Boss balance: HP and damage derived from the player's ship model."""
from dataclasses import dataclass

from ..config.loadouts import MK1, Loadout


@dataclass(frozen=True)
class BossSpec:
    """Balance numbers for one boss appearance.

    strength   -- how many times stronger than the rocket (3-5 level boss, ~1.5 rematch)
    fight_time -- seconds a player needs to kill it with every gun bullet hitting
    player     -- the ship model the player flies in that level

    Derived so that (boss HP / player DPS) / (player HP / boss DPS) == strength.
    """
    name: str
    strength: float
    fight_time: float
    player: Loadout = MK1

    @property
    def hp(self):
        return self.player.gun_dps * self.fight_time

    @property
    def dps(self):
        """Damage per second a rocket that never moves would take."""
        return self.strength * self.player.max_hp / self.fight_time


GUNSHIP_SPEC = BossSpec("GUNSHIP", strength=3.0, fight_time=40)
