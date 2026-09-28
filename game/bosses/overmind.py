"""Galaxy boss: THE OVERMIND, heart of the Swarm (level 10) — hive wall, glands, heart,
tentacle and bio-beam. Its phases echo the bosses of the galaxy (Gunship fans, the
Leviathan's lunge, the Mothership's beam): the Swarm learned from every fight."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, HEAL, HIVE_FLESH, HIVE_VEIN
from ..core.pixelart import CharCanvas, dither, outlined, sprite_from_rows
from ..minions.bullets import bullet
from ..minions.swarm import SporePod, larva_flock
from .base import Boss

WALL_H = 64                      # the hive wall covers the top of the screen (phase 1)
GLAND_X = (58, 124, 196, 262)    # gland positions along the wall's lower edge
HEART = 24                       # heart sprite radius
HEART_LIGHTS = (((150, 240, 90), (60, 150, 50)), ((150, 240, 90), (60, 150, 50)),
                ((255, 200, 70), (190, 100, 30)), ((255, 90, 90), (170, 30, 40)))
COLORS = {"K": (16, 6, 14), "H": HIVE_FLESH[0], "M": HIVE_FLESH[1], "L": HIVE_FLESH[2],
          "W": HIVE_FLESH[3], "w": HIVE_FLESH[4], "V": HIVE_VEIN, "E": (30, 10, 22)}

GLAND_ROWS = (
    "....KKKKK....",
    "..KKLLWLLKK..",
    ".KLWwwWWWLLK.",
    ".KLwWVVVWWLK.",
    "KLWWVQQQVWWLK",
    "KLWVQqqqQVWLK",
    "KLWVQqYqQVWLK",
    "KLWVQqqqQVWLK",
    "KLWWVQQQVWWLK",
    ".KLWWVVVWWLK.",
    ".KMLLWWWLLMK.",
    "..KKMLLLMKK..",
    "....KKKKK....",
)


def _heart_rows(phase):
    """The heart: a lumpy muscle with ventricles, veins and an eye that opens with rage."""
    size = HEART * 2 + 1
    c = CharCanvas(size, size)
    c.circle(HEART, HEART + 2, HEART - 2, "M")
    c.circle(HEART - 9, HEART - 6, 12, "M")                   # two ventricle lobes
    c.circle(HEART + 9, HEART - 6, 12, "M")
    c.circle(HEART - 10, HEART - 8, 8, "L")
    c.circle(HEART + 8, HEART - 8, 8, "L")
    c.circle(HEART - 12, HEART - 11, 3, "W")
    c.circle(HEART + 6, HEART - 11, 3, "W")
    c.rect(HEART - 3, 1, HEART + 3, 8, "H")                   # the aorta (to the hive)
    c.rect(HEART - 1, 1, HEART + 1, 8, "L")
    for x0, y0, x1, y1 in ((HEART - 16, HEART + 2, HEART - 6, HEART + 16),
                           (HEART + 16, HEART + 2, HEART + 6, HEART + 16),
                           (HEART - 4, HEART - 14, HEART - 8, HEART + 2),
                           (HEART + 4, HEART - 14, HEART + 8, HEART + 2)):
        c.line(x0, y0, x1, y1, "V")                           # glowing veins
    eye = 4 + 2 * phase
    c.circle(HEART, HEART + 8, eye + 2, "E")
    c.circle(HEART, HEART + 8, eye, "q")
    c.circle(HEART, HEART + 8, max(1, eye - 3), "Q")
    c.set(HEART - 1, HEART + 7, "w")
    if phase == 3:                                            # torn open
        for x0, y0, x1, y1 in ((HEART - 18, HEART - 4, HEART - 10, HEART + 4),
                               (HEART + 14, HEART + 10, HEART + 20, HEART + 2)):
            c.line(x0, y0, x1, y1, "E")
    return outlined(c.rows())


def _wall_surface():
    """The hive wall (phase 1): dithered flesh, a wavy lower edge, veins."""
    surf = pygame.Surface((LOW_W, WALL_H), pygame.SRCALPHA)
    tones = len(HIVE_FLESH)
    for x in range(LOW_W):
        edge = WALL_H - 8 + math.sin(x * 0.09) * 4 + math.sin(x * 0.23) * 2
        for y in range(WALL_H):
            if y > edge:
                continue
            shade = 0.3 + 0.55 * (y / WALL_H) + 0.2 * math.sin(x * 0.3 + y * 0.2) * math.sin(y * 0.4)
            color = HIVE_FLESH[dither(min(0.99, shade), x, y, tones)]
            if y > edge - 2:
                color = (16, 6, 14)
            surf.set_at((x, y), color)
    rng = random.Random(10)
    for i in range(9):                                        # veins across the wall
        x, y = i * 38 + 12, 4
        for _ in range(40):
            x += rng.choice((-1, 0, 1))
            y += 1
            if 0 <= x < LOW_W and y < WALL_H - 10:
                surf.set_at((x, y), (70, 120, 60))
    return surf


class Gland:
    """A gland on the hive wall: its own armour, fires spit; its hits count for the boss."""

    def __init__(self, x, y, image, mask, white):
        self.x, self.y = float(x), float(y)
        self.image, self.mask, self.white = image, mask, white
        self.hp = 0.0
        self.flash = 0.0
        self.dead = False

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

    def draw(self, surf, beat):
        if self.dead:                                         # a bleeding hole
            pygame.draw.circle(surf, (16, 6, 14), (int(self.x), int(self.y)), 5)
            pygame.draw.circle(surf, HIVE_FLESH[0], (int(self.x), int(self.y)), 5, 1)
            return
        image = self.white if self.flash > 0 else self.image
        if beat > 0.5:                                        # swells with the heartbeat
            w, h = image.get_size()
            image = pygame.transform.scale(image, (w + 2, h + 2))
        surf.blit(image, image.get_rect(center=(int(self.x), int(self.y))))


class Tentacle:
    """The heart's lash: locks onto the rocket, lunges to that spot, pulls back."""

    SPEED = 420
    WARN = 1.1

    def __init__(self):
        self.state = 0            # 0 idle, 1 locking on, 2 lunging, 3 holding, 4 retracting
        self.length = 0.0
        self.reach = 0.0
        self.angle = math.pi / 2
        self.target = None
        self.time = 0.0

    def points(self, x, y):
        """Segment centres from the heart's mouth to the tip (with a wriggle)."""
        n = max(1, int(self.length / 6))
        out = []
        nx, ny = -math.sin(self.angle), math.cos(self.angle)
        for i in range(1, n + 1):
            d = self.length * i / n
            wig = math.sin(self.time * 14 - i * 0.8) * 3 * (i / n)
            out.append((x + math.cos(self.angle) * d + nx * wig,
                        y + math.sin(self.angle) * d + ny * wig, 5 - 3 * i / n))
        return out


