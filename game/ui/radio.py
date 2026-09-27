"""Radio cards: short story lines from COMMANDER VEGA (with a pixel portrait) at the start of
a level or wave. They type themselves out while the game runs; ENTER skips."""
import pygame

from ..config.display import LOW_W
from ..config.palette import ACCENT, EMPTY, INK, TEXT, TEXT_DIM, TEXT_SHADOW
from ..config.tuning import RADIO_CHARS_PER_S, RADIO_HOLD
from ..core.pixelart import sprite_from_rows

VEGA_ROWS = (
    "........KKKKKKKK........",
    "......KKGGGGGGGGKK......",
    ".....KGGLLLLLLLLGGK.....",
    "....KGLLLLLLLLLLLLGK....",
    "....KGLKKKKKKKKKKLGK....",
    "...KGLKCCCCCCCCCCKLGK...",
    "...KGKCSSSSSSSSSSCKGK...",
    "...KGKSSSSSSSSSSSSKGK...",
    "...KGKSKKSSSSSSKKSKGK...",
    "...KGKSWBSSSSSSWBSKGK...",
    "...KGKSSSSSsSSSSSSKGK...",
    "...KGKSSSSSsSSSSSSKGK...",
    "...KGKsSSSSSSSSSSsKGK...",
    "...KGKKsSSRRRRSSsKKGK...",
    "...KGGKKsSSSSSSsKKGGK...",
    "....KGGKKssssssKKGGK....",
    "....KGGGKKKKKKKKGGGK....",
    "...KDDGGGGGGGGGGGGDDK...",
    "..KDDDGGGYYGGYYGGGDDDK..",
    ".KDDDDGGGGGGGGGGGGDDDDK.",
    "KDDDDDDGGGGGGGGGGDDDDDDK",
    "KDDDDDDDGGGGGGGGDDDDDDDK",
    "KDDDDDDDDGGGGGGDDDDDDDDK",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
)
VEGA_COLORS = {
    "K": INK, "G": (110, 118, 140), "L": (170, 178, 196), "C": (120, 220, 255),
    "S": (232, 186, 150), "s": (184, 132, 104), "W": (250, 250, 245), "B": (60, 120, 220),
    "R": (170, 70, 80), "D": (48, 56, 92), "Y": (255, 204, 64),
}
PANEL = pygame.Rect(8, 34, LOW_W - 16, 42)          # under the HUD, over the incoming field


class RadioCard:
    """A message: who speaks and 1-3 lines (<= 42 characters each)."""

    def __init__(self, lines, speaker="COMMANDER VEGA", delay=0.0):
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
    """Draws a RadioCard under the HUD (it slides in and out)."""

    def __init__(self, font):
        self.font = font
        self.portrait = sprite_from_rows(VEGA_ROWS, VEGA_COLORS)

    def draw(self, surf, card, time):
        if not card.visible:
            return
        panel = PANEL.move(0, -int((1 - card.fade) * 60))
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((*INK, 190))
        surf.blit(shade, panel)
        pygame.draw.rect(surf, TEXT_DIM, panel, 1)
        frame = pygame.Rect(panel.x + 5, panel.y + 7, 28, 28)
        surf.fill(EMPTY, frame)
        surf.blit(self.portrait, (frame.x + 2, frame.y + 2))
        for y in range(frame.y + int(time * 20) % 3, frame.bottom, 3):   # radio scanlines
            surf.fill((0, 0, 0), (frame.x, y, frame.w, 1), special_flags=pygame.BLEND_MULT)
        pygame.draw.rect(surf, ACCENT, frame, 1)
        f, x = self.font, panel.x + 40
        f.draw(surf, card.speaker, (x, panel.y + 4), ACCENT, shadow=TEXT_SHADOW)
        left = card.typed
        for i, line in enumerate(card.lines):
            shown = line[:max(0, left)]
            left -= len(line)
            if shown:
                f.draw(surf, shown, (x, panel.y + 15 + i * 9), TEXT, shadow=TEXT_SHADOW)
        if card.typed >= card.chars and int(time * 3) % 2:
            f.draw(surf, "ENTER", (panel.right - 4 - f.size("ENTER")[0], panel.y + 4), TEXT_DIM)
