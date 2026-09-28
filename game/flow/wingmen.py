"""Wingmen in the game: the equipped one (+ the TWIN boost copy), their hits, knock-outs, XP."""
import random

from ..config.palette import GOOD
from ..config.tuning import (MAGPIE_BONUS, MEDIC_REVIVE, WINGMAN_TRAIN_COST, WINGMAN_TRAIN_XP,
                             WINGMAN_XP, WINGMAN_XP_BOSS, WINGMAN_XP_KILL, WINGMAN_XP_OWN)
from ..core.particles import Shockwave
from ..ui.popup import Popup
from ..wingmen.base import level_for
from ..wingmen.types import WINGMEN, Magpie, Medic, Twin
from .states import State


class WingmenMixin:
    """Game mixin. XP earned in a level is banked when the level ends (won or lost)."""

    def _reset_wingmen(self):
        self.wingmen = []
        name = self.save.wingman
        if name in WINGMEN and self.inventory.owns(name):
            self.wingmen.append(WINGMEN[name](self.wingman_level(name)))
        second = self.save.wingman2                   # the WING BAY's wingman, on the right
        if (second in WINGMEN and second != name and self.inventory.owns(second)
                and self.inventory.owns("WING BAY")):
            self.wingmen.append(WINGMEN[second](self.wingman_level(second), side=1))
        self.wingman_xp_gain = 0
        self.wingman2_xp_gain = 0
        self.last_hurt = -99.0                  # game time of the last hull damage (MEDIC)

    @property
    def wingman(self):
        """The equipped wingman in flight (None without one)."""
        return next((w for w in self.wingmen if not w.temporary), None)

    @property
    def wingman2(self):
        """The second wingman (WING BAY) in flight, or None."""
        own = [w for w in self.wingmen if not w.temporary]
        return own[1] if len(own) > 1 else None

    def _flying(self, cls):
        """The first own wingman of this class that flies (MEDIC, MAGPIE perks)."""
        return next((w for w in self.wingmen if isinstance(w, cls) and not w.temporary), None)

    def wingman_xp(self, name):
        return self.save.wingmen_xp.get(name, 0)

    def wingman_level(self, name):
        return level_for(self.wingman_xp(name))

    def weapon_targets(self):
        """Everything the player's side can hit."""
        targets = self.asteroids + self.enemies
        if self.boss and self.boss.targetable:
            targets += self.boss.parts()
        return targets

    # --- per frame -------------------------------------------------------------------------
    def _update_wingmen(self, dt, firing):
        """Move every wingman; returns their Hits (applied like the player's)."""
        if self.boost_left("TWIN") <= 0:
            self.wingmen = [w for w in self.wingmen if not isinstance(w, Twin)]
        hits = []
        for w in self.wingmen:
            hits += w.update(dt, self, firing and self.state == State.PLAYING)
        if self.state == State.PLAYING:
            for rock in self.asteroids:                 # rocks knock wingmen out (not TWIN)
                for w in self.wingmen:
                    if (w.flying and not w.temporary and abs(rock.x - w.x) < rock.bound
                            and abs(rock.y - w.y) < rock.bound and rock.contains(w.x, w.y)):
                        w.knock_out(self)
        return hits

    def wingman_block(self, bullet):
        """An enemy bullet touching a wingman: it blocks (GUARDIAN) or is knocked out."""
        for w in self.wingmen:
            if not w.temporary and w.touches(bullet.x, bullet.y) and w.block(bullet, self):
                return True
        return False

    def start_twin(self):
        self.wingmen = [w for w in self.wingmen if not isinstance(w, Twin)]
        self.wingmen.append(Twin(self.ship.frames[0], side=-(self.wingman.side if self.wingman
                                                              else -1)))

    # --- XP ----------------------------------------------------------------------------------
    def wingman_kill(self, source=None, boss=False):
        """A kill while the wingman flies (+ extra when it made the kill itself)."""
        if self.state != State.PLAYING or self.dev:
            return
        for attr, w in (("wingman_xp_gain", self.wingman), ("wingman2_xp_gain", self.wingman2)):
            if not w or not w.flying:
                continue
            gain = WINGMAN_XP_BOSS if boss else WINGMAN_XP_KILL
            if source is w:
                gain += WINGMAN_XP_OWN
            before = level_for(self.wingman_xp(w.name) + getattr(self, attr))
            setattr(self, attr, getattr(self, attr) + gain)
            after = level_for(self.wingman_xp(w.name) + getattr(self, attr))
            if after > before:
                w.level = after
                self.popups.append(Popup(f"{w.name} LEVEL {after}!", w.x, w.y - 12, GOOD))
                self.audio.play("power_up")

    def _bank_wingman_xp(self):
        for attr, w in (("wingman_xp_gain", self.wingman), ("wingman2_xp_gain", self.wingman2)):
            if w and getattr(self, attr):
                self.save.wingmen_xp[w.name] = self.wingman_xp(w.name) + getattr(self, attr)
                self.save.save()
            setattr(self, attr, 0)

    def train_wingman(self, name):
        """Hangar: buy WINGMAN_TRAIN_XP for coins (not past level 5)."""
        if self.wingman_level(name) >= len(WINGMAN_XP) or self.save.coins < WINGMAN_TRAIN_COST:
            return False
        self.save.coins -= WINGMAN_TRAIN_COST
        self.save.wingmen_xp[name] = self.wingman_xp(name) + WINGMAN_TRAIN_XP
        self.save.save()
        return True

    # --- hooks for MEDIC / MAGPIE ------------------------------------------------------------
    def try_revive(self):
        """MEDIC level 5: the killing blow leaves the ship at MEDIC_REVIVE of its hull."""
        w = self._flying(Medic)
        if not w or not w.can_revive():
            return False
        w.revived = True
        ship = self.ship
        ship.hp = max(1, int(ship.max_hp * MEDIC_REVIVE))
        ship.invulnerable_time = 2.0
        self.shockwaves.append(Shockwave(ship.x, ship.y, max_radius=40, duration=0.5,
                                         color=GOOD))
        self.popups.append(Popup("REVIVED BY MEDIC!", ship.x, ship.y - 24, GOOD))
        self.audio.play("power_up")
        return True

    def coin_bonus(self, value):
        """MAGPIE level 5: sometimes a coin counts twice."""
        w = self._flying(Magpie)
        if w and w.level >= 5 and w.flying:
            if random.random() < MAGPIE_BONUS:
                return value * 2
        return value

    def draw_wingmen(self, surf):
        for w in self.wingmen:
            w.draw_shots(surf)
        for w in self.wingmen:
            w.draw(surf)

