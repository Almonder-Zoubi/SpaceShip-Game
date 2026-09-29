"""HOLLOW LEADER squads (galaxy 2, LAST LIGHT): a leader with a crest flies in front, four
followers hold a V behind it and fire only on its order. Kill the leader and the squad
panics: it scatters and holds fire for SQUAD_PANIC seconds - then the leaderless ships dive
at whatever they were sent for (Vega's flagship in the siege, otherwise you)."""
import math
import random

from ..config.display import LOW_H, LOW_W
from ..config.palette import ELITE_GOLD
from ..config.tuning import (FOLLOWER_HP, LEADER_FIRE, LEADER_HP, POINTS_FOLLOWER, POINTS_LEADER,
                             SQUAD_PANIC, WISP_BULLET_DAMAGE)
from ..core.pixelart import sprite_from_rows
from ..ui.popup import Popup
from .base import Enemy
from .veil_bullets import LeadShot, VeilBullet, aimed

LEADER_ROWS = (
    "....G.G....",
    "...GKGKG...",
    "K..KHHHK..K",
    "KK.KHWHK.KK",
    ".KKHHHHHKK.",
    "..KHRHRHK..",
    "...KHHHK...",
    "....KHK....",
    ".....K.....",
)
FOLLOWER_ROWS = (
    "K.....K",
    "KK...KK",
    ".KHHHK.",
    ".KHRHK.",
    "..KHK..",
    "...K...",
)
COLORS = {"K": (10, 6, 16), "H": (70, 60, 96), "W": (200, 190, 230), "R": (230, 60, 80),
          "G": (255, 204, 64)}
V_SLOTS = ((-16, -10), (16, -10), (-30, -20), (30, -20))


class Squad:
    """What the squad shares: its leader, the panic timer, its target."""

    def __init__(self):
        self.leader = None
        self.panic_until = 0.0           # game time until which the squad panics
        self.orphaned = False            # the leader is dead (after the panic: dive)
        self.volley = False              # the leader's order this frame


def target_of(world):
    """What the squad was sent for: the flagship in a siege, else the rocket."""
    flagship = getattr(world.hazard, "flagship", None)
    if flagship is not None and flagship.alive:
        return flagship.x + random.uniform(-60, 60), flagship.y
    target = world.aim_target()
    return target.x, target.y


class Leader(Enemy):
    points = POINTS_LEADER
    contact_damage = 24
    _image = None

    def __init__(self, x, squad):
        if Leader._image is None:
            Leader._image = sprite_from_rows(LEADER_ROWS, COLORS)
        super().__init__(Leader._image, x, -10, LEADER_HP)
        self.squad = squad
        squad.leader = self
        self.order = random.uniform(1.0, LEADER_FIRE)
        self.side = random.choice((-1, 1))

    @property
    def offscreen(self):
        return self.time > 30 or super().offscreen

    def move(self, dt, world):
        self.y += (40 if self.y < 64 else 0) * dt
        self.x += self.side * 34 * dt
        if not 50 < self.x < LOW_W - 50:
            self.side = -self.side
        if self.time > 24:                                 # its time is up: it leaves
            self.y -= 70 * dt

    def attack(self, dt, world):
        self.order -= dt
        self.squad.volley = False
        if self.order <= 0:
            self.order = LEADER_FIRE * random.uniform(0.85, 1.15)
            self.squad.volley = True                       # the followers fire this frame
            tx, ty = target_of(world)
            aim = math.atan2(ty - self.y, tx - self.x)
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 6, aim, 115,
                                             WISP_BULLET_DAMAGE * 1.3))

    def on_death(self, world, scored):
        self.squad.panic_until = world.time + SQUAD_PANIC
        self.squad.orphaned = True
        self.squad.leader = None
        if scored:
            world.popups.append(Popup("LEADER DOWN!", self.x, self.y - 10, ELITE_GOLD[0]))


class Follower(Enemy):
    points = POINTS_FOLLOWER
    contact_damage = 14
    _image = None

    def __init__(self, x, squad, slot):
        if Follower._image is None:
            Follower._image = sprite_from_rows(FOLLOWER_ROWS, COLORS)
        super().__init__(Follower._image, x, -30, FOLLOWER_HP)
        self.squad, self.slot = squad, slot
        self.vx = self.vy = 0.0
        self.diving = False

    @property
    def offscreen(self):
        return self.time > 34 or self.y > LOW_H + 10 or not -30 < self.x < LOW_W + 30

    def move(self, dt, world):
        squad = self.squad
        if world.time < squad.panic_until:                  # scatter
            if abs(self.vx) < 1:
                self.vx, self.vy = random.uniform(-90, 90), random.uniform(-40, 20)
            self.x += self.vx * dt
            self.y = max(10.0, self.y + self.vy * dt)
            return
        if squad.orphaned or self.diving:                   # nobody left to follow: dive
            if not self.diving:
                self.diving = True
                tx, ty = target_of(world)
                d = math.hypot(tx - self.x, ty - self.y) or 1
                self.vx, self.vy = (tx - self.x) / d * 130, (ty - self.y) / d * 130
            self.x += self.vx * dt
            self.y += self.vy * dt
            return
        leader = squad.leader
        dx, dy = V_SLOTS[self.slot]
        self.x += (leader.x + dx - self.x) * min(1.0, 4 * dt)
        self.y += (leader.y + dy - self.y) * min(1.0, 4 * dt)

    def attack(self, dt, world):
        squad = self.squad
        if squad.volley and not squad.orphaned:
            tx, ty = target_of(world)
            a = math.atan2(ty - self.y, tx - self.x) + random.uniform(-0.08, 0.08)
            world.enemy_bullets.append(VeilBullet(self.x, self.y + 3, math.cos(a) * 100,
                                                  math.sin(a) * 100, WISP_BULLET_DAMAGE * 0.8))


def leader_squad(game):
    squad = Squad()
    x = random.uniform(70, LOW_W - 70)
    leader = Leader(x, squad)
    return [leader] + [Follower(x + V_SLOTS[i][0], squad, i) for i in range(4)]
