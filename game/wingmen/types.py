"""The wingmen: PIP (gunner), GUARDIAN (blocks bullets), MEDIC (repairs), HUNTER (rockets at
minions), MAGPIE (collects coins), and TWIN (the temporary copy from the TWIN boost)."""
import math
import random

import pygame

from ..config.palette import BOOST_COLORS, FLAME, HEAL, SPARK
from ..config.tuning import (GUARDIAN_COOLDOWN, GUARDIAN_ORBIT, GUARDIAN_SPIN, HUNTER_DAMAGE,
                             HUNTER_INTERVAL, HUNTER_ROCKETS, MAGPIE_RADIUS, MEDIC_DELAY,
                             MEDIC_RATE, PIP_INTERVAL, PIP_SHARE, TWIN_SHARE)
from ..weapons.homing import RocketSwarm
from .art import GUARDIAN_ROWS, HUNTER_ROWS, MAGPIE_ROWS, MEDIC_ROWS, PIP_ROWS
from .base import Bolts, Wingman


class Pip(Wingman):
    """Gunner: fires with the player (a share of the gun's DPS); level 5 adds angled shots."""

    name = "PIP"
    rows = PIP_ROWS
    role = ("GUNNER: FIRES WITH YOU", "SMALL SHARE OF YOUR DPS")
    perk = "LV5: ANGLED SHOTS"

    def __init__(self, level=1, side=-1):
        super().__init__(level, side)
        self.bolts = Bolts()
        self.cooldown = 0.0

    @property
    def share(self):
        return PIP_SHARE[self.level - 1]

    def act(self, dt, game, firing):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = PIP_INTERVAL
            damage = self.share * game.ship.loadout.gun_dps * PIP_INTERVAL
            angle = game.ship.angle
            if self.level >= 5:                      # the same damage, split three ways
                for off in (-0.25, 0.0, 0.25):
                    self.bolts.fire(self.x, self.y - 5, angle + off, 300, damage / 3)
            else:
                self.bolts.fire(self.x, self.y - 5, angle, 300, damage)
        return self.bolts.update(dt, game.weapon_targets(), self)

    def reset(self):
        super().reset()
        self.bolts.clear()

    def draw_shots(self, surf):
        self.bolts.draw(surf)


class Twin(Pip):
    """TWIN boost: a copy of the player's ship flies on the other side for a while."""

    name = "TWIN"
    temporary = True
    role = ("A COPY OF YOUR SHIP",)

    def __init__(self, ship_image, side=1):
        self.ship_image = ship_image
        super().__init__(1, side)
        self.bolts = Bolts(BOOST_COLORS["OVERDRIVE"])

    def build_frames(self):
        image = self.ship_image
        return [pygame.transform.rotate(image, -90 * i) for i in range(4)]

    @property
    def share(self):
        return TWIN_SHARE

    @property
    def bound(self):
        return self.frames[0].get_width() // 2

    def slot(self, ship):
        return ship.to_world(self.side * (ship.w + 6), 6)


class Guardian(Wingman):
    """Orbits the ship and eats an enemy bullet every few seconds; level 5 reflects it."""

    name = "GUARDIAN"
    rows = GUARDIAN_ROWS
    role = ("ORBITS YOU AND BLOCKS", "AN ENEMY BULLET NOW AND THEN")
    perk = "LV5: REFLECTS THE BULLET"

    def __init__(self, level=1, side=-1):
        super().__init__(level, side)
        self.cooldown = 0.0
        self.orbit = 0.0
        self.bolts = Bolts()

    @property
    def ready(self):
        return self.cooldown <= 0

    def slot(self, ship):
        return (ship.x + math.cos(self.orbit) * GUARDIAN_ORBIT,
                ship.y + math.sin(self.orbit) * GUARDIAN_ORBIT * 0.8)

    def update(self, dt, game, firing):
        self.orbit += GUARDIAN_SPIN * dt
        return super().update(dt, game, firing)

    def act(self, dt, game, firing):
        self.cooldown = max(0.0, self.cooldown - dt)
        return self.bolts.update(dt, game.weapon_targets(), self)

    def touches(self, x, y, radius=0):
        return self.flying and math.hypot(x - self.x, y - self.y) < 6 + radius

    def block(self, bullet, game):
        """Blocks when charged; otherwise the bullet flies past (it isn't knocked out)."""
        if not self.ready:
            return False
        self.cooldown = GUARDIAN_COOLDOWN[self.level - 1]
        game.fire.burst(bullet.x, bullet.y, 8, 60, 0.25, BOOST_COLORS["SHIELD"], size=(1, 1))
        game.audio.play("shield")
        if self.level >= 5:                          # reflected: flies back as a shot
            self.bolts.fire(self.x, self.y, 0.0, 260, bullet.damage * 2)
        return True

    def reset(self):
        super().reset()
        self.bolts.clear()

    def draw(self, surf):
        super().draw(surf)
        if self.flying and self.ready:               # charged: a small halo
            pygame.draw.circle(surf, BOOST_COLORS["SHIELD"][3], (int(self.x), int(self.y)), 7, 1)

    def draw_shots(self, surf):
        self.bolts.draw(surf)


