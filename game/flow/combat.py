"""Combat: the player's weapons hitting rocks, minions and bosses — damage, kills, rewards."""
import math
import random

from ..config.palette import ACCENT, DANGER, FLAME, ICE_SHARDS, LASER, POWER, SMOKE, SPARK
from ..config.tuning import (BLAST_CHARGE_PER_DAMAGE, BLAST_CHARGE_PER_KILL, BOSS_ROAR_TIME,
                             DRONE_KIT_CHANCE, POINTS_BOSS, POINTS_PER_RADIUS, ROCK_KIT_CHANCE,
                             ULT_CHARGE_PER_BOSS_THIRD, ULT_CHARGE_PER_DAMAGE, ULT_CHARGE_PER_KILL)
from ..core.particles import Shockwave
from ..minions.base import Enemy
from ..obstacles.asteroid import Asteroid
from ..pickups.types import FullRepair, PowerCore, RepairKit
from ..ui.popup import Popup
from .states import Phase, State


class CombatMixin:
    """Game mixin: weapons -> Hits -> damage, destruction, score, BLAST/ULT charge, explosions."""

    def _update_weapons(self, dt, firing):
        """Every weapon keeps simulating (bullets in flight, laser cooling); only the active one fires.
        A charged BLAST takes over from the normal weapon while it lasts."""
        targets = self.asteroids + self.enemies
        boss_parts = self.boss.parts() if self.boss and self.boss.targetable else []
        targets += boss_parts
        firing = firing and self.ship.alive
        self.track_fire(firing)
        hits = []
        if self.ship.loadout.blast:
            self.blast.colors = LASER if self.weapon.name == "LASER" else FLAME[:4]
            hits += self.blast.update(dt, firing, self.ship, targets, self.fire)
        for weapon in self.weapons:
            weapon.rate = self.fire_rate                  # OVERDRIVE / FEVER
            active = firing and weapon is self.weapon and not self.blast.active
            hits += weapon.update(dt, active, self.ship, targets, self.fire)
        hits += self._update_wingmen(dt, firing)
        secondary = self.secondary
        for weapon in self.secondaries.values():   # automatic; rocks + minions only
            live = weapon is secondary and self.state == State.PLAYING
            hits += weapon.update(dt, live, self.ship, self.asteroids + self.enemies
                                  if live else [], self.fire)
        missile_hits = self.ultimate.update(dt, False, self.ship, targets, self.fire)
        if missile_hits:
            self.audio.play("missile_hit")
        for hit in hits + missile_hits:
            if hit.target is self.boss or hit.target in boss_parts:
                self._damage_boss(hit)
            elif isinstance(hit.target, Enemy):
                self._damage_enemy(hit)
            else:
                self._damage_rock(hit)
            if not hit.continuous and hit.charges:
                self.audio.play("hit_rock" if isinstance(hit.target, Asteroid) else "hit_metal")

    def _damage_rock(self, hit):
        rock = hit.target
        if rock.destroyed or rock not in self.asteroids:
            return
        rock.damage(hit.damage, flash=not hit.continuous)
        rock.push(hit.dx, hit.dy, hit.push)
        if hit.charges:
            self._charge(hit.damage, killed=rock.destroyed)
        chips = 1 if hit.continuous and random.random() < 0.3 else 0 if hit.continuous else 2
        colors = rock.art.palette[:0:-1]
        for _ in range(chips):
            a = random.uniform(0, math.tau)
            self.smoke.emit(hit.x, hit.y, math.cos(a) * 40, math.sin(a) * 40,
                            random.uniform(0.2, 0.5), colors, drag=2)
        if rock.destroyed:
            self._destroy_rock(rock, scored=True, source=hit.source)

    def _destroy_rock(self, rock, scored, source=None):
        """Explode a rock; big ones break into smaller fragments."""
        r = rock.radius
        colors = rock.art.palette[:0:-1]    # light -> dark, without outline
        self.smoke.burst(rock.x, rock.y, 8 + r * 3, 40 + r * 4, 1.0, colors, size=(1, 2), drag=1.5)
        self.fire.burst(rock.x, rock.y, 4 + r * 2, 50 + r * 5, 0.45, FLAME[:4], size=(1, 2), drag=3)
        self.shockwaves.append(Shockwave(rock.x, rock.y, max_radius=r * 2 + 4, duration=0.3,
                                         color=colors[0]))
        if rock.SPARKLE:
            self.fire.burst(rock.x, rock.y, 6 + r * 2, 70 + r * 6, 0.5, ICE_SHARDS, size=(1, 1),
                            drag=2)
        if r >= 10 and scored:
            self.juice("medium", rock.x, rock.y)
        else:
            self.shake.add(0.04 + r * 0.012)
        if rock in self.asteroids:
            self.asteroids.remove(rock)
        self.audio.play(rock.break_sound())
        if scored:
            self.score += self.add_kill(r * POINTS_PER_RADIUS, rock.x, rock.y)
            self.wingman_kill(source)
            self.stats.destroyed += 1
            self._drop_rock_coins(rock)
            if r >= 10 and random.random() < ROCK_KIT_CHANCE:
                self.pickups.append(RepairKit(rock.x, rock.y))
        if rock.splits:
            self._split(rock)

    def _split(self, rock):
        """Fragments of the same kind (ice shatters into ice)."""
        r = rock.radius
        count, r_min, r_max, (kick_min, kick_max) = rock.fragments()
        base = random.uniform(0, math.tau)
        for i in range(count):
            art = self.library.pick(r_min, r_max, (rock.art.palette_name,))
            a = base + math.tau * i / count + random.uniform(-0.4, 0.4)
            speed = random.uniform(kick_min, kick_max)
            dx, dy = math.cos(a), math.sin(a)
            self.asteroids.append(type(rock)(
                art, rock.x + dx * r * 0.5, rock.y + dy * r * 0.5,
                rock.vx + dx * speed, rock.vy * 0.8 + dy * speed,
                spin=random.choice((-1, 1)) * random.uniform(1.5, 3.5)))

    def _damage_enemy(self, hit):
        enemy = hit.target
        if enemy not in self.enemies:
            return
        enemy.damage(hit.damage, flash=not hit.continuous)
        if not hit.continuous:
            self.fire.burst(hit.x, hit.y, 2, 40, 0.12, SPARK, size=(1, 1))
        if hit.charges:
            self._charge(hit.damage, killed=enemy.destroyed, minion=True)
        if enemy.destroyed:
            self._destroy_enemy(enemy, scored=True, source=hit.source)

    def _destroy_enemy(self, enemy, scored, source=None):
        self.explosion(enemy.x, enemy.y, size=0.6)
        if scored:
            self.juice("medium", enemy.x, enemy.y)
        self.audio.play("drone_explode")
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        if scored and self.state == State.PLAYING:
            self.score += self.add_kill(enemy.points, enemy.x, enemy.y)
            self.wingman_kill(source)
            self.stats.destroyed += 1
            self._drop_minion_coins(enemy)
            self._minion_boost(enemy)
            self.track_minion()
            if random.random() < DRONE_KIT_CHANCE:
                self.pickups.append(RepairKit(enemy.x, enemy.y))

    def _damage_boss(self, hit):
        phase, hp = self.boss.phase, self.boss.hp
        self.boss.hit_part(hit.target, hit.damage, flash=not hit.continuous)
        if self.boss.hp < hp:
            self.tally_boss_damage(hp - self.boss.hp, hit.x, hit.y)
        if self.boss.phase != phase:
            self._boss_phase_changed()
        b = self.boss
        thirds = int((b.max_hp - b.hp) / b.max_hp * 3 + 1e-6)
        if thirds > self.boss_thirds:             # every third of its health charges the ULTIMATE
            if self.ship.loadout.ultimate:
                self._charge_ultimate((thirds - self.boss_thirds) * ULT_CHARGE_PER_BOSS_THIRD)
            self.boss_thirds = thirds
        if not hit.continuous:
            self.fire.burst(hit.x, hit.y, 3, 50, 0.15, SPARK, size=(1, 1))

    def _boss_phase_changed(self):
        """The boss gets angrier; the player gets a clean screen, a POWER core and a repair kit."""
        b = self.boss
        self._clear_bullets()
        self.shockwaves.append(Shockwave(b.x, b.y, max_radius=90, duration=0.7, color=DANGER))
        self.juice("large", b.x, b.y)
        y = b.y + b.h / 2
        self.pickups.append(PowerCore(b.x - 14, y, vx=-35, vy=50))
        kit = FullRepair if b.phase == b.PHASES - 1 else RepairKit
        self.pickups.append(kit(b.x + 14, y, vx=35, vy=50))
        self._drop_boss_coins(b, phase_change=True)
        self.audio.play("boss_roar")
        mood = "IS FURIOUS!" if b.phase == b.PHASES - 1 else "IS ANGRY!"
        self.alert = [f"PHASE {b.phase + 1}", f"{b.spec.name} {mood}", DANGER, BOSS_ROAR_TIME + 0.8]

    def _boss_destroyed(self):
        b = self.boss
        self.explosion(b.x, b.y, size=3.0)
        for _ in range(6):
            self.explosion(*b.random_hull_point(), size=1.2)
        self.shockwaves.append(Shockwave(b.x, b.y, max_radius=110, duration=0.8))
        self.juice("large", b.x, b.y)
        self.screen_flash(0.15)
        self.audio.play("boss_explode")
        if self.state == State.PLAYING:
            self.wingman_kill(boss=True)
            if not self.boss_hurt:
                self.achieve("NO_HIT")
            self.score += POINTS_BOSS
            self._record_boss_time(b)
            self._drop_boss_coins(b)
            self.set_phase(Phase.CLEARED)

    def _charge(self, damage, killed, minion=False):
        """Hitting rocks and minions fills the MK III's BLAST and ULTIMATE meters."""
        bonus = 3 if minion else 1
        loadout = self.ship.loadout
        if loadout.blast and self.blast.add_charge(loadout.charge_rate * (
                damage * BLAST_CHARGE_PER_DAMAGE + killed * BLAST_CHARGE_PER_KILL * bonus)):
            self.popups.append(Popup("BLAST READY", self.ship.x, self.ship.y - 24, ACCENT))
            self.audio.play("blast_ready")
        if loadout.ultimate:
            self._charge_ultimate(damage * ULT_CHARGE_PER_DAMAGE
                                  + killed * ULT_CHARGE_PER_KILL * bonus)

    def _charge_ultimate(self, amount):
        if self.ultimate.add_charge(amount * self.ship.loadout.charge_rate):
            self.popups.append(Popup("ULTIMATE READY: T", self.ship.x, self.ship.y - 34, POWER[1]))
            self.audio.play("blast_ready")

    def explosion(self, x, y, size=1.0):
        """Generic fiery blast (used by the boss death sequence)."""
        self.fire.burst(x, y, int(25 * size), 60 + 50 * size, 0.6, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, int(8 * size), 150, 0.3, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, int(12 * size), 40, 1.0, SMOKE, size=(2, 3), drag=1.8)
        self.shockwaves.append(Shockwave(x, y, max_radius=int(14 * size), duration=0.3))
        self.shake.add(0.12 * size)
