"""Main loop and state machine."""
import math
import os
import random
from enum import Enum, auto

import pygame

from .audio import Audio
from .background import Background
from .enemies import Enemy, drone_formation
from .entities import Asteroid
from .hud import Hud, Popup
from .levels import LEVELS
from .particles import ParticleSystem, ScreenShake, Shockwave
from .pickups import FullRepair, PowerCore, RepairKit
from .pixelart import opaque_surface
from .pixelfont import PixelFont
from .settings import (ACCENT, BLAST_CHARGE_PER_DAMAGE, BLAST_CHARGE_PER_KILL,
                       BOSS_CONTACT_DAMAGE, BOSS_KIT_INTERVAL, BOSS_ROAR_TIME, BULLET_KNOCKBACK,
                       DANGER, DEATH_DELAY, DRONE_KIT_CHANCE, FLAME, FPS, FULL_KIT_CHANCE, GOOD,
                       HEAL, KIT_INTERVAL, LASER, LOW_H, LOW_W, MAX_DT, POINTS_BOSS, POINTS_DODGE,
                       POINTS_PER_RADIUS, POWER, ROCK_DAMAGE_BASE, ROCK_DAMAGE_PER_RADIUS,
                       ROCK_KIT_CHANCE, ROCK_SPLIT_RADIUS, SCALE, SMOKE, SPACE, SPARK, TEXT,
                       TEXT_DIM, TEXT_SHADOW, THROTTLE_BOOST, THROTTLE_IDLE, THROTTLE_RETRO, TITLE,
                       ULT_CHARGE_PER_BOSS_THIRD, ULT_CHARGE_PER_DAMAGE, ULT_CHARGE_PER_KILL,
                       SAVE_FILE, WARNING_TIME, WIN_H, WIN_W, WORLD_SPEED_FAST,
                       WORLD_SPEED_SLOW)
from .ship import Ship
from .storage import SaveData
from .spawner import AsteroidSpawner
from .sprites import AsteroidLibrary, ship_icon
from .weapons import Blast, Hit, Laser, MachineGun, Ultimate


class State(Enum):
    TITLE = auto()
    DEV_MENU = auto()    # --dev: pick any level / wave / boss to start from
    PLAYING = auto()
    PAUSED = auto()
    DYING = auto()       # explosion plays, then GAME_OVER
    GAME_OVER = auto()
    LEVEL_CLEAR = auto() # rocket blasts off, upgrade screen, ENTER starts the next level
    WIN = auto()         # last level cleared


class Phase(Enum):
    """Stages of a level while PLAYING."""
    FIELD = auto()       # asteroid field, progress bar fills up
    WARNING = auto()     # hull repaired, "WARNING" banner
    BOSS = auto()        # boss fight
    CLEARED = auto()     # boss destroyed, short pause before the next boss / level clear


class Keys:
    """Set of held keys, indexable like pygame.key.get_pressed().

    The game fills one from KEYDOWN/KEYUP events instead of polling get_pressed(),
    which can report stale state on macOS depending on how the window got focus.
    """

    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


