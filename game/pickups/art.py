"""Pickup sprites as character rows (coins: one row set per spin frame)."""
from ..core.pixelart import sprite_from_rows

KIT_SMALL_ROWS = (
    "...KKK...",
    "..K...K..",
    "KKKKKKKKK",
    "KWWWRWWWK",
    "KWWRRRWWK",
    "KWWWRWWWK",
    "KLLLLLLLK",
    "KKKKKKKKK",
)
KIT_FULL_ROWS = (
    "....KKK....",
    "...K...K...",
    "KKKKKKKKKKK",
    "KYYYYWYYYYK",
    "KYYYWRWYYYK",
    "KYYWRRRWYYK",
    "KYYYWRWYYYK",
    "KYYYYWYYYYK",
    "KyyyyyyyyyK",
    "KKKKKKKKKKK",
)
POWER_ROWS = (
    "....K....",
    "...KCK...",
    "..KCBCK..",
    ".KCBWBCK.",
    "KCBWWWBCK",
    ".KCBWBCK.",
    "..KCBCK..",
    "...KCK...",
    "....K....",
)
# A coin spins: face, narrower, edge (played face, narrow, edge, narrow).
COIN_FRAMES = (
    ("..KKK..",
     ".KYYYK.",
     "KYWYYyK",
     "KYYWYyK",
     "KYYYYyK",
     ".KyyyK.",
     "..KKK.."),
    (".KKK.",
     "KYWyK",
     "KYYyK",
     "KYWyK",
     "KYYyK",
     "KYyyK",
     ".KKK."),
    (".K.",
     "KWK",
     "KYK",
     "KYK",
     "KYK",
     "KyK",
     ".K."),
)
BIG_COIN_FRAMES = (
    ("...KKK...",
     ".KKYYYKK.",
     ".KYWYYyK.",
     "KYWYyyYyK",
     "KYYyYYyyK",
     "KYYyyyYyK",
     ".KYYYYyK.",
     ".KKyyyKK.",
     "...KKK..."),
    ("..KKK..",
     ".KYWYK.",
     "KYWyYyK",
     "KYyYyyK",
     "KYyyYyK",
     "KYYYYyK",
     "KYYyyyK",
     ".KyyyK.",
     "..KKK.."),
    (".KKK.",
     "KWYyK",
     "KWyyK",
     "KYYyK",
     "KYyyK",
     "KYYyK",
     "KYyyK",
     "KYyyK",
     ".KKK."),
)
# Boosts: 9x9 icons in a dark capsule.
OVERDRIVE_ROWS = (
    "..KKKKK..",
    ".KOOOOOK.",
    "KOWOOWOOK",
    "KOOWOOWOK",
    "KOOOWOOWK",
    "KOOWOOWOK",
    "KOWOOWOOK",
    ".KOOOOOK.",
    "..KKKKK..",
)
SHIELD_ROWS = (
    "..KKKKK..",
    ".KCCCCCK.",
    "KCW...BCK",
    "KC.....CK",
    "KC..W..CK",
    "KC.....CK",
    "KCB...BCK",
    ".KCCCCCK.",
    "..KKKKK..",
)
MAGNET_ROWS = (
    "..KKKKK..",
    ".KRRKLLK.",
    "KRRK.KLLK",
    "KRK...KLK",
    "KRK...KLK",
    "KRK...KLK",
    "KRRKKKLLK",
    ".KRRRLLK.",
    "..KKKKK..",
)
SLOWDOWN_ROWS = (
    "..KKKKK..",
    ".KPPPPPK.",
    "KKWWWWWKK",
    ".KPWWWPK.",
    "..KPWPK..",
    ".KPPWPPK.",
    "KKPWWWPKK",
    ".KPPPPPK.",
    "..KKKKK..",
)
PICKUP_COLORS = {
    "K": (18, 14, 30), "W": (250, 250, 245), "L": (170, 176, 196), "R": (228, 44, 64),
    "Y": (255, 204, 64), "y": (184, 120, 36), "C": (110, 226, 255), "B": (40, 120, 220),
    "O": (255, 150, 40), "P": (170, 110, 255),
}


def build_pickup(rows):
    return sprite_from_rows(rows, PICKUP_COLORS)
