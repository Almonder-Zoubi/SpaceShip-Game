"""Boss 6: WRAITH, the stealth frigate (level 6) — sprite, decoys and behaviour."""
import math
import random

import pygame

from ..config.palette import DANGER, SPARK
from ..core.pixelart import CharCanvas
from ..minions.bullets import CurvedBullet, shoot
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss

WRAITH_HALF_W, WRAITH_HALF_H = 32, 40
WRAITH_COLORS = {**HULL_COLORS, "H": (28, 40, 44), "M": (46, 64, 70), "L": (80, 110, 112),
                 "W": (140, 190, 180), "G": (16, 22, 26), "g": (60, 90, 90),
                 "E": (90, 220, 190), "e": (40, 120, 110)}
POINTS = ((60, 52), (160, 42), (260, 52), (104, 92), (216, 92))   # teleport spots
ALPHAS = 10


def _wraith_half():
    """Left half: a flat blade-like hull, swept wings with teal edges, a long nose."""
    c = CharCanvas(WRAITH_HALF_W, WRAITH_HALF_H)
    c.poly([(31, 0), (18, 14), (2, 24), (0, 30), (14, 28), (24, 34), (31, 39)], "M")
    c.line(31, 0, 18, 14, "W")
    c.line(18, 14, 2, 24, "L")
    c.line(2, 24, 0, 30, "E")
    c.line(0, 30, 14, 28, "e")
    c.poly([(31, 4), (24, 16), (26, 30), (31, 34)], "H")
    c.line(28, 8, 27, 30, "g")
    for x, y in ((10, 25), (16, 22), (22, 19)):
        c.set(x, y, "E")
    c.rect(29, 20, 31, 26, "G")                  # the stealth "eye" slit
    c.set(30, 22, "E")
    c.line(14, 28, 24, 34, "H")
    return c.rows()


class Decoy:
    """A copy of the Wraith (phase 2): it pops in one hit and hurts nothing."""

    def __init__(self, boss, x, y):
        self.boss, self.x, self.y = boss, x, y
        self.popped = False

    @property
    def bound(self):
        return self.boss.bound

    def contains(self, px, py):
        left = int(self.x - self.boss.w / 2)
        top = int(self.y - self.boss.h / 2)
        mx, my = int(px) - left, int(py) - top
        return (0 <= mx < self.boss.w and 0 <= my < self.boss.h
                and self.boss.mask.get_at((mx, my)))


