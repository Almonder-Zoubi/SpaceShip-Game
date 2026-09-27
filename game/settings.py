"""Global constants: resolution, tuning values, colour palettes."""
import os
from dataclasses import dataclass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(*parts):
    """Absolute path to an asset, independent of the working directory."""
    return os.path.join(BASE_DIR, *parts)


# --- Display -----------------------------------------------------------------
TITLE = "Dodging Asteroid"
LOW_W, LOW_H = 320, 240          # logical (pixel-art) resolution
SCALE = 3                        # window = logical * SCALE
WIN_W, WIN_H = LOW_W * SCALE, LOW_H * SCALE
FPS = 60
MAX_DT = 1 / 30                  # clamp long frames so physics never explodes

# --- Ship --------------------------------------------------------------------
SHIP_ACCEL = 800                 # px/s^2 while a direction key is held
SHIP_MAX_SPEED = 130             # px/s
SHIP_FRICTION = 5.5              # velocity damping per second
SHIP_MARGIN = 4                  # keep this many px from screen edges

THROTTLE_RETRO = 0.12            # DOWN held: flames nearly out
THROTTLE_IDLE = 0.45             # cruising
THROTTLE_BOOST = 1.0             # UP held: full burn
THROTTLE_RESPONSE = 7.0          # how fast throttle follows its target (1/s)

# World scroll speed multiplier at retro / boost throttle
WORLD_SPEED_RETRO = 0.8
WORLD_SPEED_BOOST = 1.35

# --- Rules -------------------------------------------------------------------
WIN_SCORE = 30                   # asteroids dodged to win the single level
DEATH_DELAY = 1.4                # seconds of explosion before "game over"


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


DEFAULT_DIFFICULTY = Difficulty(
    spawn_interval=0.75,
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

NEBULA = [(16, 10, 32), (26, 14, 48), (40, 20, 68)]
STAR_COLORS = [(255, 255, 255), (200, 220, 255), (255, 236, 200), (170, 170, 210)]
PLANET_PALETTES = [
    [(26, 20, 46), (58, 40, 90), (96, 64, 130), (140, 104, 168)],
    [(34, 22, 30), (86, 48, 52), (140, 82, 70), (190, 132, 96)],
    [(14, 30, 44), (30, 70, 90), (54, 112, 128), (104, 164, 170)],
]

# Light comes from the upper left (x, y, z towards viewer), normalised in code.
LIGHT_DIR = (-0.55, -0.65, 0.52)
