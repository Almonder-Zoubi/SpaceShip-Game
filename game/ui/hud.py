"""Heads-up display (health, score, coins, weapon, boss bar) and banners."""
import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import (ACCENT, BOOST_COLORS, COIN, DANGER, EMPTY, GOOD, INK, LASER,
                              POWER, RAINBOW, TEXT, TEXT_DIM, TEXT_SHADOW)
from ..config.tuning import (COMBO_STEP, FEVER_TIME, MAGNET_TIME, OVERDRIVE_TIME, POWER_MAX,
                             SHIELD_HITS, SHIP_MAX_HP, SLOWDOWN_TIME)

BOOST_TIMES = {"OVERDRIVE": OVERDRIVE_TIME, "MAGNET": MAGNET_TIME, "SLOW-MO": SLOWDOWN_TIME}


class Hud:
    def __init__(self, font):
        self.font = font

    def draw(self, surf, ship, score, best, progress, weapon, time, boss=None, level="1",
             blast=None, ultimate=None, galaxy=1, coins=None, switchable=True, boosts=None,
             combo=None):
        """coins: (bank, pending, flash) — pending coins are only banked when the level is won.
        boosts: ({name: seconds left}, shield hits, fever seconds); combo: (count, mult,
        0..1 time left)."""
        blink = int(time * 6) % 2 == 0
        self._health(surf, ship, blink)
        self.font.draw(surf, f"G{galaxy} LEVEL {level}", (6, 15), TEXT_DIM, shadow=TEXT_SHADOW)
        if coins:
            self._coins(surf, *coins)
        if blast:
            self._meter(surf, LOW_H - 22, "BLAST", blast, ACCENT, blink, "HOLD SPACE")
        if ultimate:
            self._meter(surf, LOW_H - 12, "ULT", ultimate, POWER[2], blink, "PRESS T")
        if boss:
            self._boss_bar(surf, boss)
        else:
            self._progress(surf, progress)
        f = self.font
        text = f"{score:06d}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text)[0], 5), TEXT, shadow=TEXT_SHADOW)
        text = f"HI {best:06d}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text)[0], 15), TEXT_DIM, shadow=TEXT_SHADOW)
        self._weapon(surf, weapon, blink, switchable)
        if boosts:
            self._boosts(surf, *boosts, time)
        if combo and combo[0] >= COMBO_STEP:
            self._combo(surf, *combo, time)

    def _boosts(self, surf, timed, shield, fever, time):
        """Active boosts under the level label: name + a draining bar."""
        f = self.font
        rows = [(name, BOOST_COLORS[name][2], left / BOOST_TIMES[name])
                for name, left in timed.items()]
        if shield:
            rows.append(("SHIELD", BOOST_COLORS["SHIELD"][2], shield / SHIELD_HITS))
        if fever:
            rows.append(("FEVER", RAINBOW[int(time * 12) % len(RAINBOW)], fever / FEVER_TIME))
        for i, (name, color, ratio) in enumerate(rows):
            y = 25 + i * 9
            f.draw(surf, name, (6, y), color, shadow=TEXT_SHADOW)
            self._bar(64, y + 2, 24, 3, surf, ratio, color)

    def _combo(self, surf, count, mult, ratio, time):
        """Right side under the coins: 'X4' big-ish, the count and the combo timer."""
        f = self.font
        color = RAINBOW[mult % len(RAINBOW)] if mult > 1 else TEXT
        text = f"X{mult}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text, 2)[0], 35), color, scale=2,
               shadow=TEXT_SHADOW)
        label = f"COMBO {count}"
        f.draw(surf, label, (LOW_W - 6 - f.size(label)[0], 51), TEXT_DIM, shadow=TEXT_SHADOW)
        self._bar(LOW_W - 46, 60, 40, 2, surf, ratio, color)

    def _coins(self, surf, bank, pending, flash):
        """Right side under the score: 'CR 1240' and the pending '+86' (flashes on pickup)."""
        f = self.font
        x = LOW_W - 6
        if pending:
            text = f"+{pending}"
            x -= f.size(text)[0]
            f.draw(surf, text, (x, 25), TEXT if flash > 0 else COIN[2], shadow=TEXT_SHADOW)
            x -= 6
        text = f"CR {bank}"
        f.draw(surf, text, (x - f.size(text)[0], 25), TEXT_DIM, shadow=TEXT_SHADOW)

    def _bar(self, x, y, w, h, surf, ratio, color):
        pygame.draw.rect(surf, INK, (x - 1, y - 1, w + 2, h + 2))
        pygame.draw.rect(surf, TEXT_DIM, (x - 1, y - 1, w + 2, h + 2), 1)
        surf.fill(EMPTY, (x, y, w, h))
        filled = int(w * max(0.0, min(1.0, ratio)))
        if filled:
            surf.fill(color, (x, y, filled, h))
            highlight = tuple(min(255, c + 70) for c in color)
            surf.fill(highlight, (x, y, filled, 1))

    def _health(self, surf, ship, blink):
        ratio = ship.hp / ship.max_hp
        color = GOOD if ratio > 0.5 else ACCENT if ratio > 0.25 else DANGER
        self.font.draw(surf, "HP", (6, 6), TEXT, shadow=TEXT_SHADOW)
        w = min(80, 60 * ship.max_hp // SHIP_MAX_HP)       # a bigger hull gets a longer bar
        self._bar(20, 6, w, 5, surf, ratio if ratio > 0.25 or blink else 0, color)   # blink when low

    def _progress(self, surf, progress):
        w = 80
        x = (LOW_W - w) // 2
        self._bar(x, 7, w, 3, surf, progress, ACCENT)
        marker = x + int(w * min(1.0, progress))
        surf.fill(TEXT, (marker - 1, 5, 3, 7))

    def _boss_bar(self, surf, boss):
        w = 110
        x = (LOW_W - w) // 2
        name = boss.spec.name
        if boss.PHASES > 1:
            name += f"  {boss.phase + 1}/{boss.PHASES}"
        self.font.draw(surf, name, (LOW_W // 2, 3), DANGER, shadow=TEXT_SHADOW, center=True)
        ratio = boss.hp / boss.max_hp
        if boss.state == "enter":                       # bar fills up as the boss arrives
            ratio = min(1.0, boss.state_time / boss.ENTER_TIME)
        self._bar(x, 12, w, 4, surf, ratio, DANGER)
        for mark in boss.phase_marks:                   # phase thresholds (or quarters)
            tall = boss.PHASES > 1
            surf.fill(TEXT if tall else INK, (x + int(w * mark), 11 if tall else 12, 1, 6 if tall else 4))

    def _weapon(self, surf, weapon, blink, switchable):
        x, y = 6, LOW_H - 12
        self.font.draw(surf, weapon.name, (x, y), TEXT, shadow=TEXT_SHADOW)
        if weapon.name == "LASER":
            if weapon.overheated:
                color = DANGER
                if blink:
                    self.font.draw(surf, "OVERHEAT", (x + 80, y), DANGER, shadow=TEXT_SHADOW)
            else:
                color = LASER[2] if weapon.heat < 0.7 else ACCENT
            self._bar(x + 34, y + 1, 40, 4, surf, weapon.heat, color)
        if switchable:
            self.font.draw(surf, "R SWITCH", (x, y - 10), TEXT_DIM, shadow=TEXT_SHADOW)
        if weapon.power:                                # POWER pips from boss phase rewards
            self.font.draw(surf, "PWR", (x + 54, y - 10), POWER[2], shadow=TEXT_SHADOW)
            for i in range(POWER_MAX):
                color = POWER[1] if i < weapon.power else EMPTY
                surf.fill(INK, (x + 73 + i * 6, y - 10, 5, 7))
                surf.fill(color, (x + 74 + i * 6, y - 9, 3, 5))

    def _meter(self, surf, y, label, weapon, color, blink, hint):
        """Charge meter of a Charged weapon (bottom right); blinks with a hint when ready."""
        f = self.font
        w = 50
        x = LOW_W - 6 - w
        lx = x - 4 - f.size(label)[0]
        lit = weapon.ready or weapon.active
        if weapon.ready and blink:
            f.draw(surf, hint, (lx - 6 - f.size(hint)[0], y), TEXT, shadow=TEXT_SHADOW)
            color = TEXT
        f.draw(surf, label, (lx, y), color if lit else TEXT_DIM, shadow=TEXT_SHADOW)
        self._bar(x, y + 1, w, 4, surf, weapon.charge, TEXT if weapon.active else color)

    def alert(self, surf, title, subtitle, color, blink_on=True, y=62):
        """Big mid-screen announcement without a panel (level intro, boss phase change)."""
        if blink_on:
            self.font.draw(surf, title, (LOW_W // 2, y), color, scale=3, shadow=TEXT_SHADOW,
                           center=True)
        if subtitle:
            self.font.draw(surf, subtitle, (LOW_W // 2, y + 28), TEXT, shadow=TEXT_SHADOW,
                           center=True)

    def banner(self, surf, title, subtitle=None, title_color=TEXT, blink_on=True, y=None):
        """Big centred title with an optional blinking subtitle."""
        f = self.font
        y = LOW_H // 2 - 24 if y is None else y
        panel_w = max(f.size(title, 3)[0], f.size(subtitle or "")[0]) + 24
        panel = pygame.Rect(0, 0, panel_w, 58 if subtitle else 36)
        panel.midtop = (LOW_W // 2, y - 8)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((*INK, 190))
        surf.blit(shade, panel)
        pygame.draw.rect(surf, TEXT_DIM, panel, 1)
        f.draw(surf, title, (LOW_W // 2, y), title_color, scale=3, shadow=TEXT_SHADOW, center=True)
        if subtitle and blink_on:
            f.draw(surf, subtitle, (LOW_W // 2, y + 32), TEXT, shadow=TEXT_SHADOW, center=True)
