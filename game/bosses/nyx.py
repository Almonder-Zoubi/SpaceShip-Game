"""Galaxy 2's herald: NYX, THE FIRST HERALD (G2 level 10, THE HOLLOW THRONE). A sleek black
ship with a white mask. It duels like a pilot: lead shots, and it side-steps shots you line
up on it. It learns (the bandit) and it talks.

In the COURT OF NYX (level 9) it only tests you: NyxCourt leaves at NYX_RETREAT of its hull.

Phases (the finale):
1 DUEL      -- lead-shot fans, twinned shots, dashes that leave splitters behind
2 RIFTS     -- rifts open round the screen (a ring first) and it fires through them, from
               behind and from the sides
3 ECLIPSE   -- the lights go out (the hazard's darkness); shadow rings
4 UNMAKING  -- the void closes in from the edges (the arena shrinks); patterns overlap
5 VANTA     -- VANTA speaks through it; runes and cages
"""
import math
import random

import pygame

from ..brains.insight import insights
from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, VEIL_GLOW
from ..config.tuning import NYX_RETREAT
from ..core.pixelart import CharCanvas
from ..minions.veil_bullets import (LeadShot, RuneMark, ShadowBullet, SplitterBullet, aimed,
                                    cage, twinned)
from ..story.dialog import NYX, VANTA, Line
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

HALF_W, H = 24, 40
COLORS = {"K": (0, 0, 0), "D": (22, 16, 30), "d": (44, 32, 60), "V": (110, 60, 170),
          "W": (236, 236, 240), "g": (160, 160, 172), "R": (220, 40, 60)}

TAUNTS = {                           # on each phase change (NYX, then VANTA at the end)
    1: "YOU FLY LIKE THE LAST SCOUT DID.",
    2: "LET'S SEE YOU WITHOUT YOUR LIGHT.",
    3: "THE VEIL IS CLOSING. SO ARE YOU.",
}
VANTA_WORDS = ("KEEP THE SHARD, LITTLE SCOUT.", "I WILL TAKE IT FROM YOUR LIGHT.")


def _half(phase):
    """A black dart; the mask is its cockpit, cracked more with every phase."""
    c = CharCanvas(HALF_W, H)
    c.poly([(23, 39), (18, 30), (4, 12), (1, 2), (8, 6), (16, 10), (23, 12)], "D")
    c.poly([(23, 35), (18, 28), (8, 12), (6, 6), (16, 12), (23, 14)], "d")
    c.line(2, 3, 12, 18, "V")                                   # violet edge on the wing
    c.circle(23, 22, 6, "W")                                    # the mask
    c.rect(19, 21, 21, 22, "K")                                 # an eye slit
    c.set(22, 26, "g")
    if phase >= 2:
        c.line(20, 17, 23, 20, "K")                             # cracks
    if phase >= 4:
        c.rect(20, 21, 21, 22, "R")                             # something else looks out
    return c.rows()


