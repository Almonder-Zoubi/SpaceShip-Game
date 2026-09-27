"""Minimal save file: top records, unlocked levels and the chosen ship, stored as JSON."""
import datetime
import json
import os

MAX_RECORDS = 5


class SaveData:
    """Loads on creation, saves after every change. path=None keeps everything in memory
    (dev mode and tests), so debugging never touches the real records."""

    def __init__(self, path):
        self.path = path
        self.records = []        # [{"score": int, "level": int, "date": "YYYY-MM-DD"}], best first
        self.unlocked = 1        # highest level the player may start from
        self.ship = "ARROW"      # hull picked in the hangar last time
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
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            self.records, self.unlocked, self.ship = [], 1, "ARROW"   # unreadable: start fresh

    def save(self):
        if not self.path:
            return
        tmp = self.path + ".tmp"                        # write, then swap: never half a file
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"records": self.records, "unlocked": self.unlocked, "ship": self.ship},
                          f, indent=2)
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

    def choose_ship(self, name):
        if name != self.ship:
            self.ship = name
            self.save()
