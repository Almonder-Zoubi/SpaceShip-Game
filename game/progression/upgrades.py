"""Upgrades: 5 tracks x 5 tiers bought in the hangar, applied on top of the level's ship model.

The boss balance (BossSpec) always uses the level's *par* model, so upgrades are the
player's edge: capped, and shown as POWER % (100% = par).
"""
from dataclasses import dataclass, replace

from ..config.tuning import UPGRADE_BONUS, UPGRADE_COSTS, UPGRADE_TIERS


@dataclass(frozen=True)
class Track:
    id: str
    stat: str                    # what one tier improves, e.g. "HULL"
    blurb: tuple                 # 1-2 short lines for the hangar

    @property
    def bonus(self):
        """Share of the par value added per tier."""
        return UPGRADE_BONUS[self.id]

    def multiplier(self, tier):
        return 1 + self.bonus * tier


TRACKS = (
    Track("ARMOR", "HULL", ("THICKER PLATING.", "MORE HULL POINTS.")),
    Track("GUNS", "GUN DAMAGE", ("HOTTER ROUNDS.", "MACHINE GUN HITS HARDER.")),
    Track("LASER", "LASER DPS", ("FOCUSED LENS.", "STRONGER BEAM.")),
    Track("ENGINE", "SPEED", ("TUNED THRUSTERS.", "HIGHER TOP SPEED.")),
    Track("CHARGE", "CHARGE RATE", ("CAPACITOR BANKS.", "BLAST + ULT FILL FASTER.")),
)
TRACK_IDS = tuple(t.id for t in TRACKS)


def track_named(track_id):
    return next(t for t in TRACKS if t.id == track_id)


def cost(tier):
    """Price of the next tier for a track at this tier (None when maxed)."""
    return UPGRADE_COSTS[tier] if tier < UPGRADE_TIERS else None


def _mult(tiers, track_id):
    return track_named(track_id).multiplier(tiers.get(track_id, 0))


def apply(loadout, tiers):
    """The ship model with upgrades on top. tiers: {track id: tier}."""
    return replace(loadout,
                   max_hp=round(loadout.max_hp * _mult(tiers, "ARMOR")),
                   gun_damage=loadout.gun_damage * _mult(tiers, "GUNS"),
                   laser_dps=loadout.laser_dps * _mult(tiers, "LASER"),
                   max_speed=loadout.max_speed * _mult(tiers, "ENGINE"),
                   charge_rate=loadout.charge_rate * _mult(tiers, "CHARGE"))


def power_ratio(tiers):
    """Edge in the boss damage race over par: hull x the better weapon (they don't stack,
    one fires at a time). 1.0 = par; the hangar shows it as POWER %."""
    return _mult(tiers, "ARMOR") * max(_mult(tiers, "GUNS"), _mult(tiers, "LASER"))
