"""Ship art: paint jobs per model and the banked / leaning frames of any hull (see hulls.py)."""
from ..config.palette import SHIP_COLORS
from ..core.pixelart import rotate_pixel_art, sprite_from_rows


def _bank_rows(rows, direction):
    """Fake a roll: foreshorten the fin on the side we turn towards (-1 left, 1 right)."""
    out = []
    for row in rows:
        chars = list(row if direction < 0 else row[::-1])
        if chars[0] != ".":
            chars[0] = "."
            if chars[1] != ".":
                chars[1] = "K"
        # The far fin rotates into the light.
        for i in range(len(chars) - 3, len(chars)):
            if chars[i] == "r":
                chars[i] = "R"
        row = "".join(chars)
        out.append(row if direction < 0 else row[::-1])
    return out


# Ship models: MK II swaps the red paint for cobalt blue with gold trim and a green canopy.
SHIP_PALETTES = {
    "mk1": SHIP_COLORS,
    "mk2": {**SHIP_COLORS,
            "R": (52, 110, 220), "r": (26, 50, 136), "P": (150, 200, 255),
            "Y": (255, 226, 96), "y": (200, 132, 30),
            "C": (200, 255, 210), "B": (72, 208, 140), "b": (24, 104, 84)},
    # MK III: violet stealth paint, gold trim, glowing amber canopy.
    "mk3": {**SHIP_COLORS,
            "R": (150, 72, 220), "r": (78, 30, 138), "P": (214, 168, 255),
            "L": (176, 172, 196), "G": (112, 108, 136), "D": (66, 62, 90),
            "Y": (255, 214, 80), "y": (196, 120, 24),
            "C": (255, 244, 190), "B": (255, 170, 60), "b": (170, 90, 20)},
    # MK IV: polished gold on gunmetal, red trim, ice-blue canopy.
    "mk4": {**SHIP_COLORS,
            "R": (236, 176, 48), "r": (150, 92, 22), "P": (255, 226, 140),
            "W": (236, 236, 244), "L": (150, 156, 176), "G": (96, 102, 124), "D": (54, 58, 78),
            "Y": (255, 84, 72), "y": (160, 34, 44),
            "C": (220, 255, 255), "B": (70, 210, 255), "b": (24, 104, 170)},
    # --- skins (G8): paint jobs the player picks; they replace the level's MK paint ---
    # SOLAR: gold hull, red trim, orange canopy.
    "solar": {**SHIP_COLORS,
              "R": (255, 190, 50), "r": (190, 110, 20), "P": (255, 236, 150),
              "Y": (230, 50, 50), "y": (140, 20, 30),
              "C": (255, 230, 170), "B": (255, 140, 40), "b": (170, 70, 20)},
    # NEON: 80s magenta and cyan on a dark hull.
    "neon": {**SHIP_COLORS,
             "R": (255, 60, 200), "r": (150, 20, 120), "P": (255, 170, 240),
             "W": (200, 200, 230), "L": (110, 110, 150), "G": (70, 70, 110), "D": (40, 40, 70),
             "Y": (60, 240, 255), "y": (20, 140, 180),
             "C": (200, 255, 255), "B": (60, 240, 255), "b": (20, 120, 170)},
    # STEALTH: black and grey, a faint red canopy.
    "stealth": {**SHIP_COLORS,
                "R": (70, 72, 86), "r": (40, 40, 52), "P": (120, 122, 140),
                "W": (150, 152, 168), "L": (96, 98, 112), "G": (64, 66, 80), "D": (36, 36, 48),
                "Y": (120, 122, 140), "y": (70, 72, 86),
                "C": (255, 140, 140), "B": (170, 40, 50), "b": (90, 20, 30)},
    # RETRO: NES blue and red.
    "retro": {**SHIP_COLORS,
              "R": (228, 40, 40), "r": (140, 16, 16), "P": (255, 140, 120),
              "W": (252, 252, 252), "L": (188, 188, 188), "G": (116, 116, 116),
              "D": (64, 64, 64), "Y": (32, 80, 236), "y": (16, 40, 140),
              "C": (164, 228, 252), "B": (60, 188, 252), "b": (0, 88, 248)},
    # GOLD TRIM (no-hit boss achievement): white hull, gold everywhere.
    "gold": {**SHIP_COLORS,
             "R": (255, 214, 80), "r": (196, 136, 30), "P": (255, 244, 180),
             "Y": (255, 255, 220), "y": (220, 180, 90),
             "C": (255, 250, 220), "B": (255, 200, 60), "b": (170, 110, 20)},
}


def build_ship_frames(rows, colors=SHIP_COLORS):
    """Return {-1: bank left, 0: level, 1: bank right} surfaces."""
    return {
        -1: sprite_from_rows(_bank_rows(rows, -1), colors),
        0: sprite_from_rows(rows, colors),
        1: sprite_from_rows(_bank_rows(rows, 1), colors),
    }


def build_ship_tilts(rows, max_degrees, steps, colors=SHIP_COLORS):
    """Leaning frames for diagonal flight: index 0 = most left ('\\'), last = most right ('/')."""
    angles = [max_degrees * i / steps for i in range(-steps, steps + 1)]
    return [rotate_pixel_art(rows, colors, a) for a in angles]
