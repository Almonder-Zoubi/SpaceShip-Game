"""Boss 3: MOTHERSHIP, the final boss — sprite and behaviour (3 phases, sweeping beam)."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, ENEMY_SHOT, SPARK
from ..core.pixelart import CharCanvas
from ..minions.bullets import bullet
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss

# Boss 3 "MOTHERSHIP": huge swept-wing alien flagship. Four wing turrets, two hangar bays,
# a glowing eye dome and a beam cannon under the nose. Lights change with its 3 phases.
MOTHERSHIP_HALF_W, MOTHERSHIP_HALF_H = 62, 58
# In final-sprite pixels (126x60 after mirror + outline).
MOTHERSHIP_MUZZLES = {"turrets": ((17, 42), (39, 46), (86, 46), (108, 42)),
                      "eye": (62, 21), "beam": (62, 59)}
MOTHERSHIP_BAYS = ((29, 42), (96, 42))
MOTHERSHIP_VENTS = ((56, 1), (69, 1), (30, 12), (95, 12))
MOTHERSHIP_LIGHTS = (   # calm green -> angry orange -> furious red
    ((130, 255, 170), (30, 140, 90)),
    ((255, 176, 60), (176, 84, 20)),
    ((255, 64, 64), (150, 20, 34)),
)
MOTHERSHIP_COLORS = {
    **HULL_COLORS,
    "H": (44, 38, 68), "M": (78, 70, 112), "L": (124, 116, 162), "W": (184, 178, 218),
    "E": (70, 200, 170), "e": (30, 110, 100),
}


def _mothership_half(damaged=False):
    c = CharCanvas(MOTHERSHIP_HALF_W, MOTHERSHIP_HALF_H)
    # Swept wing: lit leading edge, shadowed trailing edge, teal stripes and panel seams.
    c.poly([(61, 6), (30, 10), (4, 26), (0, 34), (10, 38), (36, 40), (61, 44)], "M")
    c.line(61, 6, 30, 10, "W")
    c.line(30, 10, 4, 26, "L")
    c.line(30, 11, 5, 26, "L")
    c.line(0, 34, 10, 38, "H")
    c.line(10, 38, 36, 40, "H")
    c.line(36, 40, 61, 44, "H")
    c.line(46, 14, 12, 30, "E")
    c.line(46, 15, 12, 31, "e")
    c.line(40, 21, 20, 33, "H")
    for x in (22, 34):
        c.line(x, 17 if x == 34 else 23, x, 38, "H")
    c.set(0, 34, "Q")                                    # wing-tip light
    # Engine pods on the wing.
    c.rect(26, 8, 34, 13, "H")
    c.rect(27, 8, 33, 8, "V")
    c.rect(27, 9, 33, 9, "y")
    # Hangar bay under the wing.
    c.rect(24, 34, 32, 40, "G")
    for y in (36, 38, 40):
        c.line(25, y, 31, y, "q")
    c.line(24, 33, 32, 33, "Q")
    # Wing turrets with barrels.
    for tx, ty, length in ((16, 30, 10), (38, 34, 10)):
        c.circle(tx, ty, 3, "H")
        c.circle(tx, ty, 2, "M")
        c.set(tx, ty - 1, "E")
        c.rect(tx - 1, ty + 3, tx + 1, ty + length, "G")
        c.line(tx, ty + 4, tx, ty + length, "g")
    # Central body with armour bands and rivets.
    c.rect(48, 1, 61, 50, "L")
    c.rect(52, 0, 61, 0, "W")
    c.line(48, 1, 48, 50, "H")
    c.line(49, 1, 49, 50, "M")
    c.rect(52, 0, 58, 0, "V")
    for y in (31, 39):
        c.line(50, y, 61, y, "M")
    for y in (5, 34, 42):
        c.set(51, y, "W")
    c.rect(50, 44, 61, 45, "E")
    # Eye dome.
    c.circle(61, 20, 8, "G")
    c.circle(61, 20, 6, "q")
    c.circle(61, 20, 4, "Q")
    c.set(59, 17, "W")
    # Beam cannon under the nose.
    c.poly([(50, 50), (62, 50), (62, 55), (54, 55)], "M")
    c.rect(57, 46, 61, 56, "G")
    c.rect(59, 47, 61, 56, "g")
    c.rect(58, 56, 61, 57, "Q")
    if damaged:                                          # phase 3: cracked, burning armour
        c.line(50, 4, 54, 11, "K")
        c.line(54, 11, 52, 16, "K")
        c.line(18, 24, 24, 29, "K")
        c.line(24, 29, 21, 35, "K")
        c.line(40, 16, 44, 22, "K")
        for x, y in ((53, 12), (22, 30), (43, 21), (55, 36)):
            c.set(x, y, "V")
    return c.rows()


def build_mothership():
    """One sprite per phase (lights recoloured, phase 3 cracked)."""
    return [build_boss_sprite(_mothership_half(damaged=phase == 2),
                              {**MOTHERSHIP_COLORS, "Q": light, "q": dark})
            for phase, (light, dark) in enumerate(MOTHERSHIP_LIGHTS)]


class Mothership(Boss):
    """Boss 3, the final boss. Three phases, one per third of its health.

    Phase 1 (calm)    -- aimed 3-shot fans from four wing turrets, drone launches, bullet rings
    Phase 2 (angry)   -- x1.2; adds a sweeping BEAM: a red warning line, then a deadly column
                         straight down that follows the ship slowly; spirals
    Phase 3 (furious) -- x1.4; counter-rotating double spirals, 5-shot fans, faster rings
    Like the Carrier it roars between phases, and the game hands out rewards.
    """

    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("fans", 3.0), ("drones", 1.6), ("rings", 2.4), ("rest", 1.2)),
        (("beam", 3.2), ("fans", 2.6), ("drones", 1.4), ("spiral", 2.6), ("rest", 0.8)),
        (("spiral", 3.0), ("beam", 3.0), ("rings", 2.0), ("drones", 1.2), ("fans", 2.2),
         ("rest", 0.5)),
    )
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.45, 115, 0.2
    RING_INTERVAL, RING_SHOTS, RING_SPEED = 0.8, 14, 70
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.1, 74, 2.0
    DRONE_INTERVAL, DRONE_LAUNCHES, MAX_DRONES = 0.6, (1, 2, 2), 6
    BEAM_WARN, BEAM_HALF, BEAM_DAMAGE_X = 0.9, 4, 2.5     # telegraph s, half width px, x bullet
    # Aimed bullets per second at a rocket sitting still, phase 1: the centre shot of every
    # fan plus two shots from each of the two drones launched per cycle.
    AIMED_RATE = (3.0 / FAN_INTERVAL + 2 * 2) / (3.0 + 1.6 + 2.4 + 1.2)

    def __init__(self, spec):
        super().__init__(spec, build_mothership(), MOTHERSHIP_MUZZLES, list(MOTHERSHIP_VENTS))
        self.home_y = 20 + self.h / 2
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.8
        self.turret = 0
        self.launches = 0
        self.spiral_angle = 0.0
        self.beam = 0            # 0 off, 1 warning line, 2 firing

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.launches = 0
        self.beam = 0

    @property
    def rate(self):
        return self.RAGE[self.phase]

    @property
    def light(self):
        return MOTHERSHIP_LIGHTS[self.phase][0]

    def fight(self, dt, world):
        rate = self.rate
        pattern = self.PATTERNS[self.phase]
        name, duration = pattern[self.pattern_index % len(pattern)]
        # Slows down while the beam fires, so the beam sweeps instead of whipping around.
        self.move_time += dt * rate * (0.3 if name == "beam" else 1.0)
        swing = LOW_W / 2 - self.w / 2 - 4
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.4) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.0) * 3

        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.launches = 0
            self.beam = 0
            return
        if name == "beam":
            self._beam(dt, world, duration)
            return
        self.fire_timer -= dt * rate
        if name == "spiral":
            self.spiral_angle += self.SPIRAL_TURN * dt * rate
        if self.fire_timer > 0 or name == "rest":
            return
        getattr(self, "_" + name)(world)

    # --- attacks ------------------------------------------------------------------------
    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        ship = world.ship
        turrets = self.muzzles["turrets"]
        mx, my = self.point(*turrets[self.turret % len(turrets)])
        self.turret += 1
        aim = math.atan2(ship.y - my, ship.x - mx)
        n = 5 if self.phase == 2 else 3
        for i in range(n):
            self._shoot(world, mx, my, aim + (i - n // 2) * self.FAN_GAP, self.FAN_SPEED,
                        self.bullet_damage)

    def _drones(self, world):
        self.fire_timer = self.DRONE_INTERVAL
        if self.launches >= self.DRONE_LAUNCHES[self.phase] or len(world.enemies) >= self.MAX_DRONES:
            return
        self.launches += 1
        self._launch_drones(world, MOTHERSHIP_BAYS, self.bullet_damage)

    def _rings(self, world):
        self.fire_timer = self.RING_INTERVAL
        cx, cy = self.point(*self.muzzles["eye"])
        offset = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            world.enemy_bullets.append(bullet(cx, cy, offset + math.tau * i / self.RING_SHOTS,
                                              self.RING_SPEED, self.bullet_damage))

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        cx, cy = self.point(*self.muzzles["eye"])
        arms = 2
        spins = (1, -1) if self.phase == 2 else (1,)
        for spin in spins:
            for i in range(arms):
                a = spin * self.spiral_angle + math.tau * i / arms
                world.enemy_bullets.append(bullet(cx, cy, a, self.SPIRAL_SPEED,
                                                  self.bullet_damage))

    def _beam(self, dt, world, duration):
        """Warning line, then a column straight down from the beam cannon."""
        if self.attack_time < self.BEAM_WARN:
            self.beam = 1
            return
        if self.attack_time > duration - 0.2:
            self.beam = 0
            return
        if self.beam != 2:
            world.shake.add(0.35)
            world.audio.play("beam")
        self.beam = 2
        bx, by = self.point(*self.muzzles["beam"])
        ship = world.ship
        if random.random() < 30 * dt:                   # sparks where it hits the bottom
            world.fire.emit(bx + random.uniform(-4, 4), LOW_H - 1, random.uniform(-60, 60),
                            -random.uniform(40, 90), 0.3, SPARK)
        if ship.alive and ship.y > by and abs(ship.x - bx) < self.BEAM_HALF + ship.w * 0.35:
            world.hurt_ship(self.bullet_damage * self.BEAM_DAMAGE_X, bx, ship.y)

    def draw(self, surf):
        super().draw(surf)
        if self.state != "fight":
            return
        cx, cy = self.point(*self.muzzles["eye"])
        pulse = 0.5 + 0.5 * math.sin(self.move_time * 6 * self.rate)
        pygame.draw.circle(surf, self.light, (int(cx), int(cy)), 1 + int(pulse * (2 + self.phase)))
        surf.fill((255, 255, 255), (int(cx), int(cy), 1, 1))
        if self.roar > 0 or not self.beam:
            return
        bx, by = self.point(*self.muzzles["beam"])
        bx, by = int(bx), int(by)
        if self.beam == 1:                               # blinking warning line
            if int(self.attack_time * 12) % 2 == 0:
                pygame.draw.line(surf, DANGER, (bx, by), (bx, surf.get_height()))
            return
        wobble = int(self.attack_time * 30) % 2
        h = surf.get_height() - by
        half = self.BEAM_HALF + wobble
        surf.fill(ENEMY_SHOT[3], (bx - half - 1, by, 2 * half + 3, h))
        surf.fill(ENEMY_SHOT[2], (bx - half + 1, by, 2 * half - 1, h))
        surf.fill(ENEMY_SHOT[1], (bx - 1, by, 3, h))
        surf.fill(ENEMY_SHOT[0], (bx, by, 1, h))
        pygame.draw.circle(surf, ENEMY_SHOT[1], (bx, by), half + 2)
