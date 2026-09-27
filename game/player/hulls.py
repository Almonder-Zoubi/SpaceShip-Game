"""Hull classes the player picks in the hangar: shape, size, engines, barrels and stat trade-offs.

A hull multiplies the level's ship model (MK I/II/III). Balance rule: hp * firepower == 1,
so every hull is equally strong in the boss damage race (see bosses/spec.py) and the real
differences are size (collision is pixel-exact), speed and weapon focus.
"""
from dataclasses import dataclass, replace

from ..core.pixelart import CharCanvas, outlined

# --- ARROW: the original 17x25 rocket --------------------------------------------
# Tapered red nose cone, gold band, porthole, hull panel seam, swept fins, twin engine bells.
ARROW_ROWS = (
    "........K........",
    ".......KPK.......",
    "......KPRrK......",
    "......KPRrK......",
    ".....KPRRRrK.....",
    ".....KPRRRrK.....",
    "....KPRRRRRrK....",
    "....KRRRRRRrK....",
    "....KYYYYYyyK....",
    "....KWLLLLLGK....",
    "....KWLKKKLGK....",
    "....KWKCBbKGK....",
    "....KWKBBbKGK....",
    "....KWKbbbKGK....",
    "....KWLKKKLGK....",
    "....KWLLLLLGK....",
    "..KRKWLLDLLGKrK..",
    ".KPRKWLLDLLGKRrK.",
    "KPRRKWLLDLLGKRRrK",
    "KPRRKWLLDLLGKRRrK",
    "KRRrKLLLDLLDKRrrK",
    "KRrrKDDDDDDDKrrrK",
    "KKKKKKKKKKKKKKKKK",
    ".....KOK.KOK.....",
    "....KOOOKOOOK....",
)

# --- WASP: small 13x17 interceptor, one engine, delta wings ------------------------
WASP_ROWS = (
    "......K......",
    ".....KPK.....",
    ".....KRK.....",
    "....KPRrK....",
    "....KCBbK....",
    "....KBbbK....",
    "...KWLLLGK...",
    "..KRKWLGKrK..",
    ".KPRKWLGKRrK.",
    "KPRRKWLGKRRrK",
    "KRRRKWLGKRRrK",
    "KRRrKLLDKRrrK",
    "KKrrKDDDKrrKK",
    "..KKKYYyKKK..",
    "....KKKKK....",
    ".....KOK.....",
    "....KOOOK....",
)


def _titan_rows():
    """TITAN: wide 27x25 heavy gunship — central hull, two engine pods, three engines."""
    c = CharCanvas(25, 23)
    # Wings joining the pods to the hull (lit leading edge, dark trailing edge).
    c.poly([(9, 8), (4, 11), (4, 17), (9, 17)], "R")
    c.poly([(16, 8), (21, 11), (21, 17), (16, 17)], "r")
    c.line(9, 8, 4, 11, "P")
    c.line(16, 8, 21, 11, "R")
    c.line(4, 17, 9, 17, "r")
    c.line(16, 17, 21, 17, "r")
    # Engine pods with red nose caps, gold band and dark vents.
    for x0, lit in ((0, True), (21, False)):
        c.rect(x0, 6, x0 + 3, 19, "L" if lit else "G")
        c.line(x0, 6, x0, 19, "W" if lit else "L")
        c.line(x0 + 3, 6, x0 + 3, 19, "G" if lit else "D")
        c.rect(x0, 3, x0 + 3, 5, "R" if lit else "r")
        c.line(x0 + 1, 2, x0 + 2, 2, "P" if lit else "R")
        c.rect(x0, 9, x0 + 3, 9, "Y" if lit else "y")
        c.rect(x0 + 1, 12, x0 + 2, 16, "D")
        c.rect(x0 + 1, 20, x0 + 2, 20, "D")
    # Central hull: nose cone, gold band, big canopy, seam and armour plates.
    c.poly([(12.5, 0), (9, 6), (16, 6)], "R")
    c.line(12, 0, 9, 6, "P")
    c.line(13, 0, 16, 6, "r")
    c.rect(9, 6, 16, 20, "L")
    c.line(9, 6, 9, 20, "W")
    c.line(16, 6, 16, 20, "G")
    c.rect(9, 6, 16, 7, "Y")
    c.line(15, 6, 16, 7, "y")
    c.rect(11, 9, 14, 13, "B")
    c.rect(11, 9, 12, 10, "C")
    c.line(14, 9, 14, 13, "b")
    c.rect(11, 13, 14, 13, "b")
    c.line(12, 15, 12, 20, "D")
    c.line(10, 16, 11, 16, "G")
    c.line(14, 16, 15, 16, "G")
    c.rect(9, 20, 16, 20, "D")
    # Engine bells: one under each pod and a big one under the hull.
    c.rect(1, 21, 2, 22, "O")
    c.rect(22, 21, 23, 22, "O")
    c.rect(11, 21, 14, 22, "O")
    return tuple(outlined(c.rows()))


