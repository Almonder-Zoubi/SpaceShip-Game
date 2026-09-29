"""Learner: a mixin for bosses that learn (galaxy 2 on). It picks attacks with a saved
bandit (the ones that hurt *you*), aims where you will be, and counters your habits."""
import math
import random

from ..config.tuning import LEAD_AIM


class Learner:
    """Use with a Boss subclass: class Nyx(Learner, Boss). Call begin_attack() whenever a
    pattern slot starts and learn_tick(dt) every fight frame; the game calls credit() with
    every point of damage the boss deals (flow/world.py)."""

    learns = True

    def _learner(self):
        if not hasattr(self, "_attack"):
            self._attack, self._dealt, self._elapsed, self._bandit = None, 0.0, 0.0, None

    def begin_attack(self, world, options):
        """Close the last attack (reward = its damage per second) and choose the next."""
        self._learner()
        self._bandit = world.bandit_for(self.spec.name)     # (fresh: the brain may reload)
        if self._attack and self._elapsed > 0.2:
            self._bandit.reward(self._attack, self._dealt / self._elapsed)
        self._attack = self._bandit.choose(options, random)
        self._dealt = self._elapsed = 0.0
        return self._attack

    def learn_tick(self, dt):
        self._learner()
        self._elapsed += dt

    def credit(self, damage):
        self._learner()
        self._dealt += damage

    @staticmethod
    def lead_aim(world, x, y, speed):
        """Angle to where the rocket will be when the bullet gets there (not where it is)."""
        ship = world.aim_target()                          # (a DECOY fools it)
        t = math.hypot(ship.x - x, ship.y - y) / max(1.0, speed)
        tx = ship.x + ship.vx * t * LEAD_AIM
        ty = ship.y + ship.vy * t * LEAD_AIM
        return math.atan2(ty - y, tx - x)

    @staticmethod
    def counters(world):
        """Habits worth punishing: 'floor' (hides at the bottom), 'left' / 'right' (keeps to
        a side), 'mirror' (laser-heavy)."""
        model = world.player_model
        out = set()
        if model.seconds < 10:
            return out
        if model.zone_share(rows=range(model.rows - 2, model.rows)) >= 0.55:
            out.add("floor")
        left = model.zone_share(cols=range(0, model.cols // 2))
        if left >= 0.65:
            out.add("left")
        elif left <= 0.35:
            out.add("right")
        if model.weapon_share("LASER") >= 0.6:
            out.add("mirror")
        return out
