"""The story as data: boss files, the heralds, VANTA's file, the ECHOES (puzzle pieces),
the hidden message in Vega's radio and the transmissions. Pure data, no pygame.

How the mystery fits together (the answer, revealed in galaxy 5): the Dawn Key saves the
stars, but the pilot who uses it is hollowed and becomes VANTA. VANTA was the scout before
you, with the same callsign ARROW-01; Vega was its wingmate and turned back. Vega needs a new
scout for every turn of the cycle. Every clue below points there and none contradicts it:
the first letters of Vega's opening lines, the margin notes in this logbook (written by the
previous owner of the callsign), the ARROW-01 plate in Scrapjaw's jaw, the impossible record
on the title screen, and the ECHO mosaics.
"""
from dataclasses import dataclass

from .dialog import UNKNOWN, VANTA, VEGA, Line

CALLSIGN = "ARROW-01"
TEXT_WIDTH = 32                   # characters that fit a journal panel line

# The first letters of the first radio line of levels 1..10 (levels/data.py) spell this.
ACROSTIC = "YOUARENEXT"
DECODED = "YOU ARE NEXT"


@dataclass(frozen=True)
class Dossier:
    """A boss's file in the journal. `boss` is its BossSpec name."""
    boss: str
    facts: tuple                  # what the fleet knows
    vanta: tuple                  # its link to VANTA
    note: str                     # a margin note in someone else's hand (red)


DOSSIERS = (
    Dossier("GUNSHIP", ("IRON FLEET ENFORCER.", "HIRED MUSCLE, CHEAP AND LOUD."),
            ("ITS CREW WAS PAID IN BLACK GOLD.", "GOLD THAT SWALLOWS LIGHT."),
            "AIM FOR THE CHARGE GLOW. I DID."),
    Dossier("CARRIER", ("A DRONE FACTORY WITH ENGINES.", "LAUNCHES SWARMS OF DRONES."),
            ("ITS DRONES KEPT A COUNTDOWN", "NOBODY PROGRAMMED."),
            "THE DRONES REMEMBER ME."),
    Dossier("MOTHERSHIP", ("FLAGSHIP OF THE IRON FLEET.", "HID IN THE DARK NEBULA."),
            ("ITS LOG HELD ONE ORDER:", "DIG AT THE FROZEN RIFT."),
            "SAME BEAM. SAME SCAR."),
    Dossier("LEVIATHAN", ("AN ANCIENT SERPENT IN THE ICE.", "ITS SONG KEPT THE SWARM AWAY."),
            ("THE DIGGING WOKE IT. ITS CRY", "CALLED THE SWARM. AS PLANNED."),
            "WE BROKE THE SONG. AGAIN."),
    Dossier("HELIOS", ("A FORGE BUILT TO MAKE STARS.", "THE SWARM TAUGHT IT WAR."),
            ("THE DAWN KEY WAS FORGED HERE,", "IN FIVE SHARDS. LONG AGO."),
            "DON'T LOOK INTO THE FORGE."),
    Dossier("WRAITH", ("A STEALTH FRIGATE. NO CREW", "WAS EVER FOUND ABOARD."),
            ("THE CREW IS NOT GONE.", "THEY ARE HOLLOW."),
            "HOLLOW IS NOT DEAD. I KNOW."),
    Dossier("KALEIDOS", ("A QUEEN OF LIVING CRYSTAL.", "IT SPLITS LIGHT, AND SHIPS."),
            ("ITS SHARDS SHOWED A SECOND", "SHIP BEHIND YOURS. ALWAYS."),
            "IT SHOWED ME TWO SHIPS. BOTH ME."),
    Dossier("SCRAPJAW", ("A KING BUILT FROM WRECKS.", "IT WEARS WHAT IT KILLS."),
            ("A PLATE IN ITS JAW READS", "'" + CALLSIGN + "'. YOUR CALLSIGN."),
            "THAT PLATE IS MINE."),
    Dossier("THE TWINS", ("ORA AND ZEN. ONE SHIP ONCE,", "TORN IN TWO BY THE HOLE."),
            ("ONE HALF WENT ON.", "ONE HALF WAS LEFT BEHIND."),
            "ONE GOES ON. ONE STAYS."),
    Dossier("THE WARDEN", ("THE DOOR OF THE VEIL.", "IT OPENS ONLY THROUGH ITS GAP."),
            ("VANTA BUILT IT TO WAIT", "FOR A SHIP THAT CARRIES A SHARD."),
            "IT LET ME THROUGH. LAST TIME."),
    Dossier("THE OVERMIND", ("THE HEART OF THE SWARM.", "IT GUARDED SHARD 1."),
            ("IT WAS NOT INVADING.", "IT WAS RUNNING FROM VANTA."),
            "IT WASN'T THE ENEMY. RUN."),
    Dossier("LEECH MAW", ("A REEF-EEL AS BIG AS A MOON.", "IT HUNTS WHAT RUNS."),
            ("IT FOLLOWS SHARD-LIGHT.", "IT WAS BRED TO FOLLOW MINE."),
            "DON'T LOOK BACK. JUST BOOST."),
    Dossier("THE HOLLOW REAPER", ("IT HARVESTS THE YOUNG OF", "EVERY KIND. NONE COME BACK."),
            ("IT BRINGS THEM TO VANTA.", "HOLLOW ONES START YOUNG."),
            "I LET IT TAKE THE BROOD."),
    Dossier("ECLIPSE", ("A DEAD STAR THAT EATS LIGHT.", "ONLY ITS CORONA STILL BURNS."),
            ("VANTA WEARS ITS DARK.", "IT IS A PIECE OF THE KING."),
            "IT GOES DARK LIKE I DID."),
    Dossier("THE MIMIC", ("A CHROME HUNTER. IT COPIES", "THE PILOT IT FACES."),
            ("IT SHOWS YOU WHAT YOU WILL", "BE. SAME SHIP. SAME GUNS."),
            "IT COPIED ME FIRST."),
    Dossier("TEMPO", ("A METRONOME AS BIG AS A", "CRUISER. IT KEEPS THE BEAT."),
            ("VANTA'S CLOCK. IT COUNTS", "THE TURNS OF THE CYCLE."),
            "IT WAS ON 3. NOW IT'S ON 4."),
)
DOSSIER_BY_BOSS = {d.boss: d for d in DOSSIERS}


