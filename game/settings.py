"""Global constants: resolution, tuning values, colour palettes."""
import os
from dataclasses import dataclass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(*parts):
    """Absolute path to an asset, independent of the working directory."""
    return os.path.join(BASE_DIR, *parts)


SAVE_FILE = asset("save.json")   # records + unlocked levels (see storage.py)

# --- Display -----------------------------------------------------------------
TITLE = "Dodging Asteroid"
LOW_W, LOW_H = 320, 240          # logical (pixel-art) resolution
SCALE = 3                        # window = logical * SCALE
WIN_W, WIN_H = LOW_W * SCALE, LOW_H * SCALE
FPS = 60
MAX_DT = 1 / 30                  # clamp long frames so physics never explodes

# --- Ship --------------------------------------------------------------------
# Arrows move the ship directly; two arrows (e.g. UP + RIGHT) move diagonally.
SHIP_ACCEL = 800                 # px/s^2 while a direction key is held
SHIP_MAX_SPEED = 130             # px/s
SHIP_FRICTION = 5.5              # velocity damping per second on released axes
SHIP_MARGIN = 4                  # keep this many px from screen edges
TILT_DEGREES = 30                # UP + LEFT/RIGHT leans the rocket like '\' or '/'
TILT_STEPS = 3                   # frames per side (10 degrees apart)
TILT_RATE = 240                  # degrees per second when leaning / straightening

THROTTLE_RETRO = 0.12            # DOWN held: flames nearly out
THROTTLE_IDLE = 0.45             # cruising
THROTTLE_BOOST = 1.0             # UP held: full burn
THROTTLE_RESPONSE = 7.0          # how fast throttle follows its target (1/s)

# World scroll speed multiplier at retro / boost throttle
WORLD_SPEED_SLOW = 0.8
WORLD_SPEED_FAST = 1.35

# --- Health ------------------------------------------------------------------
SHIP_MAX_HP = 100
ROCK_DAMAGE_BASE = 8             # damage from a rock = base + per_radius * radius
ROCK_DAMAGE_PER_RADIUS = 2       # (radius 4 -> 16, radius 14 -> 36)
HIT_INVULNERABLE = 1.0           # seconds of blinking after a hit
HIT_KNOCKBACK = 110              # px/s pushed away from the rock
BULLET_KNOCKBACK = 40            # px/s pushed by an enemy bullet

# --- Weapons (R switches, SPACE fires where the nose points) -----------------
GUN_INTERVAL = 0.07              # seconds between bullets
GUN_SPEED = 340                  # px/s
GUN_DAMAGE = 5                   # per bullet (~70 dps if every bullet hits)
GUN_SPREAD = 0.05                # radians of random spread
LASER_DPS = 80                   # damage per second while the beam touches
LASER_RANGE = 360
LASER_HEAT_RATE = 0.4            # heat per second while firing (full in 2.5 s)
LASER_COOL_RATE = 0.35           # heat lost per second when not firing
LASER_RESUME = 0.35              # after overheating, usable again below this heat

# --- Asteroids ---------------------------------------------------------------
ROCK_HP_BASE = 6                 # hp = base + per_area * radius^2
ROCK_HP_PER_AREA = 0.8           # (radius 4 -> 19, radius 8 -> 57, radius 14 -> 163)
ROCK_SPLIT_RADIUS = 8            # rocks at least this big break into fragments
# Getting shot slows a rock down: push in px/s for a radius-4 rock, scaled by 4/radius.
GUN_PUSH = 5                     # per bullet
LASER_PUSH = 70                  # per second of beam
ROCK_MIN_FALL = 12               # rocks never get pushed slower than this (px/s)

# --- Score & rules -----------------------------------------------------------
POINTS_PER_RADIUS = 10           # destroying a rock
POINTS_DODGE = 5                 # a rock leaving the screen
POINTS_BOSS = 5000
LEVEL_LENGTH = 75                # seconds of flight (at normal speed) to finish
DEATH_DELAY = 1.4                # seconds of explosion before "game over"
WARNING_TIME = 3.0               # "WARNING" before the boss enters

