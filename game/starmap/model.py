"""The star map as data and rules (no pygame): where the level planets are, the hidden data
caches with their story, and the little rocket that flies between them."""
import math
from dataclasses import dataclass

from ..config.tuning import (MAP_ACCEL, MAP_CACHE_SEEN, MAP_DRAG, MAP_GRAVITY, MAP_H, MAP_REACH,
                             MAP_SPEED, MAP_W)

# Level planet positions (map px), in play order: a winding route through the ORION REACH.
NODES = ((90, 440), (190, 400), (262, 318), (170, 236), (238, 138), (372, 104), (486, 176),
         (452, 306), (576, 372), (660, 238))
GATE = (676, 78)                         # the warp gate to galaxy 2 (open with the medal)
BLACK_HOLE = 8                           # the node that pulls the rocket (level 9)


@dataclass(frozen=True)
class Cache:
    """A hidden data cache: found by flying into it; pays coins once and tells a story."""
    id: str
    x: float
    y: float
    title: str
    lines: tuple                         # the story (short lines: they go on a card)
    coins: int


CACHES = (
    Cache("VEGA", 34, 34, "VEGA'S PERSONAL LOG",
          ("DAY 1 OF THE BLOCKADE.",
           "THE PIRATES ARE ONLY THE SYMPTOM.",
           "SOMETHING PAYS THEM IN ALIEN GOLD.",
           "I NEED A PILOT WHO ASKS NO QUESTIONS."), 120),
    Cache("PIRATE", 350, 488, "IRON FLEET LEDGER",
          ("CARGO: 40 T ORE. BUYER: UNKNOWN.",
           "DELIVERY POINT: DEEP IN THE REACH.",
           "THE BUYER SPEAKS IN CLICKS.",
           "NOBODY ASKS. THE PAY IS TOO GOOD."), 100),
    Cache("HOLLOW", 356, 238, "THE HOLLOW",
          ("A SPOT WHERE NO STARS SHINE.",
           "THE PROBES SAY: NOTHING IS HERE.",
           "THE PROBES ARE LYING.",
           "(YOU FOUND THE MIDDLE OF THE MAP.)"), 150),
    Cache("HELIOS", 120, 150, "FORGE BLUEPRINT",
          ("HELIOS WAS BUILT TO MAKE STARS.",
           "THE SWARM TAUGHT IT TO MAKE WAR.",
           "ITS PODS STILL HUM A LULLABY",
           "IN A LANGUAGE NOBODY KNOWS."), 100),
    Cache("HORIZON", 628, 462, "A VOICE BEYOND THE HORIZON",
          ("...THE TWINS WERE ONE SHIP ONCE.",
           "THE BLACK HOLE SPLIT IT IN TWO.",
           "THEY HAVE BEEN LOOKING FOR EACH",
           "OTHER EVER SINCE..."), 150),
    Cache("VEIL", 590, 36, "SIGNAL FROM THE VEIL",
          ("THE SWARM DID NOT COME TO CONQUER.",
           "IT CAME RUNNING.",
           "SOMETHING IN THE VEIL HUNTS IT.",
           "SOON IT WILL HUNT US TOO."), 200),
)


class MapShip:
    """The rocket on the map: steers towards a wanted direction, drifts to a stop."""

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.angle = 0.0                 # radians clockwise from "nose up"

    def update(self, dt, ax, ay, pull=(0.0, 0.0)):
        """ax, ay: -1..1 from the arrows (or the mouse); pull: extra acceleration."""
        length = math.hypot(ax, ay)
        if length > 1:
            ax, ay = ax / length, ay / length
        self.vx += (ax * MAP_ACCEL + pull[0]) * dt
        self.vy += (ay * MAP_ACCEL + pull[1]) * dt
        drag = max(0.0, 1 - MAP_DRAG * dt)
        self.vx *= drag
        self.vy *= drag
        speed = math.hypot(self.vx, self.vy)
        if speed > MAP_SPEED:
            self.vx, self.vy = self.vx / speed * MAP_SPEED, self.vy / speed * MAP_SPEED
        self.x = min(MAP_W - 8, max(8, self.x + self.vx * dt))
        self.y = min(MAP_H - 8, max(8, self.y + self.vy * dt))
        if speed > 12:
            self.angle = math.atan2(self.vx, -self.vy)

    @property
    def thrusting(self):
        return math.hypot(self.vx, self.vy) > 20


class StarMap:
    """Which planets are open, what the rocket is near, which caches are found."""

    def __init__(self, levels, unlocked, found, medal, ranks=None):
        self.levels = levels             # the galaxy's Level entries (NODES order)
        self.unlocked = unlocked         # levels the player may start (count)
        self.ranks = ranks or {}         # level index -> best rank (cleared levels)
        self.found = set(found)          # cache ids already opened
        self.medal = medal               # the galaxy is beaten: the gate is open
        self.ship = MapShip(0, 0)
        self.time = 0.0
        self.card = None                 # the Cache whose story is on screen

    def place_at(self, index):
        x, y = NODES[index]
        self.ship.x, self.ship.y = x, y + MAP_REACH * 0.6
        self.ship.vx = self.ship.vy = 0.0

    # --- where the rocket is --------------------------------------------------------------
    def near_node(self):
        """Index of the level planet within reach of the rocket (or None)."""
        best = None
        for i, (x, y) in enumerate(NODES[:len(self.levels)]):
            d = math.hypot(self.ship.x - x, self.ship.y - y)
            if d < MAP_REACH and (best is None or d < best[0]):
                best = (d, i)
        return best[1] if best else None

    def near_gate(self):
        return math.hypot(self.ship.x - GATE[0], self.ship.y - GATE[1]) < MAP_REACH

    def is_open(self, index):
        return index < self.unlocked

    def hidden_caches(self):
        return [c for c in CACHES if c.id not in self.found]

    def signal(self):
        """0..1: how close the nearest hidden cache is (the scanner's beeping)."""
        caches = self.hidden_caches()
        if not caches:
            return 0.0
        d = min(math.hypot(c.x - self.ship.x, c.y - self.ship.y) for c in caches)
        return max(0.0, 1 - d / (MAP_CACHE_SEEN * 3))

    def visible(self, cache):
        return math.hypot(cache.x - self.ship.x, cache.y - self.ship.y) < MAP_CACHE_SEEN

    def pull(self):
        """The black hole planet tugs at the rocket (it can always fly away)."""
        if not self.levels[BLACK_HOLE:]:
            return 0.0, 0.0
        x, y = NODES[BLACK_HOLE]
        dx, dy = x - self.ship.x, y - self.ship.y
        d = math.hypot(dx, dy)
        if d < 6 or d > 110:
            return 0.0, 0.0
        k = MAP_GRAVITY * (1 - d / 110) / d
        return dx * k, dy * k

    # --- update -------------------------------------------------------------------------
    def update(self, dt, ax, ay):
        """Move the rocket; returns a Cache it just flew into (or None)."""
        self.time += dt
        if self.card:
            ax = ay = 0.0                # reading: the rocket drifts
        self.ship.update(dt, ax, ay, self.pull())
        for cache in self.hidden_caches():
            if math.hypot(cache.x - self.ship.x, cache.y - self.ship.y) < 9:
                self.found.add(cache.id)
                self.card = cache
                return cache
        return None
