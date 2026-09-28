"""The Veil's bullet types (galaxy 2). Every one shows what it will do before it does it.

SplitterBullet -- swells, then bursts into three (its children come out of burst())
Boomerang      -- flies out, stops, comes back along the same line
RuneMark       -- a marker on the field (harmless); it blooms into a ring of bullets
LeadShot       -- aimed where you will be; a thin line shows its heading at first
ShadowBullet   -- a dark core with a bright rim (for the dark levels)
TwinBullet     -- two bullets orbiting a shared centre as they travel

World contract: a bullet may have `burst()` returning new bullets once (the world swaps them
in), and `solid = False` means it can't hurt (rune marks).
"""
import math

import pygame

from ..config.palette import DANGER, ENEMY_SHOT, VEIL_GLOW
from ..config.tuning import BOOMERANG_TIME, RUNE_SHOTS, RUNE_TIME, SPLIT_TIME
from .bullets import EnemyBullet


class VeilBullet(EnemyBullet):
    """Base: an age, a violet look, an optional burst."""
    __slots__ = ("age", "done")
    solid = True

    def __init__(self, x, y, vx, vy, damage):
        super().__init__(x, y, vx, vy, damage)
        self.age = 0.0
        self.done = False                 # burst already happened (the world drops it)

    def update(self, dt):
        self.age += dt
        super().update(dt)

    def burst(self):
        return None

    @property
    def offscreen(self):
        return self.done or super().offscreen

    def draw(self, surf, blink):
        x, y = int(self.x), int(self.y)
        add = pygame.BLEND_ADD
        surf.fill(VEIL_GLOW[3], (x - 2, y - 1, 5, 3), special_flags=add)
        surf.fill(VEIL_GLOW[3], (x - 1, y - 2, 3, 5), special_flags=add)
        surf.fill(VEIL_GLOW[2 if blink else 1], (x - 1, y - 1, 3, 3), special_flags=add)
        surf.fill(VEIL_GLOW[0], (x, y, 1, 1), special_flags=add)


class SplitterBullet(VeilBullet):
    __slots__ = ()
    SPREAD = 0.5

    def burst(self):
        if self.age < SPLIT_TIME or self.done:
            return None
        self.done = True
        speed = math.hypot(self.vx, self.vy) * 1.1
        heading = math.atan2(self.vy, self.vx)
        return [VeilBullet(self.x, self.y, math.cos(a) * speed, math.sin(a) * speed, self.damage)
                for a in (heading - self.SPREAD, heading, heading + self.SPREAD)]

    def draw(self, surf, blink):
        k = min(1.0, self.age / SPLIT_TIME)
        r = 2 + int(k * 3)
        if k > 0.6 and blink:                               # about to split
            pygame.draw.circle(surf, DANGER, (int(self.x), int(self.y)), r + 2, 1)
        pygame.draw.circle(surf, VEIL_GLOW[2], (int(self.x), int(self.y)), r)
        pygame.draw.circle(surf, VEIL_GLOW[0], (int(self.x), int(self.y)), max(1, r - 2))


class Boomerang(VeilBullet):
    """Decelerates to a stop at half its time, then comes back the way it came."""
    __slots__ = ("ax", "ay")

    def __init__(self, x, y, vx, vy, damage):
        super().__init__(x, y, vx, vy, damage)
        self.ax, self.ay = -2 * vx / BOOMERANG_TIME, -2 * vy / BOOMERANG_TIME

    def update(self, dt):
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        super().update(dt)

    def draw(self, surf, blink):
        a = self.age * 14
        for i in range(2):
            dx, dy = math.cos(a + i * math.pi) * 3, math.sin(a + i * math.pi) * 3
            surf.fill(VEIL_GLOW[1], (int(self.x + dx), int(self.y + dy), 2, 2),
                      special_flags=pygame.BLEND_ADD)
        surf.fill(VEIL_GLOW[0], (int(self.x), int(self.y), 1, 1), special_flags=pygame.BLEND_ADD)


