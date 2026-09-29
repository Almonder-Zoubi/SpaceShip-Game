"""Boss 7: KALEIDOS, the prism queen (level 7) — sprite, shards and behaviour."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER, SPARK
from ..core.pixelart import CharCanvas, outlined, sprite_from_rows
from ..minions.bullets import ColoredBullet, bullet, shoot
from ..weapons.laser import Laser
from .base import Boss

KALEIDOS_COLORS = {"K": (18, 14, 30), "H": (60, 40, 110), "M": (100, 70, 190),
                   "L": (150, 130, 240), "W": (240, 240, 255), "C": (120, 230, 255),
                   "c": (50, 140, 190), "E": (255, 90, 160), "Q": (255, 255, 255)}
LIGHTS = ((120, 230, 255), (255, 170, 230), (255, 255, 255))
# Seven hot hues for the prism spirals (rim, body): pinks, reds, oranges, never blue.
PRISM = (((200, 30, 90), (255, 100, 170)), ((220, 30, 50), (255, 110, 110)),
         ((230, 80, 20), (255, 170, 90)), ((220, 130, 20), (255, 210, 110)),
         ((200, 40, 160), (255, 120, 230)), ((240, 60, 90), (255, 160, 170)),
         ((230, 100, 40), (255, 190, 140)))
SHARD_ROWS = (
    "...K...",
    "..KWK..",
    ".KCWCK.",
    ".KCWcK.",
    "KCCWccK",
    "KCWCccK",
    "KCWCccK",
    ".KCCcK.",
    ".KCccK.",
    "..KcK..",
    "...K...",
)


def _core_rows(phase):
    """The hive: a faceted crystal gem, bigger light in the middle when it's furious."""
    c = CharCanvas(45, 49)
    c.poly([(22, 0), (44, 14), (44, 34), (22, 48), (0, 34), (0, 14)], "M")
    c.poly([(22, 0), (44, 14), (22, 24), (0, 14)], "L")
    c.poly([(0, 14), (22, 24), (22, 48), (0, 34)], "H")
    c.line(22, 0, 22, 48, "c")
    c.line(0, 14, 44, 34, "H")
    c.line(44, 14, 0, 34, "H")
    c.line(22, 1, 3, 14, "W")
    for x, y in ((10, 10), (32, 30), (14, 36), (34, 16)):
        c.set(x, y, "W")
    r = 6 + 2 * phase
    c.circle(22, 24, r + 1, "c")
    c.circle(22, 24, r, "C")
    c.circle(22, 24, max(1, r - 3), "Q")
    if phase == 2:
        for x0, y0, x1, y1 in ((4, 18, 12, 26), (40, 20, 32, 30), (18, 42, 24, 34)):
            c.line(x0, y0, x1, y1, "E")
    return outlined(c.rows())


class Shard:
    """One of the six crystal shards: a mirror in phase 1, a beam post in phase 2."""

    REGROW = 10.0

    def __init__(self, boss, index, image, mask):
        self.boss, self.index = boss, index
        self.image, self.mask = image, mask
        self.x = self.y = 0.0
        self.hp = self.max_hp = 1.0
        self.broken = 0.0                  # seconds until it regrows (0 = whole)
        self.flash = 0.0

    @property
    def whole(self):
        return self.broken <= 0

    @property
    def bound(self):
        return 7

    @property
    def topleft(self):
        return int(self.x - self.image.get_width() / 2), int(self.y - self.image.get_height() / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        w, h = self.mask.get_size()
        return 0 <= mx < w and 0 <= my < h and self.mask.get_at((mx, my))


def _segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - dx * t, py - ay - dy * t)


