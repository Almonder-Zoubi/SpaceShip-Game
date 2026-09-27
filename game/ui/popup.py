"""Floating text popups."""
import random

from ..config.display import LOW_W
from ..config.palette import ACCENT, TEXT_SHADOW, WHITE


class Popup:
    """Short text that floats up from where something happened (e.g. '+30 HP')."""

    LIFE = 1.1

    def __init__(self, text, x, y, color):
        self.text, self.x, self.y, self.color = text, x, y, color
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.LIFE

    def update(self, dt):
        self.t += dt
        self.y -= 18 * dt

    def draw(self, surf, font):
        if self.t > self.LIFE * 0.7 and int(self.t * 20) % 2:
            return                                   # blink out
        w = font.size(self.text)[0]
        x = min(LOW_W - w - 2, max(2, int(self.x) - w // 2))
        font.draw(surf, self.text, (x, int(self.y)), self.color, shadow=TEXT_SHADOW)


class DamageNumber(Popup):
    """Small number that pops off a boss where it was hit; bigger hits are gold."""

    LIFE = 0.6

    def __init__(self, amount, x, y):
        color = ACCENT if amount >= 60 else WHITE
        super().__init__(str(int(amount)), x + random.uniform(-6, 6), y - 6, color)
        self.vx = random.uniform(-14, 14)

    def update(self, dt):
        self.t += dt
        self.x += self.vx * dt
        self.y -= 30 * dt * (1 - self.t / self.LIFE)