class Medic(Wingman):
    """Repairs the hull while no damage is taken; level 5 revives the ship once per level."""

    name = "MEDIC"
    rows = MEDIC_ROWS
    role = ("REPAIRS YOUR HULL WHEN", "YOU TAKE NO DAMAGE FOR 3 S")
    perk = "LV5: REVIVES YOU ONCE"

    def __init__(self, level=1, side=-1):
        super().__init__(level, side)
        self.revived = False
        self._beam = False

    def act(self, dt, game, firing):
        ship = game.ship
        self._beam = False
        if game.time - game.last_hurt >= MEDIC_DELAY and ship.hp < ship.max_hp:
            ship.heal(MEDIC_RATE[self.level - 1] * ship.max_hp * dt)
            self._beam = True
            self._target = (ship.x, ship.y)
            if random.random() < 12 * dt:
                game.fire.emit(ship.x + random.uniform(-4, 4), ship.y + random.uniform(-4, 4),
                               0, -20, 0.4, HEAL[1:], size=1)
        return []

    def can_revive(self):
        return self.level >= 5 and not self.revived and self.flying

    def draw_shots(self, surf):
        if self._beam and int(self.time * 10) % 2:
            pygame.draw.line(surf, HEAL[2], (int(self.x), int(self.y)),
                             (int(self._target[0]), int(self._target[1])))


class Hunter(Wingman):
    """Fires homing micro-rockets at minions (and rocks) every few seconds; never at bosses."""

    name = "HUNTER"
    rows = HUNTER_ROWS
    role = ("HOMING ROCKETS AT MINIONS", "AND ROCKS EVERY 2 S")
    perk = "LV5: 3 ROCKETS A VOLLEY"

    def __init__(self, level=1, side=-1):
        super().__init__(level, side)
        self.swarm = RocketSwarm(speed=190, turn=5.0)
        self.timer = HUNTER_INTERVAL

    def act(self, dt, game, firing):
        targets = game.enemies + game.asteroids
        self.timer -= dt
        if self.timer <= 0 and self.swarm.on_screen(targets):
            self.timer = HUNTER_INTERVAL
            damage = HUNTER_DAMAGE * game.ship.loadout.gun_damage
            visible = self.swarm.on_screen(targets)
            for i in range(HUNTER_ROCKETS[self.level - 1]):
                target = min(visible, key=lambda t: (0 if t in game.enemies else 1,
                                                     (t.x - self.x) ** 2 + (t.y - self.y) ** 2))
                self.swarm.launch(self.x, self.y, self.side * 60 * (i + 1), -60, target, damage)
            game.fire.burst(self.x, self.y - 4, 4, 40, 0.15, FLAME[:3], size=(1, 1))
        return self.swarm.update(dt, targets, game.fire, source=self)

    def reset(self):
        super().reset()
        self.swarm.clear()

    def draw_shots(self, surf):
        self.swarm.draw(surf)


class Magpie(Wingman):
    """Collects coins and pickups in a large radius; level 5: a coin may count twice."""

    name = "MAGPIE"
    rows = MAGPIE_ROWS
    role = ("PULLS IN COINS AND", "PICKUPS FROM FAR AWAY")
    perk = "LV5: +10% COINS"

    @property
    def radius(self):
        return MAGPIE_RADIUS[self.level - 1]

    def act(self, dt, game, firing):
        for pickup in game.pickups:
            pickup.magnet = max(pickup.magnet, self.radius)
        if random.random() < 6 * dt:
            game.fire.emit(self.x, self.y, random.uniform(-20, 20), random.uniform(-20, 20), 0.3,
                           SPARK, size=1)
        return []


WINGMEN = {cls.name: cls for cls in (Pip, Guardian, Medic, Hunter, Magpie)}
