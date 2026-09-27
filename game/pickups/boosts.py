"""Boost pickups: temporary, automatic power (no key). The game runs them (flow/boosts.py)."""
from ..config.palette import BOOST_COLORS
from .art import MAGNET_ROWS, OVERDRIVE_ROWS, SHIELD_ROWS, SLOWDOWN_ROWS, TWIN_ROWS
from .base import Pickup


class Boost(Pickup):
    """Base: collecting it starts the boost `name` (BoostsMixin.start_boost)."""

    name = "BOOST"
    sound = "boost"

    def apply(self, game):
        return game.start_boost(self.name)


class Overdrive(Boost):
    """Fire rate x2 for a few seconds, white-hot flames."""
    name = "OVERDRIVE"
    rows = OVERDRIVE_ROWS
    glow = BOOST_COLORS[name]


class Shield(Boost):
    """A bubble that absorbs the next few hits."""
    name = "SHIELD"
    rows = SHIELD_ROWS
    glow = BOOST_COLORS[name]


class Magnet(Boost):
    """Every coin and pickup on screen flies to the ship."""
    name = "MAGNET"
    rows = MAGNET_ROWS
    glow = BOOST_COLORS[name]


class SlowDown(Boost):
    """Enemies, rocks and bullets at half speed; the ship stays at full speed."""
    name = "SLOW-MO"
    rows = SLOWDOWN_ROWS
    glow = BOOST_COLORS[name]


class TwinBoost(Boost):
    """A copy of the ship flies alongside and fires with it."""
    name = "TWIN"
    rows = TWIN_ROWS
    glow = BOOST_COLORS[name]


BOOSTS = {cls.name: cls for cls in (Overdrive, Shield, Magnet, SlowDown, TwinBoost)}
