"""Boss 1: GUNSHIP — sprite and behaviour."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import ENEMY_SHOT
from ..core.pixelart import CharCanvas
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss
from .spec import BossSpec

GUNSHIP_SPEC = BossSpec("GUNSHIP", strength=3.0, fight_time=40)

# Boss 1 "GUNSHIP": heavy armoured gunship flying nose-down towards the player.
# Drawn as the left half on a CharCanvas, then mirrored and outlined (70x48 px).
GUNSHIP_HALF_W, GUNSHIP_HALF_H = 34, 46
# Muzzles in final-sprite pixels (after mirror + outline): main cannon, left & right turrets.
GUNSHIP_MUZZLES = {"main": (34, 47), "left": (8, 39), "right": (61, 39)}
# Engine vents (for exhaust particles) in final-sprite pixels.
GUNSHIP_VENTS = ((22, 1), (47, 1))


def _gunship_half():
    c = CharCanvas(GUNSHIP_HALF_W, GUNSHIP_HALF_H)
    # Swept wing with a lit leading edge, shadowed trailing edge, red stripe and panel seams.
    c.poly([(25, 12), (1, 23), (1, 28), (25, 31)], "M")
    c.line(25, 12, 1, 23, "W")
    c.line(25, 13, 1, 24, "L")
    c.line(25, 31, 1, 28, "H")
    c.line(25, 17, 3, 25, "E")
    c.line(25, 18, 3, 26, "e")
    for x in (11, 18):
        c.line(x, 13 + (25 - x) // 2 + 3, x, 28, "H")
    c.set(1, 23, "E")                                   # wing-tip light
    # Engine nacelle with intake and glowing vents on top.
    c.rect(17, 0, 25, 14, "M")
    c.line(17, 0, 17, 14, "H")
    c.line(18, 1, 18, 13, "L")
    c.rect(19, 0, 24, 0, "V")
    c.rect(19, 1, 24, 1, "y")
    c.rect(19, 4, 23, 9, "H")
    c.rect(20, 5, 22, 8, "G")
    # Fuselage: rounded top, lit centre, armour seams, rivets, red emblem.
    c.rect(26, 3, 33, 36, "L")
    c.rect(29, 2, 33, 2, "L")
    c.line(26, 3, 26, 36, "H")
    c.line(27, 3, 27, 36, "M")
    c.rect(30, 2, 33, 4, "W")
    for y in (11, 19):
        c.line(27, y, 33, y, "H")
    for y in (7, 15, 23):
        c.set(29, y, "W")
    c.rect(32, 13, 33, 16, "E")
    c.set(31, 14, "E")
    c.set(31, 15, "e")
    # Glowing cockpit near the nose.
    c.rect(29, 25, 33, 32, "G")
    c.rect(30, 26, 33, 31, "Y")
    c.line(30, 26, 30, 31, "y")
    c.rect(32, 27, 33, 27, "W")
    # Nose taper and main cannon.
    c.poly([(26, 36), (34, 36), (34, 44), (30, 44)], "M")
    c.line(27, 37, 30, 43, "H")
    c.rect(32, 37, 33, 45, "G")
    c.rect(33, 38, 33, 44, "g")
    # Wing turret with barrel.
    c.circle(7, 27, 4, "H")
    c.circle(7, 27, 3, "M")
    c.circle(7, 26, 1, "E")
    c.rect(6, 30, 8, 37, "G")
    c.line(7, 31, 7, 37, "g")
    return c.rows()


def build_gunship():
    return build_boss_sprite(_gunship_half(), HULL_COLORS)


class Gunship(Boss):
    """Boss 1. Strafes left/right and cycles through attacks:

    spread  -- 5-shot fan from the nose cannon, aimed at the rocket (short charge-up glow)
    turrets -- alternating aimed shots from the wing turrets
    ring    -- (below 50% hp) a radial burst of bullets
    Below 50% hp it also moves and fires 30% faster; bullet damage is scaled down by the
    same factor so its damage per second (and therefore its strength) stays as specified.
    """

    EPITHET = "IRON FLEET ENFORCER"          # boss name card

    SPREAD_INTERVAL, SPREAD_SHOTS, SPREAD_GAP, SPREAD_SPEED = 1.2, 5, 0.22, 105
    TURRET_INTERVAL, TURRET_SPEED = 0.45, 135
    RING_SHOTS, RING_SPEED = 14, 75
    CHARGE_TIME = 0.35
    RAGE = 1.3
    PATTERN = (("spread", 4.0), ("turrets", 3.0), ("rest", 1.2))
    PATTERN_RAGE = (("spread", 4.0), ("turrets", 3.0), ("ring", 0.6), ("rest", 0.6))
    # Bullets that would hit a rocket sitting still, per second, averaged over PATTERN:
    # one per spread volley (the centre shot) plus every turret shot.
    AIMED_RATE = (4.0 / SPREAD_INTERVAL + 3.0 / TURRET_INTERVAL) / (4.0 + 3.0 + 1.2)

    def __init__(self, spec=GUNSHIP_SPEC):
        super().__init__(spec, build_gunship(), GUNSHIP_MUZZLES, list(GUNSHIP_VENTS))
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.turret_side = 0
        self.charge = 0.0

    @property
    def enraged(self):
        return self.hp < self.max_hp / 2

    def fight(self, dt, world):
        rate = self.RAGE if self.enraged else 1.0
        self.move_time += dt * rate
        swing = LOW_W / 2 - self.w / 2 - 6
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.55) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.4) * 5

        pattern = self.PATTERN_RAGE if self.enraged else self.PATTERN
        name, duration = pattern[self.pattern_index % len(pattern)]
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.charge = 0.0
            return
        self.fire_timer -= dt * rate
        damage = self.bullet_damage / rate
        ship = world.ship

        if name == "spread":
            self.charge = max(0.0, 1 - self.fire_timer / self.CHARGE_TIME)
            if self.fire_timer <= 0:
                self.fire_timer = self.SPREAD_INTERVAL
                mx, my = self.point(*self.muzzles["main"])
                aim = math.atan2(ship.y - my, ship.x - mx)
                for i in range(self.SPREAD_SHOTS):
                    a = aim + (i - self.SPREAD_SHOTS // 2) * self.SPREAD_GAP
                    self._shoot(world, mx, my, a, self.SPREAD_SPEED, damage)
                self.charge = 0.0
        elif name == "turrets":
            self.charge = 0.0
            if self.fire_timer <= 0:
                self.fire_timer = self.TURRET_INTERVAL
                mx, my = self.point(*self.muzzles["left" if self.turret_side == 0 else "right"])
                self.turret_side = 1 - self.turret_side
                self._shoot(world, mx, my, math.atan2(ship.y - my, ship.x - mx),
                            self.TURRET_SPEED, damage)
        elif name == "ring":
            if self.fire_timer <= 0:
                self.fire_timer = 99.0                 # once per ring attack
                offset = random.uniform(0, math.tau)
                for i in range(self.RING_SHOTS):
                    self._shoot(world, self.x, self.y, offset + math.tau * i / self.RING_SHOTS,
                                self.RING_SPEED, damage)
        else:
            self.charge = 0.0

    def draw(self, surf):
        super().draw(surf)
        if self.charge > 0 and self.state == "fight":
            mx, my = self.point(*self.muzzles["main"])
            r = 1 + int(self.charge * 4)
            pygame.draw.circle(surf, ENEMY_SHOT[1], (int(mx), int(my)), r)
            pygame.draw.circle(surf, ENEMY_SHOT[0], (int(mx), int(my)), max(1, r - 2))
