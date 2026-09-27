"""Bosses: big enemy ships with a health bar, attack patterns and a death sequence."""
import math
import random
from dataclasses import dataclass

import pygame

from .enemies import Drone, EnemyBullet, shoot
from .settings import (BOSS_ROAR_TIME, DANGER, ENEMY_SHOT, FLAME, LOW_H, LOW_W, MK1, SMOKE, SPARK,
                       Loadout)
from .sprites import (CARRIER_BAYS, CARRIER_LIGHTS, CARRIER_MUZZLES, CARRIER_VENTS,
                      GUNSHIP_MUZZLES, GUNSHIP_VENTS, MOTHERSHIP_BAYS, MOTHERSHIP_LIGHTS,
                      MOTHERSHIP_MUZZLES, MOTHERSHIP_VENTS, build_carrier, build_gunship,
                      build_mothership)


@dataclass(frozen=True)
class BossSpec:
    """Balance numbers for one boss appearance.

    strength   -- how many times stronger than the rocket (3-5 level boss, ~1.5 rematch)
    fight_time -- seconds a player needs to kill it with every gun bullet hitting
    player     -- the ship model the player flies in that level

    Derived so that (boss HP / player DPS) / (player HP / boss DPS) == strength.
    """
    name: str
    strength: float
    fight_time: float
    player: Loadout = MK1

    @property
    def hp(self):
        return self.player.gun_dps * self.fight_time

    @property
    def dps(self):
        """Damage per second a rocket that never moves would take."""
        return self.strength * self.player.max_hp / self.fight_time


GUNSHIP_SPEC = BossSpec("GUNSHIP", strength=3.0, fight_time=40)


class Boss:
    """Common boss behaviour: enter, fight (subclass), dying explosions, dead.

    Shares the weapon-target interface with asteroids: x, y, bound, contains(), damage().
    `world` passed to update() is the Game: it provides ship, enemy_bullets, fire,
    smoke and explosion(x, y, size).
    """

    ENTER_TIME = 2.5
    DEATH_TIME = 2.4
    PHASES = 1          # multi-phase bosses change phase at every 1/PHASES of their health

    def __init__(self, spec, images, muzzles, vents):
        self.spec = spec
        self.images = images if isinstance(images, list) else [images]
        self.mask = pygame.mask.from_surface(self.images[0])
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.red = self.mask.to_surface(setcolor=DANGER, unsetcolor=(0, 0, 0, 0))
        self.w, self.h = self.images[0].get_size()
        self.muzzles, self.vents = muzzles, vents
        self.max_hp = self.hp = spec.hp
        self.x = LOW_W / 2
        self.y = -self.h / 2 - 4
        self.home_y = 26 + self.h / 2          # below the HUD
        self.state = "enter"                   # enter -> fight -> dying -> dead
        self.state_time = 0.0
        self.flash = 0.0
        self.phase = 0                         # 0 .. PHASES-1
        self.roar = 0.0                        # > 0 while changing phase (invulnerable)
        self._boom_timer = 0.0
        self._vent_debt = 0.0

    @property
    def image(self):
        return self.images[min(self.phase, len(self.images) - 1)]

    @property
    def phase_marks(self):
        """Health-bar tick positions (0..1): phase thresholds, or quarters."""
        n = self.PHASES if self.PHASES > 1 else 4
        return [i / n for i in range(1, n)]

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
        if self.state != "fight" or self.roar > 0:
            return                          # armour holds while entering / roaring / exploding
        self.hp = max(0.0, self.hp - amount)
        if flash:
            self.flash = 0.05
        threshold = self.max_hp * (self.PHASES - 1 - self.phase) / self.PHASES
        if self.phase < self.PHASES - 1 and self.hp <= threshold:
            self.hp = threshold             # one burst can't skip a whole phase
            self.phase += 1
            self.roar = BOSS_ROAR_TIME
            self.on_phase()
        elif self.hp <= 0:
            self._set_state("dying")

    def on_phase(self):
        """Hook: the boss just entered self.phase (it roars for BOSS_ROAR_TIME first)."""

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
            if self.roar > 0:
                self.roar = max(0.0, self.roar - dt)
                if random.random() < 30 * dt:
                    world.fire.burst(*self.random_hull_point(), 6, 70, 0.3, SPARK, size=(1, 1))
            else:
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

    def _shoot(self, world, x, y, angle, speed, damage):
        shoot(world, x, y, angle, speed, damage)

    def _launch_drones(self, world, bays, damage):
        """One drone out of every hangar bay (sprite pixels), kicked outwards."""
        for side, (bx, by) in zip((-1, 1), bays):
            x, y = self.point(bx, by)
            world.enemies.append(Drone(x, y, vx=side * 45, vy=70, sway=14, shots=2,
                                       bullet_damage=damage))
            world.fire.burst(x, y, 6, 40, 0.25, FLAME[:3], size=(1, 1))

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
        if self.state == "dying" or self.roar > 0:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
        if self.roar > 0 and int(self.roar * 10) % 2:
            surf.blit(self.red, (x, y))          # roaring: flashes red
        else:
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

    def draw(self, surf):
        super().draw(surf)
        if self.charge > 0 and self.state == "fight":
            mx, my = self.point(*self.muzzles["main"])
            r = 1 + int(self.charge * 4)
            pygame.draw.circle(surf, ENEMY_SHOT[1], (int(mx), int(my)), r)
            pygame.draw.circle(surf, ENEMY_SHOT[0], (int(mx), int(my)), max(1, r - 2))


