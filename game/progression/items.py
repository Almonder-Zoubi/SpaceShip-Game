"""The item catalog: everything the player can own, the level gifts and the shop prices.

Item ids match the names the game uses (hull names, weapon names), so owning an item is a
simple lookup. A level gift offers 1 or 2 items; the one not chosen goes to the shop.
"""
from dataclasses import dataclass

SHIP, WEAPON, WINGMAN = "SHIP", "WEAPON", "WINGMAN"   # item kinds = inventory tabs
UPGRADE = "UPGRADE"                      # the upgrades tab lists tracks, not items
PRIMARY, SECONDARY = "PRIMARY", "SECONDARY"   # weapon slots
TABS = (SHIP, WEAPON, WINGMAN, UPGRADE)  # (the skins tab comes later)


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    kind: str                            # SHIP, WEAPON or WINGMAN
    blurb: tuple                         # 1-2 short lines for the hangar and the gift cards
    price: int                           # shop price (after it was offered as a gift)
    sold_after: str = None               # never a gift: in the shop once this level is cleared
    slot: str = None                     # weapons: PRIMARY (R switches 2) or SECONDARY (auto)


ITEMS = {item.id: item for item in (
    Item("ARROW", "ARROW", SHIP, ("THE ORIGINAL ROCKET.", "BALANCED ALL-ROUNDER."), 0),
    Item("WASP", "WASP", SHIP, ("SMALL, FAST, AGILE.", "FRAGILE, HITS HARDER."), 250),
    Item("TITAN", "TITAN", SHIP, ("HEAVY ARMOUR.", "WIDE AND SLOW."), 350),
    Item("LANCE", "LANCE", SHIP, ("LONG AND THIN.", "LASER SPECIALIST."), 350),
    Item("GUN", "MACHINE GUN", WEAPON, ("STREAM OF TRACERS.", "NEVER OVERHEATS."), 0,
         slot=PRIMARY),
    Item("LASER", "LASER", WEAPON, ("PIERCING BEAM.", "OVERHEATS WHEN HELD."), 200,
         slot=PRIMARY),
    Item("SCATTER", "SCATTER", WEAPON, ("5-PELLET SHOTGUN.", "BRUTAL UP CLOSE."), 300,
         slot=PRIMARY),
    Item("PLASMA", "PLASMA", WEAPON, ("SLOW BIG ORBS THAT", "PIERCE 3 TARGETS."), 350,
         slot=PRIMARY),
    Item("ARC", "ARC", WEAPON, ("LIGHTNING THAT JUMPS", "TO 3 TARGETS."), 400, slot=PRIMARY),
    Item("ROCKET POD", "ROCKET POD", WEAPON, ("SECONDARY: 2 HOMING", "ROCKETS EVERY 1.8 S."),
         300, slot=SECONDARY),
    Item("SIDE CANNONS", "SIDE CANNONS", WEAPON, ("SECONDARY: FIRES AT", "WHAT FLIES BESIDE YOU."),
         300, slot=SECONDARY),
    Item("SPECIALS", "BLAST + ULTIMATE", WEAPON, ("HITS CHARGE A BLAST", "AND A MISSILE STORM."), 0),
    Item("OVERDRIVE", "OVERDRIVE BOOST", WEAPON, ("BOOST PICKUP: FIRE", "RATE X2 FOR 6 S."), 250),
    Item("PIP", "PIP", WINGMAN, ("WINGMAN: A GUNNER", "THAT FIRES WITH YOU."), 300),
    Item("GUARDIAN", "GUARDIAN", WINGMAN, ("WINGMAN: ORBITS YOU,", "BLOCKS BULLETS."), 300),
    Item("HUNTER", "HUNTER", WINGMAN, ("WINGMAN: HOMING", "ROCKETS AT MINIONS."), 350),
    Item("MEDIC", "MEDIC", WINGMAN, ("WINGMAN: REPAIRS YOUR", "HULL BETWEEN HITS."), 350),
    Item("MAGPIE", "MAGPIE", WINGMAN, ("WINGMAN: PULLS IN", "COINS FROM AFAR."), 300,
         sold_after="1-4"),
)}
BLURB_CHARS = 21                         # a gift card fits this many characters per line

STARTER = ("ARROW", "GUN")               # what a new player owns

# Level key -> the gift offered after its first clear (1 item = fixed gift, 2 = choose one).
GIFTS = {
    "1-1": ("LASER", "WASP"),
    "1-2": ("SPECIALS",),                # level 3 is built around BLAST + ULTIMATE
    "1-3": ("TITAN", "LANCE"),
    "1-4": ("PIP", "GUARDIAN"),          # the wingman slot opens
}


def items_of(kind):
    return tuple(item for item in ITEMS.values() if item.kind == kind)


def gift_level(item_id):
    """Key of the level whose gift offers this item (None if it's never a gift)."""
    return next((key for key, options in GIFTS.items() if item_id in options), None)
