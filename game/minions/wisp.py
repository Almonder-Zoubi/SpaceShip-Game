"""WISP (galaxy 2): a light, fast Hollow scout. It side-steps when the rocket lines up a shot
on it, and fires lead shots at where the rocket will be."""
import math
import random

from ..config.display import LOW_W
from ..config.tuning import (POINTS_WISP, WISP_BULLET_DAMAGE, WISP_BULLET_SPEED, WISP_DODGE,
                             WISP_DODGE_COOLDOWN, WISP_FIRE, WISP_HP, WISP_SPEED)
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .veil_bullets import LeadShot, aimed

ROWS = (
    "...KKK...",
    "..KVWVK..",
    ".KVWWWVK.",
    "KVVWKWVVK",
    ".KVVVVVK.",
    "..KVVVK..",
    "...KvK...",
    "...KvK...",
    "....K....",
)
COLORS = {"K": (20, 10, 34), "V": (150, 100, 240), "v": (80, 50, 160), "W": (230, 220, 255)}


class Wisp(Enemy):
    points = POINTS_WISP
    contact_damage = 14
    _image = None

    def __init__(self, x, y=-8):
        if Wisp._image is None:
            Wisp._image = sprite_from_rows(ROWS, COLORS)
        super().__init__(Wisp._image, x, y, WISP_HP)
        self.vx = 0.0
        self.cooldown = 0.0
        self.fire_timer = random.uniform(0.8, WISP_FIRE)
        self.phase = random.uniform(0, math.tau)

    def lined_up(self, world):
        """Is the rocket below it, close enough in x for a straight shot to hit?"""
        ship = world.ship
        return ship.alive and ship.y > self.y and abs(ship.x - self.x) < self.w / 2 + 5

    def move(self, dt, world):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.cooldown <= 0 and self.lined_up(world):
            side = -1 if world.ship.x > self.x else 1           # step away from the line
            if not 16 < self.x + side * 30 < LOW_W - 16:
                side = -side
            self.vx = side * WISP_DODGE
            self.cooldown = WISP_DODGE_COOLDOWN
        self.vx *= max(0.0, 1 - 4 * dt)
        self.x += (self.vx + math.sin(self.time * 2 + self.phase) * 14) * dt
        self.y += WISP_SPEED * dt
        self.x = min(LOW_W - 8, max(8, self.x))

    def attack(self, dt, world):
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = WISP_FIRE * random.uniform(0.8, 1.2)
            ship = world.ship
            t = math.hypot(ship.x - self.x, ship.y - self.y) / WISP_BULLET_SPEED
            angle = math.atan2(ship.y + ship.vy * t * 0.8 - self.y, ship.x + ship.vx * t * 0.8 - self.x)
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 4, angle,
                                             WISP_BULLET_SPEED, WISP_BULLET_DAMAGE))


def wisp_pair(game):
    x = random.uniform(50, LOW_W - 50)
    return [Wisp(x - 24), Wisp(x + 24, -20)]
