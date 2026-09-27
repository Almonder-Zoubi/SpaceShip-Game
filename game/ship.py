"""The player's rocket: direct arrow controls, engine effects and health."""
import math
import random

import pygame

from .pixelart import make_glow, ramp
from .settings import (FLAME, FLAME_LEAN, HIT_INVULNERABLE, HIT_KNOCKBACK, LOW_H, LOW_W, MK1, RCS,
                       SHIP_ACCEL, SHIP_FRICTION, SHIP_MARGIN, SMOKE, THROTTLE_BOOST,
                       THROTTLE_IDLE, THROTTLE_RESPONSE, THROTTLE_RETRO, TILT_DEGREES, TILT_RATE,
                       TILT_STEPS)
from .sprites import (NOZZLE_OFFSETS, NOZZLE_ROW, SHIP_PALETTES, SHIP_ROWS, build_ship_frames,
                      build_ship_tilts)

HALF_H = len(SHIP_ROWS) / 2


def pressed(keys, *codes):
    return any(keys[c] for c in codes)


class Ship:
    """Player rocket. Faces up; leans like '/' or '\\' while flying diagonally up.

    Arrows move the ship directly (two arrows = diagonal) with a little inertia.
    UP + LEFT/RIGHT leans the rocket up to TILT_DEGREES; it straightens on release.
    UP    -> full boost: long white-hot flames, smoke trail, faster world.
    DOWN  -> retro: flames shrink to a lean blue flicker, world slows down.
    LEFT/RIGHT -> bank sprite + side thruster puffs.
    """

    GLOW_STEPS = 8

    def __init__(self, x, y):
        self._models = {}                        # sprite sets per colour scheme, built on demand
        self.glows = [make_glow(9, (255, 150, 60), (i + 1) / self.GLOW_STEPS)
                      for i in range(self.GLOW_STEPS)]
        self.equip(MK1)
        self.reset(x, y)

    def equip(self, loadout):
        """Switch ship model (sprites, hull, speed). Weapons are equipped by the game."""
        self.loadout = loadout
        self.max_hp = loadout.max_hp
        self.max_speed = loadout.max_speed
        if loadout.colors not in self._models:
            colors = SHIP_PALETTES[loadout.colors]
            frames = build_ship_frames(colors)
            tilts = build_ship_tilts(TILT_DEGREES, TILT_STEPS, colors)
            self._models[loadout.colors] = (
                frames, {bank: pygame.mask.from_surface(f) for bank, f in frames.items()},
                tilts, [pygame.mask.from_surface(f) for f in tilts])
        self.frames, self.masks, self.tilt_frames, self.tilt_masks = self._models[loadout.colors]
        self.colors = SHIP_PALETTES[loadout.colors]
        self.w, self.h = self.frames[0].get_size()

    def reset(self, x, y):
        self.x, self.y = float(x), float(y)      # centre of the sprite
        self.vx = self.vy = 0.0
        self.bank = 0
        self.tilt = 0.0                          # degrees, + = leaning right ('/')
        self.throttle = THROTTLE_IDLE
        self.alive = True
        self.hp = self.max_hp
        self.invulnerable_time = 0.0
        self._emit_debt = 0.0
        self._rcs_debt = 0.0
        self._flicker = 0.0

    # --- geometry --------------------------------------------------------------
    @property
    def tilt_index(self):
        """-TILT_STEPS..TILT_STEPS: which leaning frame is shown (0 = upright)."""
        return round(self.tilt / TILT_DEGREES * TILT_STEPS)

    @property
    def angle(self):
        """Displayed lean in radians (clockwise), matching the frame on screen."""
        return math.radians(self.tilt_index * TILT_DEGREES / TILT_STEPS)

    @property
    def image(self):
        i = self.tilt_index
        return self.frames[self.bank] if i == 0 else self.tilt_frames[i + TILT_STEPS]

    @property
    def mask(self):
        i = self.tilt_index
        return self.masks[self.bank] if i == 0 else self.tilt_masks[i + TILT_STEPS]

    @property
    def topleft(self):
        w, h = self.image.get_size()
        return round(self.x - w / 2), round(self.y - h / 2)

    @property
    def forward(self):
        a = self.angle
        return math.sin(a), -math.cos(a)

    @property
    def right(self):
        a = self.angle
        return math.cos(a), math.sin(a)

    def to_world(self, lx, ly):
        """Sprite-local offset from the centre (x right, y down, nose up) -> world position."""
        c, s = math.cos(self.angle), math.sin(self.angle)
        return self.x + lx * c - ly * s, self.y + lx * s + ly * c

    def nozzles(self):
        return [self.to_world(off, NOZZLE_ROW - HALF_H) for off in NOZZLE_OFFSETS]

    def nose(self):
        return self.to_world(0, -HALF_H)

    @property
    def invulnerable(self):
        return self.invulnerable_time > 0

    # --- actions ---------------------------------------------------------------
    def take_hit(self, damage, from_x, from_y, knockback=HIT_KNOCKBACK):
        """Apply damage and knockback. Returns True if this hit destroyed the ship."""
        if self.invulnerable:
            return False
        self.hp = max(0, self.hp - damage)
        self.invulnerable_time = HIT_INVULNERABLE
        dx, dy = self.x - from_x, self.y - from_y
        dist = math.hypot(dx, dy) or 1.0
        self.vx += dx / dist * knockback
        self.vy += dy / dist * knockback
        return self.hp <= 0

    def heal(self, amount):
        """Restore hull points (capped). Returns how much was actually repaired."""
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    # --- update ----------------------------------------------------------------
    def update(self, dt, keys, fire, smoke, autopilot=False):
        """Apply input (or autopilot), move, and emit exhaust into the particle systems."""
        if autopilot:
            ax, ay, target = 0, -1, THROTTLE_BOOST
        else:
            ax = pressed(keys, pygame.K_RIGHT, pygame.K_d) - pressed(keys, pygame.K_LEFT, pygame.K_a)
            up = pressed(keys, pygame.K_UP, pygame.K_w)
            down = pressed(keys, pygame.K_DOWN, pygame.K_s)
            ay = down - up
            target = THROTTLE_BOOST if ay < 0 else THROTTLE_RETRO if ay > 0 else THROTTLE_IDLE

        self.throttle += (target - self.throttle) * min(1.0, THROTTLE_RESPONSE * dt)
        self.bank = ax
        tilt_target = TILT_DEGREES * ax if ay < 0 else 0.0
        step = TILT_RATE * dt
        self.tilt += max(-step, min(step, tilt_target - self.tilt))
        self.invulnerable_time = max(0.0, self.invulnerable_time - dt)

        self.vx += ax * SHIP_ACCEL * dt
        self.vy += ay * SHIP_ACCEL * dt
        damp = max(0.0, 1 - SHIP_FRICTION * dt)
        if not ax:
            self.vx *= damp
        if not ay:
            self.vy *= damp
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx, self.vy = self.vx / speed * self.max_speed, self.vy / speed * self.max_speed

        self.x += self.vx * dt
        self.y += self.vy * dt
        if not autopilot:
            self._keep_on_screen()

        self._flicker = random.random()
        self._emit_exhaust(dt, fire, smoke)
        self._emit_rcs(dt, ax, smoke)

    def _keep_on_screen(self):
        hw, hh = self.w / 2 + SHIP_MARGIN, self.h / 2 + SHIP_MARGIN
        if not hw <= self.x <= LOW_W - hw:
            self.x = min(max(self.x, hw), LOW_W - hw)
            self.vx = 0
        if not hh + 16 <= self.y <= LOW_H - hh - 10:      # stay clear of the HUD rows
            self.y = min(max(self.y, hh + 16), LOW_H - hh - 10)
            self.vy = 0

    def _flame_colors(self):
        return FLAME_LEAN if self.throttle < 0.25 else FLAME

    def _flame_length(self):
        return 2 + self.throttle * 9 + self._flicker * (1 + 3 * self.throttle)

    def _emit_exhaust(self, dt, fire, smoke):
        t = self.throttle
        self._emit_debt += (30 + 280 * t) * dt
        colors = self._flame_colors()
        length = self._flame_length()
        fx, fy = self.forward
        rx, ry = self.right
        while self._emit_debt >= 1:
            self._emit_debt -= 1
            nx, ny = random.choice(self.nozzles())
            back = length * random.uniform(0.3, 0.7)
            side = random.uniform(-1.0, 1.0)
            speed = 40 + 110 * t + random.uniform(0, 25)
            jitter = random.uniform(-8, 8)
            fire.emit(nx - fx * back + rx * side, ny - fy * back + ry * side,
                      -fx * speed + rx * jitter + self.vx * 0.2,
                      -fy * speed + ry * jitter + max(0.0, self.vy) * 0.5,
                      (0.06 + 0.2 * t) * random.uniform(0.6, 1.0), colors,
                      size=2 if t > 0.6 and random.random() < 0.35 else 1)
            if t > 0.7 and random.random() < 0.18:
                smoke.emit(nx - fx * length, ny - fy * length,
                           -fx * (55 + 40 * t) + random.uniform(-8, 8),
                           -fy * (55 + 40 * t) + random.uniform(-8, 8),
                           random.uniform(0.4, 0.8), SMOKE, size=random.randint(1, 2), drag=1.5)

    def _emit_rcs(self, dt, ax, smoke):
        """Side thruster: gas goes out opposite to the steering direction."""
        if not ax:
            return
        self._rcs_debt += 45 * dt
        x, y = self.to_world(-ax * 5, -1)
        while self._rcs_debt >= 1:
            self._rcs_debt -= 1
            smoke.emit(x, y + random.uniform(-1, 1),
                       -ax * random.uniform(40, 80), random.uniform(-6, 12),
                       random.uniform(0.12, 0.22), RCS, drag=4)

    # --- draw ------------------------------------------------------------------
    def draw_flames(self, surf):
        """Solid flame cones under the nozzles, plus a nozzle glow (additive)."""
        t = self.throttle
        colors = self._flame_colors()
        length = int(self._flame_length())
        glow = self.glows[min(self.GLOW_STEPS - 1, int(t * self.GLOW_STEPS))]
        fx, fy = self.forward
        rx, ry = self.right
        add = pygame.BLEND_ADD
        for nx, ny in self.nozzles():
            surf.blit(glow, (int(nx - fx * 2) - 9, int(ny - fy * 2) - 9), special_flags=add)
            for i in range(length):
                k = i / max(1, length)
                color = ramp(colors, k * 0.9)
                px, py = nx - fx * i, ny - fy * i
                for s in ((-1, 0, 1) if k < 0.45 and t > 0.3 else (0,)):
                    surf.fill(color, (int(px + rx * s), int(py + ry * s), 1, 1), special_flags=add)

    def draw(self, surf):
        if self.invulnerable_time > 0 and int(self.invulnerable_time * 16) % 2:
            return                                   # blink after a hit
        surf.blit(self.image, self.topleft)
