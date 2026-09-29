"""Game feel: juice tiers (shake, hit-stop, embers, flash, slow-mo), boss damage numbers and
radio cards."""
from ..config.palette import FLAME
from ..config.tuning import (DAMAGE_NUMBER_EVERY, JUICE, REDUCED_FLASH, SLOWMO_SCALE,
                             SLOWMO_TIME)
from ..ui.popup import DamageNumber
from ..story.dialog import cards, is_hijack
from ..ui.radio import RadioCard
from .states import State


class JuiceMixin:
    """Game mixin. Events call juice(tier, x, y); update() asks world_dt() how much time the
    world gets this frame (0 during a hit-stop, slower during slow-mo)."""

    def _reset_juice(self):
        self.hitstop = 0.0
        self.slowmo = 0.0
        self.damage_sum = 0.0          # boss damage not shown yet
        self.damage_at = (0, 0)
        self.damage_timer = 0.0
        self.radio = None              # RadioCard on screen (or None)
        self.radio_queue = []          # the cards that follow it (a conversation)

    def juice(self, tier, x=None, y=None, colors=FLAME):
        """Feedback proportional to the event: 'small', 'medium' or 'large'."""
        shake, stop, embers, flash = JUICE[tier]
        self.shake.add(shake)
        self.hitstop = max(self.hitstop, stop)
        if embers and x is not None:
            self.fire.burst(x, y, embers, 40, 1.2, colors[1:], size=(1, 1), drag=1.2)
        if flash:
            self.screen_flash(flash)
        if tier == "large":
            self.slowmo = SLOWMO_TIME

    def screen_flash(self, seconds):
        """White flash (softer with the 'reduce flashes' option)."""
        scale = 1.0 if self.options["flashes"] else REDUCED_FLASH
        self.flash = max(self.flash, seconds * scale)

    def world_dt(self, dt):
        """Time the world advances this frame: hit-stop freezes it, slow-mo slows it."""
        if self.state not in (State.PLAYING, State.DYING):
            self.hitstop = self.slowmo = 0.0
            return dt
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            return 0.0
        if self.slowmo > 0:
            self.slowmo = max(0.0, self.slowmo - dt)
            return dt * SLOWMO_SCALE
        return dt

    # --- boss damage numbers -------------------------------------------------------------
    def tally_boss_damage(self, amount, x, y):
        self.damage_sum += amount
        self.damage_at = (x, y)

    def _update_damage_numbers(self, dt):
        self.damage_timer -= dt
        if self.damage_timer <= 0 and self.damage_sum >= 1:
            self.damage_timer = DAMAGE_NUMBER_EVERY
            self.popups.append(DamageNumber(self.damage_sum, *self.damage_at))
            self.damage_sum = 0.0

    # --- radio -----------------------------------------------------------------------------
    def radio_say(self, lines, delay=None):
        """Radio cards after the level / wave title (self.alert) has faded. lines: strings
        (Vega speaks) or story Lines; a change of speaker starts the next card."""
        if delay is None:
            delay = self.alert[3] if self.alert else 0.0
        self.radio_queue = [RadioCard(text, speaker) for speaker, text in cards(lines)]
        self.radio = None
        if self.radio_queue:
            self.radio = self.radio_queue.pop(0)
            self.radio.t = -delay

    def _update_radio(self, dt):
        if self.radio:
            was_visible = self.radio.visible
            self.radio.update(dt)
            if self.radio.visible and not was_visible and is_hijack(self.radio.speaker):
                self.audio.play("hijack")
            if self.radio.done:
                self.radio = self.radio_queue.pop(0) if self.radio_queue else None
                if self.radio and is_hijack(self.radio.speaker):
                    self.audio.play("hijack")

    def skip_radio(self):
        """ENTER: finish typing / close this card (the next one follows)."""
        self.radio.skip()
        if self.radio.done:
            self.radio = self.radio_queue.pop(0) if self.radio_queue else None
