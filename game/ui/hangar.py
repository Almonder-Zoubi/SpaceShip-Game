"""HANGAR 2.0: inventory tabs (ships, weapons), a live preview, stats, and the shop."""
from dataclasses import dataclass

import pygame

from ..config.display import LOW_W
from ..config.palette import (ACCENT, COIN, DANGER, EMPTY, GOOD, INK, TEXT, TEXT_DIM,
                              TEXT_SHADOW)
from ..config.tuning import BLAST_DPS, BLAST_TIME, GUN_INTERVAL, ULT_INTERVAL, ULT_TIME
from ..player.hulls import HULLS, hull_named
from ..progression.inventory import LOCKED, OWNED, SHOP
from ..progression.items import SHIP, WEAPON
from .item_art import ItemArt

TAB_NAMES = {SHIP: "SHIPS", WEAPON: "WEAPONS"}
PREVIEW = pygame.Rect(8, 40, 112, 106)
LIST_X, LIST_Y, ROW_H = 130, 42, 13


@dataclass
class HangarView:
    """Everything the hangar shows; built by the game (flow/hangar.py) each frame."""
    tabs: tuple
    tab: str
    items: list                  # [(Item, status)] of the current tab
    cursor: int
    equipped: str                # hull name
    bank: int
    level: object                # the Level the launch starts
    message: tuple = None        # (text, colour) under the details, e.g. a buy prompt
    unlock_hint: str = ""        # how the selected locked item is unlocked


