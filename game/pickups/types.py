"""The concrete pickups: small repair kit, full repair, power core."""
from ..config.palette import POWER
from ..config.tuning import REPAIR_SMALL
from .art import KIT_FULL_ROWS, KIT_SMALL_ROWS, POWER_ROWS
from .base import Pickup


class RepairKit(Pickup):
    """Small repair: restores REPAIR_SMALL hull points."""

    rows = KIT_SMALL_ROWS

    def apply(self, game):
        return f"+{int(game.ship.heal(REPAIR_SMALL))} HP"


class FullRepair(Pickup):
    """Rare gold kit: restores the hull completely."""

    rows = KIT_FULL_ROWS

    def apply(self, game):
        game.ship.heal(game.ship.max_hp)
        return "FULL REPAIR"


class PowerCore(Pickup):
    """Weapon power +1 for both weapons. Always homes in on the ship (never lost)."""

    rows = POWER_ROWS
    glow = POWER
    magnet = 400

    def apply(self, game):
        for weapon in game.weapons:
            weapon.power_up()
        return "POWER UP!"
