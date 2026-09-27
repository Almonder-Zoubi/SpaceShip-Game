"""Level flow: starting runs, the field -> warning -> boss -> cleared cycle, waves, level clear."""
import random

from ..config.display import LOW_W
from ..config.palette import ACCENT
from ..config.tuning import BOSS_KIT_INTERVAL, FULL_KIT_CHANCE, KIT_INTERVAL, WARNING_TIME
from ..levels.data import LEVELS
from ..minions.diver import diver_squad
from ..minions.drone import drone_formation
from ..obstacles.spawner import AsteroidSpawner
from ..pickups.types import FullRepair, RepairKit
from ..player.hulls import HULLS
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
        self.diver_timer = level.difficulty.diver_interval
        self.boss_kit_timer = BOSS_KIT_INTERVAL
        self.alert = [f"LEVEL {level.number}", level.name, ACCENT, 3.0]   # title, sub, colour, time
        self.weapon_index = 0
        for weapon in self.weapons:
            weapon.reset()
            weapon.equip(loadout)
        self.blast.reset()
        self.ultimate.reset()
        self.fire.clear()
        self.smoke.clear()
        self.shockwaves.clear()
        self.hurt_flash = 0.0

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

    def loadout_for(self, level):
        """The level's ship model as flown with the chosen hull."""
        return self.hull.apply(level.loadout)

    def open_hangar(self):
        self.hangar_cursor = HULLS.index(self.hull)
        self.set_state(State.HANGAR)

    def choose_hull(self, hull):
        """Pick a hull (remembered in the save file) and build its sprites for every level now,
        so no level start has to."""
        self.hull = hull
        self.save.choose_ship(hull.name)
        for level in LEVELS:
            self.ship.equip(self.loadout_for(level), hull)
        self.ship.equip(self.loadout_for(self.level), hull)

    def to_title(self):
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
            if self.distance >= self.wave.length:
                if self.wave.bosses:
                    self._begin_warning()
                else:
                    self._next_wave()
        elif self.phase == Phase.WARNING and self.phase_time >= WARNING_TIME:
            self.boss = self.boss_entry.create()
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
        self.audio.play("warning")

    def is_final_boss(self):
        """True for the very last boss of the game."""
        level = self.level
        return (self.level_index == len(LEVELS) - 1 and self.wave_index == len(level.waves) - 1
                and self.boss_index == len(self.wave.bosses) - 1)

    def _spawn_field_extras(self, dt):
        """Repair kits, drone formations (from level 2) and diver squads (level 4)."""
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
        interval = self.level.difficulty.diver_interval
        if interval and self.distance < self.wave.length - 4:
            self.diver_timer -= dt
            if self.diver_timer <= 0:
                self.diver_timer = interval * random.uniform(0.8, 1.2)
                self.enemies += diver_squad(random.choice((2, 3, 3, 4)))

    def _level_label(self):
        waves = len(self.level.waves)
        return f"{self.level.number}-{self.wave_index + 1}" if waves > 1 else str(self.level.number)
