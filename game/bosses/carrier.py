"""Boss 2: CARRIER — sprite and behaviour (3 phases, launches drones)."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..core.pixelart import CharCanvas
from ..minions.bullets import bullet
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss

# Boss 2 "CARRIER": wide carrier with two hangar pods that launch drones, side cannons
# and a central energy core. Its lights change colour with every phase (3 phases).
CARRIER_HALF_W, CARRIER_HALF_H = 46, 56
# In final-sprite pixels (94x58 after mirror + outline).
CARRIER_MUZZLES = {"left": (5, 47), "right": (88, 47), "core": (46, 41)}
CARRIER_BAYS = ((13, 44), (80, 44))
CARRIER_VENTS = ((13, 5), (80, 5), (43, 1), (50, 1))
CARRIER_LIGHTS = (   # (light, dark) per phase: calm cyan -> angry orange -> furious red
    ((110, 226, 255), (30, 110, 170)),
    ((255, 176, 60), (176, 84, 20)),
    ((255, 64, 64), (150, 20, 34)),
)


def _carrier_half(damaged=False):
    c = CharCanvas(CARRIER_HALF_W, CARRIER_HALF_H)
    # Strut between hull and pod.
    c.poly([(33, 12), (20, 17), (20, 31), (33, 29)], "M")
    c.line(33, 12, 20, 17, "L")
    c.line(33, 29, 20, 31, "H")
    for y in (20, 25):
        c.line(21, y, 32, y - 1, "H")
    # Engine blocks on top of the pod.
    c.rect(8, 3, 17, 8, "H")
    c.rect(9, 3, 16, 3, "V")
    c.rect(9, 4, 16, 4, "y")
    # Hangar pod: lit upper-left edge, shadowed right edge, hazard stripes, bay at the bottom.
    c.rect(4, 8, 21, 42, "M")
    c.rect(6, 43, 19, 44, "M")
    c.line(4, 8, 21, 8, "W")
    c.line(4, 9, 4, 42, "L")
    c.line(5, 9, 5, 42, "L")
    c.line(21, 9, 21, 42, "H")
    for x in range(6, 20, 4):
        c.rect(x, 19, x + 1, 20, "Y")
        c.rect(x + 2, 19, x + 3, 20, "G")
    c.line(8, 12, 17, 12, "H")
    c.line(8, 27, 17, 27, "H")
    c.rect(8, 34, 17, 34, "Q")
    c.rect(8, 35, 17, 44, "G")
    for y in (37, 40, 43):
        c.line(9, y, 16, y, "q")
    c.set(4, 9, "Q")                                    # pod-tip light
    # Side cannon on the outer edge of the pod.
    c.circle(4, 30, 3, "H")
    c.circle(4, 30, 2, "M")
    c.set(4, 29, "E")
    c.rect(3, 33, 5, 45, "G")
    c.line(4, 34, 4, 45, "g")
    # Central hull with a rounded top, armour seams and a red stripe.
    c.rect(32, 2, 45, 46, "L")
    c.rect(36, 0, 45, 1, "L")
    c.line(32, 2, 32, 46, "H")
    c.line(33, 2, 33, 46, "M")
    c.rect(38, 0, 45, 2, "W")
    c.rect(41, 0, 45, 0, "V")
    for y in (18, 30):
        c.line(33, y, 45, y, "M")
    c.rect(34, 22, 45, 23, "E")
    c.line(34, 24, 45, 24, "e")
    for y in (5, 27, 33):
        c.set(35, y, "W")
    # Bridge tower with windows.
    c.rect(38, 6, 45, 16, "M")
    c.line(38, 6, 45, 6, "W")
    c.line(38, 7, 38, 16, "H")
    c.rect(40, 9, 45, 9, "Q")
    c.rect(40, 12, 45, 12, "q")
    # Nose and energy core that fires the spirals.
    c.poly([(32, 46), (46, 46), (46, 56), (39, 56)], "M")
    c.line(33, 47, 38, 55, "H")
    c.circle(45, 41, 6, "G")
    c.circle(45, 41, 4, "q")
    c.circle(45, 41, 2, "Q")
    c.set(44, 40, "W")
    if damaged:                                         # phase 3: cracked, burning armour
        c.line(34, 4, 37, 10, "K")
        c.line(37, 10, 35, 15, "K")
        c.line(9, 14, 14, 18, "K")
        c.line(14, 18, 12, 24, "K")
        c.line(24, 19, 29, 26, "K")
        for x, y in ((36, 11), (13, 19), (27, 24), (41, 35)):
            c.set(x, y, "V")
    return c.rows()


def build_carrier():
    """One sprite per phase (lights recoloured, phase 3 cracked)."""
    return [build_boss_sprite(_carrier_half(damaged=phase == 2),
                              {**HULL_COLORS, "Q": light, "q": dark})
            for phase, (light, dark) in enumerate(CARRIER_LIGHTS)]


class Carrier(Boss):
    """Boss 2. A wide carrier with three phases, one per third of its health.

    Phase 1 (calm)    -- launches drones from its hangar bays, aimed side-cannon shots,
                         a rain of bullets from the hull
    Phase 2 (angry)   -- faster; rotating bullet spiral from the core, cannons fire 3-shot fans,
                         more drones
    Phase 3 (furious) -- faster still; bullet walls with a gap to fly through, a 3-arm spiral
    Between phases it roars (invulnerable, flashing red); the game rewards the player with a
    POWER core and a repair kit, so the rocket grows stronger as the boss gets angrier.
    """

    EPITHET = "THE DRONE HIVE"          # boss name card

    PHASES = 3
    RAGE = (1.0, 1.25, 1.5)                    # movement / fire speed per phase
    PATTERNS = (
        (("drones", 2.0), ("cannons", 3.0), ("rain", 2.5), ("rest", 1.2)),
        (("spiral", 3.2), ("drones", 1.6), ("cannons", 2.6), ("rest", 0.8)),
        (("wall", 3.4), ("spiral", 3.0), ("drones", 1.4), ("cannons", 2.2), ("rest", 0.5)),
    )
    CANNON_INTERVAL, CANNON_SPEED, CANNON_FAN = 0.5, 125, 0.16
    RAIN_INTERVAL, RAIN_SPEED = 0.14, 80
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.11, 72, 2.2
    WALL_INTERVAL, WALL_SPEED, WALL_GAP, WALL_SPACING = 1.1, 62, 44, 11
    DRONE_INTERVAL, DRONE_LAUNCHES, MAX_DRONES = 0.7, (1, 2, 2), 6
    # Aimed bullets per second at a rocket sitting still, phase 1: every cannon shot
    # plus two shots from each of the two drones launched per cycle.
    AIMED_RATE = (3.0 / CANNON_INTERVAL + 2 * 2) / (2.0 + 3.0 + 2.5 + 1.2)

    def __init__(self, spec):
        super().__init__(spec, build_carrier(), CARRIER_MUZZLES, list(CARRIER_VENTS))
        self.home_y = 22 + self.h / 2
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.8
        self.cannon_side = 0
        self.launches = 0
        self.spiral_angle = 0.0

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.launches = 0

    @property
    def rate(self):
        return self.RAGE[self.phase]

    @property
    def light(self):
        return CARRIER_LIGHTS[self.phase][0]

    def fight(self, dt, world):
        rate = self.rate
        self.move_time += dt * rate
        swing = LOW_W / 2 - self.w / 2 - 4
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.45) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.1) * 4

        pattern = self.PATTERNS[self.phase]
        name, duration = pattern[self.pattern_index % len(pattern)]
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.launches = 0
            return
        self.fire_timer -= dt * rate
        if self.fire_timer > 0 or name == "rest":
            if name == "spiral":
                self.spiral_angle += self.SPIRAL_TURN * dt * rate
            return
        getattr(self, "_" + name)(world)

    # --- attacks: each fires once and sets fire_timer for the next shot ---------------
    def _drones(self, world):
        self.fire_timer = self.DRONE_INTERVAL
        if self.launches >= self.DRONE_LAUNCHES[self.phase] or len(world.enemies) >= self.MAX_DRONES:
            return
        self.launches += 1
        self._launch_drones(world, CARRIER_BAYS, self.bullet_damage)

    def _cannons(self, world):
        self.fire_timer = self.CANNON_INTERVAL
        ship = world.ship
        mx, my = self.point(*self.muzzles["left" if self.cannon_side == 0 else "right"])
        self.cannon_side = 1 - self.cannon_side
        aim = math.atan2(ship.y - my, ship.x - mx)
        offsets = (0,) if self.phase == 0 else (-self.CANNON_FAN, 0, self.CANNON_FAN)
        for off in offsets:
            self._shoot(world, mx, my, aim + off, self.CANNON_SPEED, self.bullet_damage)

    def _rain(self, world):
        self.fire_timer = self.RAIN_INTERVAL
        x = self.x + random.uniform(-self.w / 2 + 6, self.w / 2 - 6)
        self._shoot(world, x, self.y + self.h / 2 - 8, math.pi / 2 + random.uniform(-0.45, 0.45),
                    self.RAIN_SPEED, self.bullet_damage)

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        arms = 2 + self.phase - 1
        cx, cy = self.point(*self.muzzles["core"])
        for i in range(arms):
            a = self.spiral_angle + math.tau * i / arms
            world.enemy_bullets.append(bullet(cx, cy, a, self.SPIRAL_SPEED, self.bullet_damage))

    def _wall(self, world):
        """A row of bullets across the screen with one gap near the rocket."""
        self.fire_timer = self.WALL_INTERVAL
        gap = min(LOW_W - 30, max(30, world.ship.x + random.uniform(-60, 60)))
        y = self.y + self.h / 2 - 4
        for x in range(5, LOW_W, self.WALL_SPACING):
            if abs(x - gap) > self.WALL_GAP / 2:
                world.enemy_bullets.append(bullet(x, y, math.pi / 2, self.WALL_SPEED,
                                                  self.bullet_damage))
        world.shake.add(0.1)

    def draw(self, surf):
        super().draw(surf)
        if self.state != "fight":
            return
        # The core glows in the phase colour and pulses faster the angrier the boss is.
        cx, cy = self.point(*self.muzzles["core"])
        pulse = 0.5 + 0.5 * math.sin(self.move_time * 6 * self.rate)
        r = 1 + int(pulse * (2 + self.phase))
        pygame.draw.circle(surf, self.light, (int(cx), int(cy)), r)
        surf.fill((255, 255, 255), (int(cx), int(cy), 1, 1))
