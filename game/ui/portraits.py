"""Pixel portraits (24x24) of everyone who speaks on the radio."""
import random


from ..config.palette import INK
from ..core.pixelart import sprite_from_rows
from ..story.dialog import NYX, UNKNOWN, UNMASKED, VANTA, VEGA

VEGA_ROWS = (
    "........KKKKKKKK........",
    "......KKGGGGGGGGKK......",
    ".....KGGLLLLLLLLGGK.....",
    "....KGLLLLLLLLLLLLGK....",
    "....KGLKKKKKKKKKKLGK....",
    "...KGLKCCCCCCCCCCKLGK...",
    "...KGKCSSSSSSSSSSCKGK...",
    "...KGKSSSSSSSSSSSSKGK...",
    "...KGKSKKSSSSSSKKSKGK...",
    "...KGKSWBSSSSSSWBSKGK...",
    "...KGKSSSSSsSSSSSSKGK...",
    "...KGKSSSSSsSSSSSSKGK...",
    "...KGKsSSSSSSSSSSsKGK...",
    "...KGKKsSSRRRRSSsKKGK...",
    "...KGGKKsSSSSSSsKKGGK...",
    "....KGGKKssssssKKGGK....",
    "....KGGGKKKKKKKKGGGK....",
    "...KDDGGGGGGGGGGGGDDK...",
    "..KDDDGGGYYGGYYGGGDDDK..",
    ".KDDDDGGGGGGGGGGGGDDDDK.",
    "KDDDDDDGGGGGGGGGGDDDDDDK",
    "KDDDDDDDGGGGGGGGDDDDDDDK",
    "KDDDDDDDDGGGGGGDDDDDDDDK",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
)
VEGA_COLORS = {
    "K": INK, "G": (110, 118, 140), "L": (170, 178, 196), "C": (120, 220, 255),
    "S": (232, 186, 150), "s": (184, 132, 104), "W": (250, 250, 245), "B": (60, 120, 220),
    "R": (170, 70, 80), "D": (48, 56, 92), "Y": (255, 204, 64),
}

# VANTA: not a face. A hole with a ragged violet rim and two white points that watch.
VANTA_ROWS = (
    "........................",
    ".........vv..v..........",
    "......v.vVVvvVv.v.......",
    ".....vVVVKKKKKVVVv......",
    "....vVKKKKKKKKKKKVv.....",
    "...vVKKKKKKKKKKKKKVv....",
    "..vVKKKKKKKKKKKKKKKVv...",
    "..VKKKKKKKKKKKKKKKKKVv..",
    ".vVKKKKKKKKKKKKKKKKKKV..",
    ".VKKKKKWKKKKKKKWKKKKKVv.",
    ".VKKKKKKKKKKKKKKKKKKKKV.",
    "vVKKKKKKKKKKKKKKKKKKKKV.",
    ".VKKKKKKKKKKKKKKKKKKKKVv",
    ".VKKKKKKKKKKKKKKKKKKKKV.",
    ".vVKKKKKKKKKKKKKKKKKKVv.",
    "..VKKKKKKKKKKKKKKKKKKV..",
    "..vVKKKKKKKKKKKKKKKKVv..",
    "...vVKKKKKKKKKKKKKKVv...",
    "....vVKKKKKKKKKKKKVv....",
    ".....vVVKKKKKKKKVVv.....",
    "......vvVVVKKVVVvv......",
    "........v.vVVv.v........",
    "...........vv...........",
    "........................",
)
VANTA_COLORS = {"K": (0, 0, 0), "V": (110, 60, 170), "v": (50, 24, 80), "W": (255, 255, 255)}


# NYX: a white mask with two slits in a violet hood.
NYX_ROWS = (
    "........................",
    "........vvvvvvvv........",
    "......vvVVVVVVVVvv......",
    ".....vVVKKKKKKKKVVv.....",
    "....vVKKKKKKKKKKKKVv....",
    "....VKKWWWWWWWWWWKKV....",
    "...vVKWWWWWWWWWWWWKVv...",
    "...VKWWWWWWWWWWWWWWKV...",
    "...VKWWKKKWWWWKKKWWKV...",
    "...VKWWWKKWWWWKKWWWKV...",
    "...VKWWWWWWWWWWWWWWKV...",
    "...VKWWWWWWggWWWWWWKV...",
    "...VKKWWWWWggWWWWWKKV...",
    "...vVKWWWWWWWWWWWWKVv...",
    "....VKKWWWRRRRWWWKKV....",
    "....vVKKWWWWWWWWKKVv....",
    ".....VVKKWWWWWWKKVV.....",
    "....vVVVKKKKKKKKVVVv....",
    "...vVVVVVKKKKKKVVVVVv...",
    "..vVVVVVVVKKKKVVVVVVVv..",
    ".vVVVVVVVVVKKVVVVVVVVVv.",
    "vVVVVVVVVVVVVVVVVVVVVVVv",
    "VVVVVVVVVVVVVVVVVVVVVVVV",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
)
NYX_COLORS = {"K": (0, 0, 0), "W": (236, 236, 240), "g": (170, 170, 180),
              "V": (70, 30, 100), "v": (35, 14, 50), "R": (200, 40, 60)}

# VANTA unmasked: the same fleet helmet and collar as Vega's (look at the gold marks),
# worn out, with a black visor and two white points where the eyes were.
UNMASKED_ROWS = tuple(row.translate(str.maketrans("SsBR", "KKKK")) for row in VEGA_ROWS)
UNMASKED_COLORS = {"K": (0, 0, 0), "G": (64, 64, 76), "L": (96, 96, 110), "C": (110, 60, 170),
                   "W": (255, 255, 255), "D": (30, 30, 44), "Y": (255, 204, 64)}


class Portraits:
    """Portrait surfaces by speaker; UNKNOWN is fresh static every frame."""

    def __init__(self):
        self._faces = {VEGA: sprite_from_rows(VEGA_ROWS, VEGA_COLORS),
                       VANTA: sprite_from_rows(VANTA_ROWS, VANTA_COLORS),
                       NYX: sprite_from_rows(NYX_ROWS, NYX_COLORS),
                       UNMASKED: sprite_from_rows(UNMASKED_ROWS, UNMASKED_COLORS)}
        self._eyes = sprite_from_rows(VANTA_ROWS, {**VANTA_COLORS, "W": (0, 0, 0)})

    def draw(self, surf, speaker, pos, time):
        if speaker == UNKNOWN or speaker not in self._faces:
            rng = random.Random(int(time * 20))
            for y in range(24):
                for x in range(0, 24, 2):
                    v = rng.randrange(20, 140)
                    surf.fill((v, v, v), (pos[0] + x, pos[1] + y, 2, 1))
            return
        face = self._faces[speaker]
        if speaker == VANTA and int(time * 3) % 7 == 0:          # it blinks. slowly.
            face = self._eyes
        surf.blit(face, pos)
