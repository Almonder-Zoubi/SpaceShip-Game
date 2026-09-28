"""The item catalog: everything the player can own, the level gifts and the shop prices.

Item ids match the names the game uses (hull names, weapon names), so owning an item is a
simple lookup. A level gift offers 1 or 2 items; the one not chosen goes to the shop.
"""
from dataclasses import dataclass

SHIP, WEAPON, WINGMAN, SKIN = "SHIP", "WEAPON", "WINGMAN", "SKIN"   # kinds = inventory tabs
UPGRADE = "UPGRADE"                      # the upgrades tab lists tracks, not items
PRIMARY, SECONDARY = "PRIMARY", "SECONDARY"   # weapon slots
PAINT, TRAIL, TRACER, BEAM, DEATH = "PAINT", "TRAIL", "TRACER", "BEAM", "DEATH"   # skin slots
TABS = (SHIP, WEAPON, WINGMAN, UPGRADE, SKIN)


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    kind: str                            # SHIP, WEAPON or WINGMAN
    blurb: tuple                         # 1-2 short lines for the hangar and the gift cards
    price: int                           # shop price (after it was offered as a gift)
    sold_after: str = None               # never a gift: in the shop once this level is cleared
    slot: str = None                     # weapons: PRIMARY / SECONDARY; skins: PAINT, TRAIL ...
    hint: str = None                     # how a locked item is earned (achievement skins)
    look: str = None                     # skins: palette / colour key it stands for


ITEMS = {item.id: item for item in (
    Item("ARROW", "ARROW", SHIP, ("THE ORIGINAL ROCKET.", "BALANCED ALL-ROUNDER."), 0),
    Item("WASP", "WASP", SHIP, ("SMALL, FAST, AGILE.", "FRAGILE, HITS HARDER."), 250),
    Item("TITAN", "TITAN", SHIP, ("HEAVY ARMOUR.", "WIDE AND SLOW."), 350),
    Item("LANCE", "LANCE", SHIP, ("LONG AND THIN.", "LASER SPECIALIST."), 350),
    Item("SPECTER", "SPECTER", SHIP, ("THE SECRET HULL.", "SWIFT, HITS HARD."), 500),
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
    Item("SIDE CANNONS", "SIDE CANNONS", WEAPON, ("SECONDARY: FIRES AT", "WHATEVER IS BESIDE."),
         300, slot=SECONDARY),
    Item("SPECIALS", "BLAST + ULTIMATE", WEAPON, ("HITS CHARGE A BLAST", "AND A MISSILE STORM."), 0),
    Item("OVERDRIVE", "OVERDRIVE BOOST", WEAPON, ("BOOST PICKUP: FIRE", "RATE X2 FOR 6 S."), 250),
    Item("PIP", "PIP", WINGMAN, ("WINGMAN: A GUNNER", "WHO FIRES WITH YOU."), 300),
    Item("GUARDIAN", "GUARDIAN", WINGMAN, ("WINGMAN: ORBITS YOU,", "BLOCKS BULLETS."), 300),
    Item("HUNTER", "HUNTER", WINGMAN, ("WINGMAN: HOMING", "ROCKETS AT MINIONS."), 350),
    Item("MEDIC", "MEDIC", WINGMAN, ("WINGMAN: REPAIRS YOUR", "HULL BETWEEN HITS."), 350),
    Item("MAGPIE", "MAGPIE", WINGMAN, ("WINGMAN: PULLS IN", "COINS FROM AFAR."), 300,
         sold_after="1-4"),
    # Skins never change stats. Starter ones are the defaults of each slot.
    Item("MK PAINT", "MK PAINT", SKIN, ("THE PAINT OF EACH", "LEVEL'S SHIP MODEL."), 0,
         slot=PAINT, look=None),
    Item("SOLAR", "SOLAR PAINT", SKIN, ("GOLD AND RED, HOT", "AS A STAR."), 300, slot=PAINT,
         look="solar"),
    Item("RETRO", "RETRO PAINT", SKIN, ("THE CARTRIDGE", "CLASSIC: RED + BLUE."), 400,
         slot=PAINT, look="retro", sold_after="1-1"),
    Item("STEALTH", "STEALTH PAINT", SKIN, ("BLACK AND GREY.", "SILENT AND DEADLY."), 400,
         slot=PAINT, look="stealth", sold_after="1-2"),
    Item("NEON", "NEON PAINT", SKIN, ("MAGENTA AND CYAN,", "STRAIGHT FROM 1985."), 0,
         slot=PAINT, look="neon", hint="ACHIEVEMENT: RANK S"),
    Item("GOLD TRIM", "GOLD TRIM", SKIN, ("PURE GOLD. EARNED,", "NEVER BOUGHT."), 0,
         slot=PAINT, look="gold", hint="ACHIEVEMENT: NO-HIT BOSS"),
    Item("SWARMBANE", "SWARMBANE PAINT", SKIN, ("BLACK CHITIN, ACID", "GREEN. THE MEDAL."), 0,
         slot=PAINT, look="swarmbane"),
    Item("VEIL", "VEIL PAINT", SKIN, ("VOID BLACK, VIOLET", "TRIM. BLEND IN."), 0,
         slot=PAINT, look="veil"),
    Item("CLASSIC TRAIL", "CLASSIC TRAIL", SKIN, ("ORANGE ROCKET", "FLAMES."), 0, slot=TRAIL,
         look="CLASSIC"),
    Item("PLASMA BLUE", "PLASMA TRAIL", SKIN, ("BLUE-HOT ENGINE", "FLAMES."), 200, slot=TRAIL,
         look="PLASMA BLUE", sold_after="1-1"),
    Item("TOXIC", "TOXIC TRAIL", SKIN, ("RADIOACTIVE GREEN", "EXHAUST."), 0, slot=TRAIL,
         look="TOXIC", hint="ACHIEVEMENT: 100 MINIONS"),
    Item("RAINBOW", "RAINBOW TRAIL", SKIN, ("THE FEVER LOOK,", "ALL THE TIME."), 0, slot=TRAIL,
         look="RAINBOW", hint="ACHIEVEMENT: REACH FEVER"),
    Item("HEARTS", "HEARTS TRAIL", SKIN, ("A SECRET FOR THE", "GENTLE PILOT."), 0, slot=TRAIL,
         look="HEARTS", hint="ACHIEVEMENT: ???"),
    Item("STARDUST", "STARDUST TRAIL", SKIN, ("A WAKE OF STARS", "AND MOONDUST."), 0,
         slot=TRAIL, look="STARDUST", hint="ACHIEVEMENT: EXPLORER"),
    Item("GOLD TRACERS", "GOLD TRACERS", SKIN, ("CLASSIC GOLDEN GUN", "TRACERS."), 0,
         slot=TRACER, look="GOLD"),
    Item("CYAN TRACERS", "CYAN TRACERS", SKIN, ("ICE-BLUE GUN", "TRACERS."), 150, slot=TRACER,
         look="CYAN", sold_after="1-1"),
    Item("WHITE TRACERS", "WHITE TRACERS", SKIN, ("BRIGHT WHITE GUN", "TRACERS."), 150,
         slot=TRACER, look="WHITE", sold_after="1-1"),
    Item("EMERALD TRACERS", "EMERALD TRACERS", SKIN, ("GREEN GUN", "TRACERS."), 150,
         slot=TRACER, look="EMERALD", sold_after="1-2"),
    Item("BLUE BEAM", "BLUE BEAM", SKIN, ("THE CLASSIC BLUE", "LASER."), 0, slot=BEAM,
         look="BLUE"),
    Item("EMERALD BEAM", "EMERALD BEAM", SKIN, ("A GREEN LASER", "BEAM."), 150, slot=BEAM,
         look="EMERALD", sold_after="1-1"),
    Item("VIOLET BEAM", "VIOLET BEAM", SKIN, ("A VIOLET LASER", "BEAM."), 150, slot=BEAM,
         look="VIOLET", sold_after="1-2"),
    Item("CLASSIC BOOM", "CLASSIC BOOM", SKIN, ("FIRE, SMOKE AND", "DEBRIS."), 0, slot=DEATH,
         look="CLASSIC"),
    Item("PIXEL SHATTER", "PIXEL SHATTER", SKIN, ("THE SHIP BREAKS", "INTO PIXELS."), 200,
         slot=DEATH, look="SHATTER", sold_after="1-1"),
    Item("SUPERNOVA", "SUPERNOVA", SKIN, ("GO OUT LIKE A STAR.",), 0, slot=DEATH,
         look="SUPERNOVA", hint="ACHIEVEMENT: WIN THE GAME"),
)}
BLURB_CHARS = 21                         # a gift card fits this many characters per line

