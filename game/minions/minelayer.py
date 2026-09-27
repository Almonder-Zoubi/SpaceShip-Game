"""Mine layer (level 5): crosses the upper screen and drops mines that arm after a second.
A mine shot down blows up and hurts rocks and minions around it (never the ship)."""
import math
import random

from ..config.display import LOW_W
from ..config.palette import DANGER
from ..config.tuning import (MINE_ARM, MINE_BLAST, MINE_BLAST_DAMAGE, MINE_DAMAGE, MINE_FALL,
                             MINE_HP, MINELAYER_DROP, MINELAYER_HP, MINELAYER_SPEED,
                             POINTS_MINE, POINTS_MINELAYER)
from ..core.pixelart import sprite_from_rows
from .base import Enemy

MINELAYER_ROWS = (
    "....KKKKKKK....",
    "..KKLLLLLLLKK..",
    ".KLLWWLLLGGLLK.",
    "KOOLLLLLLLLLOOK",
    "KOOKKKQKQKKKOOK",
    ".KKGGGGGGGGGKK.",
    "..KYYKGGGKYYK..",
    "...KK.KXK.KK...",
    "......KKK......",
)
MINE_ROWS = (
    "..K.K..",
    ".KMKMK.",
    "KMMLMMK",
    ".KLQLK.",
    "KMMLMMK",
    ".KMKMK.",
    "..K.K..",
)
COLORS = {"K": (18, 14, 30), "L": (150, 110, 90), "W": (230, 210, 190), "G": (90, 70, 70),
          "O": (230, 120, 40), "Q": (255, 210, 90), "Y": (255, 170, 60), "X": (255, 90, 40),
          "M": (110, 100, 110)}
ARMED = dict(COLORS, Q=(255, 40, 40))


class MineLayer(Enemy):
    """Flies straight across the screen, dropping a mine every MINELAYER_DROP seconds."""

    points = POINTS_MINELAYER
    contact_damage = 20
    _image = None

    def __init__(self, side):
        if MineLayer._image is None:
            MineLayer._image = sprite_from_rows(MINELAYER_ROWS, COLORS)
        x = -20 if side < 0 else LOW_W + 20
        super().__init__(MineLayer._image, x, random.uniform(38, 80), MINELAYER_HP)
        self.vx = -side * MINELAYER_SPEED
        self.drop_timer = random.uniform(0.4, MINELAYER_DROP)

    @property
    def offscreen(self):
        return self.x < -30 and self.vx < 0 or self.x > LOW_W + 30 and self.vx > 0

    def move(self, dt, world):
        self.x += self.vx * dt
        self.y += math.sin(self.time * 2.5) * 6 * dt

    def attack(self, dt, world):
        self.drop_timer -= dt
        if self.drop_timer <= 0 and 10 < self.x < LOW_W - 10:
            self.drop_timer = MINELAYER_DROP
            world.enemies.append(Mine(self.x, self.y + 6))


class Mine(Enemy):
    """Drifts down; harmless for MINE_ARM seconds, then its light turns red. Shooting it sets
    off a blast that clears rocks and minions nearby."""

    points = POINTS_MINE
    drops_coins = False
    stat = False                       # neither counts for nor against the "destroyed" rating
    _images = None

    def __init__(self, x, y):
        if Mine._images is None:
            Mine._images = (sprite_from_rows(MINE_ROWS, COLORS), sprite_from_rows(MINE_ROWS, ARMED))
        super().__init__(Mine._images[0], x, y, MINE_HP)

    @property
    def armed(self):
        return self.time >= MINE_ARM

    @property
    def contact_damage(self):
        return MINE_DAMAGE if self.armed else 0

    def move(self, dt, world):
        self.y += MINE_FALL * dt
        self.x += math.sin(self.time * 3) * 4 * dt

    def attack(self, dt, world):
        pass

    def on_death(self, world, scored):
        if scored:
            world.area_blast(self.x, self.y, MINE_BLAST, MINE_BLAST_DAMAGE)
            world.audio.play("magma_burst")

    def draw(self, surf):
        blink = self.armed and int(self.time * 6) % 2 == 0
        self.image = Mine._images[1 if blink else 0]
        super().draw(surf)
        if self.armed and blink:
            surf.fill(DANGER, (int(self.x), int(self.y) - 5, 1, 1))


def minelayer_squad(game):
    """One mine layer from a random side."""
    return [MineLayer(random.choice((-1, 1)))]
