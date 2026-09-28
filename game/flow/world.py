"""World update: moving rocks, minions, the boss, enemy bullets and pickups; hazards to the ship."""
from ..config.palette import FLAME, SMOKE, SPARK
from ..config.tuning import (AMBUSH_ROCKS, BULLET_KNOCKBACK, POINTS_DODGE, ROCK_DAMAGE_BASE,
                             ROCK_DAMAGE_PER_RADIUS)
from ..core.particles import Shockwave
from ..ui.popup import Popup
from .states import MENU_STATES, Phase, State


class WorldMixin:
    """Game mixin: advances everything in the world and hurts the ship when it gets hit."""

    def _update_asteroids(self, dt, world_speed):
        # Rocks spawn in the asteroid field (and on the title screen as ambience).
        ambush = self.phase == Phase.BOSS and self.wave.ambush    # the field goes on
        if self.state in MENU_STATES or (self.state == State.PLAYING
                                         and (self.phase == Phase.FIELD or ambush)):
            rate = self.pressure * (AMBUSH_ROCKS if ambush else 1.0)
            self.asteroids += self.spawner.update(dt * rate, world_speed)
        for i, rock in enumerate(self.asteroids):
            rock.update(dt, world_speed)
            grown = getattr(rock, "transform", None)    # a marrow core grows its bone back
            new = grown() if grown else None
            if new:
                self.asteroids[i] = new
                self.fire.burst(new.x, new.y, 10, 50, 0.3, [(255, 220, 220), (220, 60, 80)],
                                size=(1, 2))
        kept = []
        for rock in self.asteroids:
            if rock.offscreen:
                if self.state == State.PLAYING:
                    self.score += POINTS_DODGE
                    self.stats.escaped += 1
            else:
                kept.append(rock)
        self.asteroids = kept

    def _update_boss(self, dt):
        if not self.boss:
            return
        result = self.boss.update(dt, self)
        if result == "defeated":
            self._boss_destroyed()
        elif result == "escaped":                   # it left the fight (NYX in its court)
            self._boss_escaped()
        if not self.boss.targetable:
            self._clear_bullets()                 # a dying boss's bullets fizzle out
            for enemy in list(self.enemies):      # and its drones blow up
                self._destroy_enemy(enemy, scored=False)
        if (self.state == State.PLAYING and self.boss.fighting and not self.ship.invulnerable
                and self.boss.collides_with(self.ship)):
            self.hurt_ship(self.boss.contact_damage, self.boss.x, self.boss.y)

    def _update_enemies(self, dt):
        ship = self.ship
        for enemy in list(self.enemies):
            enemy.update(dt, self)
            if enemy.destroyed and enemy in self.enemies:     # e.g. a turret whose rock broke
                self._destroy_enemy(enemy, scored=self.state == State.PLAYING)
                continue
            if enemy.offscreen:
                self.enemies.remove(enemy)
                if self.state == State.PLAYING and enemy.stat:
                    self.stats.escaped += 1
            elif (self.state == State.PLAYING and ship.alive and not ship.invulnerable
                  and enemy.collides_with(ship)):
                self._destroy_enemy(enemy, scored=False)
                if enemy.contact_damage:
                    self.hurt_ship(enemy.contact_damage, enemy.x, enemy.y)

    def _update_enemy_bullets(self, dt):
        ship = self.ship
        kept, born = [], []
        for b in self.enemy_bullets:
            b.update(dt)
            burst = getattr(b, "burst", None)            # splitters, runes (minions/veil_bullets)
            children = burst() if burst else None
            if children:
                born += children
            if b.offscreen:
                continue
            if not getattr(b, "solid", True):            # a rune mark can't hurt
                kept.append(b)
                continue
            if self.state == State.PLAYING and self.wingman_block(b):
                continue
            if self.state == State.PLAYING and ship.alive and not ship.invulnerable:
                sx, sy = ship.topleft
                mx, my = int(b.x) - sx, int(b.y) - sy
                w, h = ship.mask.get_size()
                if 0 <= mx < w and 0 <= my < h and ship.mask.get_at((mx, my)):
                    self.fire.burst(b.x, b.y, 8, 60, 0.25, SPARK, size=(1, 1))
                    self.hurt_ship(b.damage, b.x, b.y, knockback=BULLET_KNOCKBACK)
                    continue
            kept.append(b)
        self.enemy_bullets = kept + born

    def _clear_bullets(self):
        for b in self.enemy_bullets:
            self.fire.burst(b.x, b.y, 3, 30, 0.2, SPARK, size=(1, 1))
        self.enemy_bullets.clear()

    def _update_pickups(self, dt):
        for pickup in self.pickups:
            pickup.update(dt, self.ship)
            if pickup.collected and self.state == State.PLAYING:
                text = pickup.apply(self)
                self.audio.play(pickup.sound)
                if not pickup.fanfare:                   # coins: a small sparkle
                    self.fire.burst(pickup.x, pickup.y, 4, 40, 0.25, pickup.glow, size=(1, 1))
                    continue
                self.popups.append(Popup(text, pickup.x, pickup.y - 14, pickup.glow[1]))
                self.fire.burst(pickup.x, pickup.y, 16, 70, 0.4, pickup.glow, size=(1, 2))
                self.shockwaves.append(Shockwave(pickup.x, pickup.y, max_radius=16, duration=0.3,
                                                 color=pickup.glow[1]))
        self.pickups = [p for p in self.pickups if not p.collected and not p.offscreen]

    def _check_ship_collisions(self):
        if self.ship.invulnerable:
            return
        for rock in self.asteroids:
            if rock.collides_with(self.ship):
                damage = ROCK_DAMAGE_BASE + ROCK_DAMAGE_PER_RADIUS * rock.radius
                self._destroy_rock(rock, scored=False)
                self.hurt_ship(damage, rock.x, rock.y)
                return

    def hurt_ship(self, damage, from_x, from_y, **kwargs):
        if self.state != State.PLAYING or self.god or self.ship.invulnerable:
            return
        if self.absorb_hit(from_x, from_y):          # SHIELD boost
            return
        damage *= self.glass                         # VEIL SHIFT "GLASS CANNON"
        self.break_combo()
        hp = self.ship.hp
        died = self.ship.take_hit(damage, from_x, from_y, **kwargs)
        self.stats.damage_taken += max(0, hp - self.ship.hp)
        self.note_damage(max(0, hp - self.ship.hp))
        if self.boss and hasattr(self.boss, "credit"):       # a learning boss scores it
            self.boss.credit(max(0, hp - self.ship.hp))
        self.last_hurt = self.time
        if self.phase == Phase.BOSS and self.ship.hp < hp:
            self.boss_hurt = True
        if died and self.try_revive():               # MEDIC level 5
            died = False
        if self.ship.hp < hp and not died:
            self.audio.play("ship_hurt")
        self.juice("medium")
        self.hurt_flash = 0.25 if self.options["flashes"] else 0.08
        if died:
            self._ship_destroyed()

    def _ship_destroyed(self):
        ship = self.ship
        ship.alive = False
        x, y = ship.x, ship.y
        hull = [ship.colors[c] for c in "WLRGDr"]
        self.fire.burst(x, y, 90, 150, 0.9, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, 30, 230, 0.35, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, 40, 60, 1.4, SMOKE, size=(2, 3), drag=1.8)
        self.smoke.burst(x, y, 30, 120, 1.3, hull, size=(1, 2), drag=0.8)
        self.shockwaves.append(Shockwave(x, y, max_radius=46))
        self.shockwaves.append(Shockwave(x, y, max_radius=24, duration=0.3, color=(255, 255, 255)))
        self.juice("large", x, y)
        self.death_style(x, y)
        self.audio.play("ship_explode")
        self._bank_wingman_xp()
        self.best = max(self.best, self.score)
        self.record_rank = self.save.add_record(self.score, self.level_index + 1)
        self.set_state(State.DYING)