STARTER = ("ARROW", "GUN", "MK PAINT", "CLASSIC TRAIL", "GOLD TRACERS", "BLUE BEAM",
           "CLASSIC BOOM")               # what a new player owns (skins: the defaults)
DEFAULT_SKINS = {PAINT: "MK PAINT", TRAIL: "CLASSIC TRAIL", TRACER: "GOLD TRACERS",
                 BEAM: "BLUE BEAM", DEATH: "CLASSIC BOOM"}

# Level key -> the gift offered after its first clear (1 item = fixed gift, 2 = choose one).
GIFTS = {
    "1-1": ("LASER", "WASP"),
    "1-2": ("SPECIALS",),                # level 3 is built around BLAST + ULTIMATE
    "1-3": ("TITAN", "LANCE"),
    "1-4": ("PIP", "GUARDIAN"),          # the wingman slot opens
    "1-5": ("SCATTER", "OVERDRIVE"),
    "1-6": ("ROCKET POD", "HUNTER"),
    "1-7": ("PLASMA", "SOLAR"),
    "1-8": ("SIDE CANNONS", "MEDIC"),
    "1-9": ("ARC", "SPECTER"),
    "1-10": ("SWARMBANE",),             # the galaxy medal's paint job
    "2-1": ("VEIL",),
}


def items_of(kind):
    return tuple(item for item in ITEMS.values() if item.kind == kind)


def gift_level(item_id):
    """Key of the level whose gift offers this item (None if it's never a gift)."""
    return next((key for key, options in GIFTS.items() if item_id in options), None)