class HangarScreen:
    """Draws the hangar. Knows nothing about game state beyond the HangarView it's given."""

    def __init__(self, font, art=None):
        self.font = font
        self.art = art or ItemArt()
        self._sizes = {}          # hull name -> pixel count (the SIZE stat)

    def draw(self, surf, view, time, blink):
        f = self.font
        f.draw(surf, "HANGAR", (8, 5), ACCENT, scale=2, shadow=TEXT_SHADOW)
        bank = f"CR {view.bank}"
        f.draw(surf, bank, (LOW_W - 8 - f.size(bank)[0], 9), COIN[2], shadow=TEXT_SHADOW)
        self._tabs(surf, view)
        item, status = view.items[view.cursor]
        paint = view.level.loadout.colors
        surf.fill(EMPTY, PREVIEW)
        pygame.draw.rect(surf, ACCENT if status == OWNED else TEXT_DIM, PREVIEW, 1)
        self.art.draw(surf, item.id, paint, PREVIEW.center, time, locked=status == LOCKED,
                      lively=True)
        tag, color = self._status(item, status, view.equipped)
        f.draw(surf, tag, (PREVIEW.centerx, PREVIEW.bottom + 4), color, shadow=TEXT_SHADOW,
               center=True)
        self._list(surf, view)
        if item.kind == SHIP:
            self._ship_stats(surf, hull_named(item.id), view.level.loadout, paint)
        else:
            self._weapon_stats(surf, item.id, view.level.loadout)
        for i, line in enumerate(item.blurb):
            f.draw(surf, line, (LOW_W // 2, 162 + i * 10), TEXT, shadow=TEXT_SHADOW, center=True)
        if view.message:
            text, color = view.message
            f.draw(surf, text, (LOW_W // 2, 186), color, shadow=TEXT_SHADOW, center=True)
        elif status == LOCKED:
            f.draw(surf, f"LOCKED: {view.unlock_hint}", (LOW_W // 2, 186), TEXT_DIM,
                   shadow=TEXT_SHADOW, center=True)
        level = view.level
        f.draw(surf, f"NEXT: LEVEL {level.number} {level.name} - {level.loadout.name}",
               (LOW_W // 2, 202), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(surf, "</> TAB  UP/DOWN PICK  ENTER EQUIP/BUY  SPACE LAUNCH", (LOW_W // 2, 222),
                   TEXT, shadow=TEXT_SHADOW, center=True)

    def _tabs(self, surf, view):
        f = self.font
        step = 80
        x0 = LOW_W // 2 - step * (len(view.tabs) - 1) // 2
        for i, tab in enumerate(view.tabs):
            x = x0 + i * step
            selected = tab == view.tab
            f.draw(surf, TAB_NAMES[tab], (x, 24), ACCENT if selected else TEXT_DIM,
                   shadow=TEXT_SHADOW, center=True)
            if selected:
                w = f.size(TAB_NAMES[tab])[0]
                surf.fill(ACCENT, (x - w // 2, 33, w, 1))
        surf.fill(EMPTY, (8, 35, LOW_W - 16, 1))

    @staticmethod
    def _status(item, status, equipped):
        if status == OWNED:
            if item.kind == SHIP:
                return ("EQUIPPED", GOOD) if item.id == equipped else ("OWNED", TEXT)
            return "ON BOARD", GOOD
        if status == SHOP:
            return f"{item.price} CR", COIN[2]
        return "LOCKED", DANGER

    def _list(self, surf, view):
        f = self.font
        for i, (item, status) in enumerate(view.items):
            y = LIST_Y + i * ROW_H
            selected = i == view.cursor
            if selected:
                surf.fill(EMPTY, (LIST_X - 4, y - 3, LOW_W - LIST_X - 4, ROW_H - 1))
                f.draw(surf, ">", (LIST_X - 2, y), ACCENT, shadow=TEXT_SHADOW)
            f.draw(surf, item.name, (LIST_X + 6, y), ACCENT if selected else TEXT, shadow=TEXT_SHADOW)
            tag, color = self._status(item, status, view.equipped)
            f.draw(surf, tag, (LOW_W - 10 - f.size(tag)[0], y), color, shadow=TEXT_SHADOW)

    def _size(self, hull):
        if hull.name not in self._sizes:
            image = self.art.image(hull.name, "mk1")
            self._sizes[hull.name] = pygame.mask.from_surface(image).count()
        return self._sizes[hull.name]

    def _ship_stats(self, surf, hull, base, paint):
        """Bars comparing this hull with the others on the next level's ship model."""
        models = {h.name: h.apply(base) for h in HULLS}
        sizes = {h.name: self._size(h) for h in HULLS}
        me = models[hull.name]
        rows = (
            ("HULL", me.max_hp, max(m.max_hp for m in models.values()), f"{me.max_hp}"),
            ("GUN", me.gun_dps, max(m.gun_dps for m in models.values()), f"{me.gun_dps:.0f}"),
            ("LASER", me.laser_dps, max(m.laser_dps for m in models.values()),
             f"{me.laser_dps:.0f}"),
            ("SPEED", me.max_speed, max(m.max_speed for m in models.values()),
             f"{me.max_speed:.0f}"),
            ("SIZE", sizes[hull.name], max(sizes.values()), "{}X{}".format(*hull.size)),
        )
        y0 = LIST_Y + len(HULLS) * ROW_H + 8
        for i, (label, value, top, text) in enumerate(rows):
            self._bar_row(surf, y0 + i * 10, label, value / top, text,
                          TEXT_DIM if label == "SIZE" else GOOD)   # size: smaller is better

    def _weapon_stats(self, surf, item_id, base):
        f = self.font
        lines = {
            "GUN": (f"DAMAGE {base.gun_damage:g} X {1 / GUN_INTERVAL:.0f}/S",
                    f"{base.gun_dps:.0f} DPS, TWIN BARRELS"),
            "LASER": (f"BEAM {base.laser_dps:.0f} DPS", "PIERCES THE FIRST TARGET"),
            "SPECIALS": (f"BLAST {BLAST_DPS} DPS FOR {BLAST_TIME:g} S",
                         f"ULTIMATE {round(ULT_TIME / ULT_INTERVAL)} MISSILES"),
        }[item_id]
        y0 = LIST_Y + 3 * ROW_H + 10
        for i, line in enumerate(lines):
            f.draw(surf, line, (LIST_X, y0 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW)

    def _bar_row(self, surf, y, label, ratio, text, color):
        f = self.font
        f.draw(surf, label, (LIST_X, y), TEXT_DIM, shadow=TEXT_SHADOW)
        bar = pygame.Rect(LIST_X + 36, y + 1, 90, 5)
        pygame.draw.rect(surf, INK, bar.inflate(2, 2))
        surf.fill(EMPTY, bar)
        surf.fill(color, (bar.x, bar.y, max(1, int(bar.w * min(1.0, ratio))), bar.h))
        f.draw(surf, text, (bar.right + 6, y), TEXT, shadow=TEXT_SHADOW)
