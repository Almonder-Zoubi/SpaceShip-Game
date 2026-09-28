"""Galaxy 2 boss 3: THE HOLLOW REAPER (G2 level 3). It came for the brood, not for you:
its scythe HARVESTS the pod unless you break the harvest by hitting the scythe."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W  # noqa: F401  (LOW_H: runes stay on screen)
from ..config.palette import DANGER, HEAL, VEIL_GLOW
from ..config.tuning import REAPER_BREAK, REAPER_DRAIN
from ..core.pixelart import CharCanvas, sprite_from_rows
from ..hazards.escort import target_pod
from ..minions.latcher import latcher_trio
from ..minions.veil_bullets import LeadShot, RuneMark, VeilBullet, aimed
from .art import build_boss_sprite
from .base import Boss
from .learning import Learner

HALF_W, H = 30, 56
COLORS = {"K": (10, 6, 16), "C": (40, 26, 60), "c": (26, 16, 40), "V": (110, 70, 170),
          "M": (220, 216, 230), "E": (140, 255, 200), "e": (60, 160, 120), "W": (255, 255, 255)}
SCYTHE_ROWS = (
    "....KKKKKK.....",
    "..KKMMMMMMKK...",
    ".KMMMKKKKMMMK..",
    "KMMKK....KKMMK.",
    "KMK........KMK.",
    "KK..........KK.",
    "..............K",
    ".............KV",
    "............KVK",
    "...........KVK.",
    "..........KVK..",
    ".........KVK...",
    "........KVK....",
    ".......KVK.....",
)


def _half(phase):
    """A hooded shape: a cloak widening downwards, a white mask with glowing eyes."""
    c = CharCanvas(HALF_W, H)
    c.poly([(29, 0), (20, 4), (14, 14), (10, 30), (2, 50), (8, 55), (29, 55)], "c")
    c.poly([(29, 3), (21, 7), (16, 16), (13, 30), (6, 49), (12, 52), (29, 52)], "C")
    for y in range(20, 52, 7):                               # the cloak's folds
        c.line(29 - (y - 20) // 3, y, 14, y + 4, "c")
    c.circle(29, 16, 8, "K")                                 # the hood's hollow
    c.circle(29, 17, 6, "M")                                 # the mask
    eye = "E" if phase < 3 else "e"
    c.rect(24, 15, 26, 17, eye)
    c.set(25, 16, "W")
    c.line(29, 20, 29, 22, "K")
    if phase >= 2:
        c.line(26, 11, 22, 7, "K")                           # a crack in the mask
    return c.rows()


class Scythe:
    """The scythe: a part of the boss. Hits count, and during a harvest they break it."""

    def __init__(self, image):
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.x = self.y = 0.0
        self.flash = 0.0
        self.scythe = True

    @property
    def bound(self):
        return max(self.image.get_size()) / 2 + 1

    @property
    def topleft(self):
        return int(self.x - self.image.get_width() / 2), int(self.y - self.image.get_height() / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        w, h = self.mask.get_size()
        return 0 <= mx < w and 0 <= my < h and self.mask.get_at((mx, my))

    def tip(self):
        return self.x - 6, self.y - 6

    def draw(self, surf):
        surf.blit(self.white if self.flash > 0 else self.image, self.topleft)


class Reaper(Learner, Boss):
    """Galaxy 2, level 3. Four phases; attacks chosen by the bandit.

    HARVEST  -- a beam from the scythe drains the brood pod; hitting the scythe for enough
                damage breaks it (the Reaper staggers)
    FANS     -- lead-shot fans at the rocket
    SWEEP    -- the scythe sweeps an arc of shards
    LATCHERS -- (phase 2+) it calls three latchers for the pod
    RUNES    -- (phase 3+) rune marks where you fly
    Without a pod left to harvest, it hunts only you.
    """

    EPITHET = "IT CAME FOR THE BROOD"
    PHASES = 4
    RAGE = (1.0, 1.15, 1.3, 1.45)
    OPTIONS = (("harvest", "fans", "sweep"),
               ("harvest", "fans", "sweep", "latchers"),
               ("harvest", "fans", "sweep", "latchers", "runes"),
               ("harvest", "fans", "sweep", "runes"))
    SLOT, REST = 3.2, 0.8
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.8, 125, 0.24
    SWEEP_INTERVAL, RUNE_INTERVAL = 0.07, 1.1
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 0.8

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            bodies = [build_boss_sprite(_half(p), COLORS) for p in range(4)]
            cls._sprites = bodies, sprite_from_rows(SCYTHE_ROWS, COLORS)
        return cls._sprites

    def __init__(self, spec):
        bodies, scythe = self.prebuild()
        super().__init__(spec, list(bodies), {}, [(20, 4), (40, 4)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.scythe = Scythe(scythe)
        self.home_y = 30 + self.h / 2
        self.move_time = 0.0
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.5
        self.harvesting = False
        self.broken = 0.0                    # damage on the scythe during this harvest
        self.stagger = 0.0
        self.sweep_angle = 0.0
        self.harvests_broken = 0
        self._layout()

    def parts(self):
        return [self, self.scythe]

    def hit_part(self, part, amount, flash=True, source=None):
        if part is self.scythe:
            part.flash = 0.05 if flash else part.flash
            if self.harvesting:
                self.broken += amount
                if self.broken >= self.max_hp * REAPER_BREAK:
                    self._break_harvest()
        self.damage(amount, flash)

    def _break_harvest(self):
        self.harvesting = False
        self.stagger = 1.4
        self.harvests_broken += 1
        self.attack, self.attack_time = "rest", 0.0

    def collides_with(self, ship):
        return super().collides_with(ship)

    def _layout(self):
        a = self.move_time * 1.4
        self.scythe.x = self.x + 26 + math.cos(a) * 3
        self.scythe.y = self.y + 4 + math.sin(a) * 3

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.6
        self.harvesting = False

    def update(self, dt, world):
        self.scythe.flash = max(0.0, self.scythe.flash - dt)
        result = super().update(dt, world)
        self._layout()
        if self.state != "fight":
            self.harvesting = False
        return result

    def enter(self, k):
        super().enter(k)
        self._layout()

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.learn_tick(dt)
        if self.stagger > 0:                              # broken harvest: it reels
            self.stagger -= dt
            self.x += math.sin(self.stagger * 30) * 0.8
            return
        self.move_time += dt * rate
        pod = target_pod(world)
        goal = pod.x if pod and self.attack == "harvest" else LOW_W / 2 + math.sin(self.move_time * 0.5) * 100
        self.x += (goal - self.x) * min(1.0, 1.5 * dt)
        self.y = self.home_y + math.sin(self.move_time * 1.2) * 5
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time, self.fire_timer = 0.0, 0.3
            self.harvesting = False
            if self.attack == "rest":
                options = [o for o in self.OPTIONS[self.phase] if o != "harvest" or pod]
                self.attack = self.begin_attack(world, options)
                if self.attack == "harvest":
                    self.harvesting, self.broken = True, 0.0
                    world.telegraph()
                    world.audio.play("lock_on")
            else:
                self.attack = "rest"
            return
        if self.attack == "harvest":
            self.harvest_target = (pod.x, pod.y) if pod else None
            if pod and self.attack_time > 0.6:           # a moment's wind-up, then it drains
                pod.hurt(REAPER_DRAIN * rate * dt)
            elif not pod:
                self.attack = "rest"
                self.harvesting = False
            return
        if self.attack == "sweep":
            self.sweep_angle += 2.2 * dt * rate
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    # --- attacks ------------------------------------------------------------------------
    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y + 10, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _sweep(self, world):
        self.fire_timer = self.SWEEP_INTERVAL
        x, y = self.scythe.tip()
        a = math.pi * 0.15 + (self.sweep_angle % math.pi) * 0.7
        world.enemy_bullets.append(VeilBullet(x, y, math.cos(a) * 95, math.sin(a) * 95,
                                              self.bullet_damage * 0.7))

    def _latchers(self, world):
        self.fire_timer = 99
        world.spawn_enemies(latcher_trio(world))

    def _runes(self, world):
        self.fire_timer = self.RUNE_INTERVAL
        ship = world.aim_target()
        world.enemy_bullets.append(RuneMark(min(LOW_W - 10, max(10, ship.x + random.uniform(-20, 20))),
                                            min(LOW_H - 10, max(60, ship.y)), self.bullet_damage))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        super().draw(surf)
        self.scythe.draw(surf)
        if self.harvesting and self.state == "fight":
            x0, y0 = self.scythe.tip()
            target = self.harvest_target
            if target:
                steps = 10
                pts = []
                for i in range(steps + 1):
                    k = i / steps
                    pts.append((x0 + (target[0] - x0) * k + random.uniform(-3, 3),
                                y0 + (target[1] - y0) * k + random.uniform(-3, 3)))
                color = HEAL[2] if self.attack_time > 0.6 else DANGER
                pygame.draw.lines(surf, color, False, pts)
                pygame.draw.lines(surf, VEIL_GLOW[2], False, [(x + 1, y) for x, y in pts])

    harvest_target = None                  # (x, y) of the pod while it harvests
