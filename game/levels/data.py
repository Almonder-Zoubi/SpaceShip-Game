"""The levels, grouped into galaxies. A new level = a new Level entry in its galaxy's tuple."""
from ..background.events import CrystalSparkle, Lightning, SunCorona, Wrecks
from ..bosses.carrier import Carrier
from ..bosses.gunship import GUNSHIP_SPEC, Gunship
from ..bosses.helios import Helios
from ..bosses.kaleidos import Kaleidos
from ..bosses.leviathan import Leviathan
from ..bosses.mothership import Mothership
from ..bosses.overmind import Overmind
from ..bosses.scrapjaw import Scrapjaw
from ..bosses.spec import BossSpec
from ..bosses.twins import Twins
from ..bosses.warden import Warden
from ..bosses.wraith import Wraith
from ..config.loadouts import MK1, MK2, MK3, MK4, MK5, MK6, MK7, MK8, MK9, MK10, MK11
from ..config.palette import (NEBULA, NEBULA_ABYSS, NEBULA_CRIMSON, NEBULA_CRYSTAL, NEBULA_FORGE,
                              NEBULA_FROST, NEBULA_GHOST, NEBULA_HIVE, NEBULA_HORIZON,
                              NEBULA_RUST, NEBULA_VEIL)
from ..hazards.blackhole import BlackHole
from ..hazards.fog import FogBanks
from ..hazards.hive import HiveTunnel
from ..hazards.rifts import RiftPortals
from ..config.tuning import BOSS_REPAIR_G2, LEVEL_LENGTH
from ..minions.interceptor import interceptor_pair
from ..minions.minelayer import minelayer_squad
from ..minions.phantom import phantom_pair
from ..minions.prism import prism_turret
from ..minions.salvager import salvager
from ..minions.swarm import larva_flock, spore_cluster
from ..minions.wisp import wisp_pair
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
          radio=("YOU'RE MY SCOUT NOW. THE REACH IS YOURS.",
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
          radio=("ON TO THE CRIMSON BELT. DRONES AHEAD.",
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
          radio=("UNDER THE DARK NEBULA HIDES THEIR FLAGSHIP.",
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
          radio=("ALL THAT MINING CRACKED THE FROZEN RIFT.",
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
          radio=("RED HOT: THE SOLAR FORGE SMELTS SHIPS.",
                 "MAGMA ROCKS EXPLODE. USE THE CHAIN!",
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
          radio=("ENTER THE GHOST NEBULA. FOG HIDES ROCKS.",
                 "THE FOG NEVER HIDES YOU OR ENEMY SHOTS.",
                 "PHANTOMS SHIMMER BEFORE THEY FIRE."),
          upgrade_notes=("FOG HIDES ROCKS AND MINIONS",
                         "PHANTOMS: WATCH THE SHIMMER")),
    # Crystal rocks that split the laser, prism turrets, the Wraith again, KALEIDOS.
    Level(7, "CRYSTAL VEIL", MK7,
          Difficulty(spawn_interval=0.5, speed_min=66, speed_max=126, radius_min=4,
                     radius_max=14, drift=20, palettes=("crystal", "slate", "grey"),
                     formation_interval=12, extras=((prism_turret, 11),), rock_hp=2.0,
                     enemy_hp=1.9),
          tuple(NEBULA_CRYSTAL),
          (Wave(45, name="THE CRYSTAL VEIL"),
           Wave(40, (BossEntry(Wraith, BossSpec("WRAITH", strength=1.5, fight_time=35,
                                                player=MK7)),),
                name="A GHOST RETURNS",
                radio=("THE WRAITH SLIPPED OUT OF THE NEBULA.",)),
           Wave(40, (BossEntry(Kaleidos, BossSpec("KALEIDOS", strength=5.0, fight_time=80,
                                                  player=MK7), music="kaleidos"),),
                name="THE PRISM QUEEN",
                radio=("HER SHARDS ARE MIRRORS. LASERS BOUNCE BACK!",
                       "BREAK THEM WITH THE GUN, THEN BURN HER.",
                       "WHEN THE LINES BLINK, GET OUT OF THEM."))),
          music="level7", event=CrystalSparkle,
          radio=("NOW THE CRYSTAL VEIL. LASER THE CRYSTALS:",
                 "THE BEAM SPLITS TO EVERYTHING NEARBY.",
                 "BREAK THE BIG ONES TO DROP THEIR TURRETS."),
          upgrade_notes=("CRYSTALS SPLIT YOUR LASER",
                         "PRISM TURRETS RIDE BIG CRYSTALS")),
    # Wreck chunks (tough, coins), salvagers that steal, Kaleidos again, SCRAPJAW.
    Level(8, "IRON GRAVEYARD", MK8,
          Difficulty(spawn_interval=0.52, speed_min=60, speed_max=115, radius_min=5,
                     radius_max=14, drift=16, palettes=("wreck", "rust", "grey"),
                     formation_interval=12, diver_interval=13, extras=((salvager, 10),),
                     rock_hp=2.2, enemy_hp=2.1),
          tuple(NEBULA_RUST),
          (Wave(45, name="THE IRON GRAVEYARD"),
           Wave(40, (BossEntry(Kaleidos, BossSpec("KALEIDOS", strength=1.5, fight_time=35,
                                                  player=MK8)),),
                name="THE QUEEN'S SHARDS",
                radio=("KALEIDOS FOLLOWED THE LIGHT OF OUR ENGINES.",)),
           Wave(40, (BossEntry(Scrapjaw, BossSpec("SCRAPJAW", strength=5.0, fight_time=80,
                                                  player=MK8), music="scrapjaw"),),
                name="THE JUNK KING",
                radio=("THE WRECKS ARE MOVING. THEY'RE BUILDING IT!",
                       "SHOOT THE ARMOUR OFF - IT THROWS IT BACK.",
                       "STAY AWAY FROM ITS MAGNET CLAW."))),
          music="level8", event=Wrecks,
          radio=("EVERYONE DIED HERE: THE IRON GRAVEYARD.",
                 "WRECK CHUNKS ARE TOUGH BUT FULL OF CREDITS.",
                 "SALVAGERS STEAL: SHOOT THEM, GET IT X2."),
          upgrade_notes=("WRECKS: TOUGH, FULL OF COINS",
                         "SALVAGERS STEAL - GET IT BACK X2")),
    # The black hole: it pulls everything, the ship too. Comets, interceptors, Scrapjaw
    # again, THE TWINS.
    Level(9, "EVENT HORIZON", MK9,
          Difficulty(spawn_interval=0.55, speed_min=60, speed_max=118, radius_min=4,
                     radius_max=13, drift=16, palettes=("comet", "slate", "grey"),
                     formation_interval=14, extras=((interceptor_pair, 9),), rock_hp=2.4,
                     enemy_hp=2.3),
          tuple(NEBULA_HORIZON),
          (Wave(45, name="THE EVENT HORIZON"),
           Wave(40, (BossEntry(Scrapjaw, BossSpec("SCRAPJAW", strength=1.5, fight_time=35,
                                                  player=MK9)),),
                name="THE JUNK KING RETURNS",
                radio=("SCRAPJAW REBUILT ITSELF FROM THE DEBRIS.",)),
           Wave(40, (BossEntry(Twins, BossSpec("THE TWINS", strength=5.0, fight_time=80,
                                               player=MK9), music="twins"),),
                name="ORA AND ZEN",
                radio=("TWO SHIPS, ONE TETHER: DON'T TOUCH IT!",
                       "KILL ONE AND THE OTHER REVIVES IT IN 8 S:",
                       "BRING THEM DOWN TOGETHER."))),
          music="level9", hazard=BlackHole,
          radio=("X MARKS THE EVENT HORIZON. IT PULLS YOU.",
                 "FLY THE BLUE RING: TRIPLE SCORE AND COINS.",
                 "WHEN THE DISC TURNS WHITE, IT SPITS IT OUT!"),
          upgrade_notes=("THE BLACK HOLE PULLS YOU",
                         "INTERCEPTORS: HIT THEM FROM THE SIDE")),
    # The galaxy finale: inside the hive. Living walls, spore pods, larva swarms, a boss rush
    # of old enemies, THE OVERMIND, then the escape run as the hive collapses.
    Level(10, "SWARM HEART", MK10,
          Difficulty(spawn_interval=0.62, speed_min=58, speed_max=110, radius_min=4,
                     radius_max=12, drift=12, palettes=("chitin", "slate"),
                     extras=((spore_cluster, 7), (larva_flock, 11)),
                     rock_hp=2.6, enemy_hp=2.5),
          tuple(NEBULA_HIVE),
          (Wave(45, name="INTO THE HIVE"),
           Wave(30, (BossEntry(Mothership, BossSpec("MOTHERSHIP", strength=1.5, fight_time=25,
                                                    player=MK10)),
                     BossEntry(Leviathan, BossSpec("LEVIATHAN", strength=1.5, fight_time=25,
                                                   player=MK10), music="leviathan"),
                     BossEntry(Helios, BossSpec("HELIOS", strength=1.5, fight_time=25,
                                                player=MK10), music="helios")),
                name="THE HIVE REMEMBERS",
                radio=("THE HIVE GREW COPIES OF EVERYTHING",
                       "YOU EVER KILLED. DO IT AGAIN.")),
           Wave(30, (BossEntry(Overmind, BossSpec("THE OVERMIND", strength=5.0, fight_time=90,
                                                  player=MK10), music="overmind"),),
                name="HEART OF THE SWARM",
                radio=("THAT'S IT - THE OVERMIND. THE HEART.",
                       "BURST THE GLANDS TO TEAR THE WALL OPEN.",
                       "THEN END THIS, SCOUT. FOR THE REACH.")),
           Wave(20, name="ESCAPE!", music="escape", escape=True,
                radio=("THE HIVE IS COLLAPSING! FULL THROTTLE!",
                       "DON'T TOUCH THE WALLS. GO, GO, GO!"))),
          music="level10", hazard=HiveTunnel, finale=True,
          radio=("THIS IS IT: THE SWARM'S HIVE WORLD.",
                 "THE WALLS ARE ALIVE - DON'T TOUCH THEM.",
                 "SHOOT SPORE PODS BEFORE THEY BURST."),
          upgrade_notes=("THE HIVE WALLS HURT",
                         "SPORE PODS BURST - SHOOT THEM EARLY")),
)

# Galaxy 2, THE VEIL: every level has its own flow (docs/DESIGN.md section 4), the DIRECTOR
# paces the fields, every attempt rolls a VEIL SHIFT, elites appear, bosses learn.
GALAXY_2_LEVELS = (
    # AMBUSH: no warning. The Warden waits behind the gate and strikes mid-field.
    Level(1, "VEIL GATE", MK11,
          Difficulty(spawn_interval=0.56, speed_min=62, speed_max=120, radius_min=4,
                     radius_max=13, drift=16, palettes=("veil", "bone"),
                     extras=((wisp_pair, 8),), rock_hp=2.9, enemy_hp=2.8, elite_chance=0.12),
          tuple(NEBULA_VEIL),
          (Wave(45, name="THROUGH THE GATE"),
           Wave(70, (BossEntry(Warden, BossSpec("THE WARDEN", strength=5.5, fight_time=45,
                                                player=MK11), music="warden"),),
                name="THE GATE IS QUIET", ambush=0.3,
                radio=("QUIET HERE. TOO QUIET. KEEP MOVING.",))),
          music="veil", hazard=RiftPortals, director=True, shifts=True,
          radio=("WELCOME TO THE VEIL. STAY SHARP, SCOUT.",
                 "RIFTS CARRY EVERYTHING - YOUR SHOTS TOO.",
                 "GOLDEN ONES ARE ELITES. WORTH THE TROUBLE."),
          upgrade_notes=("THE VEIL: ELITES, SHIFTS, RIFTS",
                         "BOSS REPAIR ONLY 50% FROM NOW")),
)

GALAXIES = (
    Galaxy(1, "ORION REACH", GALAXY_1_LEVELS),
    Galaxy(2, "THE VEIL", GALAXY_2_LEVELS, boss_repair=BOSS_REPAIR_G2),
)

# Every level of every galaxy in play order; the game indexes this (Game.level_index).
LEVELS = tuple(level for galaxy in GALAXIES for level in galaxy.levels)


def galaxy_of(level):
    """The galaxy a level belongs to."""
    return next(g for g in GALAXIES if any(lv is level for lv in g.levels))


# Save-file keys of every level in play order ("1-1", "1-2", ...).
LEVEL_KEYS = tuple(galaxy_of(level).key(level) for level in LEVELS)


def level_title(level):
    """'LEVEL 4' in galaxy 1, 'G2 LEVEL 1' later (levels are numbered inside their galaxy)."""
    number = galaxy_of(level).number
    return f"LEVEL {level.number}" if number == 1 else f"G{number} LEVEL {level.number}"
