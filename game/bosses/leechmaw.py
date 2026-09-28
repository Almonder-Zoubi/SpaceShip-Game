"""Galaxy 2 boss 2: LEECH MAW, the reef's hunger (G2 level 2). It chased the rocket up the
reef; now it overtakes it from below and turns to fight. A learning boss."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, MAW_FLESH
from ..core.pixelart import CharCanvas
from ..minions.veil_bullets import LeadShot, SplitterBullet, VeilBullet, aimed
from ..obstacles.asteroid import BoneRock
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

HALF_W, H = 42, 58
MOUTH = (42, 50)                           # sprite pixel of the mouth (the gullet)
COLORS = {"K": (20, 8, 12), "B": (226, 206, 186), "b": (176, 140, 124), "d": (110, 70, 70),
          "G": MAW_FLESH[1], "g": MAW_FLESH[0], "T": (250, 244, 232), "E": (255, 70, 80),
          "e": (140, 20, 30), "W": (255, 255, 255)}


def _half(phase):
    """Left half: a bone carapace, gums, a ring of teeth round the mouth, red eyes."""
    c = CharCanvas(HALF_W, H)
    c.poly([(41, 0), (22, 3), (8, 12), (2, 26), (4, 40), (14, 52), (26, 57), (41, 57)], "b")
    c.poly([(41, 3), (24, 6), (12, 14), (7, 26), (9, 38), (17, 48), (28, 53), (41, 53)], "B")
    for y in (12, 20, 28, 36):                               # carapace ridges
        c.line(12 + (y % 3), y, 38, y - 2, "d")
    c.circle(41, 44, 14, "G")                                # the mouth: gums ...
    c.circle(41, 44, 10, "g")
    c.circle(41, 46, 6, "K")                                 # ... and the gullet
    for i in range(6):                                       # teeth round the mouth
        a = math.pi * (0.55 + i * 0.09)
        x, y = int(41 + math.cos(a) * 12), int(44 + math.sin(a) * 12)
        c.line(x, y, int(41 + math.cos(a) * 7), int(44 + math.sin(a) * 7), "T")
    eye = 3 + phase // 2
    c.circle(26, 22, eye + 1, "K")
    c.circle(26, 22, eye, "E")
    c.set(25, 21, "W")
    c.circle(33, 30, max(1, eye - 1), "e")
    if phase >= 2:                                           # cracked bone
        c.line(10, 20, 20, 30, "d")
        c.line(16, 40, 24, 34, "d")
    return c.rows()


class LeechMaw(Learner, Boss):
    """Galaxy 2, level 2. Four phases; attacks chosen by the bandit.

    SUCK   -- it pulls the rocket towards its mouth (thrust escapes) and spits tooth
              splitters
    TEETH  -- fans of lead shots
    SPIT   -- bone rocks thrown at the rocket (they regrow like reef bone)
    BITE   -- (phase 2+) a red column marks a spot, then it lunges down through it
    ROWS   -- (phase 3+) walls of bone shards with one gap fall down the screen
    """

    EPITHET = "THE REEF'S HUNGER"
    PHASES = 4
    RAGE = (1.0, 1.15, 1.3, 1.45)
    OPTIONS = (("suck", "teeth", "spit"),
               ("suck", "teeth", "spit", "bite"),
               ("teeth", "spit", "bite", "rows"),
               ("suck", "teeth", "bite", "rows", "spit"))
    ENTER_TIME = 2.8
    SLOT, REST = 3.0, 0.8
    TEETH_INTERVAL, TEETH_SPEED, TEETH_GAP = 0.85, 120, 0.2
    SUCK_PULL, SUCK_SPLIT = 55, 1.0
    SPIT_INTERVAL = 1.1
    BITE_WARN, BITE_SPEED, BITE_X = 0.9, 330, 3.0
    ROW_INTERVAL, ROW_SPEED, ROW_GAP = 1.3, 62, 52
    AIMED_RATE = 1 / TEETH_INTERVAL * SLOT / (SLOT + REST) + 0.8

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = [build_boss_sprite(_half(p), COLORS) for p in range(4)]
        return cls._sprites

    def __init__(self, spec):
        super().__init__(spec, list(self.prebuild()), {"mouth": MOUTH}, [(20, 4), (64, 4)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.home_y = 28 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.bite = 0                         # 0 none, 1 marking, 2 lunging, 3 back up
        self.bite_x = 0.0

    # --- movement -----------------------------------------------------------------------
    def enter(self, k):
        """It comes from BELOW: it swims up past the rocket to its place at the top."""
        start = LOW_H + self.h / 2 + 10
        self.y = start + (self.home_y - start) * (1 - (1 - k) ** 2)
        self.x = LOW_W / 2 + math.sin(k * math.pi * 2) * 40

    @property
    def contact_damage(self):
        return self.bullet_damage * self.BITE_X if self.bite == 2 else super().contact_damage

    def mouth(self):
        return self.point(*self.muzzles["mouth"])

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer, self.bite = "rest", 0.0, 0.6, 0

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.learn_tick(dt)
        if self.bite == 0:
            self.x += (LOW_W / 2 + math.sin(self.move_time * 0.4) * 90 - self.x) * min(1.0, 2 * dt)
            self.y += (self.home_y + math.sin(self.move_time) * 4 - self.y) * min(1.0, 3 * dt)
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length and self.bite not in (1, 2):
            self.attack_time, self.fire_timer, self.bite = 0.0, 0.3, 0
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                if self.attack == "bite":
                    world.telegraph()
            else:
                self.attack = "rest"
            return
        if self.attack == "suck":
            self._pull(dt, world, rate)
        elif self.attack == "bite":
            self._bite(dt, world)
            return
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    # --- attacks ------------------------------------------------------------------------
    def _pull(self, dt, world, rate):
        """The rocket is pulled towards the mouth (a capped pull: thrust always escapes)."""
        ship = world.ship
        mx, my = self.mouth()
        dx, dy = mx - ship.x, my - ship.y
        d = math.hypot(dx, dy) or 1.0
        ship.x += dx / d * self.SUCK_PULL * rate * dt
        ship.y += dy / d * self.SUCK_PULL * rate * dt
        if random.random() < 40 * dt:                           # streaks into the mouth
            a = random.uniform(0, math.tau)
            r = random.uniform(40, 90)
            world.fire.emit(mx + math.cos(a) * r, my + math.sin(a) * r, -math.cos(a) * r * 2,
                            -math.sin(a) * r * 2, 0.4, [(255, 230, 220), (200, 90, 90)], size=1)

    def _teeth(self, world):
        self.fire_timer = self.TEETH_INTERVAL
        mx, my = self.mouth()
        aim = self.lead_aim(world, mx, my, self.TEETH_SPEED)
        for i in range(-2, 3):
            world.enemy_bullets.append(aimed(LeadShot, mx, my, aim + i * self.TEETH_GAP,
                                             self.TEETH_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _spit(self, world):
        self.fire_timer = self.SPIT_INTERVAL
        mx, my = self.mouth()
        art = world.library.pick(6, 9, ("reef",))
        target = world.aim_target()
        a = math.atan2(target.y - my, target.x - mx)
        world.asteroids.append(BoneRock(art, mx, my + 6, math.cos(a) * 60, max(60, math.sin(a) * 120),
                                        random.uniform(-2, 2), world.level.difficulty.rock_hp))
        world.enemy_bullets.append(aimed(SplitterBullet, mx, my, a, 80, self.bullet_damage))

    def _suck(self, world):
        """While it sucks, tooth splitters fly out of the mouth."""
        self.fire_timer = self.SUCK_SPLIT
        mx, my = self.mouth()
        aim = self.lead_aim(world, mx, my, 85)
        world.enemy_bullets.append(aimed(SplitterBullet, mx, my, aim, 85, self.bullet_damage))

    def _bite(self, dt, world):
        """Mark a column (red), then lunge down it and come back."""
        ship = world.ship
        if self.bite == 0:
            self.bite, self.bite_x = 1, ship.x
            world.audio.play("lock_on")
        if self.bite == 1:
            if self.attack_time < self.BITE_WARN - 0.25:
                self.bite_x = ship.x
            self.x += (self.bite_x - self.x) * min(1.0, 4 * dt)
            if self.attack_time >= self.BITE_WARN:
                self.bite = 2
                world.shake.add(0.3)
                world.audio.play("dive")
        elif self.bite == 2:
            self.y += self.BITE_SPEED * dt
            if self.y >= LOW_H - self.h / 2 - 6:
                self.bite = 3
        elif self.bite == 3:
            self.y -= self.BITE_SPEED * 0.6 * dt
            if self.y <= self.home_y:
                self.y = self.home_y
                self.bite, self.attack, self.attack_time = 0, "rest", 0.0

    def _rows(self, world):
        """A wall of bone shards across the screen with one gap, falling."""
        self.fire_timer = self.ROW_INTERVAL
        gap = random.uniform(30, LOW_W - 30 - self.ROW_GAP)
        y = self.y + self.h / 2
        for x in range(4, LOW_W, 10):
            if not gap < x < gap + self.ROW_GAP:
                world.enemy_bullets.append(VeilBullet(x, y, 0, self.ROW_SPEED, self.bullet_damage))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        if self.state == "fight" and self.bite == 1 and int(self.attack_time * 12) % 2 == 0:
            x = int(self.bite_x)
            for y in range(int(self.y + self.h / 2), LOW_H, 4):
                surf.fill(DANGER, (x - 12, y, 1, 2))
                surf.fill(DANGER, (x + 12, y, 1, 2))
        super().draw(surf)
        if self.state == "fight" and self.attack == "suck":
            mx, my = self.mouth()
            r = 10 + int((self.move_time * 30) % 20)
            pygame.draw.circle(surf, (200, 90, 90), (int(mx), int(my)), r, 1)
