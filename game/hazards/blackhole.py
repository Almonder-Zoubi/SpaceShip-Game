"""The black hole (level 9): a gravity well that drifts across the top third of the screen.

It pulls everything — rocks, minions, pickups, enemy bullets, the player's shots and the
ship (an extra velocity on top of the direct controls, capped so thrust always escapes).
The core (event horizon) hurts a lot; the SLINGSHOT ring around it pays x3 score and coins,
x2 BLAST / ULT charge, and gun shots through it come out faster and +50%. Every
WHITE_HOLE_EVERY seconds it flips into a WHITE HOLE and pushes everything out.
"""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER, SPARK
from ..config.tuning import (BH_CORE, BH_CORE_DAMAGE, BH_PULL, BH_RANGE, BH_RING, BH_SHIP_PULL,
                             BH_SHIP_PULL_MAX, WHITE_HOLE_EVERY, WHITE_HOLE_TIME,
                             WHITE_HOLE_WARN)
from ..core.particles import Shockwave
from ..minions.bullets import bullet
from ..ui.popup import Popup
from .base import Hazard

DISC = [(120, 60, 160), (200, 90, 120), (255, 160, 90), (255, 230, 170)]
WHITE_DISC = [(200, 220, 255), (230, 240, 255), (255, 255, 255), (255, 255, 255)]