class RuneMark(VeilBullet):
    """Harmless mark: a closing circle, then RUNE_SHOTS bullets bloom out of it."""
    __slots__ = ("speed",)
    solid = False

    def __init__(self, x, y, damage, speed=70):
        super().__init__(x, y, 0.0, 0.0, damage)
        self.speed = speed

    def burst(self):
        if self.age < RUNE_TIME or self.done:
            return None
        self.done = True
        off = self.age * 3
        return [VeilBullet(self.x, self.y, math.cos(off + math.tau * i / RUNE_SHOTS) * self.speed,
                           math.sin(off + math.tau * i / RUNE_SHOTS) * self.speed, self.damage)
                for i in range(RUNE_SHOTS)]

    def draw(self, surf, blink):
        k = min(1.0, self.age / RUNE_TIME)
        x, y = int(self.x), int(self.y)
        r = int(16 - 12 * k)
        pygame.draw.circle(surf, VEIL_GLOW[2] if blink else VEIL_GLOW[3], (x, y), max(2, r), 1)
        for i in range(4):                                  # the rune's spokes
            a = i * math.pi / 2 + k * 2
            surf.fill(VEIL_GLOW[1], (x + int(math.cos(a) * 4), y + int(math.sin(a) * 4), 1, 1))


class LeadShot(VeilBullet):
    """Aimed at where you will be: a thin line shows where it is heading for its first
    moments (so a sharp player can turn away)."""
    __slots__ = ()
    SHOW = 0.35

    def draw(self, surf, blink):
        if self.age < self.SHOW:
            ex, ey = self.x + self.vx * 0.6, self.y + self.vy * 0.6
            pygame.draw.line(surf, (90, 50, 120), (int(self.x), int(self.y)), (int(ex), int(ey)))
        super().draw(surf, blink)


class ShadowBullet(VeilBullet):
    """Dark core, bright rim: reads on a dark screen and on a bright one."""
    __slots__ = ()

    def draw(self, surf, blink):
        x, y = int(self.x), int(self.y)
        pygame.draw.circle(surf, VEIL_GLOW[1] if blink else VEIL_GLOW[2], (x, y), 3, 1)
        surf.fill((0, 0, 0), (x - 1, y - 1, 3, 3))


class TwinBullet(VeilBullet):
    """One of a pair orbiting a centre that travels in a line."""
    __slots__ = ("cx", "cy", "phase")
    RADIUS, SPIN = 7, 6.0

    def __init__(self, x, y, vx, vy, damage, phase):
        super().__init__(x, y, vx, vy, damage)
        self.cx, self.cy, self.phase = x, y, phase

    def update(self, dt):
        self.age += dt
        self.cx += self.vx * dt
        self.cy += self.vy * dt
        a = self.phase + self.age * self.SPIN
        self.x = self.cx + math.cos(a) * self.RADIUS
        self.y = self.cy + math.sin(a) * self.RADIUS

    def draw(self, surf, blink):
        x, y = int(self.x), int(self.y)
        surf.fill(ENEMY_SHOT[2], (x - 1, y - 1, 3, 3), special_flags=pygame.BLEND_ADD)
        surf.fill(VEIL_GLOW[0], (x, y, 1, 1), special_flags=pygame.BLEND_ADD)


def twinned(x, y, angle, speed, damage):
    vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
    return [TwinBullet(x, y, vx, vy, damage, 0.0), TwinBullet(x, y, vx, vy, damage, math.pi)]


def cage(world, damage, gaps=None, speed=None, gap=None, top=34):
    """CAGE: two walls of bullets slide in from the left and right edges; each wall has one
    gap (a height where it is safe). gaps: (left wall gap y, right wall gap y)."""
    from ..config.display import LOW_H, LOW_W
    from ..config.tuning import CAGE_GAP, CAGE_SPEED
    import random
    speed = speed or CAGE_SPEED
    gap = gap or CAGE_GAP
    gaps = gaps or (random.uniform(top + 20, LOW_H - 40), random.uniform(top + 20, LOW_H - 40))
    for side, gy in zip((-1, 1), gaps):
        x = 2 if side < 0 else LOW_W - 2
        for y in range(top, LOW_H, 9):
            if not gy - gap / 2 < y < gy + gap / 2:
                world.enemy_bullets.append(VeilBullet(x, y, -side * speed, 0, damage))


def aimed(cls, x, y, angle, speed, damage):
    return cls(x, y, math.cos(angle) * speed, math.sin(angle) * speed, damage)
