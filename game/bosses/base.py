"""Boss base class: health, phases, entry, death sequence and the weapon-target interface."""
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER, FLAME, SMOKE, SPARK
from ..config.tuning import BOSS_CONTACT_DAMAGE, BOSS_ROAR_TIME
from ..minions.bullets import shoot
from ..minions.drone import Drone


class Boss:
    """Common boss behaviour: enter, fight (subclass), dying explosions, dead.

    Shares the weapon-target interface with asteroids: x, y, bound, contains(), damage().
    A boss made of several pieces (the Leviathan) returns them from parts(); weapons aim at
    the parts and hit_part() turns a hit on any of them into damage to the boss.
    `world` passed to update() is the Game: it provides ship, enemies, enemy_bullets, fire,
    smoke, shake, audio, hurt_ship() and explosion(x, y, size).
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

    @classmethod
    def prebuild(cls):
        """Hook: build expensive sprites now (the game calls it at startup), not mid-fight."""

    # --- target interface ---------------------------------------------------------
    def parts(self):
        """What the player's weapons can hit."""
        return [self]

    def hit_part(self, part, amount, flash=True):
        """A weapon hit one of parts()."""
        self.damage(amount, flash)

    @property
    def contact_damage(self):
        """Damage for ramming the boss."""
        return BOSS_CONTACT_DAMAGE

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
            self.enter(k)
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

    def enter(self, k):
        """Entry movement, k = 0..1 over ENTER_TIME: glide down to home_y."""
        start = -self.h / 2 - 4
        self.y = start + (self.home_y - start) * (1 - (1 - k) ** 3)

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
