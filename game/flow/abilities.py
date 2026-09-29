"""Abilities (galaxy 2): one slot, fired with SHIFT or the right mouse button, then a cooldown.

PHASE        -- a short dash where the rocket is heading, invulnerable while it lasts
FLARE        -- the darkness lifts and lurkers show (DARKNESS levels), bullets glow brighter
TIME SLIP    -- the enemy side slows to TIME_SLIP_SCALE for a moment
REPAIR DRONE -- heals REPAIR_SHARE of the hull over REPAIR_TIME
DECOY        -- a copy of the rocket stays behind; aimed shots go for it
"""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import GOOD, VEIL_GLOW
from ..config.tuning import (ABILITY_COOLDOWN, DECOY_TIME, FLARE_TIME, PHASE_DASH, PHASE_TIME,
                             REPAIR_SHARE, REPAIR_TIME, TIME_SLIP_SCALE, TIME_SLIP_TIME)
from ..core.particles import Shockwave
from ..ui.popup import Popup
from .states import State


class Decoy:
    """What aimed shots chase while DECOY runs (same interface as the ship for aiming)."""

    def __init__(self, x, y, time):
        self.x, self.y, self.time = x, y, time
        self.vx = self.vy = 0.0
        self.alive = True


class AbilitiesMixin:
    """Game mixin: the equipped ability, its cooldown and running effects."""

    def _reset_abilities(self):
        self.ability_cooldown = 0.0
        self.flare = 0.0                 # seconds of FLARE left
        self.time_slip = 0.0
        self.repair = 0.0
        self.decoy = None
        self.phase_trail = []            # (x, y, life) after-images of a PHASE dash

    @property
    def ability(self):
        name = self.save.ability
        return name if name in ABILITY_COOLDOWN and self.inventory.owns(name) else None

    @property
    def ability_ready(self):
        return bool(self.ability) and self.ability_cooldown <= 0

    def use_ability(self):
        """SHIFT / right click. Returns True if something happened."""
        name = self.ability
        if not name or self.state != State.PLAYING or not self.ship.alive:
            return False
        if self.ability_cooldown > 0:
            self.audio.play("denied")
            return False
        self.ability_cooldown = ABILITY_COOLDOWN[name]
        getattr(self, "_ability_" + name.lower().replace(" ", "_"))()
        self.audio.play("ability")
        return True

    def _ability_phase(self):
        ship = self.ship
        speed = math.hypot(ship.vx, ship.vy)
        dx, dy = (ship.vx / speed, ship.vy / speed) if speed > 20 else (0.0, -1.0)
        for i in range(6):                                   # after-images along the dash
            k = i / 6
            self.phase_trail.append([ship.x + dx * PHASE_DASH * k, ship.y + dy * PHASE_DASH * k,
                                     0.3 + 0.05 * i])
        ship.x = min(LOW_W - ship.w / 2, max(ship.w / 2, ship.x + dx * PHASE_DASH))
        ship.y = min(LOW_H - ship.h / 2, max(30, ship.y + dy * PHASE_DASH))
        ship.invulnerable_time = max(ship.invulnerable_time, PHASE_TIME)

    def _ability_flare(self):
        self.flare = FLARE_TIME
        self.screen_flash(0.1)
        self.shockwaves.append(Shockwave(self.ship.x, self.ship.y, max_radius=120, duration=0.6,
                                         color=(255, 240, 200)))

    def _ability_time_slip(self):
        self.time_slip = TIME_SLIP_TIME
        self.shockwaves.append(Shockwave(self.ship.x, self.ship.y, max_radius=160, duration=0.8,
                                         color=VEIL_GLOW[1]))

    def _ability_repair_drone(self):
        self.repair = REPAIR_TIME
        self.popups.append(Popup("REPAIR DRONE", self.ship.x, self.ship.y - 24, GOOD))

    def _ability_decoy(self):
        self.decoy = Decoy(self.ship.x, self.ship.y, DECOY_TIME)

    def aim_target(self):
        """What aimed enemy shots go for: the decoy while it lasts, else the rocket."""
        return self.decoy if self.decoy else self.ship

    @property
    def slip_scale(self):
        return TIME_SLIP_SCALE if self.time_slip > 0 else 1.0

    def _update_abilities(self, dt):
        self.ability_cooldown = max(0.0, self.ability_cooldown - dt)
        self.flare = max(0.0, self.flare - dt)
        self.time_slip = max(0.0, self.time_slip - dt)
        for p in self.phase_trail:
            p[2] -= dt
        self.phase_trail = [p for p in self.phase_trail if p[2] > 0]
        if self.decoy:
            self.decoy.time -= dt
            if self.decoy.time <= 0:
                self.decoy = None
        if self.repair > 0 and self.state == State.PLAYING and self.ship.alive:
            self.repair = max(0.0, self.repair - dt)
            ship = self.ship
            ship.hp = min(ship.max_hp, ship.hp + ship.max_hp * REPAIR_SHARE / REPAIR_TIME * dt)
            if random.random() < 12 * dt:
                a = random.uniform(0, math.tau)
                self.fire.emit(ship.x + math.cos(a) * 10, ship.y + math.sin(a) * 10, 0, -20, 0.4,
                               [GOOD, (40, 140, 80)], size=1)

    def draw_abilities(self, surf):
        """After-images, the decoy, the repair drone and the cooldown ring round the rocket."""
        image = self.ship.image
        for x, y, life in self.phase_trail:
            ghost = image.copy()
            ghost.fill((120, 90, 255, int(255 * min(1.0, life * 3))), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(ghost, ghost.get_rect(center=(int(x), int(y))))
        if self.decoy and int(self.time * 10) % 3:
            ghost = image.copy()
            ghost.fill((150, 200, 255, 170), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(ghost, ghost.get_rect(center=(int(self.decoy.x), int(self.decoy.y))))
        ship = self.ship
        if self.repair > 0:
            a = self.time * 5
            surf.fill(GOOD, (int(ship.x + math.cos(a) * 13), int(ship.y + math.sin(a) * 13), 2, 2))
        name = self.ability
        if not name or not ship.alive or self.state != State.PLAYING:
            return
        if self.ability_cooldown > 0:                       # the ring fills up again
            k = 1 - self.ability_cooldown / ABILITY_COOLDOWN[name]
            steps = int(24 * k)
            for i in range(steps):
                t = -math.pi / 2 + math.tau * i / 24
                surf.fill((70, 60, 110), (int(ship.x + math.cos(t) * 15),
                                          int(ship.y + math.sin(t) * 15), 1, 1))
        elif int(self.time * 3) % 4 == 0:                    # ready: a short glint
            pygame.draw.circle(surf, VEIL_GLOW[2], (int(ship.x), int(ship.y)), 15, 1)