# --- Ship models (upgraded between levels) -----------------------------------
@dataclass(frozen=True)
class Loadout:
    """Player ship model: hull, speed and weapon strength."""
    name: str
    max_hp: int
    max_speed: float
    gun_damage: float
    laser_dps: float
    laser_heat_rate: float
    colors: str = "mk1"           # key into sprites.SHIP_PALETTES
    blast: bool = False           # charged BLAST beam (MK III)
    ultimate: bool = False        # T: missile storm (MK III)

    @property
    def gun_dps(self):
        """Machine gun with every bullet hitting (no power-ups) — the boss balance baseline."""
        return self.gun_damage / GUN_INTERVAL


MK1 = Loadout("MK I", max_hp=SHIP_MAX_HP, max_speed=SHIP_MAX_SPEED, gun_damage=GUN_DAMAGE,
              laser_dps=LASER_DPS, laser_heat_rate=LASER_HEAT_RATE)
MK2 = Loadout("MK II", max_hp=150, max_speed=145, gun_damage=7, laser_dps=110,
              laser_heat_rate=0.32, colors="mk2")
MK3 = Loadout("MK III", max_hp=200, max_speed=150, gun_damage=9, laser_dps=140,
              laser_heat_rate=0.28, colors="mk3", blast=True, ultimate=True)

# --- BLAST and ULTIMATE (MK III) ---------------------------------------------
# Both charge from damage dealt to rocks and minions (+ a bonus per kill, x3 for minions).
BLAST_TIME = 3.0                 # seconds the beam lasts once unleashed
BLAST_DPS = 450                  # to everything inside the beam
BLAST_WIDTH = 11                 # px
BLAST_PUSH = 160                 # rock push per second
BLAST_CHARGE_PER_DAMAGE = 1 / 1400
BLAST_CHARGE_PER_KILL = 0.025
ULT_TIME = 2.4                   # seconds of missile launches
ULT_INTERVAL = 0.05              # seconds between missiles (~48 missiles)
ULT_MISSILE_DAMAGE = 45
ULT_MISSILE_SPEED = 230          # px/s
ULT_TURN = 7.0                   # rad/s homing turn rate
ULT_CHARGE_PER_DAMAGE = 1 / 5000
ULT_CHARGE_PER_KILL = 0.008
ULT_CHARGE_PER_BOSS_THIRD = 0.25 # every 1/3 of a boss's health knocked off

# Weapon power (0..POWER_MAX) — collected from POWER cores when a boss changes phase.
POWER_MAX = 2
LASER_POWER_BONUS = 0.35         # +35% laser dps per power level
LASER_POWER_COOL = 0.2           # -20% laser heating per power level
GUN_SIDE_ANGLE = 0.22            # radians, power 2 adds angled side rounds

# --- Pickups -----------------------------------------------------------------
REPAIR_SMALL = 30                # hp restored by a small repair kit
PICKUP_FALL = 26                 # px/s
PICKUP_MAGNET = 34               # px: kits closer than this drift towards the ship
PICKUP_RADIUS = 11               # px: collected when the ship centre is this close
KIT_INTERVAL = (13, 20)          # seconds between kits in the asteroid field (random range)
FULL_KIT_CHANCE = 0.15           # chance a field kit is a full repair
BOSS_KIT_INTERVAL = 15           # seconds between small kits during a boss fight
ROCK_KIT_CHANCE = 0.08           # big rocks (radius >= 10) may drop a small kit
DRONE_KIT_CHANCE = 0.06

# --- Enemy drones ------------------------------------------------------------
DRONE_HP = 24
DRONE_SPEED = 62                 # px/s downwards
DRONE_BULLET_SPEED = 95
DRONE_BULLET_DAMAGE = 8
DRONE_CONTACT_DAMAGE = 14
POINTS_DRONE = 150

# --- Boss balance ------------------------------------------------------------
# A boss is STRENGTH times stronger than the rocket, measured as a damage race:
#   (boss HP / player DPS) / (player HP / boss DPS) = strength
# where player DPS = the machine gun with every bullet hitting, and boss DPS = the damage
# a rocket that never moves would take. fight_time = seconds to kill the boss at that DPS.
# Both use the ship model of the level (Loadout.gun_dps / max_hp); pickups and power-ups are
# the player's edge on top.
BOSS_CONTACT_DAMAGE = 20         # ramming the boss hurts
BOSS_ROAR_TIME = 1.6             # a multi-phase boss is invulnerable while changing phase


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


