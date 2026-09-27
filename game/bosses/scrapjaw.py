"""Boss 8: SCRAPJAW, the junk king (level 8) — frame, armour plates, thrown junk, behaviour."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import COIN, FLAME, SPARK
from ..config.tuning import JUNK_HP
from ..core.pixelart import CharCanvas, sprite_from_rows
from ..minions.base import Enemy
from ..minions.bullets import bullet, shoot
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss

SCRAP_COLORS = {**HULL_COLORS, "H": (60, 44, 40), "M": (104, 76, 60), "L": (150, 112, 84),
                "W": (200, 170, 140), "E": (230, 110, 40), "e": (140, 60, 24),
                "G": (36, 30, 34), "g": (90, 80, 84)}
SCRAP_HALF_W, SCRAP_HALF_H = 32, 44
# Armour plates: (x, y) centre offsets from the boss centre.
PLATE_SLOTS = ((-22, -8), (22, -8), (-14, 8), (14, 8), (-26, 12), (26, 12))
PLATE_ROWS = (
    ".KKKKKKKKK.",
    "KLLWLLLLLMK",
    "KLMMMMMMMHK",
    "KLMEMMMEMHK",
    "KLMMMMMMMHK",
    "KMMMMMMMMHK",
    "KHHHHHHHHHK",
    ".KKKKKKKKK.",
)


def _frame_half():
    """The bare mech: a spine, rib girders, a jaw with teeth, claw arms, a glowing eye."""
    c = CharCanvas(SCRAP_HALF_W, SCRAP_HALF_H)
    c.rect(26, 0, 31, 40, "M")                       # spine
    c.line(26, 0, 26, 40, "L")
    c.line(31, 0, 31, 40, "H")
    for y in (6, 12, 18, 24):                        # rib girders
        c.line(8, y + 4, 26, y, "g")
        c.line(8, y + 5, 26, y + 1, "G")
    c.poly([(4, 26), (18, 22), (26, 30), (26, 42), (14, 43), (6, 36)], "H")   # jaw
    c.line(4, 26, 18, 22, "L")
    for x in (10, 14, 18, 22):                       # teeth
        c.line(x, 38, x + 1, 43, "W")
    c.rect(0, 10, 5, 32, "M")                        # claw arm
    c.line(0, 10, 0, 32, "L")
    c.poly([(0, 32), (5, 32), (7, 40), (2, 43)], "g")
    c.rect(27, 14, 31, 19, "G")                      # eye socket
    c.rect(28, 15, 31, 18, "E")
    c.set(29, 16, "W")
    return c.rows()


class Plate:
    """An armour plate: bolted on (hits count for the boss too), or shot off."""

    def __init__(self, boss, slot, image, mask, white):
        self.boss, self.slot = boss, slot
        self.image, self.mask, self.white = image, mask, white
        self.x = self.y = 0.0
        self.hp = 0.0
        self.attached = True
        self.flash = 0.0
        self.start = (random.choice((-30, LOW_W + 30)), random.uniform(-40, 120))

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

    def draw(self, surf):
        surf.blit(self.white if self.flash > 0 else self.image, self.topleft)


class JunkShot(Enemy):
    """A thrown armour plate: big and slow, can be shot apart."""

    points = 40
    drops_coins = False
    stat = False

    def __init__(self, image, x, y, angle, speed, damage):
        super().__init__(pygame.transform.scale2x(image), x, y, JUNK_HP)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.damage_on_contact = damage

    @property
    def contact_damage(self):
        return self.damage_on_contact

    def move(self, dt, world):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if random.random() < 10 * dt:
            world.smoke.emit(self.x, self.y, 0, -10, 0.4, [(90, 80, 84), (60, 50, 50)], size=2)

    def attack(self, dt, world):
        pass

    @property
    def offscreen(self):
        return self.y > LOW_H + 20 or not -30 < self.x < LOW_W + 30


class Scrapjaw(Boss):
    """Boss 8. A mech built from wrecks: it assembles itself when it arrives.

    Phase 1 (calm)    -- armour plates can be shot off (hits on them count for the boss too);
                         it THROWS armour back (big slow junk that can be shot apart),
                         cannon pairs, scrap spreads
    Phase 2 (angry)   -- x1.2; a MAGNET CLAW pulls rocks and coins in (the ship is not
                         pulled); every rock it catches becomes more junk to throw
    Phase 3 (furious) -- x1.4; the armour falls off: a fast skeleton spraying sparks
    The idea: the arena is its ammunition.
    """

    EPITHET = "THE JUNK KING"
    PHASES = 3
    ENTER_TIME = 3.2
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("cannon", 2.6), ("throw", 1.6), ("scatter", 2.2), ("rest", 1.0)),
        (("magnet", 3.0), ("throw", 1.4), ("cannon", 2.2), ("throw", 1.4), ("rest", 0.6)),
        (("sparks", 3.0), ("cannon", 2.0), ("throw", 1.2), ("sparks", 2.6), ("rest", 0.4)),
    )
    CANNON_INTERVAL, CANNON_SPEED = 0.4, 130
    SCATTER_INTERVAL, SCATTER_SHOTS, SCATTER_SPEED = 0.7, 7, 95
    THROW_INTERVAL, THROW_SPEED, JUNK_X = 1.0, 72, 3.0
    SPARK_INTERVAL, SPARK_SPEED = 0.07, 88
    MAGNET_RANGE, MAGNET_PULL = 150, 110
    PLATE_HP = 0.04                  # share of the boss's max hp per plate
    # Phase 1 aimed damage per second at a rocket sitting still: both cannon shots, one
    # thrown plate (worth JUNK_X bullets) per throw, the middle shot of every scatter.
    AIMED_RATE = ((2.6 / CANNON_INTERVAL) * 2 + 1.6 / THROW_INTERVAL * JUNK_X
                  + 2.2 / SCATTER_INTERVAL) / (2.6 + 1.6 + 2.2 + 1.0)

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            frame = build_boss_sprite(_frame_half(), SCRAP_COLORS)
            plate = sprite_from_rows(PLATE_ROWS, SCRAP_COLORS)
            mask = pygame.mask.from_surface(plate)
            white = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
            cls._sprites = frame, (plate, mask, white)
        return cls._sprites

    def __init__(self, spec):
        frame, plate = self.prebuild()
        super().__init__(spec, frame, {}, [(22, 1), (41, 1)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.plate_image = plate[0]
        self.plates = [Plate(self, slot, *plate) for slot in PLATE_SLOTS]
        for p in self.plates:
            p.hp = self.max_hp * self.PLATE_HP
        self.home_y = 26 + self.h / 2
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.stock = 0                    # caught rocks / shot-off plates to throw
        self.pulled = []                  # things the magnet pulls this frame (for the lines)
        self.falling = []                 # [x, y, vy, spin] plates dropping off
        self._clang = False
        self._layout(1.0)

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        return [self] + [p for p in self.plates if p.attached]

    def hit_part(self, part, amount, flash=True, source=None):
        if part is not self and self.state == "fight" and self.roar <= 0:
            part.flash = 0.05 if flash else part.flash
            part.hp -= amount
            if part.hp <= 0:
                self._drop_plate(part)
        self.damage(amount, flash)

    def _drop_plate(self, plate):
        plate.attached = False
        self.stock += 1
        self.falling.append([plate.x, plate.y, 20.0, random.uniform(-4, 4)])
        self._clang = True

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        if self.phase == 2:                          # the armour falls off
            for plate in self.plates:
                if plate.attached:
                    self._drop_plate(plate)

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    def _layout(self, k):
        """Plates on their slots; k < 1 while it assembles (they fly in from the edges)."""
        e = 1 - (1 - k) ** 3
        for plate in self.plates:
            if plate.attached:
                tx, ty = self.x + plate.slot[0], self.y + plate.slot[1]
                sx, sy = plate.start
                plate.x, plate.y = sx + (tx - sx) * e, sy + (ty - sy) * e

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        self.pulled = []
        for plate in self.plates:
            plate.flash = max(0.0, plate.flash - dt)
        for f in self.falling:
            f[2] += 160 * dt
            f[1] += f[2] * dt
        self.falling = [f for f in self.falling if f[1] < LOW_H + 20]
        if self._clang:
            self._clang = False
            world.audio.play("metal_break")
            world.shake.add(0.2)
        result = super().update(dt, world)
        if self.state in ("fight", "dying"):
            self._layout(1.0)
        return result

    def enter(self, k):
        super().enter(k)
        self._layout(min(1.0, k * 1.25))

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        fast = 1.5 if self.phase == 2 else 1.0
        self.move_time += dt * rate * fast
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.45) * (LOW_W / 2 - 50)
        self.y = self.home_y + math.sin(self.move_time * 1.1) * (4 + 6 * (self.phase == 2))
        name, duration = self._pattern()
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            return
        if name == "magnet":
            self._magnet(dt, world)
            return
        self.fire_timer -= dt * rate
        if self.fire_timer > 0 or name == "rest":
            return
        getattr(self, "_" + name)(world)

    def _claw(self):
        return self.x - 28, self.y + 14

    # --- attacks ------------------------------------------------------------------------
    def _aim(self, world, x, y):
        return math.atan2(world.ship.y - y, world.ship.x - x)

    def _cannon(self, world):
        self.fire_timer = self.CANNON_INTERVAL
        for side in (-1, 1):
            x, y = self.x + side * 8, self.y + self.h / 2 - 4
            shoot(world, x, y, self._aim(world, x, y), self.CANNON_SPEED, self.bullet_damage)

    def _scatter(self, world):
        self.fire_timer = self.SCATTER_INTERVAL
        x, y = self.x, self.y + self.h / 2 - 4
        aim = self._aim(world, x, y)
        for i in range(self.SCATTER_SHOTS):
            a = aim + (i - self.SCATTER_SHOTS // 2) * 0.18
            world.enemy_bullets.append(bullet(x, y, a, self.SCATTER_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _throw(self, world):
        """Hurl a piece of junk (a shot-off plate or a caught rock, else scrap off its back)."""
        self.fire_timer = self.THROW_INTERVAL
        self.stock = max(0, self.stock - 1)
        x, y = self._claw()
        world.enemies.append(JunkShot(self.plate_image, x, y, self._aim(world, x, y),
                                      self.THROW_SPEED, self.bullet_damage * self.JUNK_X))
        world.fire.burst(x, y, 6, 50, 0.2, SPARK, size=(1, 1))
        world.audio.play("dive")

    def _sparks(self, world):
        self.fire_timer = self.SPARK_INTERVAL
        a = random.uniform(0.15, math.pi - 0.15)
        world.enemy_bullets.append(bullet(self.x, self.y + 8, a, self.SPARK_SPEED,
                                          self.bullet_damage))

    def _magnet(self, dt, world):
        """Pull rocks and coins in; rocks that reach it are crushed into ammunition."""
        cx, cy = self._claw()
        for rock in list(world.asteroids):
            dx, dy = cx - rock.x, cy - rock.y
            dist = math.hypot(dx, dy) or 1.0
            if dist > self.MAGNET_RANGE:
                continue
            self.pulled.append((rock.x, rock.y))
            rock.vx += dx / dist * self.MAGNET_PULL * dt
            rock.vy += dy / dist * self.MAGNET_PULL * dt
            if dist < 18:
                world.asteroids.remove(rock)
                world.fire.burst(rock.x, rock.y, 8, 40, 0.3, FLAME, size=(1, 1))
                self.stock += 1
        for pickup in list(world.pickups):
            dx, dy = cx - pickup.x, cy - pickup.y
            dist = math.hypot(dx, dy) or 1.0
            if dist < self.MAGNET_RANGE and pickup.magnet < 100:
                self.pulled.append((pickup.x, pickup.y))
                pickup.x += dx / dist * 50 * dt
                pickup.y += dy / dist * 50 * dt
                if dist < 12:
                    world.pickups.remove(pickup)

    # --- draw ---------------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        super().draw(surf)
        for plate in self.plates:
            if plate.attached:
                plate.draw(surf)
        for x, y, vy, spin in self.falling:
            image = pygame.transform.rotate(self.plate_image, spin * y)
            surf.blit(image, (int(x) - image.get_width() // 2, int(y) - image.get_height() // 2))
        if self.pulled and self.fighting:              # magnet field lines
            cx, cy = self._claw()
            step = int(self.attack_time * 20) % 4
            for x, y in self.pulled:
                for i in range(step, 12, 4):
                    k = i / 12
                    surf.fill(COIN[3] if i % 8 else COIN[2],
                              (int(cx + (x - cx) * k), int(cy + (y - cy) * k), 1, 1))
            pygame.draw.circle(surf, COIN[2], (int(cx), int(cy)), 4 + step, 1)
