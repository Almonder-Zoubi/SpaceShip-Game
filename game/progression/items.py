"""The item catalog: everything the player can own, the level gifts and the shop prices.

Item ids match the names the game uses (hull names, weapon names), so owning an item is a
simple lookup. A level gift offers 1 or 2 items; the one not chosen goes to the shop.
"""
from dataclasses import dataclass

SHIP, WEAPON = "SHIP", "WEAPON"          # item kinds = inventory tabs
UPGRADE = "UPGRADE"                      # the upgrades tab lists tracks, not items
TABS = (SHIP, WEAPON, UPGRADE)           # (wingmen and skins tabs come later)


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    kind: str                            # SHIP or WEAPON
    blurb: tuple                         # 1-2 short lines for the hangar and the gift cards
    price: int                           # shop price (after it was offered as a gift)


ITEMS = {item.id: item for item in (
    Item("ARROW", "ARROW", SHIP, ("THE ORIGINAL ROCKET.", "BALANCED ALL-ROUNDER."), 0),
    Item("WASP", "WASP", SHIP, ("SMALL, FAST, AGILE.", "FRAGILE, HITS HARDER."), 250),
    Item("TITAN", "TITAN", SHIP, ("HEAVY ARMOUR.", "WIDE AND SLOW."), 350),
    Item("LANCE", "LANCE", SHIP, ("LONG AND THIN.", "LASER SPECIALIST."), 350),
    Item("GUN", "MACHINE GUN", WEAPON, ("STREAM OF TRACERS.", "NEVER OVERHEATS."), 0),
    Item("LASER", "LASER", WEAPON, ("PIERCING BEAM.", "OVERHEATS WHEN HELD."), 200),
    Item("SPECIALS", "BLAST + ULTIMATE", WEAPON, ("HITS CHARGE A BLAST", "AND A MISSILE STORM."), 0),
    Item("OVERDRIVE", "OVERDRIVE BOOST", WEAPON, ("BOOST PICKUP: FIRE", "RATE X2 FOR 6 S."), 250),
)}
BLURB_CHARS = 21                         # a gift card fits this many characters per line

STARTER = ("ARROW", "GUN")               # what a new player owns

# Level key -> the gift offered after its first clear (1 item = fixed gift, 2 = choose one).
GIFTS = {
    "1-1": ("LASER", "WASP"),
    "1-2": ("SPECIALS",),                # level 3 is built around BLAST + ULTIMATE
    "1-3": ("TITAN", "LANCE"),
}


def items_of(kind):
    return tuple(item for item in ITEMS.values() if item.kind == kind)


def gift_level(item_id):
    """Key of the level whose gift offers this item (None if it's never a gift)."""
    return next((key for key, options in GIFTS.items() if item_id in options), None)
