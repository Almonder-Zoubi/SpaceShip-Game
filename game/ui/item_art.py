"""Pictures of inventory items for the hangar and the gift screen: ship previews (2x, with
engine flames), weapon and upgrade icons (3x) and dark silhouettes for locked items."""
import math

import pygame

from ..config.palette import BEAMS, FLAME, INK, RAINBOW, TRACERS, TRAILS
from ..core.pixelart import sprite_from_rows
from ..player.art import SHIP_PALETTES, build_ship_frames
from ..player.hulls import hull_named
from ..progression.items import BEAM, ITEMS, PAINT, SHIP, TRACER, TRAIL, WINGMAN
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
    "SCATTER": (
        "Y....Y....Y",
        ".Y...Y...Y.",
        "..y..Y..y..",
        "...........",
        "..y..y..y..",
        "...........",
        "...KKKKK...",
        "..KGGGGGK..",
        ".KGDGGGDGK.",
        ".KGGGGGGGK.",
        ".KDGGGGGDK.",
        "..KKKKKKK..",
        "...........",
    ),
    "PLASMA": (
        "....KKK....",
        "...KPPPK...",
        "..KPWWPPK..",
        "..KPWPPPK..",
        "..KPPPPpK..",
        "...KPPpK...",
        "....KKK....",
        "...........",
        "...KGGGK...",
        "..KGPPPGK..",
        ".KGGGGGGGK.",
        ".KDGGGGGDK.",
        "..KKKKKKK..",
    ),
    "ARC": (
        "C.........C",
        ".C...W...C.",
        "..C.W.W.C..",
        "...W...W...",
        "....C.C....",
        ".....W.....",
        "....KWK....",
        "...KGCGK...",
        "..KGBWBGK..",
        ".KGGBCBGGK.",
        ".KDGGGGGDK.",
        "..KKKKKKK..",
        "...........",
    ),
    "ROCKET POD": (
        "..K.....K..",
        ".KWK...KWK.",
        ".KRK...KRK.",
        ".KWK...KWK.",
        ".KWK...KWK.",
        ".KKK...KKK.",
        ".YYY...YYY.",
        "..y.....y..",
        "...........",
        "KKKKKKKKKKK",
        "KGGGGGGGGGK",
        "KDGDGDGDGDK",
        "KKKKKKKKKKK",
    ),
    "SIDE CANNONS": (
        "...........",
        "...........",
        "....KKK....",
        "...KGGGK...",
        "Y.KGGWGGK.Y",
        "yYKGCCCGKYy",
        "Y.KGGGGGK.Y",
        "..KGDGDGK..",
        "...KGGGK...",
        "....KKK....",
        "...........",
        "...........",
        "...........",
    ),
    # --- galaxy 2: abilities (SHIFT) and the WING BAY ---
    "PHASE": (
        "...........",
        "..pp.PP.KK.",
        ".pp.PP.KWWK",
        "pp.PP.KWGGK",
        ".pp.PP.KWWK",
        "..pp.PP.KK.",
        "...........",
        "..pp.PP.KK.",
        ".pp.PP.KWWK",
        "pp.PP.KWGGK",
        ".pp.PP.KWWK",
        "..pp.PP.KK.",
        "...........",
    ),
    "FLARE": (
        ".....Y.....",
        "..Y..Y..Y..",
        "...Y.Y.Y...",
        "....YWY....",
        "YYYYWWWYYYY",
        "....YWY....",
        "...Y.Y.Y...",
        "..Y..Y..Y..",
        ".....y.....",
        "....KGK....",
        "....KGK....",
        "....KDK....",
        ".....K.....",
    ),
    "TIME SLIP": (
        "..KKKKKKK..",
        ".KPPPPPPPK.",
        "..KpWWWpK..",
        "...KpWpK...",
        "....KpK....",
        ".....K.....",
        "....KPK....",
        "...KPWPK...",
        "..KPWWWPK..",
        ".KpWWWWWpK.",
        ".KPPPPPPPK.",
        "..KKKKKKK..",
        "...........",
    ),
    "REPAIR DRONE": (
        "...........",
        "....KKK....",
        "...KGGGK...",
        "..KGDDDGK..",
        "KKKGDWDGKKK",
        "KGGGDDDGGGK",
        "KKKKGGGKKKK",
        "....KGK....",
        "...KWWWK...",
        "..KWKWKWK..",
        "..KWWWWWK..",
        "...KKKKK...",
        "...........",
    ),
    "DECOY": (
        ".....K.....",
        "....KWK..p.",
        "....KWK.pPp",
        "...KWBWK.p.",
        "...KWWWK.p.",
        "..KRKWKRKp.",
        "..KRKWKRKp.",
        "...KKKKK...",
        ".p.p.p.p.p.",
        "...........",
        "...........",
        "...........",
        "...........",
    ),
    "WING BAY": (
        "...........",
        "..K.....K..",
        ".KGK...KGK.",
        ".KGK...KGK.",
        "KGBGK.KGBGK",
        "KGGGK.KGGGK",
        ".KYK...KYK.",
        "...........",
        "KKKKKKKKKKK",
        "KDDDDDDDDDK",
        "KDGGGGGGGDK",
        "KKKKKKKKKKK",
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
    "R": (228, 44, 64), "P": (170, 110, 255), "p": (100, 60, 190),
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

    def draw_skin(self, surf, item, hull_name, paint, center, time, locked=False):
        """Preview of a skin: the ship in that paint / with that trail, tracer or beam
        streaks, or a burst for a death style."""
        cx, cy = center
        if locked:
            surf.blit(self._silhouette(hull_name), self._silhouette(hull_name).get_rect(
                center=center))
            return
        if item.slot in (PAINT, TRAIL):
            look = item.look if item.slot == PAINT and item.look else paint
            key = (hull_name, look)
            if key not in self._cache:
                frame = build_ship_frames(hull_named(hull_name).rows, SHIP_PALETTES[look])[0]
                w, h = frame.get_size()
                self._cache[key] = pygame.transform.scale(frame, (w * PREVIEW_SCALE,
                                                                  h * PREVIEW_SCALE))
            image = self._cache[key]
            w, h = image.get_size()
            x, y = cx - w // 2, cy - h // 2 + int(math.sin(time * 3) * 2)
            colors = TRAILS[item.look] if item.slot == TRAIL else FLAME
            self._flames(surf, hull_named(hull_name), x + w / 2, y + h, time, colors,
                         long=item.slot == TRAIL)
            surf.blit(image, (x, y))
        elif item.slot == TRACER:
            colors = TRACERS[item.look]
            for i, dx in enumerate((-16, 0, 16)):
                y0 = cy + 30 - int((time * 90 + i * 25) % 70)
                surf.fill(colors[0], (cx + dx - 1, y0, 2, 3))
                for j in range(1, 8):
                    surf.fill(colors[min(len(colors) - 1, j // 3 + 1)], (cx + dx, y0 + 2 + j, 1, 1))
        elif item.slot == BEAM:
            colors = BEAMS[item.look]
            for dx, c in ((-3, 3), (-2, 2), (-1, 1), (0, 0), (1, 1), (2, 2), (3, 3)):
                if c < len(colors):
                    surf.fill(colors[c], (cx + dx, cy - 40, 1, 80))
        else:
            k = (time % 1.2) / 1.2
            colors = {"SHATTER": [(200, 204, 220)] * 3, "SUPERNOVA": RAINBOW}.get(item.look,
                                                                                    FLAME)
            for i in range(16):
                a = i * math.tau / 16
                r = 6 + 34 * k
                surf.fill(colors[i % len(colors)],
                          (int(cx + math.cos(a) * r), int(cy + math.sin(a) * r), 2, 2))
            pygame.draw.circle(surf, colors[0], center, int(4 + 40 * k), 1)

    def _silhouette(self, hull_name):
        key = ("silhouette", hull_name)
        if key not in self._cache:
            frame = build_ship_frames(hull_named(hull_name).rows, SHIP_PALETTES["mk1"])[0]
            w, h = frame.get_size()
            image = pygame.transform.scale(frame, (w * PREVIEW_SCALE, h * PREVIEW_SCALE))
            self._cache[key] = pygame.mask.from_surface(image).to_surface(
                setcolor=(*INK, 255), unsetcolor=(0, 0, 0, 0))
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
    def _flames(surf, hull, cx, bottom, time, colors=FLAME, long=False):
        """Flickering engine flames under a ship preview."""
        length = int((5 + 3 * abs(math.sin(time * 23))) * hull.flame) * PREVIEW_SCALE // 2
        length = length * 2 if long else length
        for off in hull.nozzles:
            x = int(cx + off * PREVIEW_SCALE)
            for i in range(length):
                color = colors[min(len(colors) - 1, i * len(colors) // max(1, length))]
                surf.fill(color, (x - 1, int(bottom) + i, 2, 1), special_flags=pygame.BLEND_ADD)
