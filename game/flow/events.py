"""Input events: what each key does in each state (one handler method per state), mouse."""
import pygame

from ..config.palette import ACCENT
from ..core.input import DOWN_KEYS, LEFT_KEYS, MOVE_KEYS, RIGHT_KEYS, START_KEYS, UP_KEYS
from ..player.hulls import HULLS
from .states import State


class EventsMixin:
    """Game mixin: turns the pygame event queue into actions (and fills self.held).

    Each state has a `_keys_<state>(key)` handler; a handler returns False to quit the game.
    The mouse steers while playing (see core.input.Mouse); a left click in a menu counts
    as ENTER.
    """

    def handle_events(self):
        """Process the event queue. Returns False when the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP:
                self.held.pressed.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.held.pressed.clear()     # avoid keys "stuck" after alt-tab
                self.mouse.firing = False
            elif event.type == pygame.MOUSEMOTION:
                self.mouse.move(event.pos, event.rel)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse.firing = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse.click(event.pos)
                if self.state not in (State.PLAYING, State.PAUSED):
                    if self._handler()(pygame.K_RETURN) is False:
                        return False
            if event.type != pygame.KEYDOWN:
                continue
            self.held.pressed.add(event.key)
            if event.key in MOVE_KEYS + (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.mouse.release()          # keyboard takes over
            if event.key == pygame.K_c:
                self.show_scanlines = not self.show_scanlines
                continue
            if self._handler()(event.key) is False:
                return False
        self._update_cursor()
        return True

    def _handler(self):
        return getattr(self, "_keys_" + self.state.name.lower())

    def _update_cursor(self):
        """Hide the system pointer while flying (the game draws its own reticle)."""
        shown = self.state != State.PLAYING
        if shown != self._cursor_shown:
            self._cursor_shown = shown
            pygame.mouse.set_visible(shown)

    # --- one handler per state ---------------------------------------------------------
    def _keys_title(self, key):
        if key in LEFT_KEYS + RIGHT_KEYS and self.selectable_levels > 1:
            step = 1 if key in RIGHT_KEYS else -1
            self.start_level = (self.start_level + step) % self.selectable_levels
            self.audio.play("select")
        elif key == pygame.K_j:
            self.open_journal()
        elif key in START_KEYS or key in MOVE_KEYS:
            self.open_star_map()
        elif key == pygame.K_ESCAPE:
            return False

    def _keys_journal(self, key):
        if key in LEFT_KEYS + RIGHT_KEYS:
            self.journal_switch(1 if key in RIGHT_KEYS else -1)
        elif key in UP_KEYS + DOWN_KEYS:
            self.journal_move(1 if key in DOWN_KEYS else -1)
        elif key in START_KEYS:
            self.journal_switch(1)
        elif key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.journal_forget_key()
        elif key in (pygame.K_ESCAPE, pygame.K_j):
            self.close_journal()

    def _keys_star_map(self, key):
        if key == pygame.K_j and not self.star_map.card:
            self.open_journal()
        elif key in START_KEYS:
            self.star_map_enter()
        elif key == pygame.K_ESCAPE:
            if self.star_map.card:
                self.star_map.card = None
            else:
                self.to_title()

    def _keys_hangar(self, key):
        if key in LEFT_KEYS + RIGHT_KEYS:
            self.hangar_switch_tab(1 if key in RIGHT_KEYS else -1)
        elif key in UP_KEYS + DOWN_KEYS:
            self.hangar_move(1 if key in DOWN_KEYS else -1)
        elif key == pygame.K_SPACE:
            self.hangar_launch()
        elif key in START_KEYS:
            self.hangar_select()
        elif key == pygame.K_ESCAPE:
            self.open_star_map(self.next_launch[0])

    def _keys_reward(self, key):
        if key in LEFT_KEYS + RIGHT_KEYS:
            self.gift_move(1 if key in RIGHT_KEYS else -1)
        elif key in START_KEYS and self.state_time > 0.5:
            self.take_gift()

    def _keys_dev_menu(self, key):
        items = self.dev_items()
        if key in UP_KEYS + DOWN_KEYS:
            step = 1 if key in DOWN_KEYS else -1
            self.dev_cursor = (self.dev_cursor + step) % len(items)
        elif key in LEFT_KEYS + RIGHT_KEYS:
            step = 1 if key in RIGHT_KEYS else -1
            self.choose_hull(HULLS[(HULLS.index(self.hull) + step) % len(HULLS)])
        elif key == pygame.K_g:
            self.god = not self.god
        elif key in START_KEYS:
            _, level_index, wave_index, boss_index = items[self.dev_cursor]
            self.start(level_index, 0, wave_index, boss_index)
        elif key == pygame.K_ESCAPE:
            return False

    def _keys_playing(self, key):
        if self.dev and self.dev_key(key):
            return
        if key == pygame.K_p:
            self.set_state(State.PAUSED)
        elif key == pygame.K_ESCAPE:
            self.to_title()
        elif key == pygame.K_r:
            self.switch_weapon()
        elif key == pygame.K_t:
            self.fire_ultimate()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.radio:
            self.skip_radio()

    def _keys_paused(self, key):
        """Paused: the options menu (UP/DOWN pick, LEFT/RIGHT change)."""
        if key == pygame.K_p:
            self.state = State.PLAYING
        elif key in UP_KEYS + DOWN_KEYS:
            self.options_move(1 if key in DOWN_KEYS else -1)
        elif key in LEFT_KEYS + RIGHT_KEYS:
            self.options_change(1 if key in RIGHT_KEYS else -1)
        elif key == pygame.K_ESCAPE:
            self.to_title()

    def _keys_dying(self, key):
        pass

    def _keys_game_over(self, key):
        if key == pygame.K_r or key in START_KEYS:
            self.start(*self.retry_point)                   # retry from where we started
        elif key == pygame.K_ESCAPE:
            self.to_title()

    def _keys_level_clear(self, key):
        if key in START_KEYS and self.state_time > 1.0:
            self.after_level_clear()
        elif key == pygame.K_ESCAPE:
            self.to_title()

    def _keys_warp(self, key):
        if key in START_KEYS and self.radio:
            self.skip_radio()
        elif key in START_KEYS and self.state_time > 1.0:
            self.finish_warp()

    def _keys_win(self, key):
        if key in START_KEYS and self.state_time > 1.0:
            self.after_win()
        elif key == pygame.K_r:
            self.start()
        elif key == pygame.K_ESCAPE:
            self.to_title()

    # --- actions -----------------------------------------------------------------------
    def switch_weapon(self):
        """R: the other equipped primary (nothing happens with only one)."""
        names = [w.name for w in self.weapons]
        slots = [names.index(name) for name in self.primaries]
        if len(slots) < 2:
            return
        self.weapon_index = slots[(slots.index(self.weapon_index) + 1) % len(slots)
                                  if self.weapon_index in slots else 0]
        self.audio.play("switch")

    def fire_ultimate(self):
        if self.ship.loadout.ultimate and self.ship.alive and self.ultimate.activate():
            self.alert = ["ULTIMATE!", "MISSILE STORM", ACCENT, 1.4]
            self.screen_flash(0.1)
            self.shake.add(0.5)
            self.audio.play("ultimate")
