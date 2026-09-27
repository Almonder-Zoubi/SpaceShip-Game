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
