"""Pickup sprites as character rows."""
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
PICKUP_COLORS = {
    "K": (18, 14, 30), "W": (250, 250, 245), "L": (170, 176, 196), "R": (228, 44, 64),
    "Y": (255, 204, 64), "y": (184, 120, 36), "C": (110, 226, 255), "B": (40, 120, 220),
}


def build_pickup(rows):
    return sprite_from_rows(rows, PICKUP_COLORS)
