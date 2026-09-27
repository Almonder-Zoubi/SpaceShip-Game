"""Pictures of inventory items for the hangar and the gift screen: ship previews (2x, with
engine flames), weapon and upgrade icons (3x) and dark silhouettes for locked items."""
import math

import pygame

from ..config.palette import FLAME, INK
from ..core.pixelart import sprite_from_rows
from ..player.art import SHIP_PALETTES, build_ship_frames
from ..player.hulls import hull_named
from ..progression.items import ITEMS, SHIP, WINGMAN
from ..wingmen.art import wingman_sprite
from ..wingmen.types import WINGMEN

PREVIEW_SCALE = 2
ICON_SCALE = 3
WINGMAN_SCALE = 4

ICON_ROWS = {
    "GUN": (
        "..Y.....Y..",
        "..Y.....Y..",
        "...........",
        "..Y.....Y..",
        "..y.....y..",
        "...........",
        ".KGK...KGK.",
        ".KGK...KGK.",
        ".KGK...KGK.",
        "KGGGKKKGGGK",
        "KGDGGGGGDGK",
        "KGGGGGGGGGK",
        ".KKKKKKKKK.",
    ),
    "LASER": (
        "....CWC....",
        "....CWC....",
        "....BCB....",
        "....CWC....",
        "....BCB....",
        "....CWC....",
        "...KBCBK...",
        "..KGGCGGK..",
        ".KGGBWBGGK.",
        ".KGDBBBDGK.",
        ".KGGGGGGGK.",
        "..KKKKKKK..",
        "...........",
    ),
    "SPECIALS": (
        ".....K.....",
        "....KWK....",
        "....KRK....",
        "....KWK....",
        "....KWK....",
        "....KWK....",
        "...KKWKK...",
        "..KRKWKRK..",
        "..KRKWKRK..",
        "...KKKKK...",
        "....YYY....",
        "....yYy....",
        ".....y.....",
    ),
    "OVERDRIVE": (
        "..KKKKKKK..",
        ".KYYYYYYYK.",
        "KYWKYWKYWKK",
        "KYKYWKYWKYK",
        "KKYWKYWKYyK",
        "KYWKYWKYWKK",
        "KYKYWKYWKYK",
        "KKYWKYWKYyK",
        "KYWKYWKYWKK",
        ".KyyyyyyyK.",
        "..KKKKKKK..",
        "...........",
        "...........",
    ),
}
# Upgrade track icons (hangar UPGRADES tab), same colour keys.
UPGRADE_ICON_ROWS = {
    "ARMOR": (
        ".KKKKKKKKK.",
        "KWWWWWWWWGK",
        "KWGGGRGGGDK",
        "KWGGRRRGGDK",
        "KWGRRRRRGDK",
        "KWGGRRRGGDK",
        "KWGGGRGGGDK",
        ".KWGGGGGDK.",
        ".KWGGGGGDK.",
        "..KWGGGDK..",
        "...KWGDK...",
        "....KDK....",
        ".....K.....",
    ),
    "GUNS": (
        ".....K.....",
        "....KWK....",
        "...KYWyK...",
        "...KYYyK...",
        "...KYYyK...",
        "..KKKKKKK..",
        "..KGWGGDK..",
        "..KGWGGDK..",
        "..KGWGGDK..",
        "..KGWGGDK..",
        "..KDDDDDK..",
        "..KKKKKKK..",
        "...........",
    ),
    "LASER": (
        ".....C.....",
        ".....W.....",
        ".....C.....",
        ".....W.....",
        "....KCK....",
        "..KKBWBKK..",
        ".KGBCWCBGK.",
        ".KGBCWCBGK.",
        ".KGDBBBDGK.",
        "..KGGGGGK..",
        "..KDGGGDK..",
        "...KKKKK...",
        "...........",
    ),
    "ENGINE": (
        "...KKKKK...",
        "..KGWGGDK..",
        "..KGWGGDK..",
        "..KDDDDDK..",
        "...KGGDK...",
        "..KGWGGDK..",
        ".KGWGGGGDK.",
        "KKKKKKKKKKK",
        "...YYWYY...",
        "....YWY....",
        "....yYy....",
        ".....y.....",
        "...........",
    ),
    "CHARGE": (
        "......KKK..",
        ".....KYWK..",
        "....KYWK...",
        "...KYWK....",
        "..KYWYKKK..",
        ".KYYYYYYK..",
        ".KKKKYYK...",
        "....KYyK...",
        "...KYyK....",
        "...KyK.....",
        "..KyK......",
        "..KK.......",
        "...........",
    ),
}
ICON_COLORS = {
    "K": INK, "W": (250, 250, 245), "G": (160, 166, 184), "D": (86, 90, 112),
    "Y": (255, 204, 64), "y": (184, 120, 36), "C": (170, 244, 255), "B": (70, 180, 255),
    "R": (228, 44, 64),
}


class ItemArt:
    """Builds and caches item pictures; draw() puts one centred on a point."""

    def __init__(self):
        self._cache = {}

    def image(self, item_id, paint, locked=False):
        key = (item_id, paint, locked)
        if key not in self._cache:
            kind = ITEMS[item_id].kind
            if kind == SHIP:
                hull = hull_named(item_id)
                frame = build_ship_frames(hull.rows, SHIP_PALETTES[paint])[0]
                scale = PREVIEW_SCALE
            elif kind == WINGMAN:
                frame = wingman_sprite(item_id, WINGMEN[item_id].rows)[0]
                scale = WINGMAN_SCALE
            else:
                frame = sprite_from_rows(ICON_ROWS[item_id], ICON_COLORS)
                scale = ICON_SCALE
            w, h = frame.get_size()
            image = pygame.transform.scale(frame, (w * scale, h * scale))
            if locked:                        # dark silhouette: shape visible, details hidden
                image = pygame.mask.from_surface(image).to_surface(
                    setcolor=(*INK, 255), unsetcolor=(0, 0, 0, 0))
            self._cache[key] = image
        return self._cache[key]

    def upgrade_icon(self, track_id):
        key = ("upgrade", track_id)
        if key not in self._cache:
            frame = sprite_from_rows(UPGRADE_ICON_ROWS[track_id], ICON_COLORS)
            w, h = frame.get_size()
            self._cache[key] = pygame.transform.scale(frame, (w * ICON_SCALE, h * ICON_SCALE))
        return self._cache[key]

    def draw(self, surf, item_id, paint, center, time, locked=False, lively=False):
        """lively: bob and (for ships) engine flames — for the selected item."""
        image = self.image(item_id, paint, locked)
        w, h = image.get_size()
        bob = int(math.sin(time * 3) * 2) if lively else 0
        x, y = center[0] - w // 2, center[1] - h // 2 + bob
        if lively and not locked and ITEMS[item_id].kind == SHIP:
            self._flames(surf, hull_named(item_id), x + w / 2, y + h, time)
        surf.blit(image, (x, y))

    @staticmethod
    def _flames(surf, hull, cx, bottom, time):
        """Flickering engine flames under a ship preview."""
        length = int((5 + 3 * abs(math.sin(time * 23))) * hull.flame) * PREVIEW_SCALE // 2
        for off in hull.nozzles:
            x = int(cx + off * PREVIEW_SCALE)
            for i in range(length):
                color = FLAME[min(len(FLAME) - 1, i * len(FLAME) // max(1, length))]
                surf.fill(color, (x - 1, int(bottom) + i, 2, 1), special_flags=pygame.BLEND_ADD)