DEFAULT_DIFFICULTY = Difficulty(
    spawn_interval=0.6,
    speed_min=55, speed_max=100,
    radius_min=4, radius_max=14,
    drift=12,
)

# --- Palette -----------------------------------------------------------------
SPACE = (8, 6, 18)
INK = (18, 14, 30)                # universal dark outline
WHITE = (250, 248, 240)
TEXT = (236, 232, 220)
TEXT_DIM = (130, 124, 150)
TEXT_SHADOW = (24, 16, 40)
ACCENT = (255, 204, 64)
DANGER = (240, 64, 72)
GOOD = (96, 228, 128)
HURT = (255, 40, 40)

SHIP_COLORS = {
    "K": INK,
    "W": (250, 250, 245),
    "L": (196, 200, 212),
    "G": (140, 146, 164),
    "D": (86, 90, 112),
    "R": (228, 44, 64),
    "r": (150, 22, 50),
    "P": (255, 146, 156),
    "C": (190, 244, 255),
    "B": (64, 144, 224),
    "b": (28, 60, 132),
    "O": (72, 66, 84),
    "Y": (255, 204, 64),
    "y": (184, 120, 36),
}

# Asteroid palettes: [outline, darkest ... lightest]
ROCK_PALETTES = {
    "grey":  [(20, 16, 32), (56, 50, 70), (92, 86, 104), (138, 130, 142), (192, 184, 186)],
    "brown": [(30, 16, 22), (78, 46, 40), (122, 78, 54), (170, 118, 74), (216, 170, 114)],
    "slate": [(14, 16, 32), (40, 52, 80), (66, 86, 116), (106, 128, 156), (164, 182, 200)],
    "rust":  [(30, 12, 20), (96, 38, 36), (148, 64, 44), (198, 106, 60), (238, 164, 102)],
}

# Particle colour ramps (start -> end of life)
FLAME = [(255, 255, 230), (255, 240, 140), (255, 190, 60), (245, 118, 36),
         (190, 52, 40), (90, 26, 40)]
FLAME_LEAN = [(220, 240, 255), (130, 190, 255), (70, 110, 230), (40, 50, 140)]
SMOKE = [(96, 92, 108), (72, 68, 86), (50, 46, 64), (34, 30, 48)]
RCS = [(236, 244, 255), (160, 176, 206), (92, 100, 130)]
SPARK = [(255, 255, 255), (255, 236, 140), (255, 160, 60)]
TRACER = [(255, 255, 230), (255, 226, 120), (240, 150, 40)]
LASER = [(255, 255, 255), (170, 244, 255), (70, 180, 255), (30, 80, 200)]
ENEMY_SHOT = [(255, 255, 255), (255, 200, 90), (255, 96, 32), (200, 40, 16)]

NEBULA = [(16, 10, 32), (26, 14, 48), (40, 20, 68)]
NEBULA_CRIMSON = [(20, 8, 22), (32, 10, 30), (48, 14, 36)]
NEBULA_ABYSS = [(8, 14, 30), (12, 24, 44), (18, 36, 60)]
POWER = [(255, 255, 255), (200, 255, 255), (90, 220, 255), (40, 120, 220)]
HEAL = [(255, 255, 255), (190, 255, 200), (96, 228, 128), (40, 140, 80)]
STAR_COLORS = [(255, 255, 255), (200, 220, 255), (255, 236, 200), (170, 170, 210)]
PLANET_PALETTES = [
    [(26, 20, 46), (58, 40, 90), (96, 64, 130), (140, 104, 168)],
    [(34, 22, 30), (86, 48, 52), (140, 82, 70), (190, 132, 96)],
    [(14, 30, 44), (30, 70, 90), (54, 112, 128), (104, 164, 170)],
]

# Light comes from the upper left (x, y, z towards viewer), normalised in code.
LIGHT_DIR = (-0.55, -0.65, 0.52)