class Carrier(Boss):
    """Boss 2. A wide carrier with three phases, one per third of its health.

    Phase 1 (calm)    -- launches drones from its hangar bays, aimed side-cannon shots,
                         a rain of bullets from the hull
    Phase 2 (angry)   -- faster; rotating bullet spiral from the core, cannons fire 3-shot fans,
                         more drones
    Phase 3 (furious) -- faster still; bullet walls with a gap to fly through, a 3-arm spiral
    Between phases it roars (invulnerable, flashing red); the game rewards the player with a
    POWER core and a repair kit, so the rocket grows stronger as the boss gets angrier.
    """

    PHASES = 3
    RAGE = (1.0, 1.25, 1.5)                    # movement / fire speed per phase
    PATTERNS = (
        (("drones", 2.0), ("cannons", 3.0), ("rain", 2.5), ("rest", 1.2)),
        (("spiral", 3.2), ("drones", 1.6), ("cannons", 2.6), ("rest", 0.8)),
        (("wall", 3.4), ("spiral", 3.0), ("drones", 1.4), ("cannons", 2.2), ("rest", 0.5)),
    )
    CANNON_INTERVAL, CANNON_SPEED, CANNON_FAN = 0.5, 125, 0.16
    RAIN_INTERVAL, RAIN_SPEED = 0.14, 80
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.11, 72, 2.2
    WALL_INTERVAL, WALL_SPEED, WALL_GAP, WALL_SPACING = 1.1, 62, 44, 11
    DRONE_INTERVAL, DRONE_LAUNCHES, MAX_DRONES = 0.7, (1, 2, 2), 6
    # Aimed bullets per second at a rocket sitting still, phase 1: every cannon shot
    # plus two shots from each of the two drones launched per cycle.
    AIMED_RATE = (3.0 / CANNON_INTERVAL + 2 * 2) / (2.0 + 3.0 + 2.5 + 1.2)

    def __init__(self, spec):
        super().__init__(spec, build_carrier(), CARRIER_MUZZLES, list(CARRIER_VENTS))
        self.home_y = 22 + self.h / 2
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.8
        self.cannon_side = 0
        self.launches = 0
        self.spiral_angle = 0.0

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.launches = 0

    @property
    def rate(self):
        return self.RAGE[self.phase]

    @property
    def light(self):
        return CARRIER_LIGHTS[self.phase][0]

    def fight(self, dt, world):
        rate = self.rate
        self.move_time += dt * rate
        swing = LOW_W / 2 - self.w / 2 - 4
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.45) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.1) * 4

        pattern = self.PATTERNS[self.phase]
        name, duration = pattern[self.pattern_index % len(pattern)]
        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.launches = 0
            return
        self.fire_timer -= dt * rate
        if self.fire_timer > 0 or name == "rest":
            if name == "spiral":
                self.spiral_angle += self.SPIRAL_TURN * dt * rate
            return
        getattr(self, "_" + name)(world)

    # --- attacks: each fires once and sets fire_timer for the next shot ---------------
    def _drones(self, world):
        self.fire_timer = self.DRONE_INTERVAL
        if self.launches >= self.DRONE_LAUNCHES[self.phase] or len(world.enemies) >= self.MAX_DRONES:
            return
        self.launches += 1
        self._launch_drones(world, CARRIER_BAYS, self.bullet_damage)

    def _cannons(self, world):
        self.fire_timer = self.CANNON_INTERVAL
        ship = world.ship
        mx, my = self.point(*self.muzzles["left" if self.cannon_side == 0 else "right"])
        self.cannon_side = 1 - self.cannon_side
        aim = math.atan2(ship.y - my, ship.x - mx)
        offsets = (0,) if self.phase == 0 else (-self.CANNON_FAN, 0, self.CANNON_FAN)
        for off in offsets:
            self._shoot(world, mx, my, aim + off, self.CANNON_SPEED, self.bullet_damage)

    def _rain(self, world):
        self.fire_timer = self.RAIN_INTERVAL
        x = self.x + random.uniform(-self.w / 2 + 6, self.w / 2 - 6)
        self._shoot(world, x, self.y + self.h / 2 - 8, math.pi / 2 + random.uniform(-0.45, 0.45),
                    self.RAIN_SPEED, self.bullet_damage)

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        arms = 2 + self.phase - 1
        cx, cy = self.point(*self.muzzles["core"])
        for i in range(arms):
            a = self.spiral_angle + math.tau * i / arms
            world.enemy_bullets.append(_bullet(cx, cy, a, self.SPIRAL_SPEED, self.bullet_damage))

    def _wall(self, world):
        """A row of bullets across the screen with one gap near the rocket."""
        self.fire_timer = self.WALL_INTERVAL
        gap = min(LOW_W - 30, max(30, world.ship.x + random.uniform(-60, 60)))
        y = self.y + self.h / 2 - 4
        for x in range(5, LOW_W, self.WALL_SPACING):
            if abs(x - gap) > self.WALL_GAP / 2:
                world.enemy_bullets.append(_bullet(x, y, math.pi / 2, self.WALL_SPEED,
                                                   self.bullet_damage))
        world.shake.add(0.1)

    def draw(self, surf):
        super().draw(surf)
        if self.state != "fight":
            return
        # The core glows in the phase colour and pulses faster the angrier the boss is.
        cx, cy = self.point(*self.muzzles["core"])
        pulse = 0.5 + 0.5 * math.sin(self.move_time * 6 * self.rate)
        r = 1 + int(pulse * (2 + self.phase))
        pygame.draw.circle(surf, self.light, (int(cx), int(cy)), r)
        surf.fill((255, 255, 255), (int(cx), int(cy), 1, 1))