@dataclass(frozen=True)
class Herald:
    """A boss still to come: a black file until its galaxy opens it."""
    name: str
    galaxy: int
    title: str
    lines: tuple


HERALDS = (
    Herald("NYX", 2, "THE FIRST HERALD", ("GUARDS SHARD 2 IN THE VEIL.", "SEES IN THE DARK.")),
    Herald("MORROW", 3, "THE WITHERING", ("GUARDS SHARD 3 IN BLOOM.", "WHAT IT TOUCHES ROTS.")),
    Herald("KAIROS", 4, "WHO STOLE TIME", ("GUARDS SHARD 4.", "IT HAS SEEN THIS BEFORE.")),
    Herald("VANTA", 5, "THE HOLLOW KING", ("WAITS AT THE CORE.",)),
)


def redact(text, shown=1):
    """'NYX' -> 'N##' (the font draws # as a black block)."""
    return "".join(c if i < shown or c == " " else "#" for i, c in enumerate(text))


# VANTA's file: lines that open as the player learns more. (condition, text)
# Conditions: "medal1" = galaxy 1 beaten, "decoder" = every galaxy 1 echo found,
# "never" = stays black until galaxy 5.
VANTA_FILE = (
    ("medal1", "NAME: VANTA, THE HOLLOW KING."),
    ("medal1", "A HOLE IN THE LIGHT. IT THINKS."),
    ("medal1", "WANTS: THE FIVE SHARDS OF THE"),
    ("medal1", "DAWN KEY. YOU CARRY ONE."),
    ("decoder", "VEGA KNEW. READ VEGA'S FIRST"),
    ("decoder", "WORDS, LEVEL BY LEVEL."),
    ("never", "WHO IT WAS: " + redact(CALLSIGN, 0)),
)


@dataclass(frozen=True)
class Echo:
    """A fragment of VANTA's memory, found in a star map data cache: one mosaic tile."""
    cache: str                    # starmap.model.CACHES id
    tile: int                     # position in the galaxy's mosaic (reading order)
    text: str


ECHOES = (
    Echo("VEGA", 0, "TWO SHIPS LEAVE AT DAWN."),
    Echo("PIRATE", 1, "WING TO WING ACROSS THE REACH."),
    Echo("HELIOS", 2, "THE KEY BURNS IN MY HOLD."),
    Echo("VEIL", 3, "AT THE CORE, LIGHT ASKS A PRICE."),
    Echo("HORIZON", 4, "MY WINGMATE TURNS BACK."),
    Echo("HOLLOW", 5, "THE LIGHT GOES OUT IN ME."),
)
ECHO_BY_CACHE = {e.cache: e for e in ECHOES}
MOSAIC = "TWO SHIPS, SIDE BY SIDE"    # what galaxy 1's finished mosaic shows

# Story beats that play once (their ids are saved in SaveData.story).
TRANSMISSIONS = {
    "G1_WARP": (
        Line(UNKNOWN, "...SCOUT... CAN YOU HEAR..."),
        Line(VANTA, "YOU CARRY MY SHARD, LITTLE SCOUT."),
        Line(VANTA, "CARRY IT WELL. ALL THE WAY IN."),
        Line(VANTA, "WE HAVE DONE THIS BEFORE."),
        Line(VEGA, "IGNORE IT. THAT SIGNAL IS A LIE."),
        Line(VEGA, "JUMP. NOW."),
    ),
}

# A record on the title's score board that can't exist: all 50 levels, by your callsign.
GHOST_RECORD = {"score": 999999, "level": 50, "date": CALLSIGN}