class Overmind(Boss):
    """Galaxy boss. Four phases:

    Phase 1 (the hive)  -- a flesh WALL covers the top of the screen; the heart beats behind
                           it. Four GLANDS fire spit and drop spore pods; kill all four and the
                           wall tears open (their hits count for the boss).
    Phase 2 (the heart) -- the heart descends: Gunship-style FANS, larva swarms, rings
    Phase 3 (angry)     -- x1.2; the TENTACLE: locks onto the rocket (red crosshair), lashes
                           out to that spot (the Leviathan's lunge), spore pods
    Phase 4 (furious)   -- x1.4; the BIO-BEAM: a warning line, then a column of acid down from
                           the heart as it tracks the rocket (the Mothership's beam), spirals
    """

    EPITHET = "HEART OF THE SWARM"
    PHASES = 4
    RAGE = (1.0, 1.0, 1.2, 1.4)
    PATTERNS = (
        (("spit", 3.0), ("spores", 1.2), ("spit", 2.4), ("larvae", 0.8), ("rest", 1.0)),
        (("fans", 3.0), ("larvae", 0.8), ("rings", 2.2), ("rest", 0.8)),
        (("lash", 3.0), ("fans", 2.4), ("spores", 1.0), ("lash", 3.0), ("rings", 2.0),
         ("rest", 0.6)),
        (("beam", 3.6), ("spiral", 2.6), ("lash", 2.8), ("larvae", 0.6), ("beam", 3.2),
         ("rest", 0.5)),
    )
    SPIT_INTERVAL, SPIT_SPEED, SPIT_GAP = 0.45, 105, 0.22
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.55, 115, 0.2
    RING_INTERVAL, RING_SHOTS, RING_SPEED = 0.7, 14, 70
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.11, 85, 2.3
    BEAM_WARN, BEAM_HALF, BEAM_DAMAGE_X = 1.0, 5, 0.12       # beam: x bullet damage per frame
    LASH_X = 3.0                                              # a lash hit = 3 bullets
    LARVAE = 7
    # Phase 1-2 aimed damage per second at a rocket sitting still: the centre shot of every
    # spit / fan, and a ring bullet now and then.
    AIMED_RATE = (3.0 / FAN_INTERVAL + 2.2 / RING_INTERVAL * 0.3) / (3.0 + 0.8 + 2.2 + 0.8)

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            hearts = [sprite_from_rows(_heart_rows(phase), {**COLORS, "Q": light, "q": dark})
                      for phase, (light, dark) in enumerate(HEART_LIGHTS)]
            gland = sprite_from_rows(GLAND_ROWS, {**COLORS, "Q": HIVE_VEIN, "q": (60, 150, 50),
                                                  "Y": (230, 255, 200)})
            mask = pygame.mask.from_surface(gland)
            white = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
            cls._sprites = hearts, (gland, mask, white), _wall_surface()
        return cls._sprites

    def __init__(self, spec):
        hearts, gland, self.wall = self.prebuild()
        super().__init__(spec, list(hearts), {"mouth": (HEART, HEART * 2 - 4)}, [(HEART, 2)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.wall_y = -WALL_H                     # the wall slides down on entry
        self.tear = 0.0                           # 0..1: the wall tears open (phase 2)
        self.hidden_y = 22.0                      # the heart behind the wall
        self.home_y = 30 + self.h / 2
        self.glands = [Gland(x, 0, *gland) for x in GLAND_X]
        for g in self.glands:
            g.hp = self.max_hp / self.PHASES / len(self.glands)
        self.tentacle = Tentacle()
        self.move_time = 0.0
        self.beat = 0.0                           # heartbeat pulse 0..1
        self.beat_timer = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.turn = 0
        self.spiral_angle = 0.0
        self.beam = 0                             # 0 off, 1 warning line, 2 firing
        self.pending_bursts = []                  # glands killed since the last update
        self.y = self.hidden_y
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    @property
    def hive(self):
        return self.phase == 0

    def parts(self):
        if self.hive:
            return [g for g in self.glands if not g.dead]
        return [self]

    def hit_part(self, part, amount, flash=True, source=None):
        if part is self:
            if not self.hive:
                self.damage(amount, flash)
            return
        if part.dead or self.state != "fight" or self.roar > 0:
            return
        amount = min(amount, part.hp)
        part.hp -= amount
        part.flash = 0.05 if flash else part.flash
        if part.hp <= 1e-6:
            part.dead = True
            self.pending_bursts.append(part)
        if all(g.dead for g in self.glands):          # the last gland: the wall tears
            self.damage(self.hp - self.max_hp * (self.PHASES - 1) / self.PHASES + 1, flash)
        else:
            self.damage(amount, flash)

    def contains(self, px, py):
        return not self.hive and super().contains(px, py)

    def collides_with(self, ship):
        if self.hive:
            return any(not g.dead and g.overlaps(ship) for g in self.glands)
        if self.tentacle.state >= 2 and self._lash_touches(ship):
            return True
        return super().collides_with(ship)

    @property
    def contact_damage(self):
        if self.tentacle.state >= 2:
            return self.bullet_damage * self.LASH_X
        return super().contact_damage

    def _lash_touches(self, ship):
        mx, my = self.point(*self.muzzles["mouth"])
        return any(math.hypot(ship.x - x, ship.y - y) < r + ship.w * 0.3
                   for x, y, r in self.tentacle.points(mx, my))

    @property
    def phase_marks(self):
        return [i / self.PHASES for i in range(1, self.PHASES)]

    @property
    def lock_target(self):
        """The red crosshair while the tentacle locks on (drawn by the boss)."""
        return self.tentacle.target if self.tentacle.state == 1 else None

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.beam = 0
        self.tentacle.state = 0
        self.tentacle.length = 0.0

    def _layout(self):
        for g in self.glands:
            g.y = self.wall_y + WALL_H - 10 + math.sin(g.x * 0.09) * 3

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        for g in self.glands:
            g.flash = max(0.0, g.flash - dt)
        self._heartbeat(dt, world)
        if self.phase >= 1 and self.tear < 1 and self.state == "fight":
            self.tear = min(1.0, self.tear + dt / 1.6)        # the wall tears, the heart drops
            self.y = self.hidden_y + (self.home_y - self.hidden_y) * (1 - (1 - self.tear) ** 2)
            if random.random() < 20 * dt:
                x = random.uniform(0, LOW_W)
                world.fire.burst(x, random.uniform(10, WALL_H), 4, 60, 0.4, HEAL, size=(1, 2))
        result = super().update(dt, world)
        self._layout()
        for g in self.pending_bursts:
            world.explosion(g.x, g.y, size=1.0)
            world.fire.burst(g.x, g.y, 20, 90, 0.5, HEAL, size=(1, 2))
            world.drop_coins(g.x, g.y, 4)
            world.audio.play("spore")
            world.shake.add(0.2)
        self.pending_bursts.clear()
        if self.state != "fight":
            self.beam = 0
            self.tentacle.state = 0
            self.tentacle.length = 0.0
        return result

    def _heartbeat(self, dt, world):
        self.beat = max(0.0, self.beat - dt * 3)
        if self.state not in ("enter", "fight"):
            return
        self.beat_timer -= dt
        if self.beat_timer <= 0:
            self.beat_timer = 1.4 / self.RAGE[self.phase]
            self.beat = 1.0
            if self.state == "fight":
                world.audio.play("heartbeat")

    def enter(self, k):
        self.wall_y = -WALL_H + WALL_H * (1 - (1 - k) ** 3)
        self.y = self.hidden_y
        self._layout()

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        name, duration = self._pattern()
        self.move_time += dt * rate * (0.3 if name == "beam" and self.beam == 2 else 1.0)
        if not self.hive and self.tear >= 1:
            target = LOW_W / 2 + math.sin(self.move_time * 0.4) * 70
            if name == "beam":                                # tracks the rocket, slowly
                target = min(LOW_W - 60, max(60, world.ship.x))
                self.x += (target - self.x) * min(1.0, (0.5 if self.beam == 2 else 2.0) * dt)
            else:
                self.x += (target - self.x) * min(1.0, 2.0 * dt)
            self.y = self.home_y + math.sin(self.move_time * 1.1) * 4
        self.tentacle.time += dt
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.beam = 0
            self.tentacle.state = 0
            self.tentacle.length = 0.0
            return
        if name == "beam":
            self._beam(dt, world, duration)
            return
        if name == "lash":
            self._lash(dt, world)
            return
        self.fire_timer -= dt * rate
        if name == "spiral":
            self.spiral_angle += self.SPIRAL_TURN * dt * rate
        if self.fire_timer > 0 or name == "rest":
            return
        getattr(self, "_" + name)(world)

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    # --- attacks ------------------------------------------------------------------------
    def _aim(self, world, x, y):
        return math.atan2(world.ship.y - y, world.ship.x - x)

    def _mouth(self):
        return self.point(*self.muzzles["mouth"])

    def _spit(self, world):
        """One gland in turn spits a 3-way aimed spread."""
        self.fire_timer = self.SPIT_INTERVAL
        alive = [g for g in self.glands if not g.dead]
        if not alive:
            return
        g = alive[self.turn % len(alive)]
        self.turn += 1
        aim = self._aim(world, g.x, g.y)
        for i in (-1, 0, 1):
            world.enemy_bullets.append(bullet(g.x, g.y + 4, aim + i * self.SPIT_GAP,
                                              self.SPIT_SPEED, self.bullet_damage))
        world.fire.burst(g.x, g.y + 4, 5, 40, 0.2, HEAL, size=(1, 1))
        world.audio.play("enemy_shot")

    def _spores(self, world):
        """Spore pods drop out of the glands (or the heart)."""
        self.fire_timer = 99                     # once per pattern slot
        sources = ([(g.x, g.y) for g in self.glands if not g.dead] if self.hive
                   else [self._mouth()])
        for x, y in random.sample(sources, min(2, len(sources))):
            pod = SporePod(x + random.uniform(-10, 10))
            pod.y = y + 6
            world.spawn_enemies([pod])

    def _larvae(self, world):
        self.fire_timer = 99
        x, y = self._mouth() if not self.hive else (random.choice(GLAND_X), self.wall_y + WALL_H)
        flock = larva_flock(world, self.LARVAE)
        for larva in flock:
            larva.x, larva.y = x + random.uniform(-12, 12), y + random.uniform(0, 8)
        world.spawn_enemies(flock)
        world.fire.burst(x, y, 12, 60, 0.4, HEAL, size=(1, 2))
        world.audio.play("spore")

    def _fans(self, world):
        """The Gunship's fan, grown in flesh: 5 shots, the middle one aimed."""
        self.fire_timer = self.FAN_INTERVAL
        mx, my = self._mouth()
        aim = self._aim(world, mx, my)
        for i in range(-2, 3):
            world.enemy_bullets.append(bullet(mx, my, aim + i * self.FAN_GAP, self.FAN_SPEED,
                                              self.bullet_damage))
        world.audio.play("enemy_shot")

    def _rings(self, world):
        self.fire_timer = self.RING_INTERVAL
        offset = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            world.enemy_bullets.append(bullet(self.x, self.y, offset + math.tau * i / self.RING_SHOTS,
                                              self.RING_SPEED, self.bullet_damage))

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        mx, my = self._mouth()
        for i in range(4):
            world.enemy_bullets.append(bullet(mx, my, self.spiral_angle + math.tau * i / 4,
                                              self.SPIRAL_SPEED, self.bullet_damage))

    def _lash(self, dt, world):
        """The Leviathan's lunge as a tentacle: lock on, lash out, pull back."""
        t, ship = self.tentacle, world.ship
        mx, my = self._mouth()
        if t.state == 0:
            t.state = 1
            world.audio.play("lock_on")
            world.telegraph()
        if t.state == 1:
            if ship.alive and self.attack_time < t.WARN - 0.25:
                t.target = (ship.x, ship.y)                   # frozen for the last moment
            if self.attack_time >= t.WARN and t.target:
                tx, ty = t.target
                t.angle = math.atan2(ty - my, tx - mx)
                t.reach = math.hypot(tx - mx, ty - my) + 30
                t.state = 2
                world.shake.add(0.3)
                world.audio.play("dive")
        elif t.state == 2:
            t.length = min(t.reach, t.length + t.SPEED * dt)
            if t.length >= t.reach:
                t.state, t.hold = 3, 0.25
                tip = t.points(mx, my)[-1]
                world.fire.burst(tip[0], tip[1], 10, 80, 0.3, HEAL, size=(1, 2))
        elif t.state == 3:
            t.hold -= dt
            if t.hold <= 0:
                t.state = 4
        elif t.state == 4:
            t.length = max(0.0, t.length - t.SPEED * 0.6 * dt)
            if t.length <= 0:
                t.state = 5                                   # done until the next slot

    def _beam(self, dt, world, duration):
        """The Mothership's beam, now acid: a warning line, then a column down."""
        if self.attack_time < self.BEAM_WARN:
            self.beam = 1
            return
        if self.attack_time > duration - 0.2:
            self.beam = 0
            return
        if self.beam != 2:
            world.shake.add(0.35)
            world.audio.play("beam")
        self.beam = 2
        bx, by = self._mouth()
        ship = world.ship
        if random.random() < 30 * dt:
            world.fire.emit(bx + random.uniform(-4, 4), LOW_H - 1, random.uniform(-60, 60),
                            -random.uniform(40, 90), 0.3, HEAL)
        if ship.alive and ship.y > by and abs(ship.x - bx) < self.BEAM_HALF + ship.w * 0.35:
            world.hurt_ship(self.bullet_damage * self.BEAM_DAMAGE_X, bx, ship.y)

    # --- draw ---------------------------------------------------------------------------
    def _emit_vents(self, dt, world):
        """No engines: the heart drips instead."""
        if not self.hive and random.random() < 6 * dt:
            x, y = self.random_hull_point()
            world.smoke.emit(x, y, 0, random.uniform(20, 40), 0.6,
                             [HIVE_VEIN, (60, 150, 50), (30, 70, 30)], size=1)

    def draw(self, surf):
        if self.state == "dead":
            return
        beat = self.beat
        if not self.hive:
            self._draw_tentacle(surf)
            super().draw(surf)
            if beat > 0.6 and self.state == "fight":        # the heart swells on the beat
                pygame.draw.circle(surf, HIVE_VEIN, (int(self.x), int(self.y) + 8),
                                   HEART + 2 + int(beat * 3), 1)
            self._draw_beam(surf)
        else:
            # behind the wall: a dark heart silhouette that glows with each beat
            glow = int(40 + 80 * beat)
            pygame.draw.circle(surf, (glow, glow // 4, glow // 3),
                               (int(self.x), int(self.wall_y + 30)), 26)
        self._draw_wall(surf, beat)
        if self.hive:
            for g in self.glands:
                g.draw(surf, beat)
        if self.lock_target and int(self.attack_time * 10) % 2 == 0:
            tx, ty = map(int, self.lock_target)
            pygame.draw.circle(surf, DANGER, (tx, ty), 9, 1)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pygame.draw.line(surf, DANGER, (tx + dx * 6, ty + dy * 6), (tx + dx * 12, ty + dy * 12))

    def _draw_wall(self, surf, beat):
        if self.tear >= 1:
            return
        y = int(self.wall_y)
        if self.tear <= 0:
            surf.blit(self.wall, (0, y))
            if beat > 0.3:                                    # veins light up on the beat
                for g in self.glands:
                    if not g.dead:
                        pygame.draw.line(surf, HIVE_VEIN, (int(self.x), y + 30),
                                         (int(g.x), int(g.y) - 6))
            return
        # tearing: the two halves pull away to the sides and up
        half = LOW_W // 2
        shift = int(self.tear * (half + 10))
        lift = int(self.tear * self.tear * WALL_H)
        surf.blit(self.wall, (-shift, y - lift), (0, 0, half, WALL_H))
        surf.blit(self.wall, (half + shift, y - lift), (half, 0, half, WALL_H))
        for i in range(6):                                    # strands of flesh across the gap
            sx = half - shift + i * 3
            ex = half + shift - i * 3
            sag = int(20 * (1 - self.tear)) + i * 2
            if ex > sx:
                pygame.draw.line(surf, HIVE_FLESH[2], (sx, y + 10 + i * 7 - lift),
                                 ((sx + ex) // 2, y + 10 + i * 7 + sag - lift))
                pygame.draw.line(surf, HIVE_FLESH[2], ((sx + ex) // 2, y + 10 + i * 7 + sag - lift),
                                 (ex, y + 10 + i * 7 - lift))

    def _draw_tentacle(self, surf):
        t = self.tentacle
        if t.length <= 0:
            return
        mx, my = self._mouth()
        for i, (x, y, r) in enumerate(t.points(mx, my)):
            color = HIVE_FLESH[3] if i % 2 else HIVE_FLESH[2]
            pygame.draw.circle(surf, (16, 6, 14), (int(x), int(y)), int(r) + 1)
            pygame.draw.circle(surf, color, (int(x), int(y)), int(r))
            if i % 3 == 0:
                surf.fill(HIVE_VEIN, (int(x), int(y), 1, 1))

    def _draw_beam(self, surf):
        if self.roar > 0 or not self.beam or self.state != "fight":
            return
        bx, by = map(int, self._mouth())
        if self.beam == 1:
            if int(self.attack_time * 12) % 2 == 0:
                pygame.draw.line(surf, DANGER, (bx, by), (bx, surf.get_height()))
            return
        wobble = int(self.attack_time * 30) % 2
        h = surf.get_height() - by
        half = self.BEAM_HALF + wobble
        surf.fill(HEAL[3], (bx - half - 1, by, 2 * half + 3, h))
        surf.fill(HEAL[2], (bx - half + 1, by, 2 * half - 1, h))
        surf.fill(HEAL[1], (bx - 1, by, 3, h))
        surf.fill(HEAL[0], (bx, by, 1, h))
        pygame.draw.circle(surf, HEAL[1], (bx, by), half + 2)