def _lance_rows():
    """LANCE: long 13x33 needle — thin hull, canards, long gold-tipped nose, one big engine."""
    c = CharCanvas(11, 31)
    # Needle nose with a gold tip.
    c.line(5, 0, 5, 2, "Y")
    c.rect(4, 3, 6, 12, "R")
    c.line(4, 3, 4, 12, "P")
    c.line(6, 3, 6, 12, "r")
    # Canards near the front.
    c.poly([(4, 9), (1, 13), (4, 13)], "R")
    c.poly([(6, 9), (9, 13), (6, 13)], "r")
    # Long body with a slim canopy and a seam.
    c.rect(3, 12, 7, 27, "L")
    c.line(3, 12, 3, 27, "W")
    c.line(7, 12, 7, 27, "G")
    c.rect(3, 12, 7, 12, "Y")
    c.line(7, 12, 7, 12, "y")
    c.rect(4, 14, 6, 18, "B")
    c.line(4, 14, 4, 15, "C")
    c.line(6, 14, 6, 18, "b")
    c.line(5, 20, 5, 27, "D")
    # Swept tail fins.
    c.poly([(3, 20), (0, 25), (0, 28), (3, 27)], "R")
    c.poly([(7, 20), (10, 25), (10, 28), (7, 27)], "r")
    c.line(3, 20, 0, 25, "P")
    c.rect(3, 27, 7, 27, "D")
    # One big engine bell.
    c.rect(4, 28, 6, 30, "O")
    return tuple(outlined(c.rows()))


@dataclass(frozen=True)
class Hull:
    """A ship shape plus the multipliers it applies to the level's ship model.

    rows     -- sprite as character rows (colour keys of config.palette.SHIP_COLORS)
    nozzles  -- x of each engine bell, sprite-local from the centre (flames start below)
    barrels  -- machine-gun barrels (x, y), sprite-local from the centre (x right, y down)
    """
    name: str
    blurb: str
    rows: tuple
    nozzles: tuple
    barrels: tuple
    hp: float = 1.0               # hull points
    firepower: float = 1.0        # gun damage and laser dps (hp * firepower must stay 1)
    speed: float = 1.0
    laser: float = 1.0            # extra laser dps on top of firepower
    flame: float = 1.0            # engine flame length

    @property
    def size(self):
        return len(self.rows[0]), len(self.rows)

    @property
    def nose_y(self):
        """Sprite-local y of the nose tip."""
        return -len(self.rows) / 2

    def apply(self, loadout):
        """The level's ship model as flown with this hull."""
        return replace(loadout,
                       max_hp=round(loadout.max_hp * self.hp),
                       max_speed=loadout.max_speed * self.speed,
                       gun_damage=loadout.gun_damage * self.firepower,
                       laser_dps=loadout.laser_dps * self.firepower * self.laser)


ARROW = Hull("ARROW", "BALANCED ALL-ROUNDER", ARROW_ROWS,
             nozzles=(-2, 2), barrels=((-5.0, 1.0), (5.0, 1.0)))
WASP = Hull("WASP", "TINY AND FAST  -  FRAGILE HULL", WASP_ROWS,
            nozzles=(0,), barrels=((-5.0, 1.5), (5.0, 1.5)),
            hp=0.8, firepower=1.25, speed=1.15, flame=0.8)
TITAN = Hull("TITAN", "HEAVY ARMOUR  -  BIG AND SLOW", _titan_rows(),
             nozzles=(-11, 0, 11), barrels=((-11.0, -9.0), (11.0, -9.0)),
             hp=1.4, firepower=1 / 1.4, speed=0.85, flame=1.2)
LANCE = Hull("LANCE", "LASER SPECIALIST  -  LONG AND THIN", _lance_rows(),
             nozzles=(0,), barrels=((-4.0, -3.5), (4.0, -3.5)),
             speed=0.95, laser=1.3, flame=1.3)

HULLS = (ARROW, WASP, TITAN, LANCE)


def hull_named(name):
    """Look a hull up by name (e.g. from the save file); unknown names give the ARROW."""
    return next((h for h in HULLS if h.name == name), ARROW)
