"""Resolution, frame rate and file locations."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def asset(*parts):
    """Absolute path to an asset, independent of the working directory."""
    return os.path.join(BASE_DIR, *parts)


SAVE_FILE = asset("save.json")   # records + unlocked levels (see core/storage.py)

TITLE = "Dodging Asteroid"
LOW_W, LOW_H = 320, 240          # logical (pixel-art) resolution
SCALE = 3                        # window = logical * SCALE
WIN_W, WIN_H = LOW_W * SCALE, LOW_H * SCALE
FPS = 60
MAX_DT = 1 / 30                  # clamp long frames so physics never explodes

# Light comes from the upper left (x, y, z towards viewer), normalised in code.
LIGHT_DIR = (-0.55, -0.65, 0.52)
