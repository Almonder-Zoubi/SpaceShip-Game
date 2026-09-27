"""Heads-up display and full-screen messages."""
import pygame

from .settings import (ACCENT, DANGER, GOOD, INK, LASER, LOW_H, LOW_W, SHIP_MAX_HP, TEXT,
                       TEXT_DIM, TEXT_SHADOW)

EMPTY = (40, 34, 58)


class Hud:
    def __init__(self, font):
        self.font = font

    def draw(self, surf, ship, score, best, progress, weapon, time, boss=None):
        blink = int(time * 6) % 2 == 0
        self._health(surf, ship.hp, blink)
        if boss:
            self._boss_bar(surf, boss)
        else:
            self._progress(surf, progress)
        f = self.font
        text = f"{score:06d}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text)[0], 5), TEXT, shadow=TEXT_SHADOW)
        text = f"HI {best:06d}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text)[0], 15), TEXT_DIM, shadow=TEXT_SHADOW)
        self._weapon(surf, weapon, blink)

    def _bar(self, x, y, w, h, surf, ratio, color):
        pygame.draw.rect(surf, INK, (x - 1, y - 1, w + 2, h + 2))
        pygame.draw.rect(surf, TEXT_DIM, (x - 1, y - 1, w + 2, h + 2), 1)
        surf.fill(EMPTY, (x, y, w, h))
        filled = int(w * max(0.0, min(1.0, ratio)))
        if filled:
            surf.fill(color, (x, y, filled, h))
            highlight = tuple(min(255, c + 70) for c in color)
            surf.fill(highlight, (x, y, filled, 1))

    def _health(self, surf, hp, blink):
        ratio = hp / SHIP_MAX_HP
        color = GOOD if ratio > 0.5 else ACCENT if ratio > 0.25 else DANGER
        self.font.draw(surf, "HP", (6, 6), TEXT, shadow=TEXT_SHADOW)
        self._bar(20, 6, 60, 5, surf, ratio if ratio > 0.25 or blink else 0, color)   # blink when low

    def _progress(self, surf, progress):
        w = 80
        x = (LOW_W - w) // 2
        self._bar(x, 7, w, 3, surf, progress, ACCENT)
        marker = x + int(w * min(1.0, progress))
        surf.fill(TEXT, (marker - 1, 5, 3, 7))

    def _boss_bar(self, surf, boss):
        w = 120
        x = (LOW_W - w) // 2
        self.font.draw(surf, boss.spec.name, (LOW_W // 2, 3), DANGER, shadow=TEXT_SHADOW, center=True)
        ratio = boss.hp / boss.max_hp
        if boss.state == "enter":                       # bar fills up as the boss arrives
            ratio = min(1.0, boss.state_time / boss.ENTER_TIME)
        self._bar(x, 12, w, 4, surf, ratio, DANGER)
        for i in range(1, 4):                           # quarter ticks
            surf.fill(INK, (x + w * i // 4, 12, 1, 4))

    def _weapon(self, surf, weapon, blink):
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
        self.font.draw(surf, "R SWITCH", (x, y - 10), TEXT_DIM, shadow=TEXT_SHADOW)

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
