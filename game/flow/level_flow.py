"""Level flow: starting runs, the field -> warning -> boss -> cleared cycle, waves, level clear."""
import random
from dataclasses import replace

from ..config.display import LOW_W
from ..config.palette import ACCENT
from ..config.tuning import (BOSS_KIT_INTERVAL, FULL_KIT_CHANCE, GALAXY1_TIERS, KIT_INTERVAL,
                             WARNING_TIME)
from ..levels.data import LEVELS, galaxy_of, level_title
from ..minions.diver import diver_squad
from ..minions.drone import drone_formation
from ..obstacles.spawner import AsteroidSpawner
from ..pickups.types import FullRepair, RepairKit
from ..progression import upgrades
from ..story.dialog import UNKNOWN, Line
from .states import Phase, State


class LevelFlowMixin:
    """Game mixin: runs, levels, waves and the phases of a level."""

    def new_run(self, level_index=0, score=0):
        """Start (or retry) a level. The score carries over from the previous level."""
        self.level_index = level_index
        level = self.level
        loadout = self.loadout_for(level)
        self.ship.equip(loadout, self.hull)
        self.ship.reset(*self.SHIP_START)
        self._reset_progress()
        self._reset_juice()
        self._reset_boosts()
        self._reset_wingmen()
        self._reset_achievements()
        self._reset_brains()
        self._reset_shift()
        self._reset_abilities()
        self.background.set_nebula(level.nebula)
        self.background.set_event(level.event)
        self.hazard = level.hazard() if level.hazard else None
        self.extra_timers = [interval for _, interval in level.difficulty.extras]
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
        self.refractions = []                    # split laser beams (crystal rocks)
        self.enemies = []
        self.pickups = []
        self.popups = []
        self.kit_timer = random.uniform(*KIT_INTERVAL)
        self.formation_timer = level.difficulty.formation_interval
        self.diver_timer = level.difficulty.diver_interval
        self.boss_kit_timer = BOSS_KIT_INTERVAL
        self.alert = [level_title(level), level.name, ACCENT, 3.0]   # title, sub, colour, time
        for weapon in self.weapons + list(self.secondaries.values()):
            weapon.reset()
            weapon.equip(loadout)
        names = [w.name for w in self.weapons]
        self.weapon_index = names.index(self.primaries[0])
        self.apply_skins()
        self.blast.reset()
        self.ultimate.reset()
        self.fire.clear()
        self.smoke.clear()
        self.shockwaves.clear()
        self.hurt_flash = 0.0

    def start(self, level_index=0, score=0, wave_index=0, boss_index=None):
        """Start a level; optionally at a later wave, or straight at one of its bosses."""
        self.new_run(level_index, score)
        self.begin_learning()
        self.roll_shift()
        if boss_index is None and self.skip_to_boss:
            wave_index = len(self.level.waves) - 1
            boss_index = len(self.level.waves[wave_index].bosses) - 1
        self.retry_point = (level_index, score, wave_index, boss_index)
        if wave_index:
            self.wave_index = wave_index
            self.alert = [f"WAVE {wave_index + 1}", self.wave.name, ACCENT, 3.0]
        if boss_index is None:
            self.radio_say(self.wave.radio if wave_index else self.level.radio)
        else:
            self.distance = self.wave.length
            self.boss_index = boss_index
        self.record_rank = None
        self.medal_new = False                 # the finale awarded a new galaxy medal
        self.set_state(State.PLAYING)

    def loadout_for(self, level):
        """The level's ship model as flown with the chosen hull, plus the upgrades bought;
        BLAST + ULTIMATE only once the player owns them (the level 2 gift). Bosses keep
        using the par model (level.loadout)."""
        tiers = self.inventory.tiers
        if galaxy_of(level).number == 1:                 # tiers 6-10 are galaxy 2 tech
            tiers = {k: min(v, GALAXY1_TIERS) for k, v in tiers.items()}
        loadout = upgrades.apply(self.hull.apply(level.loadout), tiers)
        loadout = replace(loadout, colors=self.paint_for(loadout))       # paint skin
        if not self.inventory.owns("SPECIALS"):
            loadout = replace(loadout, blast=False, ultimate=False)
        return loadout

    @property
    def primaries(self):
        """The equipped primary weapons (1-2 names) the player owns; R switches between them."""
        chosen = self.save.primaries or ["GUN", "LASER"]
        owned = [name for name in chosen if self.inventory.owns(name)]
        return owned or ["GUN"]

    @property
    def secondary(self):
        """The equipped secondary weapon (or None)."""
        name = self.save.secondary
        return self.secondaries[name] if name in self.secondaries and self.inventory.owns(name) else None

    def choose_hull(self, hull):
        """Pick a hull (remembered in the save file) and build its sprites for every level now,
        so no level start has to."""
        self.hull = hull
        self.save.choose_ship(hull.name)
        for level in LEVELS:
            self.ship.equip(self.loadout_for(level), hull)
        self.ship.equip(self.loadout_for(self.level), hull)

    def to_title(self):
        if hasattr(self, "player_model"):
            self.save_brain()                     # what they learned in that attempt
        self.new_run(self.start_level)
        self.set_state(State.DEV_MENU if self.dev else State.TITLE)

    @property
    def selectable_levels(self):
        """Levels the title screen offers: every unlocked level (or the --level one)."""
        return min(len(LEVELS), max(self.save.unlocked, self.start_level + 1))

    def _update_phase(self, dt, world_speed):
        """Per wave: asteroid field -> [warning (hull repaired) -> boss -> cleared] per boss.
        After the last wave: level clear (or WIN after the last level)."""
        self.phase_time += dt
        if self.phase == Phase.FIELD:
            self.distance += dt * world_speed
            self._spawn_field_extras(dt)
            wave = self.wave
            if wave.ambush and wave.bosses and self.distance >= wave.ambush * wave.length:
                self._ambush()
            elif self.distance >= self.wave.length:
                self.track_field_done()
                if self.wave.bosses:
                    self._begin_warning()
                else:
                    self._finish_wave()
        elif self.phase == Phase.WARNING and self.phase_time >= WARNING_TIME:
            self._spawn_boss()
        elif self.phase == Phase.BOSS and self.boss.fighting:
            self.boss_kit_timer -= dt                # a repair kit now and then during the fight
            if self.boss_kit_timer <= 0 and self.kits_allowed:
                self.boss_kit_timer = BOSS_KIT_INTERVAL
                self.pickups.append(RepairKit(random.uniform(30, LOW_W - 30), -8))
        elif self.phase == Phase.CLEARED and self.phase_time >= 1.5:
            self.best = max(self.best, self.score)
            if self.boss_index + 1 < len(self.wave_bosses):
                self.boss_index += 1                 # boss rush: next boss
                self._begin_warning()
            else:
                self._finish_wave()

    def _finish_wave(self):
        """The wave is done: the next wave, level clear, or (after the last level) the win —
        a galaxy finale plays the warp cut-scene first."""
        if self.wave_index + 1 < len(self.level.waves):
            self._next_wave()
        elif self.level_index + 1 < len(LEVELS) and not self.level.finale:
            self._bank_level()
            self.save.unlock(self.level_index + 2)
            self.set_state(State.LEVEL_CLEAR)
        else:                                        # a galaxy's end (or the game's)
            self._bank_level()
            if self.level_index + 1 < len(LEVELS):
                self.save.unlock(self.level_index + 2)
            self.record_rank = self.save.add_record(self.score, self.level_index + 1)
            self.achieve("CHAMPION")
            if self.level.finale:
                self.begin_warp()
            else:
                self.set_state(State.WIN)

    def _spawn_boss(self):
        self.boss = self.boss_entry.create()
        self.boss_hurt = False
        self.boss_thirds = 0
        self.boss_kit_timer = BOSS_KIT_INTERVAL
        self.set_phase(Phase.BOSS)

    def _ambush(self):
        """AMBUSH flow: no WARNING, no repair, the rocks keep falling. Only static warns."""
        self.track_field_done()
        self._spawn_boss()
        self.radio_say([Line(UNKNOWN, "...CONTACT... IT WAS WAITING..."),
                        "AMBUSH! IT WAS BEHIND THE GATE!"], delay=0.0)
        self.shake.add(0.5)
        self.audio.play("hijack")

    def _next_wave(self):
        self.wave_index += 1
        self.boss_index = 0
        self.boss = None
        self.distance = 0.0
        self.set_phase(Phase.FIELD)
        self.alert = [f"WAVE {self.wave_index + 1}", self.wave.name, ACCENT, 3.0]
        self.radio_say(self.wave.radio)
        if self.wave.reroll and self.level.shifts:
            self.roll_shift()                    # a new arena, a new rule

    def _begin_warning(self):
        """Repair for the boss fight: full in galaxy 1, part of the hull later (the field's
        damage carries into the fight)."""
        repair = galaxy_of(self.level).boss_repair
        self.ship.hp = min(self.ship.max_hp, self.ship.hp + self.ship.max_hp * repair)
        self.boss = None
        self.set_phase(Phase.WARNING)
        self.audio.play("warning")

    def is_final_boss(self):
        """True for a galaxy's last boss (an escape wave may still follow it)."""
        level = self.level
        last = max((i for i, wave in enumerate(level.waves) if wave.bosses), default=-1)
        return (level.finale and self.wave_index == last
                and self.boss_index == len(self.wave_bosses) - 1)

    def _spawn_field_extras(self, dt):
        """Repair kits, drone formations (from level 2) and diver squads (level 4)."""
        self.kit_timer -= dt
        if self.kit_timer <= 0 and self.kits_allowed:
            self.kit_timer = random.uniform(*KIT_INTERVAL)
            kit = FullRepair if random.random() < FULL_KIT_CHANCE else RepairKit
            self.pickups.append(kit(random.uniform(30, LOW_W - 30), -8))
        interval = self.level.difficulty.formation_interval
        if interval and self.distance < self.wave.length - 4:
            self.formation_timer -= dt * self.pressure * self.minion_rate
            if self.formation_timer <= 0:
                self.formation_timer = interval * random.uniform(0.8, 1.2)
                self.spawn_enemies(drone_formation())
        interval = self.level.difficulty.diver_interval
        if interval and self.distance < self.wave.length - 4:
            self.diver_timer -= dt * self.pressure * self.minion_rate
            if self.diver_timer <= 0:
                self.diver_timer = interval * random.uniform(0.8, 1.2)
                self.spawn_enemies(diver_squad(random.choice((2, 3, 3, 4))))
        for i, (spawn, interval) in enumerate(self.level.difficulty.extras):
            if self.distance >= self.wave.length - 4:
                break
            self.extra_timers[i] -= dt * self.pressure * self.minion_rate
            if self.extra_timers[i] <= 0:
                self.extra_timers[i] = interval * random.uniform(0.8, 1.2)
                self.spawn_enemies(spawn(self))

    def spawn_enemies(self, enemies):
        """New minions, as tough as the level makes them."""
        k = self.level.difficulty.enemy_hp
        for enemy in enemies:
            enemy.max_hp = enemy.hp = enemy.hp * k
        chance = self.elite_chance()
        if chance and enemies and random.random() < chance * len(enemies):
            random.choice(enemies).make_elite()      # at most one elite per group
        self.enemies += enemies

    def _level_label(self):
        waves = len(self.level.waves)
        return f"{self.level.number}-{self.wave_index + 1}" if waves > 1 else str(self.level.number)
