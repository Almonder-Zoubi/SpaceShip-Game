"""Secondary weapons (1 slot, automatic, no key): ROCKET POD and SIDE CANNONS.

They do about SECONDARY_SHARE of the gun's DPS and only hit rocks and minions: bosses shrug
them off, so they never change the BossSpec damage race."""
import math

from ..config.palette import FLAME, TRACER
from ..config.tuning import (ROCKET_POD_INTERVAL, SECONDARY_SHARE, SIDE_CANNON_INTERVAL)
from .base import Weapon
from .bolts import Bolts
from .homing import RocketSwarm


class Secondary(Weapon):
    """targets passed to update() are rocks + minions only (the game filters them)."""


class RocketPod(Secondary):
    name = "ROCKET POD"

    def __init__(self):
        self.swarm = RocketSwarm(speed=210, turn=5.5)
        self.reset()

    def reset(self):
        self.swarm.clear()
        self.timer = ROCKET_POD_INTERVAL
        self.shots = 0

    def update(self, dt, firing, ship, targets, fire):
        self.timer -= dt
        visible = self.swarm.on_screen(targets)
        if self.timer <= 0 and visible and ship.alive:
            self.timer = ROCKET_POD_INTERVAL
            self.shots += 1
            damage = self.loadout.gun_dps * SECONDARY_SHARE * ROCKET_POD_INTERVAL / 2
            for side in (-1, 1):
                x, y = ship.to_world(side * (ship.w / 2 - 1), 0)
                target = min(visible, key=lambda t: (t.x - x) ** 2 + (t.y - y) ** 2)
                rx, ry = ship.right
                self.swarm.launch(x, y, rx * side * 70, ry * side * 70 - 40, target, damage)
                fire.burst(x, y, 3, 30, 0.1, FLAME[:3], size=(1, 1))
        return self.swarm.update(dt, targets, fire)

    def draw(self, surf):
        self.swarm.draw(surf)


class SideCannons(Secondary):
    name = "SIDE CANNONS"

    def __init__(self):
        self.bolts = Bolts(TRACER)
        self.reset()

    def reset(self):
        self.bolts.clear()
        self.cooldown = 0.0
        self.shots = 0

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if self.cooldown <= 0 and ship.alive:
            sides = {side for t in targets for side in (-1, 1)
                     if abs(t.y - ship.y) < 26 + t.bound and (t.x - ship.x) * side > 0}
            if sides:
                self.cooldown = SIDE_CANNON_INTERVAL
                self.shots += 1
                damage = self.loadout.gun_dps * SECONDARY_SHARE * SIDE_CANNON_INTERVAL
                for side in sides:
                    x, y = ship.to_world(side * (ship.w / 2), -2)
                    self.bolts.fire(x, y, ship.angle + side * math.radians(80), 260, damage)
        return self.bolts.update(dt, targets, None)

    def draw(self, surf):
        self.bolts.draw(surf)