MOVE_KEYS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
             pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Game:
    SHIP_START = (LOW_W / 2, LOW_H - 40)

    def __init__(self, skip_to_boss=False, start_level=1, dev=False, save_path=SAVE_FILE):
        self.skip_to_boss = skip_to_boss       # testing aid: start every run at the level boss
        self.start_level = start_level - 1     # index into LEVELS (title level select)
        self.dev = dev                         # dev menu + hotkeys; never writes the save file
        self.save = SaveData(None if dev else save_path)
        self.god = False                       # dev: the rocket takes no damage
        self.dev_cursor = 0
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(TITLE)
        self.canvas = opaque_surface((LOW_W, LOW_H))
        self.clock = pygame.time.Clock()
        self.font = PixelFont()
        self.hud = Hud(self.font)
        self.shake = ScreenShake()
        self.scanlines = self._make_scanlines()
        self.show_scanlines = True
        self._loading_screen()

        rng = random.Random()
        self.library = AsteroidLibrary(rng)
        palettes = tuple(dict.fromkeys(p for lv in LEVELS for p in lv.difficulty.palettes))
        self.library.prebuild(radii=range(4, 15), palettes=palettes)
        for palette in palettes:                  # fragments: every small size in every colour
            self.library.prebuild(radii=range(4, 9), palettes=(palette,))
        self.background = Background(rng)
        for level in LEVELS:                      # build every nebula now, not mid-game
            self.background.set_nebula(level.nebula)
        self.ship = Ship(*self.SHIP_START)
        for level in LEVELS:                      # same for every ship model's sprites
            self.ship.equip(level.loadout)
        pygame.display.set_icon(ship_icon(self.ship.frames[0]))
        self.audio = Audio()
        self.weapons = [MachineGun(), Laser()]
        self.blast = Blast()                      # MK III specials, charged by hitting things
        self.ultimate = Ultimate()

        self.fire = ParticleSystem(additive=True)
        self.smoke = ParticleSystem()
        self.shockwaves = []
        self.flash = 0.0
        self.hurt_flash = 0.0

        self.held = Keys()
        self.best = self.save.best
        self.record_rank = None                # rank of the last finished run in the records
        self.time = 0.0
        self.retry_point = (0, 0, 0, None)
        self.to_title()

    # --- setup -------------------------------------------------------------------
    def _loading_screen(self):
        self.canvas.fill(SPACE)
        self.font.draw(self.canvas, "BUILDING SPRITES...", (LOW_W // 2, LOW_H // 2), TEXT_DIM,
                       center=True)
        self._present()

    @staticmethod
    def _make_scanlines():
        lines = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        for y in range(0, WIN_H, SCALE):
            lines.fill((0, 0, 0, 38), (0, y + SCALE - 1, WIN_W, 1))
        return lines

    def new_run(self, level_index=0, score=0):
        """Start (or retry) a level. The score carries over from the previous level."""
        self.level_index = level_index
        level = self.level
        self.ship.equip(level.loadout)
        self.ship.reset(*self.SHIP_START)
        self.background.set_nebula(level.nebula)
        self.asteroids = []
        self.spawner = AsteroidSpawner(self.library, level.difficulty)
        self.score = self.level_start_score = score
        self.distance = 0.0
        self.phase = Phase.FIELD
        self.phase_time = 0.0
        self.boss = None
        self.wave_index = 0
        self.boss_index = 0
        self.boss_thirds = 0                     # thirds of the boss's health knocked off
        self.enemy_bullets = []
        self.enemies = []
        self.pickups = []
        self.popups = []
        self.kit_timer = random.uniform(*KIT_INTERVAL)
        self.formation_timer = level.difficulty.formation_interval
        self.boss_kit_timer = BOSS_KIT_INTERVAL
        self.alert = [f"LEVEL {level.number}", level.name, ACCENT, 3.0]   # title, sub, colour, time
        self.weapon_index = 0
        for weapon in self.weapons:
            weapon.reset()
            weapon.equip(level.loadout)
        self.blast.reset()
        self.ultimate.reset()
        self.fire.clear()
        self.smoke.clear()
        self.shockwaves.clear()
        self.hurt_flash = 0.0

    @property
    def weapon(self):
        return self.weapons[self.weapon_index]

    @property
    def level(self):
        return LEVELS[self.level_index]

    @property
    def wave(self):
        return self.level.waves[self.wave_index]

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def set_phase(self, phase):
        self.phase = phase
        self.phase_time = 0.0

    # --- main loop ---------------------------------------------------------------
    def run(self):
        self.audio.play_music()
        while self.handle_events():
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.update(dt, self.held)
            self.draw()
            self._present()
        pygame.quit()

    def handle_events(self):
        """Process the event queue. Returns False when the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP:
                self.held.pressed.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.held.pressed.clear()     # avoid keys "stuck" after alt-tab
            if event.type != pygame.KEYDOWN:
                continue
            key, s = event.key, self.state
            self.held.pressed.add(key)
            if key == pygame.K_c:
                self.show_scanlines = not self.show_scanlines
            elif s == State.TITLE:
                if key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) \
                        and self.selectable_levels > 1:
                    step = 1 if key in (pygame.K_RIGHT, pygame.K_d) else -1
                    self.start_level = (self.start_level + step) % self.selectable_levels
                elif key in START_KEYS or key in MOVE_KEYS:
                    self.start(self.start_level)
                elif key == pygame.K_ESCAPE:
                    return False
            elif s == State.DEV_MENU:
                items = self.dev_items()
                if key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                    step = 1 if key in (pygame.K_DOWN, pygame.K_s) else -1
                    self.dev_cursor = (self.dev_cursor + step) % len(items)
                elif key == pygame.K_g:
                    self.god = not self.god
                elif key in START_KEYS:
                    _, level_index, wave_index, boss_index = items[self.dev_cursor]
                    self.start(level_index, 0, wave_index, boss_index)
                elif key == pygame.K_ESCAPE:
                    return False
            elif s == State.PLAYING and self.dev and self.dev_key(key):
                pass
            elif s == State.PLAYING:
                if key == pygame.K_p:
                    self.set_state(State.PAUSED)
                elif key == pygame.K_ESCAPE:
                    self.to_title()
                elif key == pygame.K_r:
                    self.switch_weapon()
                elif key == pygame.K_t:
                    self.fire_ultimate()
            elif s == State.PAUSED:
                if key == pygame.K_p:
                    self.state = State.PLAYING
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s == State.GAME_OVER:
                if key == pygame.K_r or key in START_KEYS:
                    self.start(*self.retry_point)                   # retry from where we started
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s == State.LEVEL_CLEAR:
                if key in START_KEYS and self.state_time > 1.0:
                    self.start(self.level_index + 1, self.score)
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s == State.WIN:
                if key == pygame.K_r or key in START_KEYS:
                    self.start()
                elif key == pygame.K_ESCAPE:
                    self.to_title()
        return True

    def start(self, level_index=0, score=0, wave_index=0, boss_index=None):
        """Start a level; optionally at a later wave, or straight at one of its bosses."""
        self.new_run(level_index, score)
        if boss_index is None and self.skip_to_boss:
            wave_index = len(self.level.waves) - 1
            boss_index = len(self.level.waves[wave_index].bosses) - 1
        self.retry_point = (level_index, score, wave_index, boss_index)
        if wave_index:
            self.wave_index = wave_index
            self.alert = [f"WAVE {wave_index + 1}", self.wave.name, ACCENT, 3.0]
        if boss_index is not None:
            self.distance = self.wave.length
            self.boss_index = boss_index
        self.record_rank = None
        self.set_state(State.PLAYING)

    def to_title(self):
        self.new_run(self.start_level)
        self.set_state(State.DEV_MENU if self.dev else State.TITLE)

    @property
    def selectable_levels(self):
        """Levels the title screen offers: every unlocked level (or the --level one)."""
        return min(len(LEVELS), max(self.save.unlocked, self.start_level + 1))

    # --- dev mode --------------------------------------------------------------
    @staticmethod
    def dev_items():
        """Every start point in the game: (label, level index, wave index, boss index)."""
        items = []
        for li, level in enumerate(LEVELS):
            for wi, wave in enumerate(level.waves):
                tag = f"{level.number}-{wi + 1}" if len(level.waves) > 1 else f"{level.number}"
                items.append((f"LEVEL {tag}  FIELD", li, wi, None))
                for bi, entry in enumerate(wave.bosses):
                    spec = entry.spec
                    items.append((f"LEVEL {tag}  {spec.name} {spec.strength:g}X", li, wi, bi))
        return items

    def dev_key(self, key):
        """Dev hotkeys while playing. Returns True if the key was one of them."""
        if key == pygame.K_g:
            self.god = not self.god
            self.popups.append(Popup(f"GOD MODE {'ON' if self.god else 'OFF'}", self.ship.x,
                                     self.ship.y - 24, DANGER))
        elif key == pygame.K_n:
            self.dev_skip()
        elif key == pygame.K_1:
            self.blast.charge = self.ultimate.charge = 1.0
        elif key == pygame.K_2:
            for weapon in self.weapons:
                weapon.power_up()
        elif key == pygame.K_3:
            self.ship.hp = self.ship.max_hp
        else:
            return False
        return True

    def dev_skip(self):
        """End the field, finish the warning / boss entry, or knock the boss into its next
        phase (the last phase: kill it). Goes through the normal damage path, so rewards
        and charges happen as in a real fight."""
        b = self.boss
        if self.phase == Phase.FIELD:
            self.distance = self.wave.length
        elif self.phase == Phase.WARNING:
            self.phase_time = WARNING_TIME
        elif self.phase == Phase.BOSS and b.state == "enter":
            b.state_time = b.ENTER_TIME
        elif self.phase == Phase.BOSS and b.fighting:
            b.roar = 0
            floor = b.max_hp * (b.PHASES - 1 - b.phase) / b.PHASES if b.phase < b.PHASES - 1 else 0
            self._damage_boss(Hit(b, b.hp - floor + 1e-6, b.x, b.y, 0, -1, 0, charges=False))

    def switch_weapon(self):
        self.weapon_index = (self.weapon_index + 1) % len(self.weapons)

    def fire_ultimate(self):
        if self.ship.loadout.ultimate and self.ship.alive and self.ultimate.activate():
            self.alert = ["ULTIMATE!", "MISSILE STORM", ACCENT, 1.4]
            self.flash = 0.1
            self.shake.add(0.5)

    # --- update ------------------------------------------------------------------
    def update(self, dt, keys):
        self.time += dt
        self.state_time += dt
        if self.state == State.PAUSED:
            return

        firing = False
        if self.state in (State.TITLE, State.DEV_MENU):
            self.ship.update(dt, Keys(), self.fire, self.smoke)
            self.ship.y = self.SHIP_START[1] + math.sin(self.time * 2) * 2   # gentle hover
        elif self.state == State.PLAYING:
            firing = keys[pygame.K_SPACE]
            self.ship.update(dt, keys, self.fire, self.smoke)
        elif self.state in (State.WIN, State.LEVEL_CLEAR):
            self.ship.update(dt, keys, self.fire, self.smoke, autopilot=True)

        world_speed = self._world_speed()
        self.background.update(dt, world_speed)
        self._update_asteroids(dt, world_speed)
        self._update_boss(dt)
        self._update_enemies(dt)
        self._update_weapons(dt, firing)
        self._update_enemy_bullets(dt)
        self._update_pickups(dt)
        if self.state == State.PLAYING:
            self._check_ship_collisions()
            self._update_phase(dt, world_speed)
        for popup in self.popups:
            popup.update(dt)
        self.popups = [p for p in self.popups if not p.done]
        if self.alert:
            self.alert[3] -= dt
            if self.alert[3] <= 0:
                self.alert = None

        self.fire.update(dt)
        self.smoke.update(dt)
        for wave in self.shockwaves:
            wave.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]
        self.shake.update(dt)
        self.flash = max(0.0, self.flash - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)

        if self.state == State.DYING and self.state_time > DEATH_DELAY:
            self.set_state(State.GAME_OVER)

    def _update_phase(self, dt, world_speed):
        """Per wave: asteroid field -> [warning (hull repaired) -> boss -> cleared] per boss.
        After the last wave: level clear (or WIN after the last level)."""
        self.phase_time += dt
        if self.phase == Phase.FIELD:
            self.distance += dt * world_speed
            self._spawn_field_extras(dt)
            if self.distance >= self.wave.length:
                if self.wave.bosses:
                    self._begin_warning()
                else:
                    self._next_wave()
        elif self.phase == Phase.WARNING and self.phase_time >= WARNING_TIME:
            self.boss = self.wave.bosses[self.boss_index].create()
            self.boss_thirds = 0
            self.boss_kit_timer = BOSS_KIT_INTERVAL
            self.set_phase(Phase.BOSS)
        elif self.phase == Phase.BOSS and self.boss.fighting:
            self.boss_kit_timer -= dt                # a repair kit now and then during the fight
            if self.boss_kit_timer <= 0:
                self.boss_kit_timer = BOSS_KIT_INTERVAL
                self.pickups.append(RepairKit(random.uniform(30, LOW_W - 30), -8))
        elif self.phase == Phase.CLEARED and self.phase_time >= 1.5:
            self.best = max(self.best, self.score)
            if self.boss_index + 1 < len(self.wave.bosses):
                self.boss_index += 1                 # boss rush: next boss
                self._begin_warning()
            elif self.wave_index + 1 < len(self.level.waves):
                self._next_wave()
            elif self.level_index + 1 < len(LEVELS):
                self.save.unlock(self.level.number + 1)
                self.set_state(State.LEVEL_CLEAR)
            else:
                self.record_rank = self.save.add_record(self.score, self.level.number)
                self.set_state(State.WIN)

    def _next_wave(self):
        self.wave_index += 1
        self.boss_index = 0
        self.boss = None
        self.distance = 0.0
        self.set_phase(Phase.FIELD)
        self.alert = [f"WAVE {self.wave_index + 1}", self.wave.name, ACCENT, 3.0]

    def _begin_warning(self):
        self.ship.hp = self.ship.max_hp              # full health for every boss fight
        self.boss = None
        self.set_phase(Phase.WARNING)

    def _spawn_field_extras(self, dt):
        """Repair kits and (from level 2) drone formations in the asteroid field."""
        self.kit_timer -= dt
        if self.kit_timer <= 0:
            self.kit_timer = random.uniform(*KIT_INTERVAL)
            kit = FullRepair if random.random() < FULL_KIT_CHANCE else RepairKit
            self.pickups.append(kit(random.uniform(30, LOW_W - 30), -8))
        interval = self.level.difficulty.formation_interval
        if interval and self.distance < self.wave.length - 4:
            self.formation_timer -= dt
            if self.formation_timer <= 0:
                self.formation_timer = interval * random.uniform(0.8, 1.2)
                self.enemies += drone_formation()

    def _update_boss(self, dt):
        if not self.boss:
            return
        if self.boss.update(dt, self) == "defeated":
            self._boss_destroyed()
        if not self.boss.targetable:
            self._clear_bullets()                 # a dying boss's bullets fizzle out
            for enemy in list(self.enemies):      # and its drones blow up
                self._destroy_enemy(enemy, scored=False)
        if (self.state == State.PLAYING and self.boss.fighting and not self.ship.invulnerable
                and self.boss.collides_with(self.ship)):
            self.hurt_ship(BOSS_CONTACT_DAMAGE, self.boss.x, self.boss.y)

    def _boss_destroyed(self):
        b = self.boss
        self.explosion(b.x, b.y, size=3.0)
        for _ in range(6):
            self.explosion(*b.random_hull_point(), size=1.2)
        self.shockwaves.append(Shockwave(b.x, b.y, max_radius=110, duration=0.8))
        self.flash = 0.15
        self.shake.add(1.0)
        self.audio.play_crash()
        if self.state == State.PLAYING:
            self.score += POINTS_BOSS
            self.set_phase(Phase.CLEARED)

    def _boss_phase_changed(self):
        """The boss gets angrier; the player gets a clean screen, a POWER core and a repair kit."""
        b = self.boss
        self._clear_bullets()
        self.shockwaves.append(Shockwave(b.x, b.y, max_radius=90, duration=0.7, color=DANGER))
        self.shake.add(0.6)
        self.flash = 0.08
        y = b.y + b.h / 2
        self.pickups.append(PowerCore(b.x - 14, y, vx=-35, vy=50))
        kit = FullRepair if b.phase == b.PHASES - 1 else RepairKit
        self.pickups.append(kit(b.x + 14, y, vx=35, vy=50))
        mood = "IS FURIOUS!" if b.phase == b.PHASES - 1 else "IS ANGRY!"
        self.alert = [f"PHASE {b.phase + 1}", f"{b.spec.name} {mood}", DANGER, BOSS_ROAR_TIME + 0.8]

    def _clear_bullets(self):
        for b in self.enemy_bullets:
            self.fire.burst(b.x, b.y, 3, 30, 0.2, SPARK, size=(1, 1))
        self.enemy_bullets.clear()

    def _update_enemies(self, dt):
        ship = self.ship
        for enemy in list(self.enemies):
            enemy.update(dt, self)
            if enemy.offscreen:
                self.enemies.remove(enemy)
            elif (self.state == State.PLAYING and ship.alive and not ship.invulnerable
                  and enemy.collides_with(ship)):
                self._destroy_enemy(enemy, scored=False)
                self.hurt_ship(enemy.contact_damage, enemy.x, enemy.y)

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
            self._destroy_enemy(enemy, scored=True)

    def _destroy_enemy(self, enemy, scored):
        self.explosion(enemy.x, enemy.y, size=0.6)
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        if scored and self.state == State.PLAYING:
            self.score += enemy.points
            if random.random() < DRONE_KIT_CHANCE:
                self.pickups.append(RepairKit(enemy.x, enemy.y))

    def _charge(self, damage, killed, minion=False):
        """Hitting rocks and minions fills the MK III's BLAST and ULTIMATE meters."""
        bonus = 3 if minion else 1
        loadout = self.ship.loadout
        if loadout.blast and self.blast.add_charge(
                damage * BLAST_CHARGE_PER_DAMAGE + killed * BLAST_CHARGE_PER_KILL * bonus):
            self.popups.append(Popup("BLAST READY", self.ship.x, self.ship.y - 24, ACCENT))
        if loadout.ultimate:
            self._charge_ultimate(damage * ULT_CHARGE_PER_DAMAGE
                                  + killed * ULT_CHARGE_PER_KILL * bonus)

    def _charge_ultimate(self, amount):
        if self.ultimate.add_charge(amount):
            self.popups.append(Popup("ULTIMATE READY: T", self.ship.x, self.ship.y - 34, POWER[1]))

    def _update_pickups(self, dt):
        for pickup in self.pickups:
            pickup.update(dt, self.ship)
            if pickup.collected and self.state == State.PLAYING:
                text = pickup.apply(self)
                color = POWER[1] if isinstance(pickup, PowerCore) else HEAL[1]
                self.popups.append(Popup(text, pickup.x, pickup.y - 14, color))
                self.fire.burst(pickup.x, pickup.y, 16, 70, 0.4, pickup.glow, size=(1, 2))
                self.shockwaves.append(Shockwave(pickup.x, pickup.y, max_radius=16, duration=0.3,
                                                 color=pickup.glow[1]))
        self.pickups = [p for p in self.pickups if not p.collected and not p.offscreen]

    def explosion(self, x, y, size=1.0):
        """Generic fiery blast (used by the boss death sequence)."""
        self.fire.burst(x, y, int(25 * size), 60 + 50 * size, 0.6, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, int(8 * size), 150, 0.3, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, int(12 * size), 40, 1.0, SMOKE, size=(2, 3), drag=1.8)
        self.shockwaves.append(Shockwave(x, y, max_radius=int(14 * size), duration=0.3))
        self.shake.add(0.12 * size)

    def _update_enemy_bullets(self, dt):
        ship = self.ship
        kept = []
        for b in self.enemy_bullets:
            b.update(dt)
            if b.offscreen:
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
        self.enemy_bullets = kept

    def _world_speed(self):
        """Boosting (UP) speeds the world up, retro (DOWN) slows it."""
        if not self.ship.alive:
            return 0.7
        t = self.ship.throttle
        if t < THROTTLE_IDLE:
            k = (t - THROTTLE_RETRO) / (THROTTLE_IDLE - THROTTLE_RETRO)
            return WORLD_SPEED_SLOW + (1 - WORLD_SPEED_SLOW) * k
        k = (t - THROTTLE_IDLE) / (THROTTLE_BOOST - THROTTLE_IDLE)
        return 1 + (WORLD_SPEED_FAST - 1) * k

    def _update_asteroids(self, dt, world_speed):
        # Rocks spawn in the asteroid field (and on the title screen as ambience).
        if self.state in (State.TITLE, State.DEV_MENU) or (self.state == State.PLAYING
                                                            and self.phase == Phase.FIELD):
            self.asteroids += self.spawner.update(dt, world_speed)
        for rock in self.asteroids:
            rock.update(dt, world_speed)
        kept = []
        for rock in self.asteroids:
            if rock.offscreen:
                if self.state == State.PLAYING:
                    self.score += POINTS_DODGE
            else:
                kept.append(rock)
        self.asteroids = kept

    def _update_weapons(self, dt, firing):
        """Every weapon keeps simulating (bullets in flight, laser cooling); only the active one fires.
        A charged BLAST takes over from the normal weapon while it lasts."""
        targets = self.asteroids + self.enemies
        if self.boss and self.boss.targetable:
            targets.append(self.boss)
        firing = firing and self.ship.alive
        hits = []
        if self.ship.loadout.blast:
            self.blast.colors = LASER if self.weapon.name == "LASER" else FLAME[:4]
            hits += self.blast.update(dt, firing, self.ship, targets, self.fire)
        for weapon in self.weapons:
            active = firing and weapon is self.weapon and not self.blast.active
            hits += weapon.update(dt, active, self.ship, targets, self.fire)
        hits += self.ultimate.update(dt, False, self.ship, targets, self.fire)
        for hit in hits:
            if hit.target is self.boss:
                self._damage_boss(hit)
            elif isinstance(hit.target, Enemy):
                self._damage_enemy(hit)
            else:
                self._damage_rock(hit)

    def _damage_boss(self, hit):
        phase = self.boss.phase
        self.boss.damage(hit.damage, flash=not hit.continuous)
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
            self._destroy_rock(rock, scored=True)

    def _destroy_rock(self, rock, scored):
        """Explode a rock; big ones break into smaller fragments."""
        r = rock.radius
        colors = rock.art.palette[:0:-1]    # light -> dark, without outline
        self.smoke.burst(rock.x, rock.y, 8 + r * 3, 40 + r * 4, 1.0, colors, size=(1, 2), drag=1.5)
        self.fire.burst(rock.x, rock.y, 4 + r * 2, 50 + r * 5, 0.45, FLAME[:4], size=(1, 2), drag=3)
        self.shockwaves.append(Shockwave(rock.x, rock.y, max_radius=r * 2 + 4, duration=0.3,
                                         color=colors[0]))
        self.shake.add(0.04 + r * 0.012)
        if rock in self.asteroids:
            self.asteroids.remove(rock)
        if scored:
            self.score += r * POINTS_PER_RADIUS
            if r >= 10 and random.random() < ROCK_KIT_CHANCE:
                self.pickups.append(RepairKit(rock.x, rock.y))
        if r >= ROCK_SPLIT_RADIUS:
            self._split(rock)

    def _split(self, rock):
        r = rock.radius
        count = 2 if r < 12 else 3
        base = random.uniform(0, math.tau)
        for i in range(count):
            art = self.library.pick(max(4, int(r * 0.4)), max(4, int(r * 0.6)),
                                    (rock.art.palette_name,))
            a = base + math.tau * i / count + random.uniform(-0.4, 0.4)
            speed = random.uniform(25, 55)
            dx, dy = math.cos(a), math.sin(a)
            self.asteroids.append(Asteroid(
                art, rock.x + dx * r * 0.5, rock.y + dy * r * 0.5,
                rock.vx + dx * speed, rock.vy * 0.8 + dy * speed,
                spin=random.choice((-1, 1)) * random.uniform(1.5, 3.5)))

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
        if self.state != State.PLAYING or self.god:
            return
        died = self.ship.take_hit(damage, from_x, from_y, **kwargs)
        self.shake.add(0.45)
        self.hurt_flash = 0.25
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
        self.shake.add(0.9)
        self.flash = 0.12
        self.audio.play_crash()
        self.best = max(self.best, self.score)
        self.record_rank = self.save.add_record(self.score, self.level.number)
        self.set_state(State.DYING)

    # --- draw --------------------------------------------------------------------
    def draw(self):
        c = self.canvas
        c.fill(SPACE)
        self.background.draw(c)
        self.smoke.draw(c)
        for rock in self.asteroids:
            rock.draw(c)
        if self.boss:
            self.boss.draw(c)
        for enemy in self.enemies:
            enemy.draw(c)
        for pickup in self.pickups:
            pickup.draw(c)
        if self.ship.alive and self.state != State.DEV_MENU:   # the menu list needs the room
            self.ship.draw_flames(c)
            self.ship.draw(c)
        for weapon in self.weapons:
            weapon.draw(c)
        self.blast.draw(c)
        self.ultimate.draw(c)
        self.fire.draw(c)
        blink = int(self.time * 12) % 2 == 0
        for bullet in self.enemy_bullets:
            bullet.draw(c, blink)
        for wave in self.shockwaves:
            wave.draw(c)
        if self.hurt_flash > 0:
            v = int(110 * self.hurt_flash / 0.25)
            c.fill((v, 0, 0), special_flags=pygame.BLEND_ADD)
        self._draw_overlay(c)
        if self.flash > 0:
            v = int(255 * min(1.0, self.flash / 0.12))
            c.fill((v, v, v), special_flags=pygame.BLEND_ADD)

    def _draw_overlay(self, c):
        blink = int(self.time * 2.5) % 2 == 0
        s = self.state
        if s == State.TITLE:
            self._draw_title(c, blink)
            return
        if s == State.DEV_MENU:
            self._draw_dev_menu(c, blink)
            return
        loadout = self.ship.loadout
        self.hud.draw(c, self.ship, self.score, max(self.best, self.score),
                      self.distance / self.wave.length, self.weapon, self.time, boss=self.boss,
                      level=self._level_label(), blast=self.blast if loadout.blast else None,
                      ultimate=self.ultimate if loadout.ultimate else None)
        if self.dev:                                    # dev runs are marked, never recorded
            self.font.draw(c, "DEV GOD" if self.god else "DEV", (6, 24), DANGER,
                           shadow=TEXT_SHADOW)
        for popup in self.popups:
            popup.draw(c, self.font)
        if s == State.PLAYING and self.phase == Phase.WARNING:
            self._draw_warning(c)
        elif s == State.PLAYING and self.alert:
            title, subtitle, color, _ = self.alert
            self.hud.alert(c, title, subtitle, color, blink_on=int(self.time * 5) % 3 != 0)
        if s == State.PAUSED:
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            c.blit(shade, (0, 0))
            self.hud.banner(c, "PAUSED", "P TO RESUME  -  ESC FOR MENU", blink_on=blink)
        elif s == State.GAME_OVER:
            self.hud.banner(c, "GAME OVER", f"R: RETRY LEVEL {self.level.number}",
                            title_color=DANGER, blink_on=blink)
            self.font.draw(c, f"SCORE {self.score}", (LOW_W // 2, LOW_H // 2 + 40),
                           TEXT_DIM, shadow=TEXT_SHADOW, center=True)
            self._draw_record_rank(c, LOW_H // 2 + 52)
        elif s == State.LEVEL_CLEAR and self.state_time > 0.8:
            self._draw_level_clear(c, blink)
        elif s == State.WIN and self.state_time > 0.8:
            self.hud.banner(c, "YOU WIN!", "PRESS R TO PLAY AGAIN", title_color=GOOD, blink_on=blink)
            self._draw_record_rank(c, LOW_H // 2 + 40)

    def _level_label(self):
        waves = len(self.level.waves)
        return f"{self.level.number}-{self.wave_index + 1}" if waves > 1 else str(self.level.number)

    def _draw_warning(self, c):
        """Classic boss alert: blinking red stripes and WARNING, 'hull repaired' note."""
        on = int(self.phase_time * 4) % 2 == 0
        if on:
            for y in (70, 142):
                for x in range(-16, LOW_W, 16):
                    offset = int(self.phase_time * 40) % 16
                    pygame.draw.polygon(c, DANGER, [(x + offset, y), (x + offset + 8, y),
                                                    (x + offset + 12, y + 6), (x + offset + 4, y + 6)])
            self.font.draw(c, "WARNING", (LOW_W // 2, 88), DANGER, scale=4, shadow=TEXT_SHADOW,
                           center=True)
        level, bosses = self.level, self.wave.bosses
        name = bosses[self.boss_index].spec.name
        last = self.wave_index == len(level.waves) - 1 and self.boss_index == len(bosses) - 1
        if last and self.level_index == len(LEVELS) - 1:
            text = f"FINAL BOSS: {name}"
        elif last and sum(len(w.bosses) for w in level.waves) > 1:
            text = f"LEVEL BOSS: {name}"
        else:
            text = f"BOSS APPROACHING: {name}"
        self.font.draw(c, text, (LOW_W // 2, 124), TEXT, shadow=TEXT_SHADOW, center=True)
        if self.phase_time < 2.0:
            self.font.draw(c, "HULL REPAIRED", (LOW_W // 2, 160), GOOD, shadow=TEXT_SHADOW,
                           center=True)

    def _draw_level_clear(self, c, blink):
        """'LEVEL 1 CLEAR' and the ship upgrade waiting in the next level."""
        f = self.font
        nxt = LEVELS[self.level_index + 1]
        panel = pygame.Rect(0, 0, 220, 128)
        panel.midtop = (LOW_W // 2, 44)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((18, 14, 30, 200))
        c.blit(shade, panel)
        pygame.draw.rect(c, TEXT_DIM, panel, 1)
        f.draw(c, f"LEVEL {self.level.number} CLEAR", (LOW_W // 2, 52), GOOD, scale=2,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, f"SCORE {self.score}", (LOW_W // 2, 72), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if nxt.loadout != self.level.loadout:
            f.draw(c, f"SHIP UPGRADE: {nxt.loadout.name}", (LOW_W // 2, 88), ACCENT,
                   shadow=TEXT_SHADOW, center=True)
            for i, note in enumerate(nxt.upgrade_notes):
                f.draw(c, note, (LOW_W // 2, 102 + i * 10), TEXT, shadow=TEXT_SHADOW, center=True)
        if blink and self.state_time > 1.0:
            f.draw(c, f"ENTER: LEVEL {nxt.number}", (LOW_W // 2, 158), TEXT, shadow=TEXT_SHADOW,
                   center=True)

    def _draw_record_rank(self, c, y):
        if self.record_rank == 1:
            text, color = "NEW HIGH SCORE!", ACCENT
        elif self.record_rank:
            text, color = f"RECORD #{self.record_rank}", GOOD
        else:
            return
        if int(self.time * 4) % 2 == 0:
            self.font.draw(c, text, (LOW_W // 2, y), color, shadow=TEXT_SHADOW, center=True)

    def _draw_title(self, c, blink):
        f = self.font
        f.draw(c, "DODGING", (LOW_W // 2, 24), ACCENT, scale=4, shadow=DANGER, center=True)
        f.draw(c, "ASTEROID", (LOW_W // 2, 58), TEXT, scale=4, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(c, "PRESS ENTER", (LOW_W // 2, 100), TEXT, scale=2, shadow=TEXT_SHADOW, center=True)
        if self.selectable_levels > 1:                  # unlocked levels: choose with LEFT/RIGHT
            level = LEVELS[self.start_level]
            f.draw(c, f"<  LEVEL {level.number}: {level.name}  >", (LOW_W // 2, 119), ACCENT,
                   shadow=TEXT_SHADOW, center=True)
        records = self.save.records
        if records and int(self.time / 6) % 2 == 1:     # attract mode: alternate with controls
            f.draw(c, "TOP SCORES", (LOW_W // 2, 134), ACCENT, shadow=TEXT_SHADOW, center=True)
            for i, r in enumerate(records):
                line = f"{i + 1}. {r['score']:06d}  LEVEL {r['level']}  {r['date']}"
                f.draw(c, line, (LOW_W // 2, 147 + i * 10), TEXT if i == 0 else TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
            return
        lines = ("ARROWS / WASD  MOVE",
                 "UP  BOOST     DOWN  RETRO",
                 "SPACE  FIRE    R  GUN / LASER",
                 "T  ULTIMATE  (LEVEL 3)",
                 "P PAUSE   C SCANLINES   ESC QUIT")
        for i, line in enumerate(lines):
            f.draw(c, line, (LOW_W // 2, 134 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if self.best:
            f.draw(c, f"HI {self.best}", (LOW_W // 2, 8), ACCENT, shadow=TEXT_SHADOW, center=True)

    def _draw_dev_menu(self, c, blink):
        f = self.font
        f.draw(c, "DEV MODE", (LOW_W // 2, 8), DANGER, scale=2, shadow=TEXT_SHADOW, center=True)
        f.draw(c, "PICK A START POINT", (LOW_W // 2, 28), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        for i, (label, *_) in enumerate(self.dev_items()):
            selected = i == self.dev_cursor
            y = 42 + i * 12
            if selected:
                c.fill((40, 34, 58), (60, y - 2, LOW_W - 120, 11))
                f.draw(c, ">", (66, y), ACCENT, shadow=TEXT_SHADOW)
            f.draw(c, label, (78, y), ACCENT if selected else TEXT, shadow=TEXT_SHADOW)
        god = "ON" if self.god else "OFF"
        f.draw(c, f"G  GOD MODE: {god}", (LOW_W // 2, 178), DANGER if self.god else TEXT,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "UP/DOWN SELECT   ENTER START   ESC QUIT", (LOW_W // 2, 194), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "IN GAME:  N SKIP   1 CHARGE   2 POWER", (LOW_W // 2, 210), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "3 REPAIR   G GOD   ESC MENU", (LOW_W // 2, 221), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)

    def _present(self):
        ox, oy = self.shake.offset()
        self.window.fill(SPACE)
        self.window.blit(pygame.transform.scale(self.canvas, (WIN_W, WIN_H)), (ox * SCALE, oy * SCALE))
        if self.show_scanlines:
            self.window.blit(self.scanlines, (0, 0))
        pygame.display.flip()


def run_smoke_test(shots_dir=None, seed=None):
    """Drive the game headlessly through every state and mechanic; optionally save screenshots."""
    import json
    if seed is not None:
        random.seed(seed)
    from .boss import Carrier, Mothership
    from .settings import MK1, MK2, MK3, POWER_MAX, REPAIR_SMALL
    import tempfile
    save_path = os.path.join(tempfile.mkdtemp(), "save.json")   # never the player's records
    game = Game(save_path=save_path)
    field = LEVELS[0].difficulty
    # Regression: an alpha channel on the canvas turns sprites into black boxes on macOS.
    assert game.canvas.get_masks()[3] == 0, "canvas must not have an alpha channel"
    dt = 1 / FPS

    def shot(name):
        if shots_dir:
            os.makedirs(shots_dir, exist_ok=True)
            pygame.image.save(pygame.transform.scale(game.canvas, (WIN_W, WIN_H)),
                              os.path.join(shots_dir, f"{name}.png"))

    def run(frames, keys=Keys(), clear_rocks=False):
        for _ in range(frames):
            if clear_rocks:
                game.asteroids.clear()
            game.update(dt, keys)
            game.draw()

    def kill(boss):
        """A single hit can't skip a phase: hit through every phase, skipping the roars."""
        while boss.state == "fight":
            boss.roar = 0
            boss.damage(boss.max_hp)

    def post(kind, key):
        pygame.event.post(pygame.event.Event(kind, key=key, mod=0, unicode="", scancode=0))
        game.handle_events()

    run(90)
    shot("title")

    # Real input path: key events -> held keys -> ship moves diagonally, never rotates.
    game.start()
    pygame.event.clear()
    x0, y0 = game.ship.x, game.ship.y
    post(pygame.KEYDOWN, pygame.K_UP)
    post(pygame.KEYDOWN, pygame.K_RIGHT)
    run(30, game.held, clear_rocks=True)
    assert game.ship.x > x0 + 5 and game.ship.y < y0 - 5, "diagonal movement"
    assert game.ship.throttle > 0.9, "UP boosts the engine"
    assert game.ship.tilt_index == 3 and game.ship.forward[0] > 0.4, "UP+RIGHT leans like '/'"
    shot("diagonal")
    post(pygame.KEYUP, pygame.K_UP)
    post(pygame.KEYUP, pygame.K_RIGHT)
    run(40, game.held, clear_rocks=True)
    assert math.hypot(game.ship.vx, game.ship.vy) < 5, "ship stops quickly after release"
    assert game.ship.tilt_index == 0, "straightens after release"
    post(pygame.KEYDOWN, pygame.K_DOWN)
    run(30, game.held, clear_rocks=True)
    assert game.ship.throttle < 0.2, "DOWN shrinks the flames"
    post(pygame.KEYUP, pygame.K_DOWN)

    # Weapon switch.
    post(pygame.KEYDOWN, pygame.K_r)
    assert game.weapon.name == "LASER"

    def rock_ahead(radius, dist=50):
        art = game.library.pick(radius, radius, field.palettes)
        fx, fy = game.ship.forward
        return Asteroid(art, game.ship.x + fx * dist, game.ship.y + fy * dist, 0, 0, 0)

    # Laser: sustained fire destroys a big rock, which splits.
    game.start()
    game.switch_weapon()
    big = rock_ahead(12)
    game.asteroids = [big]
    fire_keys = Keys(pygame.K_SPACE)
    for i in range(240):
        game.update(dt, fire_keys)
        game.draw()
        if i == 20:
            shot("laser")
        if big not in game.asteroids:
            break
    assert big not in game.asteroids, f"laser failed, hp {big.hp:.0f}/{big.max_hp:.0f}"
    assert len(game.asteroids) >= 2, "big rock should split into fragments"
    assert game.score > 0

    # Shots slow a falling rock down (but never stop it).
    game.start()
    game.weapon_index = 0
    slow = rock_ahead(12, dist=90)
    slow.vy = 90.0
    game.asteroids = [slow]
    for _ in range(30):
        game.update(dt, fire_keys)
    assert slow.vy < 85 and slow.vy >= 12, f"push: vy {slow.vy:.1f}"

    # Machine gun kills a small rock.
    game.start()
    small = rock_ahead(5)
    game.asteroids = [small]
    for i in range(120):
        game.asteroids = [r for r in game.asteroids if r is small]   # no stray rocks in the way
        game.update(dt, fire_keys)
        game.draw()
        if i == 10:
            shot("gun")
        if small not in game.asteroids:
            break
    assert small not in game.asteroids, "machine gun failed"

    # Laser overheats.
    game.start()
    game.switch_weapon()
    run(int(3 / dt), fire_keys, clear_rocks=True)
    assert game.weapon.overheated

    # Asteroid collision costs health, then invulnerability protects.
    game.start()
    game.asteroids = [Asteroid(game.library.pick(10, 10, field.palettes),
                               game.ship.x, game.ship.y, 0, 0, 0)]
    run(1)
    assert 0 < game.ship.hp < 100 and game.ship.invulnerable
    shot("hurt")

    # Losing all health -> explosion -> game over.
    game.ship.invulnerable_time = 0
    game.ship.hp = 1
    game.asteroids = [Asteroid(game.library.variants[-1], game.ship.x, game.ship.y, 0, 0, 0)]
    for i in range(int((DEATH_DELAY + 0.3) * FPS)):
        game.update(dt, Keys())
        game.draw()
        if i == 8:
            shot("explosion")
    assert game.state == State.GAME_OVER, game.state
    shot("game_over")

    # Boss balance: the rocket is strength-times weaker in a damage race (with its level's ship).
    for level in LEVELS:
        for entry in (e for wave in level.waves for e in wave.bosses):
            spec = entry.spec
            assert spec.player == level.loadout, f"{spec.name} balanced for the wrong ship"
            ratio = (spec.hp / spec.player.gun_dps) / (spec.player.max_hp / spec.dps)
            assert abs(ratio - spec.strength) < 1e-6, ratio

    # Repair kits heal (capped at max hp); a full kit restores everything.
    game.start()
    game.ship.hp = 40
    game.pickups = [RepairKit(game.ship.x, game.ship.y - 60)]
    run(120, clear_rocks=True)
    assert game.ship.hp == 40 + REPAIR_SMALL and not game.pickups, "small kit (magnet + heal)"
    game.pickups = [FullRepair(game.ship.x, game.ship.y)]
    run(2, clear_rocks=True)
    assert game.ship.hp == game.ship.max_hp
    game.pickups = [RepairKit(game.ship.x, game.ship.y - 50)]
    run(20, clear_rocks=True)
    shot("pickup")

    # Boss flow: end of field -> warning (hull repaired) -> boss fight -> defeated -> level clear.
    game.start()
    game.ship.hp = 30
    game.distance = game.wave.length
    run(2)
    assert game.phase == Phase.WARNING and game.ship.hp == game.ship.max_hp
    run(int(1.0 / dt))
    shot("warning")
    run(int(WARNING_TIME / dt))
    assert game.phase == Phase.BOSS and game.boss is not None
    run(int(3.0 / dt), clear_rocks=True)
    assert game.boss.fighting
    shot("boss_enter")
    game.ship.hp = 10 ** 9          # watch the boss attack without dying
    run(int(4.0 / dt), clear_rocks=True)
    assert game.ship.hp < 10 ** 9, "boss bullets should hit a rocket that sits still"
    shot("boss_attack")
    hp0 = game.boss.hp
    game.ship.x = game.boss.x
    for _ in range(60):
        game.ship.x = game.boss.x
        game.update(dt, fire_keys)
    assert game.boss.hp < hp0, "player bullets damage the boss"
    game.boss.hp = game.boss.max_hp * 0.4             # enraged phase
    run(int(5.0 / dt), clear_rocks=True)
    shot("boss_enraged")
    game.boss.damage(game.boss.max_hp)
    assert game.boss.state == "dying"
    for i in range(int((game.boss.DEATH_TIME + 0.3) / dt)):
        game.update(dt, Keys())
        game.draw()
        if i == 40:
            shot("boss_dying")
    assert game.phase == Phase.CLEARED
    run(int(1.6 / dt))
    assert game.state == State.LEVEL_CLEAR, game.state
    run(int(1.2 / dt))
    shot("level_clear")

    # Level 2: upgraded ship, crimson field with drone formations.
    post(pygame.KEYDOWN, pygame.K_RETURN)
    assert game.state == State.PLAYING and game.level.number == 2
    assert game.score > 0, "score carries over"
    assert game.ship.loadout == MK2 and game.ship.hp == MK2.max_hp == game.ship.max_hp
    assert game.weapons[0].loadout == MK2 and game.weapons[1].power == 0
    run(int(1.0 / dt), clear_rocks=True)
    shot("level2_intro")
    game.formation_timer = 0
    run(2, clear_rocks=True)
    assert len(game.enemies) == 5, "level 2 spawns drone formations"
    game.enemies = drone_formation("line")      # one drone flies straight down the middle
    game.formation_timer = 99
    game.ship.hp = 10 ** 9
    run(int(2.5 / dt), Keys(pygame.K_SPACE), clear_rocks=True)
    shot("level2_drones")
    assert game.score > game.level_start_score, "drones get shot down"
    drone = drone_formation("v")[0]
    drone.x, drone.y = game.ship.x, game.ship.y
    game.enemies = [drone]
    game.ship.hp, game.ship.invulnerable_time = 100, 0
    run(1)
    assert game.ship.hp < 100 and drone not in game.enemies, "ramming a drone hurts"

    # Level 2 boss rush: weakened Gunship first, then the Carrier.
    game.distance = game.wave.length
    run(int((WARNING_TIME + 0.2) / dt), clear_rocks=True)
    assert game.boss.spec.name == "GUNSHIP" and game.boss.spec.strength == 1.5
    run(int(3.0 / dt), clear_rocks=True)
    game.boss.damage(game.boss.max_hp)
    game.ship.hp = 10
    run(int((game.boss.DEATH_TIME + 1.7) / dt), clear_rocks=True)
    assert game.phase == Phase.WARNING and game.boss_index == 1
    run(int((WARNING_TIME + 3.0) / dt), clear_rocks=True)
    carrier = game.boss
    assert isinstance(carrier, Carrier) and carrier.fighting, (carrier, carrier.state)
    assert game.ship.hp > 10 and game.ship.max_hp == MK2.max_hp, "hull repaired before the carrier"
    game.ship.hp = 10 ** 9
    run(int(1.2 / dt), clear_rocks=True)
    assert game.enemies, "carrier launches drones"
    run(int(2.8 / dt), clear_rocks=True)
    shot("carrier_phase1")

    # Phase change at 2/3 hp: clamped, roars (invulnerable), clears bullets, drops rewards.
    carrier.hp = carrier.max_hp * 0.7
    for _ in range(3):
        game._damage_boss(Hit(carrier, carrier.max_hp * 0.2, carrier.x, carrier.y, 0, -1, 0))
    assert carrier.phase == 1 and abs(carrier.hp - carrier.max_hp * 2 / 3) < 1e-6, carrier.hp
    assert carrier.roar > 0 and not game.enemy_bullets
    assert any(isinstance(p, PowerCore) for p in game.pickups)
    assert any(isinstance(p, RepairKit) for p in game.pickups)
    run(int(0.5 / dt), clear_rocks=True)
    shot("carrier_roar")
    run(int(4.0 / dt), clear_rocks=True)
    assert all(w.power == 1 for w in game.weapons), "POWER core homes in and powers both weapons"
    shot("carrier_phase2")
    game._damage_boss(Hit(carrier, carrier.max_hp * 0.34, carrier.x, carrier.y, 0, -1, 0))
    assert carrier.phase == 2 and any(isinstance(p, FullRepair) for p in game.pickups)
    run(int(6.0 / dt), clear_rocks=True)
    assert all(w.power == POWER_MAX for w in game.weapons)
    shot("carrier_phase3")
    hp0 = carrier.hp
    for _ in range(90):
        game.ship.x = carrier.x
        game.update(dt, fire_keys)
    assert carrier.hp < hp0, "powered gun damages the carrier"
    shot("carrier_powered_gun")
    carrier.damage(carrier.max_hp)
    run(int((carrier.DEATH_TIME + 0.3) / dt))
    assert not game.enemies, "drones die with the carrier"
    run(int(1.6 / dt))
    assert game.state == State.LEVEL_CLEAR, game.state
    run(int(1.2 / dt))
    shot("level2_clear")

    # Level 3: MK III with BLAST and ULTIMATE, three waves.
    post(pygame.KEYDOWN, pygame.K_RETURN)
    assert game.level.number == 3 and game.ship.loadout == MK3 and game.wave_index == 0
    assert game.blast.charge == 0 and game.ultimate.charge == 0
    game.ship.hp = 10 ** 9
    run(int(1.0 / dt), clear_rocks=True)
    shot("level3_intro")

    # Damaging rocks charges both meters; hits from the specials themselves don't.
    rock = rock_ahead(12)
    game.asteroids = [rock]
    game._damage_rock(Hit(rock, 700, rock.x, rock.y, 0, -1, 0))
    assert game.blast.charge > 0.5 and 0 < game.ultimate.charge < 0.5, (game.blast.charge,
                                                                         game.ultimate.charge)
    before = game.blast.charge, game.ultimate.charge
    rock = rock_ahead(12)
    game.asteroids = [rock]
    game._damage_rock(Hit(rock, 50, rock.x, rock.y, 0, -1, 0, charges=False))
    assert (game.blast.charge, game.ultimate.charge) == before

    # BLAST: charged + fire = huge beam that destroys everything in front, then recharges.
    game.blast.charge = 1.0
    front = [rock_ahead(14, dist=70), rock_ahead(11, dist=130)]
    game.asteroids = list(front)
    game.enemies = []
    for i in range(int(0.8 / dt)):
        game.update(dt, fire_keys)
        game.draw()
        if i == 20:
            shot("blast")
    assert game.blast.active and not any(r in game.asteroids for r in front), "blast destroys"
    assert not game.weapons[0].bullets, "the normal gun pauses while the blast fires"
    run(int(2.5 / dt), fire_keys, clear_rocks=True)
    assert not game.blast.active and game.blast.charge < 0.05, game.blast.charge

    # ULTIMATE: T launches homing missiles at every target on screen.
    post(pygame.KEYDOWN, pygame.K_t)
    assert not game.ultimate.active, "not charged yet"
    game.ultimate.charge = 1.0
    art = game.library.pick(6, 6, field.palettes)
    spread = [Asteroid(art, x, 70, 0, 0, 0) for x in (40, 120, 200, 280)]
    game.asteroids = list(spread)
    game.enemies = drone_formation("line")
    for e in game.enemies:
        e.y = 40
    post(pygame.KEYDOWN, pygame.K_t)
    assert game.ultimate.active
    for i in range(int(3.0 / dt)):
        game.update(dt, Keys())
        game.draw()
        if i == 40:
            shot("ultimate")
    left = [r for r in spread if r in game.asteroids]
    assert len(left) <= 1, f"missiles missed {len(left)} rocks"
    run(int(3.0 / dt), clear_rocks=True)                 # stragglers fly off or hit
    assert not game.ultimate.active and not game.ultimate.missiles

    # Wave 1 has no boss: straight on to wave 2.
    game.distance = game.wave.length
    run(2, clear_rocks=True)
    assert game.wave_index == 1 and game.phase == Phase.FIELD and game.alert[0] == "WAVE 2"
    shot("wave2")
    # Wave 2 ends with the Carrier (weakened); each third of its health charges the ULTIMATE.
    game.distance = game.wave.length
    run(int((WARNING_TIME + 3.0) / dt), clear_rocks=True)
    assert isinstance(game.boss, Carrier) and game.boss.spec.strength == 1.5
    game.ultimate.reset()
    game._damage_boss(Hit(game.boss, game.boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert abs(game.ultimate.charge - 0.25) < 1e-6, game.ultimate.charge
    kill(game.boss)
    run(int((Carrier.DEATH_TIME + 1.7) / dt), clear_rocks=True)
    assert game.wave_index == 2 and game.phase == Phase.FIELD, (game.wave_index, game.phase)

    # Wave 3: the final boss.
    game.distance = game.wave.length
    game.ship.hp = 5
    run(int(1.0 / dt), clear_rocks=True)
    assert game.phase == Phase.WARNING and game.ship.hp == MK3.max_hp
    shot("final_warning")
    run(int((WARNING_TIME + 2.0) / dt), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Mothership) and boss.fighting
    game.ship.hp = 10 ** 9
    run(int(4.5 / dt), clear_rocks=True)
    assert game.enemies, "mothership launches drones"
    shot("mothership_phase1")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 1 and any(isinstance(p, PowerCore) for p in game.pickups)
    fired = False
    game.ship.hp = 1000
    for i in range(int(4.0 / dt)):                 # phase 2 opens with the sweeping beam
        game.ship.x = boss.x
        game.update(dt, Keys())
        game.draw()
        if boss.beam == 2 and not fired:
            fired = True
            run(10, clear_rocks=True)
            shot("mothership_beam")
    assert fired and game.ship.hp < 1000, "the beam hurts a rocket under it"
    assert game.state == State.PLAYING, "invulnerability after a hit stops the beam shredding"
    game.ship.hp = 10 ** 9
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 2
    run(int(6.0 / dt), clear_rocks=True)
    shot("mothership_phase3")
    kill(boss)
    run(int((boss.DEATH_TIME + 1.9) / dt))
    assert game.state == State.WIN, game.state
    run(int(1.0 / dt))
    shot("win")

    # Records + unlocks are saved and survive a reload; a corrupt file doesn't crash.
    assert game.record_rank and game.save.unlocked == 3
    reloaded = SaveData(save_path)
    assert reloaded.records == game.save.records and reloaded.unlocked == 3
    assert reloaded.best == game.save.best > 0
    with open(save_path, "w") as f:
        f.write("{not json")
    assert SaveData(save_path).records == [] and SaveData(save_path).unlocked == 1
    game.save.save()                                     # restore it for the checks below

    # Title: unlocked levels can be chosen with LEFT/RIGHT; the score table alternates in.
    game.to_title()
    assert game.state == State.TITLE and game.selectable_levels == 3
    post(pygame.KEYDOWN, pygame.K_RIGHT)
    post(pygame.KEYDOWN, pygame.K_RIGHT)
    assert game.start_level == 2
    game.time = 6.5                                      # attract mode: TOP SCORES panel
    game.draw()
    shot("title_records")
    post(pygame.KEYDOWN, pygame.K_RETURN)
    assert game.state == State.PLAYING and game.level.number == 3 and game.score == 0
    game.start_level = 0

    # Dev mode: a menu of every start point, god mode, hotkeys, nothing saved.
    records_before = list(game.save.records)
    game.dev, game.save = True, SaveData(None)
    game.to_title()
    assert game.state == State.DEV_MENU
    items = game.dev_items()
    assert len(items) == sum(len(lv.waves) + sum(len(w.bosses) for w in lv.waves) for lv in LEVELS)
    run(2)
    shot("dev_menu")
    target = next(i for i, it in enumerate(items) if "MOTHERSHIP" in it[0])
    for _ in range(target):
        post(pygame.KEYDOWN, pygame.K_DOWN)
    post(pygame.KEYDOWN, pygame.K_g)
    assert game.god
    post(pygame.KEYDOWN, pygame.K_RETURN)
    assert game.state == State.PLAYING and game.level.number == 3 and game.wave_index == 2
    run(2)
    assert game.phase == Phase.WARNING
    post(pygame.KEYDOWN, pygame.K_n)                     # skip the warning
    run(2)
    assert isinstance(game.boss, Mothership)
    post(pygame.KEYDOWN, pygame.K_n)                     # skip the entry
    run(2)
    assert game.boss.fighting
    game.hurt_ship(50, 0, 0)
    assert game.ship.hp == MK3.max_hp, "god mode"
    post(pygame.KEYDOWN, pygame.K_n)                     # next phase, with its rewards
    assert game.boss.phase == 1 and any(isinstance(p, PowerCore) for p in game.pickups)
    post(pygame.KEYDOWN, pygame.K_1)
    post(pygame.KEYDOWN, pygame.K_2)
    assert game.blast.charge == 1 and game.weapons[0].power >= 1
    run(int(0.5 / dt))
    shot("dev_play")
    for _ in range(2):
        run(int(1.7 / dt))                               # wait out the roar
        post(pygame.KEYDOWN, pygame.K_n)
    assert game.boss.state == "dying", game.boss.state
    post(pygame.KEYDOWN, pygame.K_ESCAPE)
    assert game.state == State.DEV_MENU
    game.god = False
    game.start(1, 0, 0, None)
    game.score = 500
    game.ship.hp = 1
    game.hurt_ship(5, 0, 0)
    run(int((DEATH_DELAY + 0.2) / dt))
    assert game.state == State.GAME_OVER and game.save.records != [] and game.save.path is None
    with open(save_path) as f:
        assert len(json.load(f)["records"]) == len(records_before), "dev runs don't touch the file"
    game.dev, game.save = False, SaveData(save_path)

    # Game over in level 2 retries level 2 with the score it started with.
    game.start(1, 1234)
    game.ship.hp = 1
    game.hurt_ship(5, 0, 0)
    run(int((DEATH_DELAY + 0.2) / dt))
    post(pygame.KEYDOWN, pygame.K_r)
    assert game.level.number == 2 and game.score == 1234 and game.ship.loadout == MK2
    game.start(0)
    assert game.ship.loadout == MK1 and game.ship.max_hp == MK1.max_hp

    # A busy minute of normal play must not crash: every field, the Carrier and the Mothership,
    # with BLAST and ULTIMATE going off in level 3.
    pattern = [Keys(pygame.K_UP, pygame.K_SPACE), Keys(pygame.K_LEFT, pygame.K_SPACE),
               Keys(pygame.K_DOWN, pygame.K_RIGHT), Keys(pygame.K_SPACE)]
    for name, level_index, boss_fight in (("busy", 0, False), ("busy_level2", 1, False),
                                          ("busy_carrier", 1, True), ("busy_level3", 2, False),
                                          ("busy_mothership", 2, True)):
        game.start(level_index)
        game.ship.hp = game.ship.max_hp = 10 ** 9
        if boss_fight:
            game.wave_index = len(game.level.waves) - 1
            game.distance = game.wave.length
            game.boss_index = len(game.wave.bosses) - 1
        else:
            game.distance = -10 ** 9          # stay in the asteroid field
        for i in range(3600):
            if i % 600 == 0:
                game.switch_weapon()
            if i % 700 == 350 and game.ship.loadout.ultimate:
                game.blast.charge = game.ultimate.charge = 1.0
                game.fire_ultimate()
            if game.boss and game.boss.fighting:
                if i % 900 == 0 and game.boss.phase < game.boss.PHASES - 1:
                    game._damage_boss(Hit(game.boss, game.boss.max_hp * 0.3, 0, 0, 0, -1, 0))
                game.boss.hp = max(game.boss.hp, game.boss.max_hp * 0.2)    # keep it fighting
            game.update(dt, pattern[(i // 90) % len(pattern)])
            game.draw()
            if i == 1800:
                shot(name)
        assert game.state == State.PLAYING, game.state
    pygame.quit()
    print("smoke test OK")