class Wraith(Boss):
    """Boss 6. Nearly invisible: a shimmer outline, afterimages when it moves, and it shows
    itself when it fires.

    Phase 1 (calm)    -- TELEPORTS between 5 spots (0.5 s of static at the arrival spot
                         first), aimed fans and a stream of aimed shots
    Phase 2 (angry)   -- x1.2; 2 DECOYS appear with every jump. Only the real one has a
                         blinking red running light; decoys pop in one hit
    Phase 3 (furious) -- x1.4; the whole screen fogs over, it lights a flare on itself
                         before every attack, and its shots bend in curves
    The idea: read the tells, not the sprite.
    """

    EPITHET = "THE STEALTH FRIGATE"
    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("teleport", 0.7), ("fans", 2.4), ("teleport", 0.7), ("stream", 2.0), ("rest", 0.6)),
        (("teleport", 0.7), ("fans", 2.2), ("stream", 1.8), ("teleport", 0.7), ("fans", 2.2),
         ("rest", 0.5)),
        (("teleport", 0.8), ("curves", 2.4), ("teleport", 0.8), ("fans", 2.0), ("curves", 2.0),
         ("rest", 0.4)),
    )
    STATIC = 0.4                     # s of static at the arrival spot before it appears
    TELL = 0.35                      # phase 3: its flare burns this long before each shot
    FAN_INTERVAL, FAN_SHOTS, FAN_GAP, FAN_SPEED = 0.6, 5, 0.2, 112
    STREAM_INTERVAL, STREAM_SPEED = 0.22, 140
    CURVE_INTERVAL, CURVE_SPEED, CURVE_TURN = 0.3, 105, 1.3
    # Phase 1 aimed shots per second at a rocket sitting still: the centre of every fan and
    # every stream shot.
    AIMED_RATE = (2.4 / FAN_INTERVAL + 2.0 / STREAM_INTERVAL) / (0.7 + 2.4 + 0.7 + 2.0 + 0.6)

    _alpha_frames = None

    @classmethod
    def prebuild(cls):
        if cls._alpha_frames is None:
            image = build_boss_sprite(_wraith_half(), WRAITH_COLORS)
            frames = []
            for i in range(ALPHAS + 1):
                frame = image.copy()
                frame.set_alpha(int(255 * i / ALPHAS))
                frames.append(frame)
            cls._alpha_frames = image, frames
        return cls._alpha_frames

    def __init__(self, spec):
        image, self.frames = self.prebuild()
        super().__init__(spec, image, {}, [(26, 2), (39, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.outline = self.mask.outline()
        self.home_y = POINTS[1][1]
        self.spot = POINTS[1]
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.shown = 0.0                 # seconds it stays fully visible (after firing)
        self.hidden = False              # between spots while teleporting
        self.arrival = None              # (x, y) of the static before it appears
        self.ghosts = []                 # afterimages: [x, y, time left]
        self.decoys = []
        self.tell = 0.0                  # phase 3 flare before a shot
        self.time = 0.0
        self._pop = None                 # a decoy hit this frame (effects in update)

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        if self.hidden:
            return []
        return [self] + [d for d in self.decoys if not d.popped]

    def hit_part(self, part, amount, flash=True, source=None):
        if isinstance(part, Decoy):
            part.popped = True
            self._pop = part
            return
        self.damage(amount, flash)
        self.shown = max(self.shown, 0.15)

    def collides_with(self, ship):
        return not self.hidden and super().collides_with(ship)

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.4
        self.decoys = []
        if self.hidden:                      # it was mid-jump: land where it was going
            self.spot = self.arrival or self.spot
            self.x, self.y = self.spot
        self.hidden = False
        self.arrival = None

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        self.time += dt
        self.shown = max(0.0, self.shown - dt)
        for ghost in self.ghosts:
            ghost[2] -= dt
        self.ghosts = [g for g in self.ghosts if g[2] > 0]
        popped = self._pop
        if popped:
            self._pop = None
            world.fire.burst(popped.x, popped.y, 20, 80, 0.4, SPARK, size=(1, 2))
            world.smoke.burst(popped.x, popped.y, 12, 40, 0.8,
                              [WRAITH_COLORS["L"], WRAITH_COLORS["M"]], size=(1, 2))
            world.audio.play("drone_explode")
            self.decoys = [d for d in self.decoys if not d.popped]
        if self.state != "fight":
            self.hidden = False
        return super().update(dt, world)

    def enter(self, k):
        super().enter(k)
        self.x = POINTS[1][0]
        self.home_y = POINTS[1][1]

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        name, duration = self._pattern()
        self.attack_time += dt
        if name == "teleport":
            self._teleport(world, duration)
        else:
            self.hidden = False
            self.y = self.spot[1] + math.sin(self.time * 1.5) * 3
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3 if self.phase < 2 else self.TELL
            return
        if name in ("teleport", "rest"):
            return
        self.fire_timer -= dt * rate
        if self.phase == 2:
            self.tell = self.fire_timer if self.fire_timer < self.TELL else 0.0
        if self.fire_timer <= 0:
            getattr(self, "_" + name)(world)
            self.shown = 0.25

    def _teleport(self, world, duration):
        """Vanish (leaving afterimages), static at the next spot, reappear there."""
        if self.arrival is None:
            self.ghosts += [[self.x + dx, self.y, 0.5 - i * 0.12]
                            for i, dx in enumerate((0, -4, 4))]
            options = [p for p in POINTS if p != self.spot]
            self.arrival = random.choice(options)
            self.hidden = True
            world.audio.play("teleport")
        if self.attack_time >= self.STATIC or self.attack_time >= duration - 0.05:
            if self.hidden:
                self.spot = self.arrival
                self.x, self.y = self.spot
                self.hidden = False
                if self.phase == 1:
                    others = [p for p in POINTS if p != self.spot]
                    random.shuffle(others)
                    self.decoys = [Decoy(self, x, y) for x, y in others[:2]]
        if self.attack_time + 0.02 >= duration:
            self.arrival = None
        elif self.hidden and random.random() < 0.7:          # static crackle at the spot
            ax, ay = self.arrival
            world.fire.emit(ax + random.uniform(-18, 18), ay + random.uniform(-12, 12),
                            random.uniform(-30, 30), random.uniform(-30, 30), 0.15, SPARK)

    # --- attacks ------------------------------------------------------------------------
    def _muzzle(self):
        return self.x, self.y + self.h / 2 - 4

    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        mx, my = self._muzzle()
        aim = math.atan2(world.ship.y - my, world.ship.x - mx)
        for i in range(self.FAN_SHOTS):
            shoot(world, mx, my, aim + (i - self.FAN_SHOTS // 2) * self.FAN_GAP, self.FAN_SPEED,
                  self.bullet_damage)

    def _stream(self, world):
        self.fire_timer = self.STREAM_INTERVAL
        mx, my = self._muzzle()
        shoot(world, mx, my, math.atan2(world.ship.y - my, world.ship.x - mx),
              self.STREAM_SPEED, self.bullet_damage)

    def _curves(self, world):
        """Two shots that bend in from both sides towards the rocket."""
        self.fire_timer = self.CURVE_INTERVAL + self.TELL
        mx, my = self._muzzle()
        aim = math.atan2(world.ship.y - my, world.ship.x - mx)
        for side in (-1, 1):
            a = aim + side * 0.55
            world.enemy_bullets.append(CurvedBullet(
                mx, my, math.cos(a) * self.CURVE_SPEED, math.sin(a) * self.CURVE_SPEED,
                self.bullet_damage, -side * self.CURVE_TURN))
        world.audio.play("enemy_shot")

    # --- draw ---------------------------------------------------------------------------
    def _blit(self, surf, x, y, alpha, real):
        left, top = int(x - self.w / 2), int(y - self.h / 2)
        step = max(0, min(ALPHAS, int(alpha * ALPHAS)))
        if step:
            surf.blit(self.frames[step], (left, top))
        for i, (px, py) in enumerate(self.outline):          # shimmer outline
            if (i + int(self.time * 15)) % 4 == 0:
                surf.fill((50, 80, 76), (left + px, top + py, 1, 1),
                          special_flags=pygame.BLEND_ADD)
        if real and self.phase >= 1 and int(self.time * 4) % 2 == 0:
            surf.fill(DANGER, (int(x) - 1, top + 23, 2, 2))    # the running light

    def draw(self, surf):
        if self.state == "dead":
            return
        if self.phase == 2 and self.state == "fight":         # the screen fogs over
            fog = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            fog.fill((10, 16, 14, 150))
            surf.blit(fog, (0, 0))
        for x, y, left in self.ghosts:
            self._blit(surf, x, y, left * 0.6, False)
        if self.state in ("enter", "dying") or self.roar > 0:
            super().draw(surf)
            return
        for decoy in self.decoys:
            if not decoy.popped:
                self._blit(surf, decoy.x, decoy.y, 0.3 + 0.7 * min(1.0, self.shown * 4), False)
        if self.hidden:
            return
        if self.flash > 0:
            surf.blit(self.white, self.topleft)
        else:
            self._blit(surf, self.x, self.y, 0.3 + 0.7 * min(1.0, self.shown * 4), True)
        if self.tell > 0:                                    # phase 3 flare: it's about to fire
            mx, my = self._muzzle()
            r = 2 + int((self.TELL - self.tell) * 16)
            pygame.draw.circle(surf, (255, 240, 200), (int(mx), int(my)), r, 1)
            surf.fill((255, 255, 255), (int(mx) - 1, int(my) - 1, 3, 3))
