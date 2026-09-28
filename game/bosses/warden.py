"""Galaxy 2 boss 1: THE WARDEN, the door of the Veil (G2 level 1) — a core behind rotating
shield rings. Shots only land through the gaps; it learns (bosses/learning.Learner)."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, SPARK, VEIL_GLOW
from ..core.pixelart import CharCanvas, outlined, sprite_from_rows
from ..minions.veil_bullets import Boomerang, LeadShot, RuneMark, SplitterBullet, aimed, twinned
from .base import Boss
from .learning import Learner

CORE = 15                                  # core sprite radius
OUTER, INNER = 31, 23                      # ring radii
OUTER_GAP, INNER_GAP = 1.75, 1.55          # gap widths (radians)
ANGLES = 72                                # prebuilt ring rotations (5 degrees each)
LIGHTS = (((210, 180, 255), (120, 80, 200)), ((180, 240, 255), (60, 150, 170)),
          ((255, 210, 120), (190, 110, 40)), ((255, 110, 120), (170, 40, 60)))
COLORS = {"K": (16, 10, 26), "H": (70, 64, 70), "M": (140, 132, 124), "L": (200, 192, 178),
          "W": (242, 238, 226), "E": (40, 24, 60)}


def _core_rows(phase):
    size = CORE * 2 + 1
    c = CharCanvas(size, size)
    c.circle(CORE, CORE, CORE, "H")
    c.circle(CORE, CORE, CORE - 2, "M")
    c.circle(CORE - 3, CORE - 4, CORE - 7, "L")
    c.circle(CORE - 5, CORE - 6, 3, "W")
    for i in range(6):                                   # bone plates
        a = math.tau * i / 6 + 0.3
        c.line(int(CORE + math.cos(a) * 7), int(CORE + math.sin(a) * 7),
               int(CORE + math.cos(a) * (CORE - 1)), int(CORE + math.sin(a) * (CORE - 1)), "H")
    eye = 4 + phase
    c.circle(CORE, CORE + 2, eye + 2, "E")
    c.circle(CORE, CORE + 2, eye, "q")
    c.circle(CORE, CORE + 2, max(1, eye - 2), "Q")
    c.set(CORE - 1, CORE + 1, "W")
    return outlined(c.rows())


def _ring_image(radius, thick, gap, angle):
    """One rotation of a ring of bone plates with a gap centred on `angle` (radians,
    screen coordinates: 0 = right, pi/2 = down)."""
    size = radius * 2 + 5
    c = size // 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c)
            if not radius - thick <= d <= radius:
                continue
            a = math.atan2(y - c, x - c)
            off = (a - angle + math.pi) % math.tau - math.pi
            if abs(off) < gap / 2:
                continue
            seam = int((a + math.pi) / math.tau * 16) != int((a + math.pi + 0.05) / math.tau * 16)
            if d > radius - 1 or d < radius - thick + 1:
                color = COLORS["K"]
            elif seam:
                color = COLORS["H"]
            else:
                color = COLORS["L"] if d > radius - thick / 2 else COLORS["M"]
            if abs(abs(off) - gap / 2) < 0.12:          # the gap's edges glow
                color = VEIL_GLOW[1]
            surf.set_at((x, y), color)
    return surf


class Ring:
    """A shield ring as a boss part: hits on it are blocked (sparks), the gap lets them in."""

    def __init__(self, frames, radius):
        self.frames, self.radius = frames, radius       # [(image, mask, white)]
        self.angle = math.pi / 2
        self.x = self.y = 0.0
        self.flash = 0.0
        self.ring = True

    @property
    def index(self):
        return int(round(self.angle / math.tau * ANGLES)) % ANGLES

    @property
    def bound(self):
        return self.radius + 2

    @property
    def topleft(self):
        image = self.frames[self.index][0]
        return int(self.x - image.get_width() / 2), int(self.y - image.get_height() / 2)

    def contains(self, px, py):
        _, mask, _ = self.frames[self.index]
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        w, h = mask.get_size()
        return 0 <= mx < w and 0 <= my < h and mask.get_at((mx, my))

    def overlaps(self, ship):
        _, mask, _ = self.frames[self.index]
        sx, sy = ship.topleft
        left, top = self.topleft
        return ship.mask.overlap(mask, (left - sx, top - sy)) is not None

    def turn_towards(self, target, speed, dt):
        off = (target - self.angle + math.pi) % math.tau - math.pi
        step = max(-speed * dt, min(speed * dt, off))
        self.angle = (self.angle + step) % math.tau

    def draw(self, surf):
        image, _, white = self.frames[self.index]
        surf.blit(white if self.flash > 0 else image, self.topleft)


class Warden(Learner, Boss):
    """Galaxy 2, level 1. Four phases:

    Phase 1 -- one ring. The gap turns away from the side you like to fly (it reads the
               player model); lead-shot fans, rune marks on your favourite spot, splitters
    Phase 2 -- x1.15; an inner ring swings its gap across the outer one: shoot when they
               line up (a steady rhythm);
               + boomerangs
    Phase 3 -- x1.3; the rings spin fast and spray from the gap edges; + twinned bullets
    Phase 4 -- x1.45; the outer ring breaks loose and saws across the screen (it still blocks
               shots); the core has only the inner ring left
    Attacks are chosen by the bandit (the ones that hurt you come back more often).
    """

    EPITHET = "THE DOOR THAT WATCHES"
    PHASES = 4
    RAGE = (1.0, 1.15, 1.3, 1.45)
    OPTIONS = (("fans", "runes", "splitters"),
               ("fans", "runes", "splitters", "boomerangs"),
               ("fans", "runes", "boomerangs", "twins", "spray"),
               ("fans", "runes", "splitters", "twins", "spray"))
    SLOT, REST = 2.8, 0.7
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.55, 120, 0.22
    RUNE_INTERVAL, SPLIT_INTERVAL, BOOM_INTERVAL, TWIN_INTERVAL = 0.9, 0.8, 0.6, 0.5
    SPRAY_INTERVAL = 0.09
    RING_PASS = 0.25                       # a hit on a ring still does this share
    RING_TURN = (0.7, 0.8, 1.6, 1.8)       # rad/s the gaps can turn
    # Aimed damage per second at a rocket sitting still: the lead shot in the middle of every
    # fan (the most used attack) and about one splitter / rune bullet per second.
    AIMED_RATE = 1 / FAN_INTERVAL * SLOT / (SLOT + REST) + 1.0

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cores = [sprite_from_rows(_core_rows(p), {**COLORS, "Q": light, "q": dark})
                     for p, (light, dark) in enumerate(LIGHTS)]
            rings = []
            for radius, thick, gap in ((OUTER, 5, OUTER_GAP), (INNER, 4, INNER_GAP)):
                frames = []
                base = _ring_image(radius, thick, gap, 0.0)
                for i in range(ANGLES):
                    image = pygame.transform.rotate(base, -360 * i / ANGLES)
                    mask = pygame.mask.from_surface(image)
                    white = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
                    frames.append((image, mask, white))
                rings.append(frames)
            cls._sprites = cores, rings
        return cls._sprites

    def __init__(self, spec):
        cores, (outer, inner) = self.prebuild()
        super().__init__(spec, list(cores), {}, [(CORE - 6, 2), (CORE + 6, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.outer, self.inner = Ring(outer, OUTER), Ring(inner, INNER)
        self.inner.angle = -math.pi / 2
        self.home_y = 34 + OUTER
        self.move_time = 0.0
        self.attack = "rest"
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.saw = False                                  # phase 4: the outer ring is loose
        self.saw_time = 0.0
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    def rings(self):
        out = [self.outer]
        if self.phase >= 1:
            out.append(self.inner)
        return out

    def parts(self):
        return self.rings() + [self]

    def hit_part(self, part, amount, flash=True, source=None):
        if getattr(part, "ring", False):                 # the shield takes most of it
            part.flash = 0.04 if flash else part.flash
            self.damage(amount * self.RING_PASS, flash=False)
            return
        self.damage(amount, flash)

    def collides_with(self, ship):
        return super().collides_with(ship) or any(r.overlaps(ship) for r in self.rings())

    @property
    def contact_damage(self):
        return self.bullet_damage * 2.5 if self.saw else super().contact_damage

    def on_phase(self):
        self.attack, self.attack_time, self.fire_timer = "rest", 0.0, 0.6
        if self.phase == 3:
            self.saw = True

    def _layout(self):
        self.inner.x, self.inner.y = self.x, self.y
        if not self.saw:
            self.outer.x, self.outer.y = self.x, self.y

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        for ring in (self.outer, self.inner):
            ring.flash = max(0.0, ring.flash - dt)
        result = super().update(dt, world)
        self._layout()
        return result

    def enter(self, k):
        super().enter(k)
        self._layout()

    def _gap_target(self, world):
        """Where the gap wants to face: away from the rocket's favourite side (it has read
        the player model), else sweeping slowly across the bottom."""
        counters = self.counters(world)
        ship = world.ship
        toward = math.atan2(ship.y - self.y, ship.x - self.x)
        if "left" in counters:
            return math.pi / 2 - 0.8 + math.sin(self.move_time * 0.5) * 0.3
        if "right" in counters:
            return math.pi / 2 + 0.8 + math.sin(self.move_time * 0.5) * 0.3
        return 0.7 * toward + 0.3 * (math.pi / 2 + math.sin(self.move_time * 0.4) * 1.1)

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.learn_tick(dt)
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.33) * (LOW_W / 2 - OUTER - 30)
        self.y = self.home_y + math.sin(self.move_time * 0.8) * 5
        turn = self.RING_TURN[self.phase]
        if self.attack == "spray":
            self.outer.angle = (self.outer.angle + 2.4 * dt * rate) % math.tau
            self.inner.angle = (self.inner.angle - 2.0 * dt * rate) % math.tau
        else:
            if not self.saw:
                self.outer.turn_towards(self._gap_target(world), turn, dt)
                # the inner gap swings across the outer one: they line up in a steady rhythm
                swing = math.sin(self.move_time * 1.3) * 1.7
                self.inner.turn_towards(self.outer.angle + swing, 3.0, dt)
            else:
                self.inner.turn_towards(self._gap_target(world), turn, dt)
        if self.saw:
            self._saw(dt, world)
        self.attack_time += dt
        length = self.REST if self.attack == "rest" else self.SLOT
        if self.attack_time >= length:
            self.attack_time = 0.0
            self.fire_timer = 0.3
            if self.attack == "rest":
                self.attack = self.begin_attack(world, self.OPTIONS[self.phase])
                if self.attack == "fans":
                    world.telegraph()
            else:
                self.attack = "rest"
            return
        if self.attack == "rest":
            return
        self.fire_timer -= dt * rate
        if self.fire_timer <= 0:
            getattr(self, "_" + self.attack)(world)

    def _saw(self, dt, world):
        """Phase 4: the loose outer ring sweeps a figure eight over the screen."""
        self.saw_time += dt
        t = self.saw_time * 0.7
        self.outer.x = LOW_W / 2 + math.sin(t) * (LOW_W / 2 - OUTER - 6)
        self.outer.y = LOW_H * 0.5 + math.sin(t * 2) * (LOW_H * 0.3)
        self.outer.angle = (self.outer.angle + 5 * dt) % math.tau
        if random.random() < 20 * dt:
            a = random.uniform(0, math.tau)
            world.fire.emit(self.outer.x + math.cos(a) * OUTER, self.outer.y + math.sin(a) * OUTER,
                            math.cos(a) * 60, math.sin(a) * 60, 0.2, SPARK)

    # --- attacks ------------------------------------------------------------------------
    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, self.FAN_SPEED)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(aimed(LeadShot, self.x, self.y, aim + i * self.FAN_GAP,
                                             self.FAN_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _runes(self, world):
        """A rune where you like to be, and one where you're going."""
        self.fire_timer = self.RUNE_INTERVAL
        ship = world.ship
        hx, hy = world.player_model.hot_spot()
        spots = [(ship.x + ship.vx * 0.6, ship.y + ship.vy * 0.6)]
        if world.player_model.seconds > 10:
            spots.append((hx, hy))
        for x, y in spots:
            x = min(LOW_W - 12, max(12, x))
            y = min(LOW_H - 12, max(OUTER * 2, y))
            world.enemy_bullets.append(RuneMark(x, y, self.bullet_damage))

    def _splitters(self, world):
        self.fire_timer = self.SPLIT_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, 90)
        for i in (-1, 1):
            world.enemy_bullets.append(aimed(SplitterBullet, self.x, self.y, aim + i * 0.35, 90,
                                             self.bullet_damage))

    def _boomerangs(self, world):
        self.fire_timer = self.BOOM_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, 160)
        world.enemy_bullets.append(aimed(Boomerang, self.x, self.y, aim, 190, self.bullet_damage))

    def _twins(self, world):
        self.fire_timer = self.TWIN_INTERVAL
        aim = self.lead_aim(world, self.x, self.y, 100)
        world.enemy_bullets += twinned(self.x, self.y, aim, 100, self.bullet_damage)

    def _spray(self, world):
        """Bullets fly out of the gap edges while the rings spin."""
        self.fire_timer = self.SPRAY_INTERVAL
        for ring in self.rings():
            for side in (-1, 1):
                a = ring.angle + side * (OUTER_GAP / 2)
                x, y = ring.x + math.cos(a) * ring.radius, ring.y + math.sin(a) * ring.radius
                world.enemy_bullets.append(aimed(LeadShot, x, y, a, 85, self.bullet_damage))

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        pass

    def draw(self, surf):
        if self.state == "dead":
            return
        super().draw(surf)
        for ring in self.rings():
            ring.draw(surf)
        if self.state == "fight" and self.attack == "fans" and self.attack_time < 0.3:
            pygame.draw.circle(surf, DANGER, (int(self.x), int(self.y)), CORE + 3, 1)
