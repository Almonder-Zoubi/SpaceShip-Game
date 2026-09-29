"""Radio cards: short story lines (with a pixel portrait) at the start of a level or wave,
from COMMANDER VEGA or someone who breaks into the channel. They type themselves out while
the game runs; ENTER skips."""
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import ACCENT, DANGER, EMPTY, INK, TEXT, TEXT_DIM, TEXT_SHADOW
from ..config.tuning import RADIO_CHARS_PER_S, RADIO_HOLD
from ..story.dialog import VEGA, is_hijack
from .portraits import Portraits

HIJACK_TEXT = (255, 150, 160)

PANEL = pygame.Rect(8, 34, LOW_W - 16, 42)          # under the HUD, over the incoming field


class RadioCard:
    """A message: who speaks and 1-3 lines (<= 42 characters each)."""

    def __init__(self, lines, speaker=VEGA, delay=0.0):
        self.speaker, self.lines = speaker, tuple(lines)
        self.chars = sum(len(line) for line in self.lines)
        self.t = -delay               # waits (hidden) until the level title is gone

    @property
    def visible(self):
        return self.t >= 0

    @property
    def typed(self):
        return int(self.t * RADIO_CHARS_PER_S)

    @property
    def done(self):
        return self.t >= self.chars / RADIO_CHARS_PER_S + RADIO_HOLD

    def update(self, dt):
        self.t += dt

    def skip(self):
        """ENTER: finish the typing, or close a finished card."""
        full = self.chars / RADIO_CHARS_PER_S
        self.t = full + RADIO_HOLD if self.t >= full else full

    @property
    def fade(self):
        """0..1: slides in at the start, out at the end."""
        end = self.chars / RADIO_CHARS_PER_S + RADIO_HOLD
        return max(0.0, min(1.0, self.t / 0.2, (end - self.t) / 0.3))


class RadioView:
    """Draws a RadioCard under the HUD (it slides in and out). A hijacked card (VANTA or an
    unknown voice breaking into Vega's channel) tears, flickers and types in red."""

    def __init__(self, font):
        self.font = font
        self.portraits = Portraits()

    def draw(self, surf, card, time, top=None):
        if not card.visible:
            return
        hijack = is_hijack(card.speaker)
        panel = PANEL.move(0, -int((1 - card.fade) * 60))
        if top is not None:
            panel.y = top + int((1 - card.fade) * 60)
        if hijack and random.random() < 0.15:                        # the signal jumps
            panel.x += random.choice((-3, -2, 2, 3))
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((30, 0, 12, 200) if hijack else (*INK, 190))
        surf.blit(shade, panel)
        pygame.draw.rect(surf, DANGER if hijack else TEXT_DIM, panel, 1)
        frame = pygame.Rect(panel.x + 5, panel.y + 7, 28, 28)
        surf.fill(EMPTY, frame)
        self.portraits.draw(surf, card.speaker, (frame.x + 2, frame.y + 2), time)
        for y in range(frame.y + int(time * 20) % 3, frame.bottom, 3):   # radio scanlines
            surf.fill((0, 0, 0), (frame.x, y, frame.w, 1), special_flags=pygame.BLEND_MULT)
        pygame.draw.rect(surf, DANGER if hijack else ACCENT, frame, 1)
        f, x = self.font, panel.x + 40
        name = card.speaker
        if hijack and int(time * 8) % 5 == 0:
            name = "".join(random.choice((c, "#")) for c in name)
        f.draw(surf, name, (x, panel.y + 4), DANGER if hijack else ACCENT, shadow=TEXT_SHADOW)
        left = card.typed
        for i, line in enumerate(card.lines):
            shown = line[:max(0, left)]
            left -= len(line)
            if shown:
                f.draw(surf, shown, (x, panel.y + 15 + i * 9), HIJACK_TEXT if hijack else TEXT,
                       shadow=TEXT_SHADOW)
        if hijack:                                                     # tear lines
            for _ in range(2):
                y = random.randrange(panel.y, panel.bottom)
                row = pygame.Rect(panel.x, y, panel.w, 1).clip(surf.get_rect())
                if row.w:
                    strip = surf.subsurface(row).copy()
                    surf.blit(strip, (row.x + random.randint(-6, 6), y))
        if card.typed >= card.chars and int(time * 3) % 2:
            f.draw(surf, "ENTER", (panel.right - 4 - f.size("ENTER")[0], panel.y + 4), TEXT_DIM)
