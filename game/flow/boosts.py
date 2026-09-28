"""Boosts (OVERDRIVE, SHIELD, MAGNET, SLOW-MO) and the kill COMBO with FEVER."""
import math
import random

from ..config.display import LOW_W
from ..config.palette import BOOST_COLORS, RAINBOW
from ..config.tuning import (BOOST_INTERVAL, BOOST_MINION_CHANCE, BOSS_BOOST_INTERVAL,
                             COMBO_COIN_CAP, COMBO_MAX, COMBO_STEP, COMBO_WINDOW, FEVER_AT,
                             FEVER_TIME, MAGNET_TIME, OVERDRIVE_RATE, OVERDRIVE_TIME,
                             SHIELD_GRACE, SHIELD_HITS, SLINGSHOT_SCORE, SLOWDOWN_SCALE,
                             SLOWDOWN_TIME, TWIN_TIME)
from ..core.particles import Shockwave
from ..pickups.boosts import BOOSTS
from ..ui.popup import Popup
from .states import Phase, State

TIMED = {"OVERDRIVE": OVERDRIVE_TIME, "MAGNET": MAGNET_TIME, "SLOW-MO": SLOWDOWN_TIME,
         "TWIN": TWIN_TIME}


class BoostsMixin:
    """Game mixin: boost timers + drops, the shield, and the combo counter (the TWIN boost's
    ship lives with the wingmen, flow/wingmen.py).

    Kills within COMBO_WINDOW of each other build a combo; every COMBO_STEP kills raise the
    score multiplier (coins too, capped at COMBO_COIN_CAP). A combo of FEVER_AT starts FEVER.
    Getting hit ends the combo (a shield hit doesn't)."""

    def _reset_boosts(self):
        self.boosts = {}               # timed boost name -> seconds left
        self.shield = 0                # hits the bubble can still absorb
        self.boost_timer = random.uniform(*BOOST_INTERVAL)
        self.combo = 0
        self.combo_time = 0.0          # seconds left to extend the combo
        self.best_combo = 0
        self.fever = 0.0               # seconds of FEVER left

    # --- boosts ----------------------------------------------------------------------------
    def boost_pool(self):
        """Boosts that may drop: OVERDRIVE only once owned (a level gift)."""
        return [name for name in BOOSTS if name != "OVERDRIVE" or self.inventory.owns(name)]

    def drop_boost(self, x, y, name=None):
        name = name or random.choice(self.boost_pool())
        self.pickups.append(BOOSTS[name](x, y))

    def start_boost(self, name):
        """A boost pickup was collected. Returns the popup text."""
        if name == "SHIELD":
            self.shield = SHIELD_HITS
            return "SHIELD!"
        self.boosts[name] = TIMED[name]
        if name == "TWIN":
            self.start_twin()
        return f"{name}!"

    def boost_left(self, name):
        return self.boosts.get(name, 0.0)

    @property
    def overdrive(self):
        return self.boost_left("OVERDRIVE") > 0 or self.fever > 0

    @property
    def fire_rate(self):
        return OVERDRIVE_RATE if self.overdrive else 1.0

    def enemy_dt(self, dt):
        """Time for rocks, enemies, bosses and their bullets (SLOW-MO halves it)."""
        return dt * SLOWDOWN_SCALE if self.boost_left("SLOW-MO") > 0 else dt

    def absorb_hit(self, x, y):
        """The shield takes a hit instead of the hull. Returns True if it did."""
        if self.shield <= 0:
            return False
        self.shield -= 1
        ship = self.ship
        ship.invulnerable_time = max(ship.invulnerable_time, SHIELD_GRACE)
        color = BOOST_COLORS["SHIELD"][2]
        self.shockwaves.append(Shockwave(ship.x, ship.y, max_radius=22, duration=0.3, color=color))
        self.fire.burst(x, y, 10, 70, 0.3, BOOST_COLORS["SHIELD"], size=(1, 1))
        self.shake.add(0.15)
        self.audio.play("shield")
        if self.shield == 0:
            self.popups.append(Popup("SHIELD DOWN", ship.x, ship.y - 24, color))
        return True

    def _update_boosts(self, dt):
        for name in list(self.boosts):
            self.boosts[name] -= dt
            if self.boosts[name] <= 0:
                del self.boosts[name]
        if self.boost_left("MAGNET") > 0:
            for pickup in self.pickups:
                pickup.magnet = 400
        self.ship.overdrive = self.overdrive
        self.ship.fever = self.fever > 0
        if self.state != State.PLAYING:
            return
        self.combo_time -= dt
        if self.combo_time <= 0 and self.combo:
            self.combo = 0
        if self.fever > 0:
            self.fever = max(0.0, self.fever - dt)
            self._fever_trail()
        if self.phase in (Phase.FIELD, Phase.BOSS):
            self.boost_timer -= dt
            if self.boost_timer <= 0:
                self.boost_timer = (BOSS_BOOST_INTERVAL if self.phase == Phase.BOSS
                                    else random.uniform(*BOOST_INTERVAL))
                self.drop_boost(random.uniform(30, LOW_W - 30), -8)

    def _fever_trail(self):
        ship = self.ship
        for i in range(2):
            color = RAINBOW[int(self.time * 20 + i * 3) % len(RAINBOW)]
            self.fire.emit(ship.x + random.uniform(-3, 3), ship.y + ship.h / 2,
                           random.uniform(-10, 10), random.uniform(60, 90), 0.4,
                           [color, color, tuple(c // 2 for c in color)], size=2, drag=1.5)

    def _minion_boost(self, enemy):
        if random.random() < BOOST_MINION_CHANCE:
            self.drop_boost(enemy.x, enemy.y)

    # --- combo -----------------------------------------------------------------------------
    @property
    def combo_mult(self):
        return min(COMBO_MAX, 1 + self.combo // COMBO_STEP)

    def add_kill(self, points, x, y):
        """A rock or minion destroyed: extend the combo; returns the points to add."""
        if self.state != State.PLAYING:
            return points
        if self.slingshot:
            points *= SLINGSHOT_SCORE
        before = self.combo_mult
        self.note_kill()
        self.combo += 1
        self.combo_time = COMBO_WINDOW
        self.best_combo = max(self.best_combo, self.combo)
        if self.combo_mult > before:
            self.popups.append(Popup(f"COMBO X{self.combo_mult}", x, y - 10,
                                     RAINBOW[self.combo_mult % len(RAINBOW)]))
            self.audio.play("combo")
        if self.combo == FEVER_AT and self.fever <= 0:
            self.fever = FEVER_TIME
            self.alert = ["FEVER!", "FIRE RATE X2", RAINBOW[2], 1.6]
            self.achieve("FEVER")
            self.audio.play("fever")
            self.screen_flash(0.08)
        return points * self.combo_mult

    @property
    def coin_mult(self):
        return (min(COMBO_COIN_CAP, self.combo_mult) * (SLINGSHOT_SCORE if self.slingshot else 1)
                * self.shift_coins)

    @property
    def slingshot(self):
        """The ship flies in the black hole's SLINGSHOT ring (level 9)."""
        return bool(self.hazard and getattr(self.hazard, "ship_in_ring", False))

    def break_combo(self):
        self.combo = 0
        self.combo_time = 0.0

    @staticmethod
    def combo_ratio(time_left):
        return max(0.0, min(1.0, time_left / COMBO_WINDOW))

    def fever_hue(self, offset=0):
        return RAINBOW[int(self.time * 12 + offset) % len(RAINBOW)]

    @staticmethod
    def shield_wobble(time):
        return 1 if math.sin(time * 9) > 0.6 else 0
