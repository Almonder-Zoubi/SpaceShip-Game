"""STALKERS (galaxy 2, BONE REEF): they hunt in pairs. The LURE hovers in front of the
rocket and draws its fire; the STRIKER waits at a side, shows a dotted line, then dashes
across the screen at the rocket's height. Kill the striker first - or the lure becomes one."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER
from ..config.tuning import (POINTS_STALKER, STALKER_DAMAGE, STALKER_DASH, STALKER_HP,
                             STALKER_SPEED, STALKER_WARN, WISP_BULLET_DAMAGE)
from ..core.pixelart import sprite_from_rows
from .base import Enemy
from .veil_bullets import LeadShot, aimed

ROWS = (
    "K.......K",
    "KBK...KBK",
    ".KBKKKBK.",
    "..KBWBK..",
    ".KBBRBBK.",
    "KBBKRKBBK",
    "KBK.K.KBK",
    "K.......K",
)
COLORS = {"K": (22, 12, 18), "B": (204, 194, 176), "W": (255, 255, 255), "R": (220, 60, 80)}


class Stalker(Enemy):
    points = POINTS_STALKER
    contact_damage = STALKER_DAMAGE
    _image = None

    def __init__(self, x, y, role, partner=None):
        if Stalker._image is None:
            Stalker._image = sprite_from_rows(ROWS, COLORS)
        super().__init__(Stalker._image, x, y, STALKER_HP)
        self.role = role                  # "lure" or "striker"
        self.partner = partner
        self.mode = "wait"                # striker: wait -> aim -> dash -> wait
        self.timer = random.uniform(1.5, 2.5)
        self.dash_y = 0.0
        self.dash_dir = 1
        self.fire_timer = random.uniform(0.6, 1.4)

    def move(self, dt, world):
        ship = world.ship
        if self.time > 24:                    # the hunt is over: they drop away
            self.y += 90 * dt
            return
        if self.role == "lure" and self.partner is not None and self.partner.hp <= 0:
            self.role, self.mode, self.timer = "striker", "wait", 1.0     # it takes over
        if self.role == "lure":
            tx, ty = ship.x + math.sin(self.time * 1.3) * 40, max(40, ship.y - 95)
            self.x += max(-STALKER_SPEED, min(STALKER_SPEED, (tx - self.x) * 2)) * dt
            self.y += max(-STALKER_SPEED, min(STALKER_SPEED, (ty - self.y) * 2)) * dt
            return
        self.timer -= dt
        if self.mode == "wait":               # park at a side, out of the line of fire
            side = -1 if self.x < LOW_W / 2 else 1
            tx = 12 if side < 0 else LOW_W - 12
            self.x += (tx - self.x) * min(1.0, 3 * dt)
            self.y += (ship.y - self.y) * min(1.0, 1.5 * dt)
            if self.timer <= 0:
                self.mode, self.timer = "aim", STALKER_WARN
                self.dash_y, self.dash_dir = ship.y, (1 if side < 0 else -1)
                world.audio.play("lock_on")
        elif self.mode == "aim":
            self.y += (self.dash_y - self.y) * min(1.0, 8 * dt)
            if self.timer <= 0:
                self.mode = "dash"
                world.audio.play("dive")
        elif self.mode == "dash":
            self.x += self.dash_dir * STALKER_DASH * dt
            if not -10 < self.x < LOW_W + 10:
                self.x = min(LOW_W - 12, max(12, self.x))
                self.mode, self.timer = "wait", random.uniform(1.8, 2.8)

    @property
    def offscreen(self):
        return self.y > 260

    def attack(self, dt, world):
        if self.role != "lure":
            return
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = random.uniform(1.4, 2.0)
            target = world.aim_target()
            angle = math.atan2(target.y - self.y, target.x - self.x)
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 4, angle, 100,
                                             WISP_BULLET_DAMAGE))

    def draw(self, surf):
        if self.role == "striker" and self.mode == "aim" and int(self.time * 14) % 2:
            for x in range(0, LOW_W, 6):                      # the dotted dash line
                surf.fill(DANGER, (x, int(self.dash_y), 3, 1))
        super().draw(surf)
        if self.role == "striker" and self.mode == "dash":
            pygame.draw.line(surf, (220, 60, 80), (int(self.x - self.dash_dir * 14), int(self.y)),
                             (int(self.x), int(self.y)))


def stalker_pair(game):
    x = random.uniform(60, LOW_W - 60)
    lure = Stalker(x, -10, "lure")
    striker = Stalker(random.choice((-8, LOW_W + 8)), 60, "striker", lure)
    lure.partner = striker
    return [lure, striker]
