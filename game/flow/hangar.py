"""Hangar and gifts: the inventory screen before every level (equip, buy items and upgrades,
launch) and the gift screen after a first level clear."""
from ..config.palette import ACCENT, DANGER, GOOD, TEXT
from ..config.tuning import WINGMAN_TRAIN_COST, WINGMAN_TRAIN_XP, WINGMAN_XP
from ..levels.data import LEVEL_KEYS, LEVELS
from ..player.hulls import hull_named
from ..progression.inventory import OWNED, SHOP
from ..progression.items import (DEFAULT_SKINS, ITEMS, PAINT, PRIMARY, SECONDARY, SHIP, SKIN,
                                 TABS, UPGRADE, WINGMAN, items_of)
from ..progression.upgrades import TRACKS
from ..ui.hangar import HangarView
from .states import State


class HangarMixin:
    """Game mixin: hangar navigation (tabs, cursor, buy confirmation), upgrades, launching,
    gifts."""

    def open_hangar(self, level_index, score=0, focus=None, message=None):
        """The hangar before a level; LAUNCH starts level_index with this score.
        focus: an item id to select (e.g. a gift just taken). A cleared level's gift that
        was never taken (added by an update) is offered first."""
        key = self.inventory.unclaimed_gift()
        if key and not focus:
            self.offer_gift(key, ("hangar", level_index, score))
            return
        self.next_launch = (level_index, score)
        self.hangar_confirm = None
        self.hangar_message = message
        self.hangar_tab = SHIP
        self.hangar_cursor = {tab: 0 for tab in TABS}
        self._focus(focus or self.hull.name)
        self.set_state(State.HANGAR)

    def _focus(self, item_id):
        item = ITEMS[item_id]
        self.hangar_tab = item.kind
        self.hangar_cursor[item.kind] = [i.id for i in items_of(item.kind)].index(item_id)

    @property
    def hangar_item(self):
        """The selected item (None on the UPGRADES tab)."""
        if self.hangar_tab == UPGRADE:
            return None
        return items_of(self.hangar_tab)[self.hangar_cursor[self.hangar_tab]]

    @property
    def hangar_track(self):
        """The selected upgrade track (None on an item tab)."""
        return TRACKS[self.hangar_cursor[UPGRADE]] if self.hangar_tab == UPGRADE else None

    def hangar_view(self):
        items = [(item, self.inventory.status(item.id)) for item in items_of(self.hangar_tab)]
        item = self.hangar_item
        return HangarView(TABS, self.hangar_tab, items, self.hangar_cursor[self.hangar_tab],
                          self.hull.name, self.save.coins, LEVELS[self.next_launch[0]],
                          self.inventory.tiers, self.hangar_message,
                          self.inventory.unlock_hint(item.id) if item else "",
                          self.save.wingman, dict(self.save.wingmen_xp), tuple(self.primaries),
                          self.secondary.name if self.secondary else None,
                          {slot: self.skin(slot).id for slot in DEFAULT_SKINS},
                          len(self.save.achievements))

    def hangar_move(self, step):
        n = len(TRACKS) if self.hangar_tab == UPGRADE else len(items_of(self.hangar_tab))
        self.hangar_cursor[self.hangar_tab] = (self.hangar_cursor[self.hangar_tab] + step) % n
        self._hangar_idle()

    def hangar_switch_tab(self, step):
        self.hangar_tab = TABS[(TABS.index(self.hangar_tab) + step) % len(TABS)]
        self._hangar_idle()

    def _hangar_idle(self):
        self.hangar_confirm = None
        self.hangar_message = None
        self.audio.play("select")

    def hangar_select(self):
        """ENTER: equip an owned ship (ENTER on the equipped one = launch), buy a shop item
        (asks first), or say how a locked item is unlocked. On UPGRADES: buy the next tier."""
        if self.hangar_tab == UPGRADE:
            self._hangar_upgrade(self.hangar_track)
            return
        item = self.hangar_item
        status = self.inventory.status(item.id)
        if status == OWNED:
            if item.kind == SHIP and item.id != self.hull.name:
                self.choose_hull(hull_named(item.id))
                self.hangar_message = (f"{item.name} EQUIPPED", GOOD)
                self.audio.play("confirm")
            elif item.kind == WINGMAN and item.id != self.save.wingman:
                self.save.choose_wingman(item.id)
                self.hangar_message = (f"{item.name} JOINS YOU", GOOD)
                self.audio.play("confirm")
            elif item.kind == WINGMAN:
                self._hangar_train(item)
            elif item.kind == SKIN and self.skin(item.slot).id != item.id:
                self.wear(item.id)
                if item.slot == PAINT:
                    self.choose_hull(self.hull)          # rebuild the ship in the new paint
                self.hangar_message = (f"{item.name} ON", GOOD)
                self.audio.play("confirm")
            elif item.kind == SKIN:
                self.hangar_launch()
            elif item.slot:
                self._hangar_slot(item)
            else:
                self.hangar_launch()
        elif status == SHOP:
            if self.hangar_confirm != item.id:
                self.hangar_confirm = item.id
                self.hangar_message = (f"BUY {item.name} FOR {item.price} CR? ENTER", ACCENT)
                self.audio.play("select")
            elif self.inventory.buy(item.id):
                self.hangar_confirm = None
                if item.kind == SHIP:
                    self.choose_hull(hull_named(item.id))
                elif item.kind == WINGMAN:
                    self.save.choose_wingman(item.id)
                elif item.kind == SKIN:
                    self.wear(item.id)
                    if item.slot == PAINT:
                        self.choose_hull(self.hull)
                elif item.slot:
                    self.equip_new_weapon(item)
                self.hangar_message = (f"{item.name} BOUGHT!", GOOD)
                self.audio.play("power_up")
            else:
                self.hangar_confirm = None
                self.hangar_message = ("NOT ENOUGH CREDITS", DANGER)
                self.audio.play("denied")
        else:
            self.hangar_message = (self.inventory.unlock_hint(item.id), TEXT)
            self.audio.play("denied")

    def _hangar_slot(self, item):
        """ENTER on an owned weapon: a primary goes into a free slot (or replaces slot 2),
        an equipped one comes out (one always stays); a secondary toggles."""
        if item.slot == SECONDARY:
            equip = self.save.secondary != item.id
            self.save.secondary = item.id if equip else None
            text = f"{item.name} FITTED" if equip else f"{item.name} REMOVED"
        else:
            slots = list(self.primaries)
            if item.id in slots:
                if len(slots) == 1:
                    self.hangar_launch()
                    return
                slots.remove(item.id)
                text = f"{item.name} REMOVED"
            else:
                slots = (slots + [item.id])[-2:] if len(slots) < 2 else [slots[0], item.id]
                text = f"{item.name} IN SLOT {slots.index(item.id) + 1}"
            self.save.primaries = slots
        self.save.save()
        self.hangar_message = (text, GOOD)
        self.audio.play("confirm")

    def equip_new_weapon(self, item):
        """A new weapon (gift or shop) goes into a free slot."""
        if item.slot == PRIMARY and item.id not in self.primaries and len(self.primaries) < 2:
            self.save.primaries = list(self.primaries) + [item.id]
        elif item.slot == SECONDARY and not self.secondary:
            self.save.secondary = item.id
        self.save.save()

    def _hangar_train(self, item):
        """ENTER on the equipped wingman: TRAIN (XP for coins), with the same confirm step."""
        if self.wingman_level(item.id) >= len(WINGMAN_XP):
            self.hangar_message = (f"{item.name} IS LEVEL {len(WINGMAN_XP)}", GOOD)
            self.audio.play("denied")
        elif self.hangar_confirm != item.id:
            self.hangar_confirm = item.id
            self.hangar_message = (f"TRAIN {item.name} +{WINGMAN_TRAIN_XP} XP FOR "
                                   f"{WINGMAN_TRAIN_COST} CR? ENTER", ACCENT)
            self.audio.play("select")
        elif self.train_wingman(item.id):
            self.hangar_confirm = None
            self.hangar_message = (f"{item.name} TRAINED!", GOOD)
            self.audio.play("power_up")
        else:
            self.hangar_confirm = None
            self.hangar_message = ("NOT ENOUGH CREDITS", DANGER)
            self.audio.play("denied")

    def _hangar_upgrade(self, track):
        """ENTER on a track: ask for the next tier's price, ENTER again buys it."""
        tier = self.inventory.tier(track.id) + 1
        price = self.inventory.upgrade_cost(track.id)
        if price is None:
            self.hangar_message = (f"{track.id} IS MAXED", GOOD)
            self.audio.play("denied")
        elif self.hangar_confirm != track.id:
            self.hangar_confirm = track.id
            self.hangar_message = (f"{track.id} TIER {tier} FOR {price} CR? ENTER", ACCENT)
            self.audio.play("select")
        elif self.inventory.buy_upgrade(track.id):
            self.hangar_confirm = None
            self.hangar_message = (f"{track.id} TIER {tier}!", GOOD)
            self.audio.play("power_up")
        else:
            self.hangar_confirm = None
            self.hangar_message = ("NOT ENOUGH CREDITS", DANGER)
            self.audio.play("denied")

    def hangar_launch(self):
        self.audio.play("confirm")
        self.start(*self.next_launch)

    # --- gifts -------------------------------------------------------------------------
    def after_level_clear(self):
        """ENTER on the results screen: the level's gift (first clear only), then the hangar."""
        if self.inventory.gift_options(self.level_key):
            self.offer_gift(self.level_key, ("hangar", self.level_index + 1, self.score))
        else:
            self.open_hangar(self.level_index + 1, self.score)

    def after_win(self):
        """ENTER on the win screen: the last level's gift (if any), then the star map
        (a galaxy medal opens its warp gate)."""
        if self.inventory.gift_options(self.level_key):
            self.offer_gift(self.level_key, ("map",))
        else:
            self.new_run(self.level_index)
            self.open_star_map(self.level_index)

    def offer_gift(self, key, then):
        """REWARD screen for a level's gift; then = ("hangar", level_index, score) or
        ("map",)."""
        self.gift_key, self.gift_then = key, then
        self.gift_options = [ITEMS[i] for i in self.inventory.gift_options(key)]
        self.gift_cursor = 0
        index = LEVEL_KEYS.index(key)
        self.gift_paint = LEVELS[min(index + 1, len(LEVELS) - 1)].loadout.colors
        self.set_state(State.REWARD)

    def gift_move(self, step):
        if len(self.gift_options) > 1:
            self.gift_cursor = (self.gift_cursor + step) % len(self.gift_options)
            self.audio.play("select")

    def take_gift(self):
        item = self.gift_options[self.gift_cursor]
        self.inventory.claim(self.gift_key, item.id)
        self.audio.play("power_up")
        self.screen_flash(0.1)
        if item.kind == SHIP:
            self.choose_hull(hull_named(item.id))
        elif item.kind == WINGMAN and not self.save.wingman:
            self.save.choose_wingman(item.id)
        elif item.kind == SKIN:
            self.wear(item.id)
            if item.slot == PAINT:
                self.choose_hull(self.hull)
        elif item.slot:
            self.equip_new_weapon(item)
        if self.gift_then[0] == "map":
            self.new_run(self.level_index)
            self.open_star_map(self.level_index)
        else:
            _, level_index, score = self.gift_then
            self.open_hangar(level_index, score, focus=item.id,
                             message=(f"NEW: {item.name}", GOOD))