def _bullet(x, y, angle, speed, damage):
    """Enemy bullet without a muzzle flash (spirals and walls fire too many for flashes)."""
    return EnemyBullet(x, y, math.cos(angle) * speed, math.sin(angle) * speed, damage)


class Mothership(Boss):
    """Boss 3, the final boss. Three phases, one per third of its health.

    Phase 1 (calm)    -- aimed 3-shot fans from four wing turrets, drone launches, bullet rings
    Phase 2 (angry)   -- x1.2; adds a sweeping BEAM: a red warning line, then a deadly column
                         straight down that follows the ship slowly; spirals
    Phase 3 (furious) -- x1.4; counter-rotating double spirals, 5-shot fans, faster rings
    Like the Carrier it roars between phases, and the game hands out rewards.
    """

    PHASES = 3
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("fans", 3.0), ("drones", 1.6), ("rings", 2.4), ("rest", 1.2)),
        (("beam", 3.2), ("fans", 2.6), ("drones", 1.4), ("spiral", 2.6), ("rest", 0.8)),
        (("spiral", 3.0), ("beam", 3.0), ("rings", 2.0), ("drones", 1.2), ("fans", 2.2),
         ("rest", 0.5)),
    )
    FAN_INTERVAL, FAN_SPEED, FAN_GAP = 0.45, 115, 0.2
    RING_INTERVAL, RING_SHOTS, RING_SPEED = 0.8, 14, 70
    SPIRAL_INTERVAL, SPIRAL_SPEED, SPIRAL_TURN = 0.1, 74, 2.0
    DRONE_INTERVAL, DRONE_LAUNCHES, MAX_DRONES = 0.6, (1, 2, 2), 6
    BEAM_WARN, BEAM_HALF, BEAM_DAMAGE_X = 0.9, 4, 2.5     # telegraph s, half width px, x bullet
    # Aimed bullets per second at a rocket sitting still, phase 1: the centre shot of every
    # fan plus two shots from each of the two drones launched per cycle.
    AIMED_RATE = (3.0 / FAN_INTERVAL + 2 * 2) / (3.0 + 1.6 + 2.4 + 1.2)

    def __init__(self, spec):
        super().__init__(spec, build_mothership(), MOTHERSHIP_MUZZLES, list(MOTHERSHIP_VENTS))
        self.home_y = 20 + self.h / 2
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.move_time = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.8
        self.turret = 0
        self.launches = 0
        self.spiral_angle = 0.0
        self.beam = 0            # 0 off, 1 warning line, 2 firing

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5
        self.launches = 0
        self.beam = 0

    @property
    def rate(self):
        return self.RAGE[self.phase]

    @property
    def light(self):
        return MOTHERSHIP_LIGHTS[self.phase][0]

    def fight(self, dt, world):
        rate = self.rate
        pattern = self.PATTERNS[self.phase]
        name, duration = pattern[self.pattern_index % len(pattern)]
        # Slows down while the beam fires, so the beam sweeps instead of whipping around.
        self.move_time += dt * rate * (0.3 if name == "beam" else 1.0)
        swing = LOW_W / 2 - self.w / 2 - 4
        self.x = LOW_W / 2 + math.sin(self.move_time * 0.4) * swing
        self.y = self.home_y + math.sin(self.move_time * 1.0) * 3

        self.attack_time += dt
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.launches = 0
            self.beam = 0
            return
        if name == "beam":
            self._beam(dt, world, duration)
            return
        self.fire_timer -= dt * rate
        if name == "spiral":
            self.spiral_angle += self.SPIRAL_TURN * dt * rate
        if self.fire_timer > 0 or name == "rest":
            return
        getattr(self, "_" + name)(world)

    # --- attacks ------------------------------------------------------------------------
    def _fans(self, world):
        self.fire_timer = self.FAN_INTERVAL
        ship = world.ship
        turrets = self.muzzles["turrets"]
        mx, my = self.point(*turrets[self.turret % len(turrets)])
        self.turret += 1
        aim = math.atan2(ship.y - my, ship.x - mx)
        n = 5 if self.phase == 2 else 3
        for i in range(n):
            self._shoot(world, mx, my, aim + (i - n // 2) * self.FAN_GAP, self.FAN_SPEED,
                        self.bullet_damage)

    def _drones(self, world):
        self.fire_timer = self.DRONE_INTERVAL
        if self.launches >= self.DRONE_LAUNCHES[self.phase] or len(world.enemies) >= self.MAX_DRONES:
            return
        self.launches += 1
        self._launch_drones(world, MOTHERSHIP_BAYS, self.bullet_damage)

    def _rings(self, world):
        self.fire_timer = self.RING_INTERVAL
        cx, cy = self.point(*self.muzzles["eye"])
        offset = random.uniform(0, math.tau)
        for i in range(self.RING_SHOTS):
            world.enemy_bullets.append(_bullet(cx, cy, offset + math.tau * i / self.RING_SHOTS,
                                               self.RING_SPEED, self.bullet_damage))

    def _spiral(self, world):
        self.fire_timer = self.SPIRAL_INTERVAL
        cx, cy = self.point(*self.muzzles["eye"])
        arms = 2
        spins = (1, -1) if self.phase == 2 else (1,)
        for spin in spins:
            for i in range(arms):
                a = spin * self.spiral_angle + math.tau * i / arms
                world.enemy_bullets.append(_bullet(cx, cy, a, self.SPIRAL_SPEED,
                                                   self.bullet_damage))

    def _beam(self, dt, world, duration):
        """Warning line, then a column straight down from the beam cannon."""
        if self.attack_time < self.BEAM_WARN:
            self.beam = 1
            return
        if self.attack_time > duration - 0.2:
            self.beam = 0
            return
        if self.beam != 2:
            world.shake.add(0.35)
        self.beam = 2
        bx, by = self.point(*self.muzzles["beam"])
        ship = world.ship
        if random.random() < 30 * dt:                   # sparks where it hits the bottom
            world.fire.emit(bx + random.uniform(-4, 4), LOW_H - 1, random.uniform(-60, 60),
                            -random.uniform(40, 90), 0.3, SPARK)
        if ship.alive and ship.y > by and abs(ship.x - bx) < self.BEAM_HALF + ship.w * 0.35:
            world.hurt_ship(self.bullet_damage * self.BEAM_DAMAGE_X, bx, ship.y)

    def draw(self, surf):
        super().draw(surf)
        if self.state != "fight":
            return
        cx, cy = self.point(*self.muzzles["eye"])
        pulse = 0.5 + 0.5 * math.sin(self.move_time * 6 * self.rate)
        pygame.draw.circle(surf, self.light, (int(cx), int(cy)), 1 + int(pulse * (2 + self.phase)))
        surf.fill((255, 255, 255), (int(cx), int(cy), 1, 1))
        if self.roar > 0 or not self.beam:
            return
        bx, by = self.point(*self.muzzles["beam"])
        bx, by = int(bx), int(by)
        if self.beam == 1:                               # blinking warning line
            if int(self.attack_time * 12) % 2 == 0:
                pygame.draw.line(surf, DANGER, (bx, by), (bx, surf.get_height()))
            return
        wobble = int(self.attack_time * 30) % 2
        h = surf.get_height() - by
        half = self.BEAM_HALF + wobble
        surf.fill(ENEMY_SHOT[3], (bx - half - 1, by, 2 * half + 3, h))
        surf.fill(ENEMY_SHOT[2], (bx - half + 1, by, 2 * half - 1, h))
        surf.fill(ENEMY_SHOT[1], (bx - 1, by, 3, h))
        surf.fill(ENEMY_SHOT[0], (bx, by, 1, h))
        pygame.draw.circle(surf, ENEMY_SHOT[1], (bx, by), half + 2)
