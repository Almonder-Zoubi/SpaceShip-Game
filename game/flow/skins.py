"""Skins (paint, engine trail, tracers, beam, death style) and the achievements that unlock
some of them."""
import random

from ..config.palette import BEAMS, GOOD, RAINBOW, TRACERS, TRAILS, WHITE
from ..core.particles import Shockwave
from ..progression.achievements import BY_ID, MINIONS_GOAL
from ..progression.items import (BEAM, DEATH, DEFAULT_SKINS, ITEMS, PAINT, TRACER, TRAIL)
from ..ui.popup import Popup
from .states import Phase, State


class SkinsMixin:
    """Game mixin: what the player wears, and achievement checks."""

    def skin(self, slot):
        """The equipped skin item of a slot (owned), or the slot's default."""
        item_id = self.save.skins.get(slot)
        if item_id in ITEMS and self.inventory.owns(item_id):
            return ITEMS[item_id]
        return ITEMS[DEFAULT_SKINS[slot]]

    def paint_for(self, loadout):
        """The level's MK paint, or the chosen paint job."""
        look = self.skin(PAINT).look
        return look or loadout.colors

    def wear(self, item_id):
        """Equip a skin in its slot (saved)."""
        self.save.skins[ITEMS[item_id].slot] = item_id
        self.save.save()
        self.apply_skins()

    def apply_skins(self):
        """Trail, tracer and beam colours (the paint is part of loadout_for())."""
        self.ship.trail = TRAILS[self.skin(TRAIL).look]
        weapons = {w.name: w for w in self.weapons}
        weapons["GUN"].colors = TRACERS[self.skin(TRACER).look]
        weapons["LASER"].colors = BEAMS[self.skin(BEAM).look]

    # --- death styles ------------------------------------------------------------------------
    def death_style(self, x, y):
        """Extra effect for the chosen death skin (CLASSIC adds nothing)."""
        look = self.skin(DEATH).look
        if look == "SHATTER":                     # the hull breaks into its own pixels
            image = self.ship.image
            w, h = image.get_size()
            for px in range(0, w, 2):
                for py in range(0, h, 2):
                    color = image.get_at((px, py))
                    if color.a:
                        dx, dy = px - w / 2, py - h / 2
                        self.smoke.emit(x + dx, y + dy, dx * 9 + random.uniform(-20, 20),
                                        dy * 9 + random.uniform(-20, 20), random.uniform(0.8, 1.6),
                                        [tuple(color)[:3]] * 2, size=2, drag=1.0)
        elif look == "SUPERNOVA":
            for i, radius in enumerate((70, 110, 150)):
                self.shockwaves.append(Shockwave(x, y, max_radius=radius, duration=0.5 + i * 0.25,
                                                 color=(WHITE, (255, 230, 150), (150, 200, 255))[i]))
            self.fire.burst(x, y, 60, 260, 0.9, RAINBOW, size=(1, 2), drag=1.0)
            self.screen_flash(0.2)

    # --- achievements ------------------------------------------------------------------------
    def achieve(self, achievement_id):
        """Earn an achievement (once): its skin unlocks, a popup says so."""
        if achievement_id in self.save.achievements:
            return
        a = BY_ID[achievement_id]
        self.save.achievements.append(achievement_id)
        self.inventory.unlock(a.reward)
        self.save.save()
        self.popups.append(Popup(f"ACHIEVEMENT: {a.name}", self.ship.x, self.ship.y - 34, GOOD))
        self.popups.append(Popup(f"NEW SKIN: {ITEMS[a.reward].name}", self.ship.x,
                                 self.ship.y - 24, GOOD))
        self.audio.play("achievement")

    def _reset_achievements(self):
        self.boss_hurt = False            # damage taken since this boss appeared
        self.fired_in_field = False       # fire pressed during this wave's field

    def track_fire(self, firing):
        if firing and self.state == State.PLAYING and self.phase == Phase.FIELD:
            self.fired_in_field = True

    def track_field_done(self):
        """The field of a wave is over: PACIFIST if the player never fired in it."""
        if not self.fired_in_field and not self.dev:
            self.achieve("PACIFIST")
        self.fired_in_field = False

    def track_minion(self):
        self.save.minion_kills += 1       # saved with the next save (level end, purchases)
        if self.save.minion_kills >= MINIONS_GOAL and not self.dev:
            self.achieve("MINIONS")
