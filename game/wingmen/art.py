"""Wingman sprites: 9x11 character rows; "G" is each type's own colour."""
import pygame

from ..config.palette import INK
from ..core.pixelart import sprite_from_rows

PIP_ROWS = (
    "....K....",
    "...KWK...",
    "...KGK...",
    "..KGWGK..",
    "..KGCGK..",
    ".KGGGGGK.",
    "KGKGGGKGK",
    "KGKGGGKGK",
    "KK.KGK.KK",
    "...KOK...",
    "....K....",
)
GUARDIAN_ROWS = (
    "...KKK...",
    "..KGGGK..",
    ".KGWWGGK.",
    "KGWGGGGGK",
    "KGGGCGGGK",
    "KGGCWCGGK",
    "KGGGCGGGK",
    "KGGGGGGDK",
    ".KGGGGDK.",
    "..KGGDK..",
    "...KKK...",
)
MEDIC_ROWS = (
    "....K....",
    "...KWK...",
    "..KWWWK..",
    ".KWWRWWK.",
    ".KWRRRWK.",
    ".KWWRWWK.",
    "KGKWWWKGK",
    "KGKWWWKGK",
    "KK.KWK.KK",
    "...KOK...",
    "....K....",
)
HUNTER_ROWS = (
    "....K....",
    "...KGK...",
    "K..KGK..K",
    "KWKGWGKWK",
    "KGKGCGKGK",
    "KGKGGGKGK",
    "KGGGGGGGK",
    "KKGGGGGKK",
    "..KGKGK..",
    "..KOKOK..",
    "...K.K...",
)
MAGPIE_ROWS = (
    ".........",
    "....K....",
    "...KGK...",
    "KK.KWK.KK",
    "KGKGGGKGK",
    "KGGGYGGGK",
    ".KGGGGGK.",
    "..KGGGK..",
    "..KGKGK..",
    "...KOK...",
    "....K....",
)

WINGMAN_COLORS = {
    "PIP": (96, 228, 128),
    "GUARDIAN": (90, 170, 255),
    "MEDIC": (255, 120, 140),
    "HUNTER": (255, 150, 50),
    "MAGPIE": (190, 120, 255),
}
BASE_COLORS = {"K": INK, "W": (250, 250, 245), "C": (190, 244, 255), "R": (228, 44, 64),
               "O": (72, 66, 84), "D": (60, 64, 90), "Y": (255, 204, 64)}

_cache = {}


def wingman_sprite(name, rows):
    """The sprite and its 4 quarter turns (a knocked-out wingman spins)."""
    if name not in _cache:
        colors = dict(BASE_COLORS, G=WINGMAN_COLORS[name])
        image = sprite_from_rows(rows, colors)
        _cache[name] = [pygame.transform.rotate(image, -90 * i) for i in range(4)]
    return _cache[name]
