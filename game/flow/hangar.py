"""Hangar and gifts: the inventory screen before every level (equip, buy, launch) and the gift
screen after a first level clear."""
from ..config.palette import ACCENT, DANGER, GOOD, TEXT
from ..levels.data import LEVELS
from ..player.hulls import hull_named
from ..progression.inventory import OWNED, SHOP
from ..progression.items import ITEMS, SHIP, TABS, items_of
from ..ui.hangar import HangarView
from .states import State


class HangarMixin:
    """Game mixin: hangar navigation (tabs, cursor, buy confirmation), launching, gifts."""

    def open_hangar(self, level_index, score=0, focus=None, message=None):
        """The hangar before a level; LAUNCH starts level_index with this score.
        focus: an item id to select (e.g. a gift just taken)."""
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
        return items_of(self.hangar_tab)[self.hangar_cursor[self.hangar_tab]]

    def hangar_view(self):
        items = [(item, self.inventory.status(item.id)) for item in items_of(self.hangar_tab)]
        return HangarView(TABS, self.hangar_tab, items, self.hangar_cursor[self.hangar_tab],
                          self.hull.name, self.save.coins, LEVELS[self.next_launch[0]],
                          self.hangar_message, self.inventory.unlock_hint(self.hangar_item.id))

    def hangar_move(self, step):
        n = len(items_of(self.hangar_tab))
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
        (asks first), or say how a locked item is unlocked."""
        item = self.hangar_item
        status = self.inventory.status(item.id)
        if status == OWNED:
            if item.kind == SHIP and item.id != self.hull.name:
                self.choose_hull(hull_named(item.id))
                self.hangar_message = (f"{item.name} EQUIPPED", GOOD)
                self.audio.play("confirm")
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
                self.hangar_message = (f"{item.name} BOUGHT!", GOOD)
                self.audio.play("power_up")
            else:
                self.hangar_confirm = None
                self.hangar_message = ("NOT ENOUGH CREDITS", DANGER)
                self.audio.play("denied")
        else:
            self.hangar_message = (self.inventory.unlock_hint(item.id), TEXT)
            self.audio.play("denied")

    def hangar_launch(self):
        self.audio.play("confirm")
        self.start(*self.next_launch)

    # --- gifts -------------------------------------------------------------------------
    def after_level_clear(self):
        """ENTER on the results screen: the level's gift (first clear only), then the hangar."""
        options = self.inventory.gift_options(self.level_key)
        if options:
            self.gift_options = [ITEMS[i] for i in options]
            self.gift_cursor = 0
            self.set_state(State.REWARD)
        else:
            self.open_hangar(self.level_index + 1, self.score)

    def gift_move(self, step):
        if len(self.gift_options) > 1:
            self.gift_cursor = (self.gift_cursor + step) % len(self.gift_options)
            self.audio.play("select")

    def take_gift(self):
        item = self.gift_options[self.gift_cursor]
        self.inventory.claim(self.level_key, item.id)
        self.audio.play("power_up")
        self.flash = 0.1
        if item.kind == SHIP:
            self.choose_hull(hull_named(item.id))
        self.open_hangar(self.level_index + 1, self.score, focus=item.id,
                         message=(f"NEW: {item.name}", GOOD))