class BlackHole(Hazard):
    def __init__(self):
        self.x, self.y = LOW_W / 2, 72.0
        self.time = 0.0
        self.grow = 1.0                  # THE TWINS make it bigger in their last phase
        self.flip_timer = WHITE_HOLE_EVERY
        self.white = 0.0                 # seconds of WHITE HOLE left
        self.warning = False
        self.ship_in_ring = False
        self.stored = 0                  # bullets swallowed (they come back out on a flip)
        self.disc = [(random.uniform(0, math.tau), random.uniform(14, 34), random.randint(0, 3))
                     for _ in range(70)]

    # --- geometry ------------------------------------------------------------------------
    @property
    def core(self):
        return BH_CORE * self.grow

    @property
    def ring(self):
        return BH_RING[0] * self.grow, BH_RING[1] * self.grow

    def pull_at(self, x, y):
        """(ax, ay) acceleration towards the core (away from it as a WHITE HOLE)."""
        dx, dy = self.x - x, self.y - y
        d = math.hypot(dx, dy) or 1.0
        if d > BH_RANGE * self.grow:
            return 0.0, 0.0
        k = (1 - d / (BH_RANGE * self.grow)) ** 1.5 * BH_PULL * self.grow
        if self.white > 0:
            k *= -2.0
        return dx / d * k, dy / d * k

    def in_ring(self, x, y):
        lo, hi = self.ring
        return lo <= math.hypot(x - self.x, y - self.y) <= hi

    # --- per frame -----------------------------------------------------------------------
    def update(self, dt, game):
        self.time += dt
        self.x = LOW_W / 2 + math.sin(self.time * 0.12) * (LOW_W / 2 - 70)
        self.y = 70 + math.sin(self.time * 0.3) * 8
        self._flip(dt, game)
        for rock in list(game.asteroids):
            ax, ay = self.pull_at(rock.x, rock.y)
            rock.vx += ax * dt
            rock.vy += ay * dt
            if math.hypot(rock.x - self.x, rock.y - self.y) < self.core + rock.radius * 0.5:
                self._spaghettify(game, rock)
        for enemy in game.enemies:
            ax, ay = self.pull_at(enemy.x, enemy.y)
            enemy.x += ax * 0.25 * dt
            enemy.y += ay * 0.25 * dt
        for b in list(game.enemy_bullets):
            ax, ay = self.pull_at(b.x, b.y)
            b.vx += ax * dt
            b.vy += ay * dt
            if math.hypot(b.x - self.x, b.y - self.y) < self.core and self.white <= 0:
                game.enemy_bullets.remove(b)          # swallowed: it comes back on a flip
                self.stored += 1
        for pickup in game.pickups:
            ax, ay = self.pull_at(pickup.x, pickup.y)
            pickup.x += ax * 0.2 * dt
            pickup.y += ay * 0.2 * dt
        self._pull_shots(dt, game)
        self._pull_ship(dt, game)

    def _pull_shots(self, dt, game):
        """The player's projectiles curve around it; gun shots through the ring gain power."""
        weapons = {w.name: w for w in game.weapons}
        for b in weapons["GUN"].bullets:
            ax, ay = self.pull_at(b.x, b.y)
            b.vx += ax * dt
            b.vy += ay * dt
            if not b.boost and self.in_ring(b.x, b.y):
                b.boost = True
                b.vx *= 1.3
                b.vy *= 1.3
        for p in weapons["SCATTER"].pellets:
            ax, ay = self.pull_at(p[0], p[1])
            p[2] += ax * dt
            p[3] += ay * dt
        for o in weapons["PLASMA"].orbs:
            ax, ay = self.pull_at(o.x, o.y)
            o.vx += ax * dt
            o.vy += ay * dt

    def _pull_ship(self, dt, game):
        ship = game.ship
        self.ship_in_ring = ship.alive and self.in_ring(ship.x, ship.y)
        if not ship.alive:
            return
        dx, dy = self.x - ship.x, self.y - ship.y
        d = math.hypot(dx, dy) or 1.0
        if d < BH_RANGE * self.grow:
            k = (1 - d / (BH_RANGE * self.grow)) ** 1.5 * BH_SHIP_PULL * self.grow
            k = min(k, BH_SHIP_PULL_MAX * ship.max_speed)
            if self.white > 0:
                k *= -1.5
            ship.x += dx / d * k * dt
            ship.y += dy / d * k * dt
            ship._keep_on_screen()
        if d < self.core + 4 and self.white <= 0:     # the event horizon
            game.hurt_ship(ship.max_hp * BH_CORE_DAMAGE, self.x, self.y)
        if self.ship_in_ring and random.random() < 30 * dt:       # blue-shifted speed lines
            a = math.atan2(dy, dx) + math.pi / 2
            game.fire.emit(ship.x, ship.y, math.cos(a) * 120, math.sin(a) * 120, 0.15,
                           [(255, 255, 255), (150, 200, 255), (80, 120, 255)])

    def _spaghettify(self, game, rock):
        """A rock falls in: it stretches into a stream of shards that orbit once, then fly."""
        game.asteroids.remove(rock)
        colors = rock.art.palette[:0:-1]
        for i in range(10 + rock.radius):
            a = random.uniform(0, math.tau)
            speed = random.uniform(40, 110)
            game.smoke.emit(self.x + math.cos(a) * self.core, self.y + math.sin(a) * self.core,
                            -math.sin(a) * speed, math.cos(a) * speed, random.uniform(0.5, 1.2),
                            colors, size=1, drag=0.4)

    def _flip(self, dt, game):
        """Every WHITE_HOLE_EVERY seconds: 2 s warning, then 3 s of pushing everything out."""
        if self.white > 0:
            self.white = max(0.0, self.white - dt)
            return
        self.flip_timer -= dt
        self.warning = 0 < self.flip_timer <= WHITE_HOLE_WARN
        if self.flip_timer <= 0:
            self.flip_timer = WHITE_HOLE_EVERY
            self.white = WHITE_HOLE_TIME
            self.warning = False
            game.shockwaves.append(Shockwave(self.x, self.y, max_radius=220, duration=1.0,
                                             color=(220, 230, 255)))
            game.screen_flash(0.12)
            game.shake.add(0.5)
            game.audio.play("white_hole")
            game.popups.append(Popup("WHITE HOLE!", self.x, self.y + 30, (220, 230, 255)))
            self._release(game)

    def _release(self, game):
        """Swallowed bullets come back out as a ring."""
        count = min(24, self.stored)
        if count:
            damage = 8 + game.level.number
            for i in range(count):
                a = math.tau * i / count
                game.enemy_bullets.append(bullet(self.x, self.y, a, 70, damage))
        self.stored = 0

    # --- draw ----------------------------------------------------------------------------
    def draw_back(self, surf):
        """Lensing rings, the accretion disc and the core."""
        cx, cy = int(self.x), int(self.y)
        white = self.white > 0 or (self.warning and int(self.time * 8) % 2 == 0)
        disc = WHITE_DISC if white else DISC
        for i, r in enumerate((70, 54, 44)):                 # lensing: faint rings
            shade = 18 - i * 4
            pygame.draw.circle(surf, (shade, shade, shade + 10), (cx, cy), int(r * self.grow), 1)
        lo, hi = self.ring
        pygame.draw.circle(surf, (40, 60, 110), (cx, cy), int(hi), 1)       # SLINGSHOT ring
        pygame.draw.circle(surf, (30, 40, 90), (cx, cy), int(lo), 1)
        for angle, radius, tone in self.disc:                # the disc turns
            a = angle + self.time * (3.0 - radius * 0.05)
            r = radius * self.grow
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.35
            surf.fill(disc[tone], (int(x), int(y), 1, 1), special_flags=pygame.BLEND_ADD)
        core = int(self.core)
        pygame.draw.circle(surf, (255, 255, 255) if self.white > 0 else (0, 0, 0), (cx, cy), core)
        pygame.draw.circle(surf, disc[2], (cx, cy), core + 1, 1)

    def draw_front(self, surf):
        if self.warning and int(self.time * 6) % 2 == 0:
            pygame.draw.circle(surf, DANGER, (int(self.x), int(self.y)), int(self.ring[1] + 6), 1)
        if self.ship_in_ring:
            pygame.draw.circle(surf, SPARK[1], (int(self.x), int(self.y)), int(self.ring[1]), 1)
