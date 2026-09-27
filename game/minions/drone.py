"""Drone: small attack ship that flies in formations. Its sprite is defined here too."""
import math
import random

from ..config.display import LOW_W
from ..config.tuning import (DRONE_BULLET_DAMAGE, DRONE_BULLET_SPEED, DRONE_CONTACT_DAMAGE,
                             DRONE_HP, DRONE_SPEED, POINTS_DRONE)
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .bullets import shoot

DRONE_ROWS = (
    "KK.......KK",
    "KMK.....KMK",
    "KMMK...KMMK",
    ".KMLKKKLMK.",
    "..KLQQQLK..",
    "..KLQqQLK..",
    "...KLLLK...",
    "....KGK....",
    ".....K.....",
)
DRONE_COLORS = {
    "K": (18, 14, 30), "M": (120, 40, 76), "L": (196, 84, 110), "G": (40, 40, 56),
    "Q": (255, 210, 96), "q": (255, 120, 40),
}


def build_drone():
    return sprite_from_rows(DRONE_ROWS, DRONE_COLORS)


class Drone(Enemy):
    """Small attack drone: dives down with a sine sway, drifts towards the rocket
    and fires a couple of aimed shots before leaving the screen."""

    points = POINTS_DRONE
    contact_damage = DRONE_CONTACT_DAMAGE
    _image = None
    STEER = 0.8                 # how strongly it drifts towards the rocket's x (1/s)

    def __init__(self, x, y, vx=0.0, vy=DRONE_SPEED, sway=18.0, shots=2, bullet_damage=None,
                 steer=STEER):
        if Drone._image is None:
            Drone._image = build_drone()
        super().__init__(Drone._image, x, y, DRONE_HP)
        self.vx, self.vy = vx, vy
        self.sway, self.phase = sway, random.uniform(0, math.tau)
        self.shots, self.steer = shots, steer
        self.fire_timer = random.uniform(0.6, 1.4)
        self.bullet_damage = DRONE_BULLET_DAMAGE if bullet_damage is None else bullet_damage

    def move(self, dt, world):
        self.vx *= max(0.0, 1 - 1.5 * dt)                    # launch kick fades out
        steer = (world.ship.x - self.x) * self.steer if world.ship.alive else 0.0
        sway = math.cos(self.time * 3 + self.phase) * self.sway
        self.x += (self.vx + sway + max(-40.0, min(40.0, steer))) * dt
        self.y += self.vy * dt

    def attack(self, dt, world):
        self.fire_timer -= dt
        if self.shots and self.fire_timer <= 0 and world.ship.alive and self.y < world.ship.y - 20:
            self.shots -= 1
            self.fire_timer = random.uniform(0.9, 1.5)
            x, y = self.x, self.y + self.h / 2
            shoot(world, x, y, math.atan2(world.ship.y - y, world.ship.x - x),
                  DRONE_BULLET_SPEED, self.bullet_damage)


def drone_formation(kind=None):
    """A wave of drones entering from the top: 'v', 'line' or 'snake'."""
    kind = kind or random.choice(("v", "line", "snake"))
    cx = random.uniform(70, LOW_W - 70)
    if kind == "v":
        return [Drone(cx + i * 16, -10 - abs(i) * 12, sway=8, shots=1, steer=0.3)
                for i in range(-2, 3)]
    if kind == "line":
        return [Drone(40 + i * 60, -10, sway=24, shots=1, steer=0.1) for i in range(5)]
    return [Drone(cx, -10 - i * 16, sway=40, shots=1, steer=0.5) for i in range(5)]  # snake
