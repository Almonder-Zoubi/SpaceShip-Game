"""Heads-up display and full-screen messages."""
import pygame

from .pixelart import ramp
from .settings import (ACCENT, FLAME, INK, LOW_H, LOW_W, TEXT, TEXT_DIM, TEXT_SHADOW,
                       THROTTLE_BOOST)


class Hud:
    def __init__(self, font):
        self.font = font

    def draw(self, surf, score, best, goal, throttle):
        f = self.font
        f.draw(surf, f"SCORE {score:03d}", (6, 6), TEXT, shadow=TEXT_SHADOW)
        f.draw(surf, f"BEST {best:03d}", (LOW_W - 6 - f.size(f"BEST {best:03d}")[0], 6),
               TEXT_DIM, shadow=TEXT_SHADOW)
        self._goal_bar(surf, score, goal)
        self._throttle_gauge(surf, throttle)

    def _goal_bar(self, surf, score, goal):
        w = 80
        x, y = (LOW_W - w) // 2, 8
        pygame.draw.rect(surf, INK, (x - 1, y - 1, w + 2, 5))
        pygame.draw.rect(surf, TEXT_DIM, (x - 1, y - 1, w + 2, 5), 1)
        filled = int(w * min(1.0, score / goal))
        if filled:
            surf.fill(ACCENT, (x, y, filled, 3))
            surf.fill((255, 240, 180), (x, y, filled, 1))

    def _throttle_gauge(self, surf, throttle):
        """Segmented bar at the bottom left, coloured like the flame."""
        x, y = 6, LOW_H - 12
        self.font.draw(surf, "THR", (x, y), TEXT_DIM, shadow=TEXT_SHADOW)
        segs = 8
        lit = round(throttle / THROTTLE_BOOST * segs)
        for i in range(segs):
            color = ramp(FLAME[:4][::-1], i / segs) if i < lit else (40, 34, 58)
            surf.fill(color, (x + 22 + i * 5, y + 1, 4, 5))

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
