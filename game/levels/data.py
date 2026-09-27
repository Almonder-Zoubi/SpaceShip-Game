"""The levels, grouped into galaxies. A new level = a new Level entry in its galaxy's tuple."""
from ..bosses.carrier import Carrier
from ..bosses.gunship import GUNSHIP_SPEC, Gunship
from ..bosses.leviathan import Leviathan
from ..bosses.mothership import Mothership
from ..bosses.spec import BossSpec
from ..config.loadouts import MK1, MK2, MK3, MK4
from ..config.palette import NEBULA, NEBULA_ABYSS, NEBULA_CRIMSON, NEBULA_FROST
from ..config.tuning import LEVEL_LENGTH
from .model import BossEntry, Difficulty, Galaxy, Level, Wave

DEFAULT_DIFFICULTY = Difficulty(
    spawn_interval=0.6,
    speed_min=55, speed_max=100,
    radius_min=4, radius_max=14,
    drift=12,
)

GALAXY_1_LEVELS = (
    Level(1, "ASTEROID FIELD", MK1, DEFAULT_DIFFICULTY, tuple(NEBULA),
          (Wave(LEVEL_LENGTH, (BossEntry(Gunship, GUNSHIP_SPEC),)),)),
    Level(2, "CRIMSON BELT", MK2,
          Difficulty(spawn_interval=0.55, speed_min=60, speed_max=112, radius_min=4,
                     radius_max=14, drift=18, palettes=("rust", "brown", "grey"),
                     formation_interval=11),
          tuple(NEBULA_CRIMSON),
          (Wave(80, (BossEntry(Gunship, BossSpec("GUNSHIP", strength=1.5, fight_time=20,
                                                 player=MK2)),
                     BossEntry(Carrier, BossSpec("CARRIER", strength=4.0, fight_time=55,
                                                 player=MK2)))),),
          music="level2", upgrade_notes=("ENGINE  FASTER",)),
    # Three waves: minions, minions + the Carrier again (weakened), minions + the final boss.
    Level(3, "DARK NEBULA", MK3,
          Difficulty(spawn_interval=0.5, speed_min=65, speed_max=120, radius_min=4,
                     radius_max=14, drift=20, palettes=("slate", "grey", "rust"),
                     formation_interval=8),
          tuple(NEBULA_ABYSS),
          (Wave(45, name="ASTEROIDS AND DRONES"),
           Wave(40, (BossEntry(Carrier, BossSpec("CARRIER", strength=1.5, fight_time=30,
                                                 player=MK3)),),
                name="THE CARRIER RETURNS"),
           Wave(40, (BossEntry(Mothership, BossSpec("MOTHERSHIP", strength=5.0, fight_time=75,
                                                    player=MK3), music="final_boss"),),
                name="FINAL WAVE")),
          music="level3",
          upgrade_notes=("NEW: BLAST BEAM",
                         "SHOOT ROCKS + DRONES TO CHARGE",
                         "NEW: ULTIMATE MISSILES - KEY T")),
    # Ice rocks that shatter, drones + kamikaze divers, the Mothership again, the Leviathan.
    Level(4, "FROZEN RIFT", MK4,
          Difficulty(spawn_interval=0.5, speed_min=65, speed_max=125, radius_min=4,
                     radius_max=14, drift=22, palettes=("ice", "slate"),
                     formation_interval=11, diver_interval=9),
          tuple(NEBULA_FROST),
          (Wave(45, name="THE FROZEN RIFT"),
           Wave(40, (BossEntry(Mothership, BossSpec("MOTHERSHIP", strength=1.5, fight_time=35,
                                                    player=MK4)),),
                name="THE MOTHERSHIP RETURNS"),
           Wave(40, (BossEntry(Leviathan, BossSpec("LEVIATHAN", strength=5.0, fight_time=80,
                                                   player=MK4), music="leviathan"),),
                name="SOMETHING STIRS IN THE ICE")),
          music="level4",
          upgrade_notes=("ICE ROCKS SHATTER INTO SHARDS",
                         "BEWARE: KAMIKAZE DIVERS")),
)

GALAXIES = (
    Galaxy(1, "ORION REACH", GALAXY_1_LEVELS),
)

# Every level of every galaxy in play order; the game indexes this (Game.level_index).
LEVELS = tuple(level for galaxy in GALAXIES for level in galaxy.levels)


def galaxy_of(level):
    """The galaxy a level belongs to."""
    return next(g for g in GALAXIES if any(lv is level for lv in g.levels))


# Save-file keys of every level in play order ("1-1", "1-2", ...).
LEVEL_KEYS = tuple(galaxy_of(level).key(level) for level in LEVELS)
