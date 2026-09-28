"""LURKERS (galaxy 2, THE DARK VEIL): black ships you only see in light. They creep closer
and fire shadow bullets (dark cores, bright rims: the shots always show)."""
import math
import random

from ..config.display import LOW_W
from ..config.tuning import LURKER_FIRE, LURKER_HP, LURKER_SPEED, POINTS_LURKER, WISP_BULLET_DAMAGE
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .veil_bullets import ShadowBullet, aimed

ROWS = (
    "K.........K",
    "KK.......KK",
    ".KSK...KSK.",
    ".KSSKKKSSK.",
    "..KSSSSSK..",
    "..KSRSRSK..",
    "...KSSSK...",
    "....KSK....",
    ".....K.....",
)
COLORS = {"K": (4, 2, 8), "S": (40, 36, 60), "R": (160, 30, 50)}


class Lurker(Enemy):
    points = POINTS_LURKER
    contact_damage = 16
    _image = None

    def __init__(self, x, y=-8):
        if Lurker._image is None:
            Lurker._image = sprite_from_rows(ROWS, COLORS)
        super().__init__(Lurker._image, x, y, LURKER_HP)
        self.fire_timer = random.uniform(1.0, LURKER_FIRE)
        self.phase = random.uniform(0, math.tau)

    def move(self, dt, world):
        target = world.aim_target()
        self.x += max(-LURKER_SPEED, min(LURKER_SPEED, (target.x - self.x) * 0.5)) * dt
        self.x += math.sin(self.time * 1.5 + self.phase) * 12 * dt
        self.y += (LURKER_SPEED * 0.6 if self.y < 120 else -8) * dt

    @property
    def offscreen(self):
        return self.time > 26

    def attack(self, dt, world):
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = LURKER_FIRE * random.uniform(0.8, 1.2)
            target = world.aim_target()
            angle = math.atan2(target.y - self.y, target.x - self.x)
            world.enemy_bullets.append(aimed(ShadowBullet, self.x, self.y + 4, angle, 90,
                                             WISP_BULLET_DAMAGE))


def lurker_pair(game):
    x = random.uniform(50, LOW_W - 50)
    return [Lurker(x - 30), Lurker(x + 30, -20)]
