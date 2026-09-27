"""Boss 5: HELIOS, the living forge (level 5) — sprite, pods, solar flares and behaviour."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, FLAME, SPARK
from ..core.pixelart import CharCanvas, outlined, sprite_from_rows
from ..minions.bullets import bullet
from ..obstacles.asteroid import MagmaRock
from .art import HULL_COLORS
from .base import Boss

CORE = 27                        # core sprite radius (55x55 + outline)
RING = 40                        # px from the core's centre to the pods
FORGE_LIGHTS = (((255, 190, 70), (190, 90, 30)), ((255, 130, 50), (170, 50, 20)),
                ((255, 250, 220), (255, 150, 60)))


def _core_rows(damaged):
    """The forge station: armoured sphere, vents, a glowing forge eye (bigger when open)."""
    size = CORE * 2 + 1
    c = CharCanvas(size, size)
    c.circle(CORE, CORE, CORE, "H")
    c.circle(CORE, CORE, CORE - 2, "M")
    c.circle(CORE - 5, CORE - 6, CORE - 11, "L")          # lit upper left
    c.circle(CORE - 7, CORE - 9, 6, "W")
    for i in range(12):                                     # armour seams
        a = math.tau * i / 12
        c.line(int(CORE + math.cos(a) * 12), int(CORE + math.sin(a) * 12),
               int(CORE + math.cos(a) * (CORE - 2)), int(CORE + math.sin(a) * (CORE - 2)), "H")
    for i in range(8):                                      # vents around the rim
        a = math.tau * (i + 0.5) / 8
        c.rect(int(CORE + math.cos(a) * (CORE - 5)) - 1, int(CORE + math.sin(a) * (CORE - 5)) - 1,
               int(CORE + math.cos(a) * (CORE - 5)) + 1, int(CORE + math.sin(a) * (CORE - 5)) + 1,
               "G")
    eye = 13 if damaged else 9
    c.circle(CORE, CORE, eye + 2, "G")
    c.circle(CORE, CORE, eye, "q")
    c.circle(CORE, CORE, eye - 3, "Q")
    c.circle(CORE - 2, CORE - 2, 2, "W")
    if damaged:                                             # cracks
        for x0, y0, x1, y1 in ((6, 20, 16, 26), (40, 8, 32, 18), (44, 36, 36, 30), (16, 44, 22, 36)):
            c.line(x0, y0, x1, y1, "E")
    return outlined(c.rows())


POD_ROWS = (
    "....KKKKK....",
    "..KKHMMMHKK..",
    ".KHMLLLLLMHK.",
    ".KMLWWLLLLMK.",
    "KHMLLGGGLLMHK",
    "KMLLGqQqGLLMK",
    "KMLLGQYQGLLMK",
    "KMLLGqQqGLLMK",
    "KHMLLGGGLLMHK",
    ".KMMLLLLLMMK.",
    ".KHMMGGGMMHK.",
    "..KKKGYGKKK..",
    "....KKKKK....",
)


class Pod:
    """A turret pod: on the ring (its hits count for the core), or detached (own hp)."""

    def __init__(self, boss, index, image, mask, white):
        self.boss, self.index = boss, index
        self.image, self.mask, self.white = image, mask, white
        self.x = self.y = 0.0
        self.hp = 0.0
        self.detached = False
        self.dead = False
        self.flash = 0.0
        self.orbit = math.tau * index / 4
        self.fire_timer = random.uniform(0.5, 1.5)

    @property
    def bound(self):
        return self.image.get_width() / 2 + 1

    @property
    def topleft(self):
        return int(self.x - self.image.get_width() / 2), int(self.y - self.image.get_height() / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        w, h = self.mask.get_size()
        return 0 <= mx < w and 0 <= my < h and self.mask.get_at((mx, my))

    def overlaps(self, ship):
        sx, sy = ship.topleft
        left, top = self.topleft
        return ship.mask.overlap(self.mask, (left - sx, top - sy)) is not None

    def draw(self, surf):
        surf.blit(self.white if self.flash > 0 else self.image, self.topleft)


class Flare:
    """A wall of fire sweeping across the screen with gaps to fly through.
    orient 'h' = a horizontal wall moving down; 'v' = a vertical wall moving sideways."""

    THICK = 5

    def __init__(self, orient, pos, speed, gaps):
        self.orient, self.pos, self.speed, self.gaps = orient, pos, speed, gaps
        self.hit = False
        self.time = 0.0

    @property
    def done(self):
        return self.pos < -10 or self.pos > (LOW_H if self.orient == "h" else LOW_W) + 10

    def update(self, dt):
        self.time += dt
        self.pos += self.speed * dt

    def in_gap(self, v):
        return any(a <= v <= b for a, b in self.gaps)

    def touches(self, ship):
        if self.orient == "h":
            return abs(ship.y - self.pos) < self.THICK + ship.h / 3 and not self.in_gap(ship.x)
        return abs(ship.x - self.pos) < self.THICK + ship.w / 3 and not self.in_gap(ship.y)

    def draw(self, surf):
        length = LOW_W if self.orient == "h" else LOW_H
        flick = int(self.time * 30)
        for v in range(0, length, 2):
            if self.in_gap(v):
                continue
            for layer in range(self.THICK):
                color = FLAME[min(len(FLAME) - 1, layer + (v // 2 + flick) % 2)]
                off = layer - self.THICK // 2
                if self.orient == "h":
                    surf.fill(color, (v, int(self.pos) + off, 2, 1), special_flags=pygame.BLEND_ADD)
                else:
                    surf.fill(color, (int(self.pos) + off, v, 1, 2), special_flags=pygame.BLEND_ADD)


class Helios(Boss):
    """Boss 5. A forge station with 4 turret pods on a slowly spinning ring.

    Phase 1 (calm)    -- the pods fire aimed bursts in turn; every few seconds a SOLAR FLARE
                         (the ring glows orange for 1 s, then a wall of fire with gaps sweeps
                         down the screen)
    Phase 2 (angry)   -- x1.2; the pods DETACH and circle the rocket as separate targets with
                         their own armour (killing one drops coins and ends its attacks);
                         flares + fire rings from the core
    Phase 3 (furious) -- x1.4; the core opens (takes x1.3 damage), flares from both sides and
                         MAGMA RAIN
    The idea: kill the pods first, or burn the core.
    """

    EPITHET = "THE LIVING FORGE"
    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("bursts", 3.0), ("flare", 2.6), ("bursts", 3.0), ("rest", 1.0)),
        (("pods", 3.0), ("flare", 2.6), ("rings", 2.2), ("pods", 2.4), ("rest", 0.8)),
        (("flare2", 2.8), ("rain", 3.0), ("rings", 2.0), ("pods", 2.4), ("flare", 2.4),
         ("rest", 0.5)),
    )
    BURST_INTERVAL, BURST_SHOTS, BURST_GAP, BURST_SPEED = 0.5, 3, 0.08, 120
    POD_INTERVAL, POD_SPEED = 1.0, 110
    RING_INTERVAL, RING_SHOTS, RING_SPEED = 0.7, 16, 72
    FLARE_WARN, FLARE_SPEED, FLARE_X, GAP = 1.0, 85, 2.5, 46
    POD_HP = 0.06                  # a detached pod's armour, share of the boss's max hp
    CORE_OPEN = 1.3                # phase 3: damage multiplier on the core
    RAIN_INTERVAL = 0.7
    # Phase 1 aimed damage per second at a rocket sitting still: every burst bullet plus one
    # flare wall (worth FLARE_X bullets) per cycle.
    AIMED_RATE = ((3.0 + 3.0) / BURST_INTERVAL * BURST_SHOTS + FLARE_X) / (3.0 + 2.6 + 3.0 + 1.0)

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cores = [sprite_from_rows(_core_rows(damaged=phase == 2),
                                      {**HULL_COLORS, "Q": light, "q": dark})
                     for phase, (light, dark) in enumerate(FORGE_LIGHTS)]
            pod = sprite_from_rows(POD_ROWS, {**HULL_COLORS, "Q": (255, 190, 70),
                                              "q": (190, 90, 30)})
            mask = pygame.mask.from_surface(pod)
            white = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
            cls._sprites = cores, (pod, mask, white)
        return cls._sprites

    def __init__(self, spec):
        cores, pod_sprite = self.prebuild()
        super().__init__(spec, list(cores), {}, [(CORE - 9, 4), (CORE + 11, 4)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.pods = [Pod(self, i, *pod_sprite) for i in range(4)]
        self.home_y = 26 + self.h / 2
        self.ring_angle = 0.0
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.pod_turn = 0
        self.flares = []
        self.flared = False
        self.rain_timer = 0.0
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        return [self] + [p for p in self.pods if not p.dead]

    def hit_part(self, part, amount, flash=True):
        if part is self:
            self.damage(amount * (self.CORE_OPEN if self.phase == 2 else 1.0), flash)
        elif part.detached:
            if self.state == "fight" and self.roar <= 0:
                part.hp -= amount
                part.flash = 0.05 if flash else part.flash
        else:
            part.flash = 0.05 if flash else part.flash
            self.damage(amount, flash)

    def collides_with(self, ship):
        return super().collides_with(ship) or any(
            p.detached and not p.dead and p.overlaps(ship) for p in self.pods)

    @property
    def warning(self):
        """The ring glows before a flare."""
        name, _ = self._pattern()
        return name in ("flare", "flare2") and self.attack_time < self.FLARE_WARN

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        if self.phase == 1:
            for pod in self.pods:
                pod.detached = True
                pod.hp = self.max_hp * self.POD_HP

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    def _layout(self):
        for pod in self.pods:
            if not pod.detached:
                a = self.ring_angle + math.tau * pod.index / 4
                pod.x, pod.y = self.x + math.cos(a) * RING, self.y + math.sin(a) * RING

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        for pod in self.pods:
            pod.flash = max(0.0, pod.flash - dt)
            if pod.detached and not pod.dead and pod.hp <= 0:
                pod.dead = True
                world.explosion(pod.x, pod.y, size=1.2)
                world.drop_coins(pod.x, pod.y, 5)
                world.audio.play("boss_explode")
        for flare in self.flares:
            flare.update(dt)
            if not flare.hit and self.fighting and world.ship.alive and flare.touches(world.ship):
                flare.hit = True
                world.hurt_ship(self.bullet_damage * self.FLARE_X, world.ship.x, flare.pos)
        self.flares = [f for f in self.flares if not f.done]
        if self.state != "fight":
            self.flares.clear()
        result = super().update(dt, world)
        self._layout()
        return result

    def enter(self, k):
        super().enter(k)
        self._layout()

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        self.move_time += dt * rate
        self.ring_angle += 0.5 * dt * rate
        swing = LOW_W / 2 - 64
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.35) * swing
        self.y = self.home_y + math.sin(self.move_time * 0.9) * 4
        self._move_pods(dt, world, rate)
        name, duration = self._pattern()
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.flared = False
            return
        if name in ("flare", "flare2"):
            if self.attack_time >= self.FLARE_WARN and not self.flared:
                self.flared = True
                self._flare(world, both_sides=name == "flare2")
            return
        self.fire_timer -= dt * rate
        if name == "rain":
            self.rain_timer -= dt * rate
            if self.rain_timer <= 0:
                self.rain_timer = self.RAIN_INTERVAL
                self._magma(world)
        if self.fire_timer > 0 or name in ("rest", "rain"):
            return
        getattr(self, "_" + name)(world)

    def _move_pods(self, dt, world, rate):
        """Detached pods circle the rocket (upper arc) and fire now and then."""
        ship = world.ship
        for pod in self.pods:
            if not pod.detached or pod.dead:
                continue
            pod.orbit += 0.6 * dt * rate
            a = math.pi + math.pi * (0.5 + 0.5 * math.sin(pod.orbit + pod.index * 1.6))
            tx = min(LOW_W - 12, max(12, ship.x + math.cos(a) * 90))
            ty = min(ship.y - 50, max(30, ship.y + math.sin(a) * 90))
            pod.x += (tx - pod.x) * min(1.0, 1.8 * dt)
            pod.y += (ty - pod.y) * min(1.0, 1.8 * dt)

    # --- attacks ------------------------------------------------------------------------
    def _aim(self, world, x, y):
        return math.atan2(world.ship.y - y, world.ship.x - x)

    def _bursts(self, world):
        """One attached pod fires a quick aimed burst."""
        self.fire_timer = self.BURST_INTERVAL
        alive = [p for p in self.pods if not p.dead]
        if not alive:
            return
        pod = alive[self.pod_turn % len(alive)]
        self.pod_turn += 1
        aim = self._aim(world, pod.x, pod.y)
        for i in range(self.BURST_SHOTS):              # a line of bullets along one aim
            b = bullet(pod.x, pod.y, aim, self.BURST_SPEED - i * 14, self.bullet_damage)
            world.enemy_bullets.append(b)
        world.fire.burst(pod.x, pod.y, 4, 40, 0.12, SPARK, size=(1, 1))
        world.audio.play("enemy_shot")

    def _pods(self, world):
        """Every detached pod fires one aimed shot."""
        self.fire_timer = self.POD_INTERVAL
        for pod in self.pods:
            if pod.detached and not pod.dead:
                world.enemy_bullets.append(bullet(pod.x, pod.y, self._aim(world, pod.x, pod.y),
                                                  self.POD_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _rings(self, world):
        self.fire_timer = self.RING_INTERVAL
        offset = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            world.enemy_bullets.append(bullet(self.x, self.y, offset + math.tau * i / self.RING_SHOTS,
                                              self.RING_SPEED, self.bullet_damage))

    def _gaps(self, length, count):
        edges = sorted(random.uniform(30, length - 30 - self.GAP) for _ in range(count))
        return [(e, e + self.GAP) for e in edges]

    def _flare(self, world, both_sides=False):
        world.audio.play("flare")
        world.shake.add(0.3)
        if both_sides:
            self.flares.append(Flare("v", 0, self.FLARE_SPEED, self._gaps(LOW_H, 1)))
            self.flares.append(Flare("v", LOW_W, -self.FLARE_SPEED, self._gaps(LOW_H, 1)))
        else:
            gaps = self._gaps(LOW_W, random.choice((1, 2)))
            self.flares.append(Flare("h", self.y + self.h / 2, self.FLARE_SPEED, gaps))

    def _magma(self, world):
        art = world.library.pick(6, 11, ("magma",))
        world.asteroids.append(MagmaRock(art, random.uniform(20, LOW_W - 20), -art.size / 2,
                                         random.uniform(-15, 15), random.uniform(80, 120),
                                         random.uniform(-2, 2),
                                         hp_scale=world.level.difficulty.rock_hp))

    # --- draw ---------------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        ring_color = FLAME[2] if self.warning and int(self.attack_time * 10) % 2 == 0 else (62, 58, 74)
        if any(not p.detached for p in self.pods):
            pygame.draw.circle(surf, (24, 20, 34), (int(self.x), int(self.y)), RING + 2, 1)
            pygame.draw.circle(surf, ring_color, (int(self.x), int(self.y)), RING, 2)
        elif self.warning:
            pygame.draw.circle(surf, FLAME[2], (int(self.x), int(self.y)), CORE + 6, 1)
        super().draw(surf)
        for pod in self.pods:
            if not pod.dead:
                pod.draw(surf)
                if pod.detached and pod.hp < self.max_hp * self.POD_HP * 0.4:
                    surf.fill(DANGER, (int(pod.x), int(pod.y) - 8, 1, 1))
        for flare in self.flares:
            flare.draw(surf)
