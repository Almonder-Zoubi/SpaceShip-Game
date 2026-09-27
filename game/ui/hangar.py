"""Hangar screen: the four hulls side by side, stats of the selected one."""
import math

import pygame

from ..config.display import LOW_W
from ..config.palette import ACCENT, EMPTY, FLAME, GOOD, INK, TEXT, TEXT_DIM, TEXT_SHADOW
from ..player.art import SHIP_PALETTES, build_ship_frames
from ..player.hulls import HULLS

SLOT_W = LOW_W // len(HULLS)
SHIP_Y = 72                       # centre line of the 2x ship previews
PREVIEW_SCALE = 2


class HangarScreen:
    """Draws the hangar. Knows nothing about game state beyond what draw() is given."""

    def __init__(self, font):
        self.font = font
        self._art = {}            # (hull name, paint) -> (2x preview, mask pixel count)

    def _preview(self, hull, paint):
        key = (hull.name, paint)
        if key not in self._art:
            frame = build_ship_frames(hull.rows, SHIP_PALETTES[paint])[0]
            w, h = frame.get_size()
            big = pygame.transform.scale(frame, (w * PREVIEW_SCALE, h * PREVIEW_SCALE))
            self._art[key] = (big, pygame.mask.from_surface(frame).count())
        return self._art[key]

    def draw(self, surf, cursor, base_loadout, level_number, time, blink):
        f = self.font
        f.draw(surf, "HANGAR", (LOW_W // 2, 6), ACCENT, scale=2, shadow=TEXT_SHADOW, center=True)
        f.draw(surf, "CHOOSE YOUR SHIP", (LOW_W // 2, 24), TEXT_DIM, shadow=TEXT_SHADOW,
               center=True)
        paint = base_loadout.colors
        for i, hull in enumerate(HULLS):
            self._slot(surf, i, hull, paint, i == cursor, time)
        self._stats(surf, HULLS[cursor], base_loadout, paint)
        f.draw(surf, f"STARTS AT LEVEL {level_number}  -  {base_loadout.name}",
               (LOW_W // 2, 208), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(surf, "LEFT/RIGHT CHOOSE   ENTER LAUNCH   ESC BACK", (LOW_W // 2, 222), TEXT,
                   shadow=TEXT_SHADOW, center=True)

    def _slot(self, surf, i, hull, paint, selected, time):
        cx = SLOT_W * i + SLOT_W // 2
        image, _ = self._preview(hull, paint)
        w, h = image.get_size()
        bob = int(math.sin(time * 3) * 2) if selected else 0
        x, y = cx - w // 2, SHIP_Y - h // 2 + bob
        if selected:
            box = pygame.Rect(0, 0, SLOT_W - 8, 84)
            box.center = (cx, SHIP_Y + 4)
            surf.fill(EMPTY, box)
            pygame.draw.rect(surf, ACCENT, box, 1)
            self._flames(surf, hull, x + w / 2, y + h, time)
        surf.blit(image, (x, y))
        color = ACCENT if selected else TEXT_DIM
        self.font.draw(surf, hull.name, (cx, SHIP_Y + 50), color, shadow=TEXT_SHADOW, center=True)

    @staticmethod
    def _flames(surf, hull, cx, bottom, time):
        """Flickering engine flames under the selected preview."""
        length = int((5 + 3 * abs(math.sin(time * 23))) * hull.flame) * PREVIEW_SCALE // 2
        for off in hull.nozzles:
            x = int(cx + off * PREVIEW_SCALE)
            for i in range(length):
                color = FLAME[min(len(FLAME) - 1, i * len(FLAME) // max(1, length))]
                surf.fill(color, (x - 1, int(bottom) + i, 2, 1), special_flags=pygame.BLEND_ADD)

    def _stats(self, surf, hull, base, paint):
        """Name, one-line description and bars comparing this hull with the others."""
        f = self.font
        f.draw(surf, hull.blurb, (LOW_W // 2, 134), TEXT, shadow=TEXT_SHADOW, center=True)
        models = {h.name: h.apply(base) for h in HULLS}
        sizes = {h.name: self._preview(h, paint)[1] for h in HULLS}
        me = models[hull.name]
        rows = (
            ("HULL", me.max_hp, max(m.max_hp for m in models.values()), f"{me.max_hp}"),
            ("GUN", me.gun_dps, max(m.gun_dps for m in models.values()), f"{me.gun_dps:.0f} DPS"),
            ("LASER", me.laser_dps, max(m.laser_dps for m in models.values()),
             f"{me.laser_dps:.0f} DPS"),
            ("SPEED", me.max_speed, max(m.max_speed for m in models.values()),
             f"{me.max_speed:.0f}"),
            ("SIZE", sizes[hull.name], max(sizes.values()), "{}X{}".format(*hull.size)),
        )
        for i, (label, value, top, text) in enumerate(rows):
            y = 148 + i * 11
            f.draw(surf, label, (64, y), TEXT_DIM, shadow=TEXT_SHADOW)
            bar = pygame.Rect(112, y + 1, 100, 5)
            pygame.draw.rect(surf, INK, bar.inflate(2, 2))
            surf.fill(EMPTY, bar)
            color = TEXT_DIM if label == "SIZE" else GOOD   # size: smaller is better
            surf.fill(color, (bar.x, bar.y, max(1, int(bar.w * value / top)), bar.h))
            f.draw(surf, text, (220, y), TEXT, shadow=TEXT_SHADOW)
