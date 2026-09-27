"""Game objects: the player's ship and asteroids."""
import math
import random

import pygame

from .pixelart import lerp, make_glow, ramp
from .settings import (FLAME, FLAME_LEAN, LOW_H, LOW_W, RCS, SHIP_ACCEL, SHIP_FRICTION,
                       SHIP_MARGIN, SHIP_MAX_SPEED, SMOKE, THROTTLE_BOOST, THROTTLE_IDLE,
                       THROTTLE_RESPONSE, THROTTLE_RETRO)
from .sprites import NOZZLE_OFFSETS, NOZZLE_ROW, build_ship_frames


class Ship:
    """Player rocket with inertia and a throttle that drives the engine flames.

    UP    -> throttle to full boost: long white-hot flames, smoke trail, faster world.
    DOWN  -> retro: flames shrink to a lean blue flicker, world slows down.
    LEFT/RIGHT -> bank sprite + side thruster puffs.
    """

    GLOW_STEPS = 8

    def __init__(self, x, y):
        self.frames = build_ship_frames()
        self.mask = pygame.mask.from_surface(self.frames[0])
        self.w, self.h = self.frames[0].get_size()
        self.glows = [make_glow(9, (255, 150, 60), (i + 1) / self.GLOW_STEPS)
                      for i in range(self.GLOW_STEPS)]
        self.reset(x, y)

    def reset(self, x, y):
        self.x, self.y = float(x), float(y)      # centre of the sprite
        self.vx = self.vy = 0.0
        self.throttle = THROTTLE_IDLE
        self.bank = 0
        self.alive = True
        self._emit_debt = 0.0
        self._rcs_debt = 0.0
        self._flicker = 0.0

    # --- geometry --------------------------------------------------------------
    @property
    def topleft(self):
        return int(self.x - self.w / 2), int(self.y - self.h / 2)

    def nozzles(self):
        left, top = self.topleft
        cx = left + self.w // 2
        return [(cx + off, top + NOZZLE_ROW) for off in NOZZLE_OFFSETS]

    # --- update ----------------------------------------------------------------
    def update(self, dt, keys, fire, smoke, autopilot=False):
        """Apply input (or autopilot), move, and emit exhaust into the particle systems."""
        if autopilot:
            ax, ay, target = 0, -1, THROTTLE_BOOST
        else:
            ax = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            up = keys[pygame.K_UP] or keys[pygame.K_w]
            down = keys[pygame.K_DOWN] or keys[pygame.K_s]
            ay = down - up
            target = THROTTLE_BOOST if up and not down else THROTTLE_RETRO if down and not up else THROTTLE_IDLE

        self.throttle += (target - self.throttle) * min(1.0, THROTTLE_RESPONSE * dt)
        self.bank = ax

        self.vx += ax * SHIP_ACCEL * dt
        self.vy += ay * SHIP_ACCEL * dt
        damp = max(0.0, 1 - SHIP_FRICTION * dt)
        if not ax:
            self.vx *= damp
        if not ay:
            self.vy *= damp
        speed = math.hypot(self.vx, self.vy)
        if speed > SHIP_MAX_SPEED:
            self.vx, self.vy = self.vx / speed * SHIP_MAX_SPEED, self.vy / speed * SHIP_MAX_SPEED

        self.x += self.vx * dt
        self.y += self.vy * dt
        if not autopilot:
            hw, hh = self.w / 2 + SHIP_MARGIN, self.h / 2 + SHIP_MARGIN
            if not hw <= self.x <= LOW_W - hw:
                self.x = min(max(self.x, hw), LOW_W - hw)
                self.vx = 0
            if not hh <= self.y <= LOW_H - hh - 10:
                self.y = min(max(self.y, hh), LOW_H - hh - 10)
                self.vy = 0

        self._flicker = random.random()
        self._emit_exhaust(dt, fire, smoke)
        self._emit_rcs(dt, ax, smoke)

    def _flame_colors(self):
        return FLAME_LEAN if self.throttle < 0.25 else FLAME

    def _flame_length(self):
        return 2 + self.throttle * 9 + self._flicker * (1 + 3 * self.throttle)

    def _emit_exhaust(self, dt, fire, smoke):
        t = self.throttle
        self._emit_debt += (30 + 280 * t) * dt
        colors = self._flame_colors()
        length = self._flame_length()
        while self._emit_debt >= 1:
            self._emit_debt -= 1
            nx, ny = random.choice(self.nozzles())
            fire.emit(nx + random.uniform(-1.0, 2.0), ny + length * random.uniform(0.3, 0.7),
                      random.uniform(-8, 8) + self.vx * 0.2,
                      40 + 110 * t + random.uniform(0, 25) + max(0.0, self.vy) * 0.5,
                      (0.06 + 0.2 * t) * random.uniform(0.6, 1.0), colors,
                      size=2 if t > 0.6 and random.random() < 0.35 else 1)
            if t > 0.7 and random.random() < 0.18:
                smoke.emit(nx + random.uniform(-1, 2), ny + length,
                           random.uniform(-8, 8), 55 + 40 * t,
                           random.uniform(0.4, 0.8), SMOKE, size=random.randint(1, 2), drag=1.5)

    def _emit_rcs(self, dt, ax, smoke):
        """Side thruster: gas goes out opposite to the steering direction."""
        if not ax:
            return
        self._rcs_debt += 45 * dt
        left, top = self.topleft
        x = left + (self.w - 3 if ax < 0 else 2)
        while self._rcs_debt >= 1:
            self._rcs_debt -= 1
            smoke.emit(x, top + 11 + random.uniform(-1, 1),
                       -ax * random.uniform(40, 80), random.uniform(-6, 12),
                       random.uniform(0.12, 0.22), RCS, drag=4)

    # --- draw ------------------------------------------------------------------
    def draw_flames(self, surf):
        """Solid flame cones under the particles, plus a nozzle glow (additive)."""
        t = self.throttle
        colors = self._flame_colors()
        length = int(self._flame_length())
        glow = self.glows[min(self.GLOW_STEPS - 1, int(t * self.GLOW_STEPS))]
        for nx, ny in self.nozzles():
            surf.blit(glow, (nx - 9, ny - 7), special_flags=pygame.BLEND_ADD)
            for i in range(length):
                k = i / max(1, length)
                width = 3 if k < 0.45 and t > 0.3 else 1
                surf.fill(ramp(colors, k * 0.9), (nx - width // 2, ny + i, width, 1),
                          special_flags=pygame.BLEND_ADD)

    def draw(self, surf):
        surf.blit(self.frames[self.bank], self.topleft)


class Asteroid:
    """A falling, spinning rock drawn from pre-rendered AsteroidArt frames."""

    def __init__(self, art, x, y, vx, vy, spin):
        self.art = art
        self.x, self.y = float(x), float(y)       # centre
        self.vx, self.vy = vx, vy
        self.angle = random.uniform(0, math.tau)
        self.spin = spin

    @property
    def frame_index(self):
        return int(self.angle / math.tau * self.art.FRAMES) % self.art.FRAMES

    @property
    def topleft(self):
        half = self.art.size // 2
        return int(self.x) - half, int(self.y) - half

    @property
    def mask(self):
        return self.art.masks[self.frame_index]

    @property
    def offscreen(self):
        return self.y - self.art.size > LOW_H

    def update(self, dt, world_speed):
        self.x += self.vx * dt
        self.y += self.vy * world_speed * dt
        self.angle = (self.angle + self.spin * dt) % math.tau

    def collides_with(self, ship):
        sx, sy = ship.topleft
        ax, ay = self.topleft
        return ship.mask.overlap(self.mask, (ax - sx, ay - sy)) is not None

    def draw(self, surf):
        surf.blit(self.art.frames[self.frame_index], self.topleft)


def world_speed_for(throttle, slow, fast):
    """Map the ship's throttle onto the world scroll multiplier (idle = 1.0)."""
    if throttle < THROTTLE_IDLE:
        return lerp(slow, 1.0, (throttle - THROTTLE_RETRO) / (THROTTLE_IDLE - THROTTLE_RETRO))
    return lerp(1.0, fast, (throttle - THROTTLE_IDLE) / (THROTTLE_BOOST - THROTTLE_IDLE))