class Kaleidos(Boss):
    """Boss 7. A crystal hive with six shards.

    Phase 1 (calm)    -- the shards form a MIRROR SHIELD towards the rocket: laser hits on a
                         shard bounce back at the ship (weaker); other weapons break shards
                         (60% of that damage reaches the hive; they regrow). Prism fans
                         from the core, shard shots
    Phase 2 (angry)   -- x1.2; the shards spread out and join into a slowly turning LATTICE
                         of light beams (they blink first) — stay out of the lines
    Phase 3 (furious) -- x1.4; the queen splits her light into 7 coloured spirals
    The idea: the laser, the player's favourite, now needs thinking.
    """

    EPITHET = "THE PRISM QUEEN"
    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("prism", 2.6), ("shards", 2.4), ("rest", 1.0)),
        (("prism", 2.2), ("lattice", 3.6), ("shards", 2.0), ("rest", 0.6)),
        (("spiral7", 3.2), ("prism", 2.0), ("lattice", 3.0), ("spiral7", 2.6), ("rest", 0.4)),
    )
    MIRROR_R, LATTICE_R = 34, 72
    SHARD_HP = 0.02                  # share of the boss's max hp per shard
    SHARD_PASS = 0.6                 # a shard hit by a gun (not the laser) passes this on
    REFLECT_X = 0.6                  # a reflected laser hurts like this many bullets
    PRISM_INTERVAL, PRISM_SPEED, PRISM_GAP = 0.5, 118, 0.22
    SHARD_INTERVAL, SHARD_SPEED = 0.3, 125
    LATTICE_WARN, LATTICE_X = 0.8, 1.5
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.12, 72, 1.6
    # Phase 1 aimed shots per second at a rocket sitting still: the middle of every prism
    # fan and every shard shot (the reflection is the player's own doing).
    AIMED_RATE = (2.6 / PRISM_INTERVAL + 2.4 / SHARD_INTERVAL) / (2.6 + 2.4 + 1.0)

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cores = [sprite_from_rows(_core_rows(p), {**KALEIDOS_COLORS, "C": LIGHTS[p]})
                     for p in range(3)]
            shard = sprite_from_rows(SHARD_ROWS, KALEIDOS_COLORS)
            cls._sprites = cores, shard, pygame.mask.from_surface(shard)
        return cls._sprites

    def __init__(self, spec):
        cores, shard, mask = self.prebuild()
        super().__init__(spec, list(cores), {}, [(16, 2), (30, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.shards = [Shard(self, i, shard, mask) for i in range(6)]
        for s in self.shards:
            s.hp = s.max_hp = self.max_hp * self.SHARD_HP
        self.home_y = 30 + self.h / 2
        self.move_time = 0.0
        self.spin = 0.0
        self.aim = math.pi / 2
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.shard_turn = 0
        self.spiral_angle = 0.0
        self.reflections = []            # shards hit by the laser this frame
        self.reflect_beam = []           # (x0, y0, x1, y1) drawn this frame
        self._shattered = None           # a shard broke this frame (effects in update)
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        return [self] + [s for s in self.shards if s.whole]

    def hit_part(self, part, amount, flash=True, source=None):
        if part is self:
            self.damage(amount, flash)
            return
        if self.state != "fight" or self.roar > 0:
            return
        part.flash = 0.05
        if isinstance(source, Laser) and self.phase == 0:
            self.reflections.append(part)          # the mirror: it bounces back
            return
        part.hp -= amount
        self.damage(amount * self.SHARD_PASS, flash)            # the hive feels it
        if part.hp <= 0:
            part.broken = Shard.REGROW
            part.hp = part.max_hp
            self._shattered = part

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    @property
    def lattice(self):
        """0 off, 1 warning (blinking thin lines), 2 burning."""
        name, _ = self._pattern()
        if name != "lattice" or not self.fighting:
            return 0
        return 1 if self.attack_time < self.LATTICE_WARN else 2

    def beams(self):
        """The lattice lines between opposite whole shards."""
        return [(a.x, a.y, b.x, b.y) for a, b in zip(self.shards[:3], self.shards[3:])
                if a.whole and b.whole]

    def _layout(self):
        if self.phase == 0:                        # mirror arc towards the rocket
            for s in self.shards:
                a = self.aim + (s.index - 2.5) * 0.3
                s.x = self.x + math.cos(a) * self.MIRROR_R
                s.y = self.y + math.sin(a) * self.MIRROR_R
        else:                                      # spread out and turn
            for s in self.shards:
                a = self.spin + math.tau * s.index / 6
                s.x = self.x + math.cos(a) * self.LATTICE_R
                s.y = self.y + math.sin(a) * self.LATTICE_R * 0.8

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        self.reflect_beam = []
        for s in self.shards:
            s.flash = max(0.0, s.flash - dt)
            s.broken = max(0.0, s.broken - dt)
        shattered = self._shattered
        if shattered:
            self._shattered = None
            world.fire.burst(shattered.x, shattered.y, 14, 70, 0.4, SPARK, size=(1, 1))
            world.audio.play("ice_break")
        ship = world.ship
        for shard in self.reflections:             # the laser comes back at the ship
            self.reflect_beam.append((shard.x, shard.y, ship.x, ship.y))
            if self.fighting and ship.alive:
                world.hurt_ship(self.bullet_damage * self.REFLECT_X, shard.x, shard.y)
        self.reflections = []
        if self.lattice == 2 and ship.alive:
            for ax, ay, bx, by in self.beams():
                if _segment_distance(ship.x, ship.y, ax, ay, bx, by) < 2 + ship.w * 0.3:
                    world.hurt_ship(self.bullet_damage * self.LATTICE_X, ship.x, ship.y)
                    break
        result = super().update(dt, world)
        self._layout()
        return result

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.3) * (LOW_W / 2 - 80)
        self.y = self.home_y + math.sin(self.move_time * 0.8) * 4
        want = math.atan2(world.ship.y - self.y, world.ship.x - self.x)
        diff = (want - self.aim + math.pi) % math.tau - math.pi
        self.aim += max(-1.2 * dt, min(1.2 * dt, diff))
        self.spin += (0.35 if self.phase else 0) * dt * rate
        name, duration = self._pattern()
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            return
        self.fire_timer -= dt * rate
        if name == "spiral7":
            self.spiral_angle += self.SPIRAL_TURN * dt * rate
        if self.fire_timer > 0 or name in ("rest", "lattice"):
            return
        getattr(self, "_" + name)(world)

    # --- attacks ------------------------------------------------------------------------
    def _prism(self, world):
        self.fire_timer = self.PRISM_INTERVAL
        aim = math.atan2(world.ship.y - self.y, world.ship.x - self.x)
        for i in (-1, 0, 1):
            shoot(world, self.x, self.y + 10, aim + i * self.PRISM_GAP, self.PRISM_SPEED,
                  self.bullet_damage)

    def _shards(self, world):
        self.fire_timer = self.SHARD_INTERVAL
        whole = [s for s in self.shards if s.whole]
        if not whole:
            return
        s = whole[self.shard_turn % len(whole)]
        self.shard_turn += 1
        world.enemy_bullets.append(bullet(s.x, s.y, math.atan2(world.ship.y - s.y,
                                                               world.ship.x - s.x),
                                          self.SHARD_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _spiral7(self, world):
        """Seven arms, one hot colour each."""
        self.fire_timer = self.SPIRAL_INTERVAL
        for i, colors in enumerate(PRISM):
            a = self.spiral_angle + math.tau * i / len(PRISM)
            world.enemy_bullets.append(ColoredBullet(
                self.x, self.y, math.cos(a) * self.SPIRAL_SPEED, math.sin(a) * self.SPIRAL_SPEED,
                self.bullet_damage, colors))

    # --- draw ---------------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        lattice = self.lattice
        if lattice and self.roar <= 0:
            for ax, ay, bx, by in self.beams():
                if lattice == 1:
                    if int(self.attack_time * 12) % 2 == 0:
                        pygame.draw.line(surf, DANGER, (int(ax), int(ay)), (int(bx), int(by)))
                else:
                    pygame.draw.line(surf, (200, 40, 110), (int(ax), int(ay)), (int(bx), int(by)), 3)
                    pygame.draw.line(surf, (255, 230, 240), (int(ax), int(ay)), (int(bx), int(by)))
        super().draw(surf)
        for s in self.shards:
            if s.whole:
                if s.flash > 0:
                    surf.blit(s.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0)),
                              s.topleft)
                else:
                    surf.blit(s.image, s.topleft)
            elif random.random() < 0.3:                 # regrowing: a faint glitter
                surf.fill((80, 120, 160), (int(s.x), int(s.y), 1, 1), special_flags=pygame.BLEND_ADD)
        for x0, y0, x1, y1 in self.reflect_beam:
            pygame.draw.line(surf, (255, 200, 240), (int(x0), int(y0)), (int(x1), int(y1)))
