"""The levels, grouped into galaxies. A new level = a new Level entry in its galaxy's tuple."""
from ..background.events import Lightning, SunCorona
from ..bosses.carrier import Carrier
from ..bosses.gunship import GUNSHIP_SPEC, Gunship
from ..bosses.helios import Helios
from ..bosses.leviathan import Leviathan
from ..bosses.mothership import Mothership
from ..bosses.spec import BossSpec
from ..bosses.wraith import Wraith
from ..config.loadouts import MK1, MK2, MK3, MK4, MK5, MK6
from ..config.palette import (NEBULA, NEBULA_ABYSS, NEBULA_CRIMSON, NEBULA_FORGE, NEBULA_FROST,
                              NEBULA_GHOST)
from ..hazards.fog import FogBanks
from ..config.tuning import LEVEL_LENGTH
from ..minions.minelayer import minelayer_squad
from ..minions.phantom import phantom_pair
from .model import BossEntry, Difficulty, Galaxy, Level, Wave

DEFAULT_DIFFICULTY = Difficulty(
    spawn_interval=0.6,
    speed_min=55, speed_max=100,
    radius_min=4, radius_max=14,
    drift=12,
)

GALAXY_1_LEVELS = (
    Level(1, "ASTEROID FIELD", MK1, DEFAULT_DIFFICULTY, tuple(NEBULA),
          (Wave(LEVEL_LENGTH, (BossEntry(Gunship, GUNSHIP_SPEC),)),),
          radio=("SCOUT, THIS IS VEGA. THE REACH IS YOURS.",
                 "IRON FLEET PIRATES ARE MINING THE BELT.",
                 "CLEAR A PATH AND WATCH FOR THEIR GUNSHIP.")),
    Level(2, "CRIMSON BELT", MK2,
          Difficulty(spawn_interval=0.55, speed_min=60, speed_max=112, radius_min=4,
                     radius_max=14, drift=18, palettes=("rust", "brown", "grey"),
                     formation_interval=11),
          tuple(NEBULA_CRIMSON),
          (Wave(80, (BossEntry(Gunship, BossSpec("GUNSHIP", strength=1.5, fight_time=20,
                                                 player=MK2)),
                     BossEntry(Carrier, BossSpec("CARRIER", strength=4.0, fight_time=55,
                                                 player=MK2)))),),
          music="level2", upgrade_notes=("ENGINE  FASTER",),
          radio=("THE CRIMSON BELT. PIRATE DRONES AHEAD.",
                 "THEIR CARRIER LAUNCHES THEM IN SWARMS.",
                 "SHOOT THE DRONES BEFORE THEY FORM UP.")),
    # Three waves: minions, minions + the Carrier again (weakened), minions + the final boss.
    Level(3, "DARK NEBULA", MK3,
          Difficulty(spawn_interval=0.5, speed_min=65, speed_max=120, radius_min=4,
                     radius_max=14, drift=20, palettes=("slate", "grey", "rust"),
                     formation_interval=8),
          tuple(NEBULA_ABYSS),
          (Wave(45, name="ASTEROIDS AND DRONES"),
           Wave(40, (BossEntry(Carrier, BossSpec("CARRIER", strength=1.5, fight_time=30,
                                                 player=MK3)),),
                name="THE CARRIER RETURNS",
                radio=("THE CARRIER SURVIVED. FINISH IT OFF.",)),
           Wave(40, (BossEntry(Mothership, BossSpec("MOTHERSHIP", strength=5.0, fight_time=75,
                                                    player=MK3), music="final_boss"),),
                name="FINAL WAVE",
                radio=("THEIR MOTHERSHIP IS RIGHT BEHIND THIS.",
                       "SAVE THE MISSILE STORM FOR IT."))),
          music="level3",
          radio=("THE DARK NEBULA HIDES THEIR FLAGSHIP.",
                 "HIT ROCKS AND DRONES TO CHARGE THE BLAST.",
                 "T FIRES THE MISSILE STORM WHEN READY."),
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
                name="THE MOTHERSHIP RETURNS",
                radio=("THE MOTHERSHIP LIMPED IN HERE TO HIDE.",)),
           Wave(40, (BossEntry(Leviathan, BossSpec("LEVIATHAN", strength=5.0, fight_time=80,
                                                   player=MK4), music="leviathan"),),
                name="SOMETHING STIRS IN THE ICE",
                radio=("THE ICE IS BREAKING. IT'S ALIVE!",
                       "AIM FOR THE HEAD, SCOUT!"))),
          music="level4",
          radio=("THEIR MINING CRACKED THE FROZEN RIFT.",
                 "SENSORS SHOW SOMETHING HUGE UNDER THE ICE.",
                 "WATCH THE DIVERS: THEY AIM, THEN LUNGE."),
          upgrade_notes=("ICE ROCKS SHATTER INTO SHARDS",
                         "BEWARE: KAMIKAZE DIVERS")),
    # Magma rocks that explode (chain reactions), mine layers, the Leviathan again, HELIOS.
    Level(5, "SOLAR FORGE", MK5,
          Difficulty(spawn_interval=0.5, speed_min=68, speed_max=128, radius_min=4,
                     radius_max=14, drift=20, palettes=("magma", "brown", "rust"),
                     formation_interval=12, extras=((minelayer_squad, 9),), rock_hp=1.6,
                     enemy_hp=1.5),
          tuple(NEBULA_FORGE),
          (Wave(45, name="THE SOLAR FORGE"),
           Wave(40, (BossEntry(Leviathan, BossSpec("LEVIATHAN", strength=1.5, fight_time=35,
                                                   player=MK5)),),
                name="THE SERPENT FOLLOWED YOU",
                radio=("THE LEVIATHAN FOLLOWED US OUT OF THE ICE.",
                       "IT'S WOUNDED. FINISH IT.")),
           Wave(40, (BossEntry(Helios, BossSpec("HELIOS", strength=5.0, fight_time=80,
                                                player=MK5), music="helios"),),
                name="THE LIVING FORGE",
                radio=("THAT STATION IS ALIVE. IT BUILDS THE SWARM.",
                       "WATCH THE RING: IT GLOWS BEFORE A FLARE.",
                       "FLY THROUGH THE GAPS IN THE FIRE!"))),
          music="level5", event=SunCorona,
          radio=("THE SOLAR FORGE. THE SWARM SMELTS SHIPS HERE.",
                 "MAGMA ROCKS EXPLODE: USE THEM, BURN THE REST.",
                 "SHOOT THE MINES BEFORE THEY ARM."),
          upgrade_notes=("MAGMA ROCKS EXPLODE: CHAIN REACTIONS",
                         "MINE LAYERS: SHOOT THE MINES")),
    # Fog banks that hide rocks and minions, cloaked phantoms, Helios again, the WRAITH.
    Level(6, "GHOST NEBULA", MK6,
          Difficulty(spawn_interval=0.52, speed_min=66, speed_max=124, radius_min=4,
                     radius_max=14, drift=18, palettes=("slate", "grey"),
                     formation_interval=13, extras=((phantom_pair, 8),), rock_hp=1.8,
                     enemy_hp=1.7),
          tuple(NEBULA_GHOST),
          (Wave(45, name="THE GHOST NEBULA"),
           Wave(40, (BossEntry(Helios, BossSpec("HELIOS", strength=1.5, fight_time=35,
                                                player=MK6)),),
                name="THE FORGE FOLLOWS",
                radio=("HELIOS REBUILT ITSELF. OF COURSE IT DID.",)),
           Wave(40, (BossEntry(Wraith, BossSpec("WRAITH", strength=5.0, fight_time=80,
                                                player=MK6), music="wraith"),),
                name="SOMETHING IN THE FOG",
                radio=("MY SENSORS SEE NOTHING. THAT'S THE PROBLEM.",
                       "WATCH FOR THE STATIC: IT JUMPS THERE NEXT.",
                       "ONLY THE REAL ONE HAS A RED LIGHT."))),
          music="level6", event=Lightning, hazard=FogBanks,
          radio=("GHOST NEBULA. FOG BANKS HIDE THE ROCKS.",
                 "THE FOG NEVER HIDES YOU OR ENEMY SHOTS.",
                 "PHANTOMS SHIMMER BEFORE THEY FIRE."),
          upgrade_notes=("FOG HIDES ROCKS AND MINIONS",
                         "PHANTOMS: WATCH THE SHIMMER")),
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
