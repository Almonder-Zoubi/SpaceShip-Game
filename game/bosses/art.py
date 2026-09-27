"""Shared boss art: hull colour key and the half -> full sprite pipeline."""
from ..core.pixelart import mirrored, outlined, sprite_from_rows

# Colour key shared by every boss hull (the Carrier and Mothership override a few keys).
HULL_COLORS = {
    "K": (18, 14, 30),
    "H": (52, 56, 78),
    "M": (88, 94, 118),
    "L": (136, 142, 164),
    "W": (196, 202, 218),
    "E": (206, 44, 62),
    "e": (122, 22, 46),
    "Y": (255, 214, 96),
    "y": (220, 120, 36),
    "G": (40, 40, 56),
    "g": (104, 104, 126),
    "V": (255, 110, 50),
}


def build_boss_sprite(half_rows, colors):
    """Left half drawn on a CharCanvas -> mirrored, outlined sprite."""
    return sprite_from_rows(outlined(mirrored(half_rows)), colors)
