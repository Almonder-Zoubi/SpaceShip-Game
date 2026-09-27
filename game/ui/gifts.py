"""Gift screen after a first level clear: one fixed gift, or choose 1 of 2 (the other goes to
the shop)."""
import pygame

from ..config.display import LOW_W
from ..config.palette import ACCENT, EMPTY, INK, TEXT, TEXT_DIM, TEXT_SHADOW
from ..progression.items import SHIP, SKIN, WINGMAN

KIND_LABEL = {SHIP: "NEW SHIP", WINGMAN: "NEW WINGMAN", SKIN: "NEW SKIN"}

CARD_W, CARD_H, CARD_Y = 136, 150, 44


class GiftScreen:
    def __init__(self, font, art):
        self.font = font
        self.art = art

    def draw(self, surf, options, cursor, level_number, paint, time, blink):
        """options: Items offered; cursor: the highlighted one."""
        f = self.font
        f.draw(surf, f"LEVEL {level_number} GIFT", (LOW_W // 2, 8), ACCENT, scale=2,
               shadow=TEXT_SHADOW, center=True)
        sub = "CHOOSE ONE - THE OTHER GOES TO THE SHOP" if len(options) > 1 else "A GIFT FOR YOU"
        f.draw(surf, sub, (LOW_W // 2, 28), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        gap = 16
        total = len(options) * CARD_W + (len(options) - 1) * gap
        x0 = (LOW_W - total) // 2
        for i, item in enumerate(options):
            card = pygame.Rect(x0 + i * (CARD_W + gap), CARD_Y, CARD_W, CARD_H)
            selected = i == cursor
            shade = pygame.Surface(card.size, pygame.SRCALPHA)
            shade.fill((*(EMPTY if selected else INK), 220))
            surf.blit(shade, card)
            pygame.draw.rect(surf, ACCENT if selected else TEXT_DIM, card, 1)
            kind = KIND_LABEL.get(item.kind, "NEW WEAPON")
            f.draw(surf, kind, (card.centerx, card.y + 6), TEXT_DIM, shadow=TEXT_SHADOW,
                   center=True)
            if item.kind == SKIN:
                self.art.draw_skin(surf, item, "ARROW", paint, (card.centerx, card.y + 58), time)
            else:
                self.art.draw(surf, item.id, paint, (card.centerx, card.y + 58), time,
                              lively=selected)
            f.draw(surf, item.name, (card.centerx, card.y + 104), ACCENT if selected else TEXT,
                   shadow=TEXT_SHADOW, center=True)
            for j, line in enumerate(item.blurb):
                f.draw(surf, line, (card.centerx, card.y + 120 + j * 10), TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
        if blink:
            hint = "LEFT/RIGHT CHOOSE   ENTER TAKE" if len(options) > 1 else "ENTER TAKE"
            f.draw(surf, hint, (LOW_W // 2, 214), TEXT, shadow=TEXT_SHADOW, center=True)

