"""Interceptor (level 9): an armoured fighter with a front shield. It lines up, dashes at
the rocket, then cools down for a moment — shoot it from the side, or during the cool-down."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import SPARK
from ..config.tuning import (INTERCEPTOR_AIM, INTERCEPTOR_COOLDOWN, INTERCEPTOR_DAMAGE,
                             INTERCEPTOR_DASH, INTERCEPTOR_DASH_TIME, INTERCEPTOR_HP,
                             POINTS_INTERCEPTOR)
from ..core.pixelart import sprite_from_rows
from .base import Enemy

INTERCEPTOR_ROWS = (
    "K.........K",
    "KMK.....KMK",
    "KMMK...KMMK",
    ".KMLKKKLMK.",
    ".KLLLWLLLK.",
    "..KLQqQLK..",
    "..KLLQLLK..",
    "...KLLLK...",
    "....KWK....",
    ".....K.....",
)
COLORS = {"K": (18, 14, 30), "M": (70, 50, 110), "L": (160, 150, 200), "W": (240, 240, 255),
          "Q": (255, 70, 110), "q": (255, 200, 210)}
SHIELD = [(255, 255, 255), (150, 230, 255), (80, 160, 255)]


class Interceptor(Enemy):
    points = POINTS_INTERCEPTOR
    contact_damage = INTERCEPTOR_DAMAGE
    _image = None

    def __init__(self, x):
        if Interceptor._image is None:
            Interceptor._image = sprite_from_rows(INTERCEPTOR_ROWS, COLORS)
        super().__init__(Interceptor._image, x, -10, INTERCEPTOR_HP)
        self.mode = "enter"               # enter -> aim -> dash -> cool -> aim ... -> leave
        self.mode_time = 0.0
        self.facing = math.pi / 2         # radians, the shield's direction (down)
        self.dashes = 2
        self.home = (x, random.uniform(40, 90))
        self.blocked = 0.0                # a shield spark this long

    @property
    def shielded(self):
        return self.mode != "cool"

    def armour(self, hit):
        """The shield stops shots that hit it head-on (coming against its facing)."""
        fx, fy = math.cos(self.facing), math.sin(self.facing)
        if self.shielded and hit.dx * fx + hit.dy * fy < -0.45:
            self.blocked = 0.1
            return 0.0
        return 1.0

    def _set(self, mode):
        self.mode, self.mode_time = mode, 0.0

    def move(self, dt, world):
        self.mode_time += dt
        self.blocked = max(0.0, self.blocked - dt)
        ship = world.ship
        if self.mode == "enter":
            hx, hy = self.home
            self.x += (hx - self.x) * min(1.0, 3 * dt)
            self.y += (hy - self.y) * min(1.0, 3 * dt)
            if self.mode_time > 0.8:
                self._set("aim")
        elif self.mode == "aim":
            want = math.atan2(ship.y - self.y, ship.x - self.x)
            diff = (want - self.facing + math.pi) % math.tau - math.pi
            self.facing += max(-4 * dt, min(4 * dt, diff))
            self.x += math.sin(self.time * 3) * 20 * dt
            if self.mode_time > INTERCEPTOR_AIM:
                self._set("dash" if self.dashes > 0 else "leave")
                self.dashes -= 1
                if self.mode == "dash":
                    world.audio.play("dive")
        elif self.mode == "dash":
            self.x += math.cos(self.facing) * INTERCEPTOR_DASH * dt
            self.y += math.sin(self.facing) * INTERCEPTOR_DASH * dt
            if self.mode_time > INTERCEPTOR_DASH_TIME:
                self._set("cool")
        elif self.mode == "cool":
            if self.mode_time > INTERCEPTOR_COOLDOWN:
                self.home = (min(LOW_W - 20, max(20, self.x)), random.uniform(40, 90))
                self._set("enter")
        else:                                           # leave upwards
            self.y -= 120 * dt
        self.x = min(LOW_W - 6, max(6, self.x))

    @property
    def offscreen(self):
        return (self.mode == "leave" and self.y < -20) or super().offscreen

    def attack(self, dt, world):
        pass

    def draw(self, surf):
        angle = -math.degrees(self.facing) + 90
        image = pygame.transform.rotate(self.white if self.flash > 0 else self.image, angle)
        surf.blit(image, image.get_rect(center=(int(self.x), int(self.y))))
        if self.mode == "cool":                          # vulnerable: it glows
            if int(self.mode_time * 12) % 2:
                pygame.draw.circle(surf, SPARK[1], (int(self.x), int(self.y)), 7, 1)
            return
        fx, fy = math.cos(self.facing), math.sin(self.facing)     # the shield arc in front
        color = SHIELD[0] if self.blocked > 0 else SHIELD[2]
        for i in range(-3, 4):
            a = self.facing + i * 0.28
            surf.fill(color, (int(self.x + math.cos(a) * 9), int(self.y + math.sin(a) * 9), 1, 1))
        if self.mode == "aim" and int(self.mode_time * 10) % 2 == 0:          # the lock line
            for d in range(12, 60, 6):
                surf.fill(SHIELD[2], (int(self.x + fx * d), int(self.y + fy * d), 1, 1))


def interceptor_pair(game):
    return [Interceptor(random.uniform(40, LOW_W / 2 - 20)),
            Interceptor(random.uniform(LOW_W / 2 + 20, LOW_W - 40))]
