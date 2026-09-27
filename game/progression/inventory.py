"""What the player owns, what the shop sells and which level gifts are claimed.

Works on a SaveData (owned / shop / gifts lists) and saves after every change. A save
without an inventory (older versions) gets every gift of the levels it has already
cleared, so nobody loses what they had.
"""
from .items import GIFTS, ITEMS, STARTER, gift_level

OWNED, SHOP, LOCKED = "OWNED", "SHOP", "LOCKED"


class Inventory:
    def __init__(self, save, level_keys, everything=False):
        """level_keys: every level's key in play order (to migrate old saves)."""
        self.save = save
        self.level_keys = level_keys
        if save.owned is None:
            self._migrate()
        if everything:                   # dev mode: all items (the save is memory-only)
            self.grant_all()

    def _migrate(self):
        s = self.save
        s.owned, s.shop, s.gifts = list(STARTER), [], []
        for key in self.level_keys[:max(0, s.unlocked - 1)]:
            for item_id in GIFTS.get(key, ()):
                self._add(item_id)
            if key in GIFTS:
                s.gifts.append(key)
        s.save()

    def _add(self, item_id):
        if item_id not in self.save.owned:
            self.save.owned.append(item_id)
        if item_id in self.save.shop:
            self.save.shop.remove(item_id)

    def owns(self, item_id):
        return item_id in self.save.owned

    def status(self, item_id):
        if self.owns(item_id):
            return OWNED
        return SHOP if item_id in self.save.shop else LOCKED

    @staticmethod
    def unlock_hint(item_id):
        key = gift_level(item_id)
        return f"GIFT AFTER LEVEL {key.split('-')[1]}" if key else "COMING LATER"

    def gift_options(self, level_key):
        """Items offered after this level (empty once the gift is claimed)."""
        if level_key in self.save.gifts:
            return ()
        return GIFTS.get(level_key, ())

    def claim(self, level_key, item_id):
        """Take one gift; the other option goes to the shop."""
        options = self.gift_options(level_key)
        assert item_id in options, (level_key, item_id)
        self._add(item_id)
        for other in options:
            if other != item_id and not self.owns(other) and other not in self.save.shop:
                self.save.shop.append(other)
        self.save.gifts.append(level_key)
        self.save.save()

    def can_afford(self, item_id):
        return self.save.coins >= ITEMS[item_id].price

    def buy(self, item_id):
        """Buy a shop item with coins from the bank. Returns True if bought."""
        if self.status(item_id) != SHOP or not self.can_afford(item_id):
            return False
        self.save.coins -= ITEMS[item_id].price
        self._add(item_id)
        self.save.save()
        return True

    def grant_all(self):
        """Own every item and mark every gift as claimed (dev mode, tests)."""
        for item_id in ITEMS:
            self._add(item_id)
        self.save.gifts = sorted(set(self.save.gifts) | set(GIFTS))
        self.save.save()
