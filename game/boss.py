"""Bosses: big enemy ships with a health bar, attack patterns and a death sequence."""
import math
import random
from dataclasses import dataclass

import pygame

from .settings import ENEMY_SHOT, FLAME, LOW_H, LOW_W, PLAYER_DPS, SHIP_MAX_HP, SMOKE, SPARK
from .sprites import GUNSHIP_MUZZLES, GUNSHIP_VENTS, build_gunship


@dataclass(frozen=True)
class BossSpec:
    """Balance numbers for one boss appearance.

    strength   -- how many times stronger than the rocket (3-5 level boss, ~1.5 rematch)
    fight_time -- seconds a player needs to kill it with every gun bullet hitting

    Derived so that (boss HP / player DPS) / (player HP / boss DPS) == strength.
    """
    name: str
    strength: float
    fight_time: float

    @property
    def hp(self):
        return PLAYER_DPS * self.fight_time

    @property
    def dps(self):
        """Damage per second a rocket that never moves would take."""
        return self.strength * SHIP_MAX_HP / self.fight_time


GUNSHIP_SPEC = BossSpec("GUNSHIP", strength=3.0, fight_time=40)


class EnemyBullet:
    __slots__ = ("x", "y", "vx", "vy", "damage")

    def __init__(self, x, y, vx, vy, damage):
        self.x, self.y, self.vx, self.vy, self.damage = x, y, vx, vy, damage

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def offscreen(self):
        return not (-6 < self.x < LOW_W + 6 and -6 < self.y < LOW_H + 6)

    def draw(self, surf, blink):
        """Glowing orb: red rim, orange body, white-hot core (additive)."""
        x, y = int(self.x), int(self.y)
        add = pygame.BLEND_ADD
        surf.fill(ENEMY_SHOT[3], (x - 2, y - 1, 5, 3), special_flags=add)
        surf.fill(ENEMY_SHOT[3], (x - 1, y - 2, 3, 5), special_flags=add)
        surf.fill(ENEMY_SHOT[2 if blink else 1], (x - 1, y - 1, 3, 3), special_flags=add)
        surf.fill(ENEMY_SHOT[0], (x, y, 1, 1), special_flags=add)


