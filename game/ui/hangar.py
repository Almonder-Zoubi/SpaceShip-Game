"""HANGAR 2.0: inventory tabs (ships, weapons, upgrades), a live preview, stats, the shop and
POWER % (upgrades over the par ship model)."""
from dataclasses import dataclass

import pygame

from ..config.display import LOW_W
from ..config.palette import (ACCENT, COIN, DANGER, EMPTY, GOOD, INK, TEXT, TEXT_DIM,
                              TEXT_SHADOW)
from ..config.tuning import (BLAST_DPS, BLAST_TIME, GUN_INTERVAL, ULT_INTERVAL, ULT_TIME,
                             UPGRADE_TIERS)
from ..player.hulls import HULLS, hull_named
from ..progression import upgrades
from ..progression.inventory import LOCKED, OWNED, SHOP
from ..progression.items import SHIP, UPGRADE, WEAPON
from .item_art import ItemArt

TAB_NAMES = {SHIP: "SHIPS", WEAPON: "WEAPONS", UPGRADE: "UPGRADES"}
PREVIEW = pygame.Rect(8, 40, 112, 106)
LIST_X, LIST_Y, ROW_H = 130, 42, 13


@dataclass
class HangarView:
    """Everything the hangar shows; built by the game (flow/hangar.py) each frame."""
    tabs: tuple
    tab: str
    items: list                  # [(Item, status)] of the current tab ([] on UPGRADES)
    cursor: int
    equipped: str                # hull name
    bank: int
    level: object                # the Level the launch starts
    tiers: dict                  # upgrade track -> tier bought
    message: tuple = None        # (text, colour) under the details, e.g. a buy prompt
    unlock_hint: str = ""        # how the selected locked item is unlocked

    @property
    def power(self):
        return upgrades.power_ratio(self.tiers)

    def model(self, hull_name=None):
        """The next level's ship model as flown: hull + upgrades."""
        hull = hull_named(hull_name or self.equipped)
        return upgrades.apply(hull.apply(self.level.loadout), self.tiers)


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
        power = round(view.power * 100)
        f.draw(surf, f"POWER {power}%", (LOW_W // 2 + 30, 9), GOOD if power > 100 else TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        self._tabs(surf, view)
        self._footer(surf, view, blink)
        if view.tab == UPGRADE:
            self._upgrades(surf, view)
            return
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
            self._ship_stats(surf, hull_named(item.id), view)
        else:
            self._weapon_stats(surf, item.id, view.model(), len(view.items))
        self._blurb(surf, item.blurb)
        if not view.message and status == LOCKED:
            f.draw(surf, f"LOCKED: {view.unlock_hint}", (LOW_W // 2, 186), TEXT_DIM,
                   shadow=TEXT_SHADOW, center=True)

    def _blurb(self, surf, lines):
        for i, line in enumerate(lines):
            self.font.draw(surf, line, (LOW_W // 2, 162 + i * 10), TEXT, shadow=TEXT_SHADOW,
                           center=True)

    def _footer(self, surf, view, blink):
        f = self.font
        if view.message:
            text, color = view.message
            f.draw(surf, text, (LOW_W // 2, 186), color, shadow=TEXT_SHADOW, center=True)
        level = view.level
        f.draw(surf, f"NEXT: LEVEL {level.number} {level.name} - {level.loadout.name}",
               (LOW_W // 2, 202), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if blink:
            enter = "ENTER BUY" if view.tab == UPGRADE else "ENTER EQUIP/BUY"
            f.draw(surf, f"</> TAB  UP/DOWN PICK  {enter}  SPACE LAUNCH", (LOW_W // 2, 222),
                   TEXT, shadow=TEXT_SHADOW, center=True)

    # --- UPGRADES tab ------------------------------------------------------------------
    def _upgrades(self, surf, view):
        """Preview: the track's icon + tier pips; list: every track with pips and the next
        price; details: the stat now -> after the next tier, on the next level's model."""
        f = self.font
        track = upgrades.TRACKS[view.cursor]
        tier = view.tiers.get(track.id, 0)
        surf.fill(EMPTY, PREVIEW)
        pygame.draw.rect(surf, ACCENT if tier else TEXT_DIM, PREVIEW, 1)
        icon = self.art.upgrade_icon(track.id)
        surf.blit(icon, icon.get_rect(center=(PREVIEW.centerx, PREVIEW.y + 42)))
        self._pips(surf, PREVIEW.centerx, PREVIEW.bottom - 20, tier, size=9)
        f.draw(surf, f"TIER {tier}/{UPGRADE_TIERS}", (PREVIEW.centerx, PREVIEW.bottom + 4),
               GOOD if tier == UPGRADE_TIERS else TEXT, shadow=TEXT_SHADOW, center=True)
        for i, t in enumerate(upgrades.TRACKS):
            y = LIST_Y + i * ROW_H
            selected = i == view.cursor
            if selected:
                surf.fill(EMPTY, (LIST_X - 4, y - 3, LOW_W - LIST_X - 4, ROW_H - 1))
                f.draw(surf, ">", (LIST_X - 2, y), ACCENT, shadow=TEXT_SHADOW)
            f.draw(surf, t.id, (LIST_X + 6, y), ACCENT if selected else TEXT, shadow=TEXT_SHADOW)
            t_tier = view.tiers.get(t.id, 0)
            self._pips(surf, LIST_X + 90, y + 3, t_tier, size=5)
            price = upgrades.cost(t_tier)
            tag, color = ("MAX", GOOD) if price is None else (f"{price}", COIN[2])
            f.draw(surf, tag, (LOW_W - 10 - f.size(tag)[0], y), color, shadow=TEXT_SHADOW)
        now = view.model()
        nxt_tiers = dict(view.tiers, **{track.id: min(UPGRADE_TIERS, tier + 1)})
        nxt = upgrades.apply(hull_named(view.equipped).apply(view.level.loadout), nxt_tiers)
        y0 = LIST_Y + len(upgrades.TRACKS) * ROW_H + 8
        bonus = f"{track.stat} +{round(track.bonus * tier * 100)}%"
        if tier < UPGRADE_TIERS:
            bonus += f"  >  +{round(track.bonus * (tier + 1) * 100)}%"
        f.draw(surf, bonus, (LIST_X, y0), TEXT, shadow=TEXT_SHADOW)
        value = self._track_value
        line = f"{value(track.id, now)}"
        if tier < UPGRADE_TIERS:
            line += f"  >  {value(track.id, nxt)}"
        f.draw(surf, f"{line}  ON {view.level.loadout.name}", (LIST_X, y0 + 11), TEXT_DIM,
               shadow=TEXT_SHADOW)
        self._blurb(surf, track.blurb)

    @staticmethod
    def _track_value(track_id, model):
        return {"ARMOR": lambda: f"{model.max_hp} HP",
                "GUNS": lambda: f"{model.gun_dps:.0f} DPS",
                "LASER": lambda: f"{model.laser_dps:.0f} DPS",
                "ENGINE": lambda: f"{model.max_speed:.0f} PX/S",
                "CHARGE": lambda: f"X{model.charge_rate:.1f}"}[track_id]()

    @staticmethod
    def _pips(surf, cx, y, tier, size):
        """UPGRADE_TIERS squares centred on cx, the first `tier` lit."""
        gap = max(2, size // 3)
        width = UPGRADE_TIERS * size + (UPGRADE_TIERS - 1) * gap
        x = cx - width // 2
        for i in range(UPGRADE_TIERS):
            rect = pygame.Rect(x + i * (size + gap), y, size, size)
            pygame.draw.rect(surf, INK, rect.inflate(2, 2))
            surf.fill(GOOD if i < tier else EMPTY, rect)

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

    def _ship_stats(self, surf, hull, view):
        """Bars comparing this hull with the others on the next level's ship model (with the
        upgrades bought)."""
        models = {h.name: view.model(h.name) for h in HULLS}
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

    def _weapon_stats(self, surf, item_id, base, rows):
        f = self.font
        lines = {
            "GUN": (f"DAMAGE {round(base.gun_damage, 1):g} X {1 / GUN_INTERVAL:.0f}/S",
                    f"{base.gun_dps:.0f} DPS, TWIN BARRELS"),
            "LASER": (f"BEAM {base.laser_dps:.0f} DPS", "PIERCES THE FIRST TARGET"),
            "SPECIALS": (f"BLAST {BLAST_DPS} DPS FOR {BLAST_TIME:g} S",
                         f"ULTIMATE {round(ULT_TIME / ULT_INTERVAL)} MISSILES"),
            "OVERDRIVE": ("FALLS LIKE A REPAIR KIT", "FIRE RATE X2, WHITE FLAMES"),
        }[item_id]
        y0 = LIST_Y + rows * ROW_H + 10
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
