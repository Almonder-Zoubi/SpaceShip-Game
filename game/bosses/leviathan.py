"""Boss 4: LEVIATHAN, the final boss — a segmented space serpent (3 phases, dive attacks).

Unlike the other bosses it is not one sprite: a head and a chain of armour plates that
follow the head's trail. Every piece is a weapon target (parts()); the head is the weak spot.
"""
import math
import random
from collections import deque

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, FLAME_LEAN, ICE_SHARDS
from ..core.pixelart import CharCanvas, mirrored, outlined, rotate_pixel_art, sprite_from_rows
from ..minions.bullets import bullet
from .art import HULL_COLORS
from .base import Boss

# Colours: dark teal scales, pale bone horns and fangs; the glow ("Q"/"q") changes per phase.
LEVIATHAN_COLORS = {
    **HULL_COLORS,
    "H": (22, 52, 70), "M": (36, 92, 110), "L": (72, 150, 160), "W": (214, 236, 230),
    "B": (236, 226, 196), "e": (120, 20, 40),
}
LEVIATHAN_LIGHTS = (   # icy cyan -> angry orange -> furious red
    ((150, 255, 240), (40, 150, 170)),
    ((255, 176, 60), (176, 84, 20)),
    ((255, 64, 64), (150, 20, 34)),
)
BODY_RADII = (6, 6, 6, 6, 5, 5, 5, 4, 4, 4, 3)     # plates from the neck to the tail
HEAD_FRAMES = 16                                   # rotation steps of the head
HEAD_MOUTH = 10                                    # px from the head's centre to the mouth


def _head_half(damaged):
    """Left half of the head, snout pointing down (the way it swims when the frame is 0)."""
    c = CharCanvas(11, 22)
    c.poly([(11, 1), (4, 3), (0, 8), (1, 14), (5, 19), (8, 22), (11, 22)], "M")
    c.line(4, 3, 0, 8, "L")
    c.line(11, 1, 4, 3, "L")
    c.line(1, 9, 1, 13, "H")
    c.line(2, 14, 6, 19, "H")
    c.line(3, 4, 0, 0, "B")                              # swept-back horn
    c.set(1, 1, "W")
    c.rect(9, 1, 10, 13, "L")                            # armoured ridge down the skull
    c.set(10, 2, "W")
    for y in (4, 8, 12):
        c.line(5, y, 8, y + 1, "H")                      # scale rows
    c.rect(4, 10, 6, 12, "Q")                            # glowing eye
    c.set(5, 11, "W")
    c.set(6, 10, "q")
    c.rect(9, 16, 10, 21, "e")                           # open jaw
    c.set(8, 19, "B")                                    # fangs
    c.set(9, 21, "B")
    if damaged:
        c.line(3, 5, 6, 8, "K")
        c.line(7, 13, 5, 16, "K")
        c.set(4, 6, "V")
    return c.rows()


def _plate_half(r, damaged, tail=False):
    """Left half of a round armour plate with a side spike and a glowing spine light."""
    c = CharCanvas(r + 3, 2 * r + 3)
    cy = r + 1
    c.circle(r + 3, cy, r, "M")
    c.circle(r + 2, cy - 1, max(1, r - 2), "L")          # lit dome
    c.line(r + 3 - r, cy + r // 2, r + 2, cy + r, "H")   # shadowed underside
    c.line(0, cy, 2, cy, "B")                            # side spike
    c.rect(r + 1, cy - 1, r + 2, cy + 1, "Q")            # spine light
    c.set(r + 2, cy - 1, "q")
    if tail:
        c.rect(r + 1, cy + 1, r + 2, 2 * r + 2, "B")     # stinger
    if damaged and r >= 5:
        c.line(r - 1, cy - 3, r + 1, cy, "K")
    return c.rows()


def _colors(phase):
    light, dark = LEVIATHAN_LIGHTS[phase]
    return {**LEVIATHAN_COLORS, "Q": light, "q": dark}


def _variants(image):
    """(image, mask, white flash, red roar) for one sprite."""
    mask = pygame.mask.from_surface(image)
    return (image, mask, mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0)),
            mask.to_surface(setcolor=DANGER, unsetcolor=(0, 0, 0, 0)))


