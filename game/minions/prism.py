"""Prism turret (level 7): rides on a big crystal rock and fires refracted 3-way shots.
Break its crystal and the turret falls with it."""
import math
import random

from ..config.display import LOW_W
from ..config.tuning import (POINTS_PRISM, PRISM_BULLET_DAMAGE, PRISM_BULLET_SPEED, PRISM_HP,
                             PRISM_INTERVAL)
from ..core.pixelart import sprite_from_rows
from ..obstacles.asteroid import CrystalRock
from .base import Enemy
from .bullets import shoot

PRISM_ROWS = (
    "....K....",
    "...KWK...",
    "..KCWBK..",
    ".KCCWBBK.",
    "KCCCWBBBK",
    ".KKKKKKK.",
    "..KGQGK..",
    "..KKKKK..",
)
COLORS = {"K": (18, 14, 30), "W": (255, 255, 255), "C": (140, 230, 255), "B": (120, 90, 220),
          "G": (90, 80, 120), "Q": (255, 80, 120)}


class PrismTurret(Enemy):
    points = POINTS_PRISM
    contact_damage = 18

    _image = None

    def __init__(self, host):
        if PrismTurret._image is None:
            PrismTurret._image = sprite_from_rows(PRISM_ROWS, COLORS)
        self.host = host
        super().__init__(PrismTurret._image, host.x, host.y, PRISM_HP)
        self.fire_timer = random.uniform(0.8, PRISM_INTERVAL)

    def move(self, dt, world):
        self.x, self.y = self.host.x, self.host.y - self.host.radius - 2
        if self.host not in world.asteroids:          # its crystal broke: it falls too
            self.hp = 0

    def attack(self, dt, world):
        self.fire_timer -= dt
        if self.fire_timer <= 0 and world.ship.alive:
            self.fire_timer = PRISM_INTERVAL
            aim = math.atan2(world.ship.y - self.y, world.ship.x - self.x)
            for off in (-0.3, 0.0, 0.3):
                shoot(world, self.x, self.y, aim + off, PRISM_BULLET_SPEED, PRISM_BULLET_DAMAGE)


def prism_turret(game):
    """A big crystal rock with a turret on it; the rock joins the field."""
    art = game.library.pick(11, 13, ("crystal",))
    rock = CrystalRock(art, random.uniform(40, LOW_W - 40), -art.size / 2,
                       random.uniform(-6, 6), random.uniform(40, 55), random.uniform(-0.6, 0.6),
                       hp_scale=game.level.difficulty.rock_hp * 1.5)
    game.asteroids.append(rock)
    return [PrismTurret(rock)]