class Boss:
    """Common boss behaviour: enter, fight (subclass), dying explosions, dead.

    Shares the weapon-target interface with asteroids: x, y, bound, contains(), damage().
    `world` passed to update() is the Game: it provides ship, enemy_bullets, fire,
    smoke and explosion(x, y, size).
    """

    ENTER_TIME = 2.5
    DEATH_TIME = 2.4

    def __init__(self, spec, image, muzzles, vents):
        self.spec = spec
        self.image = image
        self.mask = pygame.mask.from_surface(image)
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.w, self.h = image.get_size()
        self.muzzles, self.vents = muzzles, vents
        self.max_hp = self.hp = spec.hp
        self.x = LOW_W / 2
        self.y = -self.h / 2 - 4
        self.home_y = 26 + self.h / 2          # below the HUD
        self.state = "enter"                   # enter -> fight -> dying -> dead
        self.state_time = 0.0
        self.flash = 0.0
        self._boom_timer = 0.0
        self._vent_debt = 0.0

    # --- target interface ---------------------------------------------------------
    @property
    def bound(self):
        return max(self.w, self.h) / 2 + 1

    @property
    def topleft(self):
        return int(self.x - self.w / 2), int(self.y - self.h / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        return 0 <= mx < self.w and 0 <= my < self.h and self.mask.get_at((mx, my))

    def damage(self, amount, flash=True):
        if self.state != "fight":
            return                          # armour holds while entering / exploding
        self.hp = max(0.0, self.hp - amount)
        if flash:
            self.flash = 0.05
        if self.hp <= 0:
            self._set_state("dying")

    @property
    def targetable(self):
        return self.state in ("enter", "fight")

    @property
    def fighting(self):
        return self.state == "fight"

    def collides_with(self, ship):
        sx, sy = ship.topleft
        bx, by = self.topleft
        return ship.mask.overlap(self.mask, (bx - sx, by - sy)) is not None

    def point(self, px, py):
        """Sprite pixel -> world position (pixel centre)."""
        left, top = self.topleft
        return left + px + 0.5, top + py + 0.5

    def random_hull_point(self):
        while True:
            px, py = random.randrange(self.w), random.randrange(self.h)
            if self.mask.get_at((px, py)):
                return self.point(px, py)

    # --- update ---------------------------------------------------------------------
    def _set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def update(self, dt, world):
        """Advance the boss. Returns "defeated" on the frame the final blast happens."""
        self.state_time += dt
        self.flash = max(0.0, self.flash - dt)
        if self.state == "dead":
            return None
        self._emit_vents(dt, world)
        if self.state == "enter":
            k = min(1.0, self.state_time / self.ENTER_TIME)
            start = -self.h / 2 - 4
            self.y = start + (self.home_y - start) * (1 - (1 - k) ** 3)
            if k >= 1:
                self._set_state("fight")
        elif self.state == "fight":
            self.fight(dt, world)
            self._damage_smoke(dt, world)
        elif self.state == "dying":
            self._boom_timer -= dt
            if self._boom_timer <= 0:
                self._boom_timer = 0.12
                world.explosion(*self.random_hull_point(), size=random.uniform(0.6, 1.2))
            if self.state_time >= self.DEATH_TIME:
                self._set_state("dead")
                return "defeated"
        return None

    def fight(self, dt, world):
        raise NotImplementedError

    def _emit_vents(self, dt, world):
        """Engine exhaust out of the top vents (the boss flies nose-down)."""
        self._vent_debt += 60 * dt
        while self._vent_debt >= 1:
            self._vent_debt -= 1
            x, y = self.point(*random.choice(self.vents))
            world.fire.emit(x + random.uniform(-2, 2), y, random.uniform(-6, 6),
                            -random.uniform(40, 80), random.uniform(0.08, 0.2), FLAME)

    def _damage_smoke(self, dt, world):
        ratio = self.hp / self.max_hp
        if ratio < 0.5 and random.random() < 12 * dt:
            x, y = self.random_hull_point()
            world.smoke.emit(x, y, random.uniform(-8, 8), -random.uniform(15, 35),
                             random.uniform(0.6, 1.2), SMOKE, size=2, drag=1)
        if ratio < 0.25 and random.random() < 10 * dt:
            x, y = self.random_hull_point()
            world.fire.burst(x, y, 5, 50, 0.3, SPARK, size=(1, 1))

    # --- draw -----------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        x, y = self.topleft
        if self.state == "dying":
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
        surf.blit(self.white if self.flash > 0 else self.image, (x, y))


class Gunship(Boss):
    """Boss 1. Strafes left/right and cycles through attacks:

    spread  -- 5-shot fan from the nose cannon, aimed at the rocket (short charge-up glow)
    turrets -- alternating aimed shots from the wing turrets
    ring    -- (below 50% hp) a radial burst of bullets
    Below 50% hp it also moves and fires 30% faster; bullet damage is scaled down by the
    same factor so its damage per second (and therefore its strength) stays as specified.
    """

    SPREAD_INTERVAL, SPREAD_SHOTS, SPREAD_GAP, SPREAD_SPEED = 1.2, 5, 0.22, 105
    TURRET_INTERVAL, TURRET_SPEED = 0.45, 135
    RING_SHOTS, RING_SPEED = 14, 75
    CHARGE_TIME = 0.35
    RAGE = 1.3
    PATTERN = (("spread", 4.0), ("turrets", 3.0), ("rest", 1.2))
    PATTERN_RAGE = (("spread", 4.0), ("turrets", 3.0), ("ring", 0.6), ("rest", 0.6))
    # Bullets that would hit a rocket sitting still, per second, averaged over PATTERN:
    # one per spread volley (the centre shot) plus every turret shot.
    AIMED_RATE = (4.0 / SPREAD_INTERVAL + 3.0 / TURRET_INTERVAL) / (4.0 + 3.0 + 1.2)

    def __init__(self, spec=GUNSHIP_SPEC):
        super().__init__(spec, build_gunship(), GUNSHIP_MUZZLES, list(GUNSHIP_VENTS))
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.turret_side = 0
        self.charge = 0.0

    @property
    def enraged(self):
        return self.hp < self.max_hp / 2

    def fight(self, dt, world):
        rate = self.RAGE if self.enraged else 1.0
        self.move_time += dt * rate
        swing = LOW_W / 2 - self.w / 2 - 6
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.55) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.4) * 5

        pattern = self.PATTERN_RAGE if self.enraged else self.PATTERN
        name, duration = pattern[self.pattern_index % len(pattern)]
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.charge = 0.0
            return
        self.fire_timer -= dt * rate
        damage = self.bullet_damage / rate
        ship = world.ship

        if name == "spread":
            self.charge = max(0.0, 1 - self.fire_timer / self.CHARGE_TIME)
            if self.fire_timer <= 0:
                self.fire_timer = self.SPREAD_INTERVAL
                mx, my = self.point(*self.muzzles["main"])
                aim = math.atan2(ship.y - my, ship.x - mx)
                for i in range(self.SPREAD_SHOTS):
                    a = aim + (i - self.SPREAD_SHOTS // 2) * self.SPREAD_GAP
                    self._shoot(world, mx, my, a, self.SPREAD_SPEED, damage)
                self.charge = 0.0
        elif name == "turrets":
            self.charge = 0.0
            if self.fire_timer <= 0:
                self.fire_timer = self.TURRET_INTERVAL
                mx, my = self.point(*self.muzzles["left" if self.turret_side == 0 else "right"])
                self.turret_side = 1 - self.turret_side
                self._shoot(world, mx, my, math.atan2(ship.y - my, ship.x - mx),
                            self.TURRET_SPEED, damage)
        elif name == "ring":
            if self.fire_timer <= 0:
                self.fire_timer = 99.0                 # once per ring attack
                offset = random.uniform(0, math.tau)
                for i in range(self.RING_SHOTS):
                    self._shoot(world, self.x, self.y, offset + math.tau * i / self.RING_SHOTS,
                                self.RING_SPEED, damage)
        else:
            self.charge = 0.0

    def _shoot(self, world, x, y, angle, speed, damage):
        dx, dy = math.cos(angle), math.sin(angle)
        world.enemy_bullets.append(EnemyBullet(x, y, dx * speed, dy * speed, damage))
        world.fire.emit(x, y, dx * 30, dy * 30, 0.08, SPARK, size=2)     # muzzle flash

    def draw(self, surf):
        super().draw(surf)
        if self.charge > 0 and self.state == "fight":
            mx, my = self.point(*self.muzzles["main"])
            r = 1 + int(self.charge * 4)
            pygame.draw.circle(surf, ENEMY_SHOT[1], (int(mx), int(my)), r)
            pygame.draw.circle(surf, ENEMY_SHOT[0], (int(mx), int(my)), max(1, r - 2))
