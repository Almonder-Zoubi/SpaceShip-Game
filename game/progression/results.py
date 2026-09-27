"""What happened in one attempt at a level, and the rank (S/A/B/C) it earns."""
from ..config.tuning import (RANK_DAMAGE_ZERO, RANK_DESTROYED_FULL, RANK_THRESHOLDS,
                             RANK_WEIGHTS)

RANKS = tuple(rank for rank, _ in RANK_THRESHOLDS)     # best first: S, A, B, C


def better_rank(a, b):
    """The better of two ranks; None counts as no rank."""
    if a is None or b is None:
        return a or b
    return min(a, b, key=RANKS.index)


class LevelStats:
    """Counters the game fills while a level is played. Three ratings 0..1:
    damage (little damage taken), speed (bosses killed within their par time) and
    destroyed (share of rocks and minions shot down instead of let through)."""

    def __init__(self, max_hp=1):
        self.max_hp = max_hp
        self.damage_taken = 0.0
        self.destroyed = 0
        self.escaped = 0
        self.boss_time = 0.0         # seconds spent fighting bosses
        self.boss_par = 0.0          # sum of their BossSpec.fight_time

    def ratings(self):
        damage = 1 - min(1.0, self.damage_taken / self.max_hp / RANK_DAMAGE_ZERO)
        speed = min(1.0, self.boss_par / self.boss_time) if self.boss_time > 0 else 1.0
        seen = self.destroyed + self.escaped
        destroyed = min(1.0, self.destroyed / seen / RANK_DESTROYED_FULL) if seen else 1.0
        return {"damage": damage, "speed": speed, "destroyed": destroyed}

    def score(self):
        ratings = self.ratings()
        return sum(RANK_WEIGHTS[name] * value for name, value in ratings.items())

    def rank(self):
        score = self.score()
        for rank, threshold in RANK_THRESHOLDS:
            if score >= threshold - 1e-9:
                return rank
        return RANKS[-1]
