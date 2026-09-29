"""Data classes that describe a level: difficulty, waves and the bosses at their end."""
from dataclasses import dataclass

from ..bosses.spec import BossSpec
from ..config.loadouts import Loadout


@dataclass(frozen=True)
class Difficulty:
    """Everything the spawner needs; levels / endless mode will vary these."""
    spawn_interval: float        # seconds between spawns (average)
    speed_min: float             # px/s
    speed_max: float
    radius_min: int              # asteroid radius in px
    radius_max: int
    drift: float                 # max sideways speed px/s
    palettes: tuple = ("grey", "brown", "slate")
    formation_interval: float = 0     # seconds between drone formations (0 = none)
    diver_interval: float = 0         # seconds between kamikaze diver squads (0 = none)
    extras: tuple = ()                # (spawn(game) -> [Enemy], seconds between) per minion type
    rock_hp: float = 1.0              # rock toughness (later ship models hit much harder)
    enemy_hp: float = 1.0             # minion toughness
    elite_chance: float = 0.0         # galaxy 2: share of minions that come as ELITES


@dataclass(frozen=True)
class BossEntry:
    """One boss of a wave's boss rush: which class, with which balance numbers."""
    boss_class: type
    spec: BossSpec
    music: str = "boss"          # track name in audio/music.py

    def create(self):
        return self.boss_class(self.spec)


@dataclass(frozen=True)
class Wave:
    """Asteroid field (with minions if the level's Difficulty has them), then its bosses."""
    length: float                # seconds of flight through the field
    bosses: tuple = ()           # BossEntry, fought in order after the field
    name: str = ""               # subtitle of the "WAVE n" announcement
    radio: tuple = ()            # radio card lines when the wave starts (ui/radio.py)
    music: str = None            # its own field track (else the level's)
    escape: bool = False         # a timed escape run (the level's hazard collapses)
    ambush: float = 0.0          # > 0: the boss arrives unannounced at this share of the field
    pursuit: bool = False        # something hunts the rocket through the field (hazards/pursuit)
    fork: bool = False           # two gates open in this field; flying into one picks a route
    route: bool = False          # the bosses are alternatives: only the chosen route's one fights
    reroll: bool = False         # a new VEIL SHIFT is rolled when this wave starts (arenas)


@dataclass(frozen=True)
class Level:
    number: int
    name: str
    loadout: Loadout             # ship model the player flies in this level
    difficulty: Difficulty
    nebula: tuple                # background cloud colours
    waves: tuple                 # Wave, played in order; the last boss is the level boss
    music: str = "level1"        # asteroid-field track (audio/music.py)
    upgrade_notes: tuple = ()    # new features, shown under the stat changes on "level clear"
    radio: tuple = ()            # radio card lines when the level starts (ui/radio.py)
    event: type = None           # background event layer (background/events.py)
    hazard: type = None          # level-wide mechanic (hazards/)
    finale: bool = False         # the galaxy's last level: warp cut-scene + medal after it
    director: bool = False       # the DIRECTOR paces the fields (galaxy 2 on)
    shifts: bool = False         # every attempt rolls a VEIL SHIFT (levels/shifts.py)


@dataclass(frozen=True)
class Galaxy:
    """Ten levels with one palette family, faction and finale (see docs/DESIGN.md)."""
    number: int
    name: str
    levels: tuple                # Level, numbered 1.. inside the galaxy
    boss_repair: float = 1.0     # share of max hull repaired before each boss

    def key(self, level):
        """Save-file key of one of its levels, e.g. "1-3"."""
        return f"{self.number}-{level.number}"
