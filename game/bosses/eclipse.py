"""Galaxy 2 boss 4: ECLIPSE (G2 level 4, THE DARK VEIL). A black disc you only see by its
corona. It puts your light out, and its one bright weapon is a sweeping beam of light that
burns - in this level, light is the danger. A learning boss."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER
from ..core.pixelart import CharCanvas
from ..minions.lurker import lurker_pair
from ..minions.veil_bullets import ShadowBullet, aimed
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

R = 26
COLORS = {"K": (2, 2, 6), "D": (14, 12, 24), "d": (24, 20, 40), "E": (180, 40, 60),
          "e": (90, 20, 40)}
CORONA = [(255, 250, 230), (255, 220, 140), (255, 160, 80), (200, 90, 60)]


def _half(phase):
    c = CharCanvas(R + 1, R * 2 + 1)
    c.circle(R, R, R, "D")
    c.circle(R, R, R - 3, "K")
    for cx, cy, r in ((14, 14, 4), (9, 30, 3), (18, 40, 2)):     # faint craters
        c.circle(cx, cy, r, "d")
    if phase >= 1:
        c.circle(R, R + 4, 2 + phase, "e")                     # an eye opens in the dark
        c.circle(R, R + 4, 1 + phase // 2, "E")
    return c.rows()


class Eclipse(Learner, Boss):
    """Galaxy 2, level 4. Four phases; attacks chosen by the bandit.

    EXTINGUISH -- the corona flickers, then the rocket's light shrinks for a while
    SHADOWRING -- rings of shadow bullets (dark cores, bright rims)
    FANS       -- lead-shot fans of shadow bullets
    CORONA     -- (phase 2+) a beam of light sweeps the screen from the disc; it burns
    LURKERS    -- (phase 3+) it calls two lurkers out of the dark
    """

    EPITHET = "THE LIGHT THAT BURNS"
    PHASES = 4
    RAGE = (1.0, 1.15, 1.3, 1.45)
    OPTIONS = (("extinguish", "shadowring", "fans"),
               ("extinguish", "shadowring", "fans", "corona"),
               ("shadowring", "fans", "corona", "lurkers"),
               ("extinguish", "shadowring", "fans", "corona", "lurkers"))
    SLOT, REST = 3.2, 0.8
    RING_INTERVAL, RING_SHOTS, RING_SPEED = 0.95, 12, 70
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.8, 115, 0.22
    DIM_TIME = 3.5
    BEAM_WARN, BEAM_TURN, BEAM_X = 0.8, 0.9, 0.12
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 0.9

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(4)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {}, [(R, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 34 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.beam_angle = math.pi / 2
        self.beam_dir = 1

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.6

    # --- light: what the Darkness hazard asks for ----------------------------------------
    def light(self):
        """The beam lights the dark along its line (hazards/darkness.py)."""
        if self.state != "fight" or self.attack != "corona" or self.attack_time < self.BEAM_WARN:
            return []
        return [(self.x + math.cos(self.beam_angle) * d, self.y + math.sin(self.beam_angle) * d, 18)
                for d in range(30, 300, 26)]

    def beam_end(self):
        return (self.x + math.cos(self.beam_angle) * 320, self.y + math.sin(self.beam_angle) * 320)

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.learn_tick(dt)
        slow = 0.3 if self.attack == "corona" else 1.0
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.4 * slow) * 100
        self.y = self.home_y + math.sin(self.move_time * 0.9) * 6
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer = 0.0, 0.3
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                world.telegraph()
                if self.attack == "corona":
                    target = world.aim_target()
                    self.beam_angle = math.atan2(target.y - self.y, target.x - self.x) - 0.9
                    self.beam_dir = 1
            else:
                self.attack = "rest"
            return
        if self.attack == "extinguish":
            if self.attack_time >= 0.8 and getattr(world.hazard, "dim", None) is not None:
                if world.hazard.dim <= 0:
                    world.audio.play("teleport")
                world.hazard.dim = max(world.hazard.dim, self.DIM_TIME)
            self._rings_timer(dt, world, rate)
            return
        if self.attack == "corona":
            self._corona(dt, world, rate)
            return
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    def _rings_timer(self, dt, world, rate):
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            self._shadowring(world)
            self.fire_timer = self.RING_INTERVAL * 1.4

    # --- attacks ------------------------------------------------------------------------
    def _shadowring(self, world):
        self.fire_timer = self.RING_INTERVAL
        off = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            a = off + math.tau * i / self.RING_SHOTS
            world.enemy_bullets.append(ShadowBullet(self.x, self.y, math.cos(a) * self.RING_SPEED,
                                                    math.sin(a) * self.RING_SPEED, self.bullet_damage))

    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(ShadowBullet, self.x, self.y, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _lurkers(self, world):
        self.fire_timer = 99
        world.spawn_enemies(lurker_pair(world))

    def _corona(self, dt, world, rate):
        """The beam sweeps across; after its warning it burns what it touches."""
        self.beam_angle += self.BEAM_TURN * rate * dt * self.beam_dir
        if self.attack_time < self.BEAM_WARN:
            return
        if self.attack_time - dt < self.BEAM_WARN:
            world.audio.play("beam")
            world.shake.add(0.25)
        ship = world.ship
        if not ship.alive:
            return
        ex, ey = self.beam_end()
        vx, vy = ex - self.x, ey - self.y
        t = max(0.0, min(1.0, ((ship.x - self.x) * vx + (ship.y - self.y) * vy) / (vx * vx + vy * vy)))
        d = math.hypot(self.x + vx * t - ship.x, self.y + vy * t - ship.y)
        if d < 5 + ship.w * 0.3:
            world.hurt_ship(self.bullet_damage * self.BEAM_X, ship.x, ship.y)

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw_rim(self, surf):
        """The corona: always visible, even in the dark (flickers before EXTINGUISH)."""
        if self.state == "dead":
            return
        t = self.move_time
        warn = self.attack == "extinguish" and self.attack_time < 0.8 and self.state == "fight"
        for i in range(40):
            if warn and (i + int(t * 20)) % 3:
                continue
            a = i * math.tau / 40 + t * 0.3
            r = R + 1 + int(2 * math.sin(t * 5 + i * 1.7) + 2)
            color = CORONA[(i + int(t * 8)) % len(CORONA)]
            surf.fill(color, (int(self.x + math.cos(a) * r), int(self.y + math.sin(a) * r), 2, 2),
                      special_flags=pygame.BLEND_ADD)
        self._draw_beam(surf)

    def _draw_beam(self, surf):
        if self.state != "fight" or self.attack != "corona":
            return
        ex, ey = self.beam_end()
        start = (int(self.x), int(self.y))
        if self.attack_time < self.BEAM_WARN:
            if int(self.attack_time * 12) % 2 == 0:
                pygame.draw.line(surf, DANGER, start, (int(ex), int(ey)))
            return
        pygame.draw.line(surf, CORONA[2], start, (int(ex), int(ey)), 5)
        pygame.draw.line(surf, CORONA[0], start, (int(ex), int(ey)), 2)

    def draw(self, surf):
        super().draw(surf)
        self.draw_rim(surf)