class Nyx(Learner, Boss):
    EPITHET = "THE FIRST HERALD"
    PHASES = 5
    RETREAT = None                   # share of hull where it leaves (NyxCourt)
    RAGE = (1.0, 1.1, 1.2, 1.3, 1.45)
    OPTIONS = (("fans", "twins", "dash"),
               ("rifts", "fans", "twins"),
               ("shadow", "rifts", "fans"),
               ("fans", "shadow", "rifts", "runes"),
               ("runes", "cage", "rifts", "fans"))
    SLOT, REST = 3.0, 0.7
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.75, 125, 0.2
    TWIN_INTERVAL, TWIN_SPEED = 0.6, 95
    PORTAL_INTERVAL, PORTAL_WARN = 0.7, 0.6
    SHADOW_INTERVAL, SHADOW_SHOTS = 1.0, 12
    RUNE_INTERVAL = 0.55
    DODGE_COOLDOWN = 0.9
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 1.1
    LEAVE_TIME = 1.6

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(5)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {}, [(10, 2), (38, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 34 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.goal_x = LOW_W / 2
        self.dodge = 0.0
        self.portals = []                # [x, y, seconds until it fires, life]
        self.said = set()
        self._pending_taunt = None       # a phase whose taunt is still to be said
        self.greeted = False

    # --- what the finale's hazard asks for --------------------------------------------
    @property
    def wants_dark(self):
        return self.phase == 2 and self.state == "fight"

    @property
    def unmaking(self):
        return self.phase >= 3 and self.state == "fight"

    # --- phases, taunts, retreat ------------------------------------------------------
    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.6
        self.portals = []

    def damage(self, amount, flash=True):
        phase = self.phase
        super().damage(amount, flash)
        if self.RETREAT and self.state == "fight" and self.hp <= self.max_hp * self.RETREAT:
            self._set_state("leaving")
        if self.phase != phase:
            self._pending_taunt = self.phase

    def _taunt(self, world):
        phase = self._pending_taunt
        if phase is None or phase in self.said:
            return
        self._pending_taunt = None
        self.said.add(phase)
        if phase == 4:
            world.radio_say([Line(VANTA, t) for t in VANTA_WORDS], delay=0)
            world.audio.play("hijack")
        elif phase in TAUNTS:
            world.radio_say([Line(NYX, TAUNTS[phase])], delay=0)

    def update(self, dt, world):
        if self.state == "leaving":                           # NyxCourt: it retreats
            self.state_time += dt
            self.flash = 0.0
            self.y -= (60 + self.state_time * 160) * dt
            if random.random() < 20 * dt:
                world.fire.burst(self.x, self.y + self.h / 2, 4, 60, 0.4, VEIL_GLOW, size=(1, 1))
            if self.state_time >= self.LEAVE_TIME:
                self._set_state("dead")
                return "escaped"
            return None
        return super().update(dt, world)

    # --- fight ---------------------------------------------------------------------------
    def _greet(self, world):
        """Its first words: what the enemy learned about you (brains/insight.py)."""
        self.greeted = True
        model = getattr(world, "player_model", None)
        seen = insights(model)[0] if model is not None else "I HAVE WATCHED YOU."
        world.radio_say([Line(NYX, "SO YOU ARE THE NEW ONE."), Line(NYX, seen)], delay=0)

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        if not self.greeted:
            self._greet(world)
        self.move_time += dt * rate
        self.learn_tick(dt)
        self._taunt(world)
        self._dodge(dt, world)
        self._portals(dt, world)
        self.x += (self.goal_x - self.x) * min(1.0, 3.5 * dt)
        self.y = self.home_y + math.sin(self.move_time * 1.1) * 6
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer = 0.0, 0.3
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                world.telegraph()
                if self.attack == "cage":
                    cage(world, self.bullet_damage * 0.8)
                    world.audio.play("warning")
            else:
                self.attack = "rest"
                self.goal_x = LOW_W / 2 + random.uniform(-90, 90)
            return
        if self.attack in ("rest", "cage"):
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)
            if self.phase == 3 and self.attack == "fans":         # UNMAKING: patterns overlap
                self._twins(world)
                self.fire_timer = self.FAN_INTERVAL

    def _dodge(self, dt, world):
        """Like a WISP: when the rocket lines up under it, it steps aside."""
        self.dodge -= dt
        ship = world.ship
        if self.dodge <= 0 and ship.alive and ship.y > self.y and abs(ship.x - self.x) < 10:
            self.dodge = self.DODGE_COOLDOWN
            side = 1 if self.x < LOW_W / 2 else -1
            if random.random() < 0.35:
                side = -side
            self.goal_x = min(LOW_W - 30, max(30, self.x + side * random.uniform(40, 70)))

    def _portals(self, dt, world):
        for p in self.portals:
            p[2] -= dt
            p[3] -= dt
            if p[2] <= 0 < p[2] + dt:                         # it fires through the rift
                aim = self.lead_aim(world, p[0], p[1], 110)
                world.enemy_bullets.append(aimed(LeadShot, p[0], p[1], aim, 110, self.bullet_damage))
        self.portals = [p for p in self.portals if p[3] > 0]

    # --- attacks ------------------------------------------------------------------------
    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 10, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _twins(self, world):
        self.fire_timer = self.TWIN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.TWIN_SPEED)
        world.enemy_bullets += twinned(self.x, self.y + 10, aim, self.TWIN_SPEED,
                                       self.bullet_damage * 0.6)

    def _dash(self, world):
        """It flashes across the screen and leaves splitters where it was."""
        self.fire_timer = 1.1
        old = self.x
        self.goal_x = LOW_W - 40 if self.x < LOW_W / 2 else 40
        self.x += (self.goal_x - self.x) * 0.5
        for k in range(3):
            x = old + (self.x - old) * k / 2
            world.enemy_bullets.append(SplitterBullet(x, self.y + 6, 0, 70, self.bullet_damage * 0.7))
        world.audio.play("teleport")

    def _rifts(self, world):
        self.fire_timer = self.PORTAL_INTERVAL
        ship = world.aim_target()
        side = random.choice(("left", "right", "below"))
        if side == "below":
            x, y = min(LOW_W - 16, max(16, ship.x + random.uniform(-60, 60))), LOW_H - 12
        else:
            x = 12 if side == "left" else LOW_W - 12
            y = min(LOW_H - 20, max(60, ship.y + random.uniform(-40, 40)))
        self.portals.append([x, y, self.PORTAL_WARN, self.PORTAL_WARN + 0.4])

    def _shadow(self, world):
        self.fire_timer = self.SHADOW_INTERVAL
        off = random.uniform(0, math.tau)
        for i in range(self.SHADOW_SHOTS):
            a = off + math.tau * i / self.SHADOW_SHOTS
            world.enemy_bullets.append(ShadowBullet(self.x, self.y, math.cos(a) * 70,
                                                    math.sin(a) * 70, self.bullet_damage * 0.8))

    def _runes(self, world):
        self.fire_timer = self.RUNE_INTERVAL
        ship = world.aim_target()
        a = random.uniform(0, math.tau)
        x = min(LOW_W - 10, max(10, ship.x + math.cos(a) * 34))
        y = min(LOW_H - 10, max(70, ship.y + math.sin(a) * 34))
        world.enemy_bullets.append(RuneMark(x, y, self.bullet_damage * 0.7))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        for x, y, warn, life in self.portals:                     # rifts round the screen
            r = 7 + int(3 * math.sin(life * 20))
            color = DANGER if warn > 0 and int(warn * 14) % 2 else VEIL_GLOW[1]
            pygame.draw.ellipse(surf, color, (int(x) - 4, int(y) - r, 8, r * 2), 1)
        super().draw(surf)

    def draw_rim(self, surf):
        """In the dark only its mask shows (hazards/darkness.py)."""
        x, y = self.point(HALF_W - 1, 23)
        pygame.draw.circle(surf, COLORS["W"], (int(x), int(y)), 5, 1)
        surf.fill(COLORS["R"] if self.phase >= 4 else COLORS["K"], (int(x) - 3, int(y) - 1, 2, 1))
        surf.fill(COLORS["R"] if self.phase >= 4 else COLORS["K"], (int(x) + 2, int(y) - 1, 2, 1))


class NyxCourt(Nyx):
    """The COURT OF NYX: it tests you, then leaves at NYX_RETREAT of its hull."""
    RETREAT = NYX_RETREAT
    EPITHET = "IT IS TESTING YOU"