_SPRITES = {}


def leviathan_sprites():
    """Built once: {"head": [phase][frame] -> variants, "plates": [phase][i] -> variants}."""
    if not _SPRITES:
        heads, plates = [], []
        for phase in range(3):
            colors = _colors(phase)
            rows = outlined(mirrored(_head_half(damaged=phase == 2)))
            heads.append([_variants(rotate_pixel_art(rows, colors, 360 * i / HEAD_FRAMES))
                          for i in range(HEAD_FRAMES)])
            last = len(BODY_RADII) - 1
            plates.append([_variants(sprite_from_rows(
                outlined(mirrored(_plate_half(r, phase == 2, tail=i == last))), colors))
                for i, r in enumerate(BODY_RADII)])
        _SPRITES.update(head=heads, plates=plates)
    return _SPRITES


class Segment:
    """One piece of the serpent (head or plate): a weapon target at its own position.
    Hits on it are forwarded to the boss (Boss.hit_part)."""

    def __init__(self, boss, radius, head=False):
        self.boss, self.radius, self.head = boss, radius, head
        self.x = self.y = 0.0
        self.sprite = None                  # (image, mask, white, red), set by the boss

    @property
    def bound(self):
        w, h = self.sprite[0].get_size()
        return max(w, h) / 2 + 1

    @property
    def topleft(self):
        w, h = self.sprite[0].get_size()
        return int(self.x - w / 2), int(self.y - h / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mask = self.sprite[1]
        mx, my = int(px) - left, int(py) - top
        w, h = mask.get_size()
        return 0 <= mx < w and 0 <= my < h and mask.get_at((mx, my))

    def overlaps(self, ship):
        sx, sy = ship.topleft
        left, top = self.topleft
        return ship.mask.overlap(self.sprite[1], (left - sx, top - sy)) is not None

    def draw(self, surf, look, jitter=0):
        image, _, white, red = self.sprite
        left, top = self.topleft
        surf.blit({"white": white, "red": red}.get(look, image), (left + jitter, top))


class Leviathan(Boss):
    """Boss 4, the final boss. A serpent that slithers around the upper screen, its armour
    plates following the head's trail. The head takes extra damage.

    Phase 1 (calm)    -- RIPPLE: the plates fire aimed shots one after another, tail to head;
                         head fans; one DIVE: it locks onto the rocket (red crosshair), then
                         lunges straight through that spot
    Phase 2 (angry)   -- x1.2; more dives, BURSTS: every other plate fires a 4-way cross
    Phase 3 (furious) -- x1.4; cracked; a head spiral, and dives shed bullets sideways
    """

    EPITHET = "THE SERPENT IN THE ICE"          # boss name card

    PHASES = 3
    ENTER_TIME = 3.0
    DEATH_TIME = 2.6
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("ripple", 3.0), ("fan", 2.4), ("dive", 3.2), ("rest", 1.0)),
        (("dive", 3.0), ("ripple", 2.6), ("burst", 2.2), ("fan", 2.0), ("dive", 3.0),
         ("rest", 0.6)),
        (("dive", 2.8), ("spiral", 3.0), ("burst", 2.0), ("dive", 2.8), ("ripple", 2.2),
         ("rest", 0.4)),
    )
    SPEED, TURN, WOBBLE = 72, 2.6, 0.45            # px/s, rad/s, slither amplitude (rad)
    RIPPLE_INTERVAL, RIPPLE_SPEED = 0.2, 100
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.5, 115, 0.18
    BURST_INTERVAL, BURST_SPEED = 0.8, 70
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.1, 76, 2.2
    DIVE_WARN, DIVE_SPEED, DIVE_CONTACT_X = 1.0, 230, 4.0   # s, px/s, x bullet damage
    SHED_INTERVAL = 0.12                           # phase 3: bullets shed while diving
    HEAD_WEAK = 1.5                                # damage multiplier for hits on the head
    # Aimed damage per second at a rocket sitting still, phase 1: every ripple shot, the
    # centre shot of every fan, and the one dive (worth DIVE_CONTACT_X bullets).
    AIMED_RATE = ((3.0 / RIPPLE_INTERVAL + 2.4 / FAN_INTERVAL + DIVE_CONTACT_X)
                  / (3.0 + 2.4 + 3.2 + 1.0))

    @classmethod
    def prebuild(cls):
        leviathan_sprites()                        # 48 rotated heads take ~0.6 s

    def __init__(self, spec):
        sprites = leviathan_sprites()
        self.head_sprites, self.plate_sprites = sprites["head"], sprites["plates"]
        super().__init__(spec, [phase[0][0] for phase in self.head_sprites], {}, [])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.head = Segment(self, 11, head=True)
        self.plates = [Segment(self, r) for r in BODY_RADII]
        # Distance of every plate from the head along the trail (plates overlap a little).
        self.offsets, dist, prev = [], 0.0, self.head.radius
        for r in BODY_RADII:
            dist += (prev + r) * 0.75
            self.offsets.append(dist)
            prev = r
        self.x, self.y = LOW_W * 0.3, -30.0
        self.heading = math.pi / 2                 # swimming down onto the screen
        self.trail = deque(((self.x, self.y - i * 2) for i in range(int(dist / 2) + 20)),
                           maxlen=600)
        self.swim_time = 0.0
        self.waypoint = (LOW_W / 2, 90)
        self.waypoint_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.8
        self.ripple = 0                            # next plate to fire (counts from the tail)
        self.burst_parity = 0
        self.spiral_angle = 0.0
        self.dive = 0                              # 0 swim, 1 locking on, 2 lunging, 3 back up
        self.dive_target = None
        self.dive_left = 0.0                       # px of lunge left
        self.shed_timer = 0.0
        self.popped = 0                            # plates blown off while dying
        self.announced = False
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        return [self.head] + self.plates[:len(self.plates) - self.popped]

    def hit_part(self, part, amount, flash=True, source=None):
        self.damage(amount * (self.HEAD_WEAK if part is self.head else 1.0), flash)

    @property
    def contact_damage(self):
        return self.bullet_damage * self.DIVE_CONTACT_X if self.dive == 2 else super().contact_damage

    @property
    def bound(self):
        return self.head.bound

    def contains(self, px, py):
        return any(p.contains(px, py) for p in self.parts())

    def collides_with(self, ship):
        return any(p.overlaps(ship) for p in self.parts())

    def random_hull_point(self):
        part = random.choice(self.parts())
        return (part.x + random.uniform(-part.radius, part.radius),
                part.y + random.uniform(-part.radius, part.radius))

    def _layout(self):
        """Place the plates along the head's trail and pick every sprite for this frame."""
        phase = min(self.phase, 2)
        turn = self.heading + self._wobble() - math.pi / 2          # frame 0 points down
        frame = round(turn / math.tau * HEAD_FRAMES) % HEAD_FRAMES
        self.head.x, self.head.y = self.x, self.y
        self.head.sprite = self.head_sprites[phase][frame]
        # Walk back along the trail, dropping a plate at each of its distances.
        i, walked, (px, py) = 0, 0.0, (self.x, self.y)
        for tx, ty in reversed(self.trail):
            step = math.hypot(tx - px, ty - py)
            while i < len(self.offsets) and walked + step >= self.offsets[i]:
                k = (self.offsets[i] - walked) / step if step else 0.0
                self.plates[i].x, self.plates[i].y = px + (tx - px) * k, py + (ty - py) * k
                i += 1
            if i == len(self.offsets):
                break
            walked += step
            px, py = tx, ty
        for plate in self.plates[i:]:
            plate.x, plate.y = px, py
        for plate, sprite in zip(self.plates, self.plate_sprites[phase]):
            plate.sprite = sprite

    # --- movement -----------------------------------------------------------------------
    def _wobble(self):
        return 0.0 if self.dive == 2 else math.sin(self.swim_time * 5) * self.WOBBLE

    def _swim(self, dt, speed, turn):
        """Turn towards the waypoint (limited turn rate) and slither forwards."""
        tx, ty = self.waypoint
        want = math.atan2(ty - self.y, tx - self.x)
        diff = (want - self.heading + math.pi) % math.tau - math.pi
        self.heading += max(-turn * dt, min(turn * dt, diff))
        angle = self.heading + self._wobble()
        self.x += math.cos(angle) * speed * dt
        self.y += math.sin(angle) * speed * dt
        self.waypoint_time += dt
        if math.hypot(tx - self.x, ty - self.y) < 24 or self.waypoint_time > 4:
            self._new_waypoint()

    def _new_waypoint(self, high=False):
        self.waypoint_time = 0.0
        self.waypoint = (random.uniform(40, LOW_W - 40),
                         random.uniform(36, 60) if high else random.uniform(40, 115))

    def _move(self, dt):
        rate = self.RAGE[self.phase]
        self.swim_time += dt * rate
        if self.dive == 2:
            step = self.DIVE_SPEED * rate * dt
            self.x += math.cos(self.heading) * step
            self.y += math.sin(self.heading) * step
            self.dive_left -= step
            if self.dive_left <= 0 or not (12 < self.x < LOW_W - 12 and 20 < self.y < LOW_H - 22):
                self.dive = 3
                self._new_waypoint(high=True)
        else:
            slow = 0.5 if self.dive == 1 else 1.0
            self._swim(dt, self.SPEED * rate * slow, self.TURN * rate * (1.6 if self.dive == 3 else 1))
        last = self.trail[-1]
        if math.hypot(self.x - last[0], self.y - last[1]) >= 1.0:
            self.trail.append((self.x, self.y))
        self._layout()

    def enter(self, k):
        pass                                        # swims in on its own (see update)

    def update(self, dt, world):
        if self.state in ("enter", "fight"):
            self._move(dt)
        result = super().update(dt, world)
        if self.state == "dying":                   # plates blow off one by one, tail first
            due = int(self.state_time / self.DEATH_TIME * (len(self.plates) + 1))
            while self.popped < min(due, len(self.plates)):
                plate = self.plates[len(self.plates) - 1 - self.popped]
                self.popped += 1
                world.explosion(plate.x, plate.y, size=0.8)
                world.fire.burst(plate.x, plate.y, 10, 90, 0.5, ICE_SHARDS, size=(1, 1))
                world.audio.play("drone_explode")
        return result

    # --- fight --------------------------------------------------------------------------
    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.dive = 0

    def fight(self, dt, world):
        if not self.announced:
            self.announced = True
            world.alert = ["LEVIATHAN", "ITS HEAD IS THE WEAK SPOT!", DANGER, 2.4]
        rate = self.RAGE[self.phase]
        pattern = self.PATTERNS[self.phase]
        name, duration = pattern[self.pattern_index % len(pattern)]
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            if self.dive:
                self.dive = 0
            return
        if name == "dive":
            self._dive(dt, world)
            return
        self.fire_timer -= dt * rate
        if name == "spiral":
            self.spiral_angle += self.SPIRAL_TURN * dt * rate
        if self.fire_timer > 0 or name == "rest":
            return
        getattr(self, "_" + name)(world)

    def _mouth(self):
        return (self.x + math.cos(self.heading) * HEAD_MOUTH,
                self.y + math.sin(self.heading) * HEAD_MOUTH)

    def _aim(self, world, x, y):
        return math.atan2(world.ship.y - y, world.ship.x - x)

    def _ripple(self, world):
        """One aimed shot per plate, travelling from the tail to the head."""
        self.fire_timer = self.RIPPLE_INTERVAL
        plate = self.plates[len(self.plates) - 1 - self.ripple % len(self.plates)]
        self.ripple += 1
        if -4 < plate.y < LOW_H:
            self._shoot(world, plate.x, plate.y, self._aim(world, plate.x, plate.y),
                        self.RIPPLE_SPEED, self.bullet_damage)

    def _fan(self, world):
        self.fire_timer = self.FAN_INTERVAL
        mx, my = self._mouth()
        aim = self._aim(world, mx, my)
        for i in range(-2, 3):
            self._shoot(world, mx, my, aim + i * self.FAN_GAP, self.FAN_SPEED, self.bullet_damage)

    def _burst(self, world):
        """Every other plate fires a 4-way cross; the next burst uses the other plates."""
        self.fire_timer = self.BURST_INTERVAL
        self.burst_parity ^= 1
        offset = math.pi / 4 * self.burst_parity
        for plate in self.plates[self.burst_parity::2]:
            for i in range(4):
                world.enemy_bullets.append(bullet(plate.x, plate.y, offset + i * math.pi / 2,
                                                  self.BURST_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        mx, my = self._mouth()
        for i in range(3):
            world.enemy_bullets.append(bullet(mx, my, self.spiral_angle + math.tau * i / 3,
                                              self.SPIRAL_SPEED, self.bullet_damage))

    def _dive(self, dt, world):
        """Lock onto the rocket (red crosshair), then lunge straight through that spot."""
        ship = world.ship
        if self.dive == 0:
            self.dive = 1
            world.audio.play("lock_on")
        if self.dive == 1:
            if ship.alive and self.attack_time < self.DIVE_WARN - 0.25:
                self.dive_target = (ship.x, ship.y)          # frozen for the last moment
            if self.attack_time >= self.DIVE_WARN and self.dive_target:
                tx, ty = self.dive_target
                self.heading = math.atan2(ty - self.y, tx - self.x)
                self.dive_left = math.hypot(tx - self.x, ty - self.y) + 50
                self.dive = 2
                world.shake.add(0.3)
                world.audio.play("dive")
        elif self.dive == 2 and self.phase == 2:
            self.shed_timer -= dt
            if self.shed_timer <= 0:                          # scales fly off sideways
                self.shed_timer = self.SHED_INTERVAL
                plate = random.choice(self.plates)
                for side in (-1, 1):
                    world.enemy_bullets.append(bullet(plate.x, plate.y,
                                                      self.heading + side * math.pi / 2,
                                                      self.BURST_SPEED, self.bullet_damage))

    def _emit_vents(self, dt, world):
        """Frosty vapour from the tail."""
        self._vent_debt += 30 * dt
        tail = self.plates[len(self.plates) - 1 - min(self.popped, len(self.plates) - 1)]
        while self._vent_debt >= 1:
            self._vent_debt -= 1
            world.fire.emit(tail.x + random.uniform(-2, 2), tail.y + random.uniform(-2, 2),
                            random.uniform(-10, 10), random.uniform(-10, 10),
                            random.uniform(0.15, 0.3), FLAME_LEAN)

    # --- draw ---------------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        look = None
        if self.roar > 0 and int(self.roar * 10) % 2:
            look = "red"
        elif self.flash > 0:
            look = "white"
        shake = self.state == "dying" or self.roar > 0
        for part in reversed(self.parts()):                  # tail first, head on top
            part.draw(surf, look, random.randint(-1, 1) if shake else 0)
        if self.dive == 1 and self.dive_target and int(self.attack_time * 12) % 2 == 0:
            self._draw_lock(surf)

    def _draw_lock(self, surf):
        """Red crosshair on the locked spot and a dotted line from the head."""
        tx, ty = int(self.dive_target[0]), int(self.dive_target[1])
        pygame.draw.circle(surf, DANGER, (tx, ty), 9, 1)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pygame.draw.line(surf, DANGER, (tx + dx * 6, ty + dy * 6), (tx + dx * 12, ty + dy * 12))
        dist = math.hypot(tx - self.x, ty - self.y) or 1.0
        for i in range(3, int(dist / 6)):
            k = i * 6 / dist
            surf.fill(DANGER, (int(self.x + (tx - self.x) * k), int(self.y + (ty - self.y) * k), 1, 1))
