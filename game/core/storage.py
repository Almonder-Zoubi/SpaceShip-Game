"""Save file (JSON): top records, unlocked levels, the chosen ship, coins, level ranks and the
inventory and the upgrade tiers.

Version 2 added the profile: coins in the bank, best rank per cleared level, owned items,
shop items, claimed gifts and upgrade tiers (missing = all 0); later fields (medals, star
map caches) default to empty. Older files load with an empty bank; their inventory is rebuilt
from the unlocked levels (progression.inventory). Broken values fall back to a fresh save."""
import datetime
import json
import os

from ..config.tuning import UPGRADE_TIERS
from ..progression.results import RANKS, better_rank

MAX_RECORDS = 5
VERSION = 2


class SaveData:
    """Loads on creation, saves after every change. path=None keeps everything in memory
    (dev mode and tests), so debugging never touches the real records."""

    def __init__(self, path):
        self.path = path
        self.records = []        # [{"score": int, "level": int, "date": "YYYY-MM-DD"}], best first
        self.unlocked = 1        # highest level the player may start from
        self.ship = "ARROW"      # hull picked in the hangar last time
        self.coins = 0           # the bank (coins only get here when a level is won)
        self.cleared = {}        # level key ("1-3" = galaxy 1, level 3) -> best rank
        self.owned = None        # item ids (None = not stored yet: Inventory rebuilds it)
        self.shop = []           # gifts not chosen: for sale now
        self.gifts = []          # level keys whose gift was claimed
        self.upgrades = {}       # upgrade track -> tier bought (missing = 0)
        self.options = {}        # core.options values (volumes, reduce shake / flashes)
        self.wingman = None      # equipped wingman (item id) or None
        self.wingmen_xp = {}     # wingman -> total XP
        self.primaries = None    # the 2 primary weapons R switches between (None = default)
        self.secondary = None    # the automatic secondary weapon (or None)
        self.skins = {}          # skin slot (PAINT, TRAIL ...) -> equipped skin item
        self.achievements = []   # ids of earned achievements
        self.minion_kills = 0    # lifetime counter (an achievement)
        self.medals = []         # galaxies beaten (numbers): the medal on the title / star map
        self.caches = []         # star map data caches found (ids)
        self.load()

    @property
    def best(self):
        return self.records[0]["score"] if self.records else 0

    def load(self):
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            records = [{"score": int(r["score"]), "level": int(r["level"]), "date": str(r["date"])}
                       for r in data.get("records", [])]
            self.records = sorted(records, key=lambda r: -r["score"])[:MAX_RECORDS]
            self.unlocked = max(1, int(data.get("unlocked", 1)))
            self.ship = str(data.get("ship", "ARROW"))
            self.coins = max(0, int(data.get("coins", 0)))
            self.cleared = {str(k): v for k, v in dict(data.get("cleared", {})).items()
                            if v in RANKS}
            owned = data.get("owned")
            self.owned = None if owned is None else _strings(owned)
            self.shop, self.gifts = _strings(data.get("shop", [])), _strings(data.get("gifts", []))
            self.upgrades = {str(k): min(UPGRADE_TIERS, max(0, int(v)))
                             for k, v in dict(data.get("upgrades", {})).items()}
            self.options = {str(k): int(v) for k, v in dict(data.get("options", {})).items()}
            wingman = data.get("wingman")
            self.wingman = None if wingman is None else str(wingman)
            self.wingmen_xp = {str(k): max(0, int(v))
                               for k, v in dict(data.get("wingmen_xp", {})).items()}
            primaries = data.get("primaries")
            self.primaries = None if primaries is None else _strings(primaries)[:2]
            secondary = data.get("secondary")
            self.secondary = None if secondary is None else str(secondary)
            self.skins = {str(k): str(v) for k, v in dict(data.get("skins", {})).items()}
            self.achievements = _strings(data.get("achievements", []))
            self.minion_kills = max(0, int(data.get("minion_kills", 0)))
            self.medals = [int(m) for m in data.get("medals", [])]
            self.caches = _strings(data.get("caches", []))
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            self._reset()                               # unreadable: start fresh

    def _reset(self):
        self.records, self.unlocked, self.ship = [], 1, "ARROW"
        self.coins, self.cleared = 0, {}
        self.owned, self.shop, self.gifts = None, [], []
        self.upgrades, self.options = {}, {}
        self.wingman, self.wingmen_xp = None, {}
        self.primaries, self.secondary = None, None
        self.skins, self.achievements, self.minion_kills = {}, [], 0
        self.medals, self.caches = [], []

    def save(self):
        if not self.path:
            return
        tmp = self.path + ".tmp"                        # write, then swap: never half a file
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"version": VERSION, "records": self.records,
                           "unlocked": self.unlocked, "ship": self.ship, "coins": self.coins,
                           "cleared": self.cleared, "owned": self.owned, "shop": self.shop,
                           "gifts": self.gifts, "upgrades": self.upgrades,
                           "options": self.options, "wingman": self.wingman,
                           "wingmen_xp": self.wingmen_xp, "primaries": self.primaries,
                           "secondary": self.secondary, "skins": self.skins,
                           "achievements": self.achievements,
                           "minion_kills": self.minion_kills, "medals": self.medals,
                           "caches": self.caches}, f, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass                                        # read-only folder: play on without saving

    def add_record(self, score, level):
        """Store a finished run. Returns its rank (1 = new high score) or None."""
        if score <= 0:
            return None
        entry = {"score": int(score), "level": int(level),
                 "date": datetime.date.today().isoformat()}
        self.records.append(entry)
        self.records.sort(key=lambda r: -r["score"])    # stable: older equal scores stay ahead
        self.records = self.records[:MAX_RECORDS]
        self.save()
        for rank, r in enumerate(self.records, 1):
            if r is entry:
                return rank
        return None

    def unlock(self, level_number):
        if level_number > self.unlocked:
            self.unlocked = level_number
            self.save()

    def choose_wingman(self, name):
        if name != self.wingman:
            self.wingman = name
            self.save()

    def choose_ship(self, name):
        if name != self.ship:
            self.ship = name
            self.save()

    def clear_level(self, key, rank, coins):
        """A won level: bank its coins and keep the best rank. Returns True on a first clear."""
        first = key not in self.cleared
        self.cleared[key] = better_rank(self.cleared.get(key), rank)
        self.coins += int(coins)
        self.save()
        return first

    def is_cleared(self, key):
        return key in self.cleared

    def add_medal(self, galaxy):
        """A galaxy beaten. Returns True the first time."""
        if galaxy in self.medals:
            return False
        self.medals.append(galaxy)
        self.save()
        return True

    def find_cache(self, cache_id):
        """A star map data cache opened. Returns True the first time."""
        if cache_id in self.caches:
            return False
        self.caches.append(cache_id)
        self.save()
        return True


def _strings(values):
    if not isinstance(values, list):
        raise ValueError("expected a list")
    return [str(v) for v in values]
