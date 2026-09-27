"""Coins: what drops them and what a cleared level pays into the bank."""
import random
from dataclasses import dataclass

from ..config.tuning import (COIN_BOSS_BASE, COIN_BOSS_PER_LEVEL, COIN_CLEAR_BASE,
                             COIN_FIRST_CLEAR, COIN_MINION, COIN_REPLAY, COIN_ROCK_CHANCE,
                             RANK_BONUS)


def rock_coins(radius, rng=random):
    """0 or 1 coin for a destroyed rock; big rocks drop one more often."""
    for min_radius, chance in COIN_ROCK_CHANCE:
        if radius >= min_radius:
            return 1 if rng.random() < chance else 0
    return 0


def minion_coins(rng=random):
    return rng.randint(*COIN_MINION)


def boss_coins(level_number, strength):
    """Coins a boss drops when it dies; a weakened rematch (strength < 2) drops half."""
    coins = COIN_BOSS_BASE + COIN_BOSS_PER_LEVEL * level_number
    return coins if strength >= 2 else coins // 2


@dataclass(frozen=True)
class Payout:
    """Coins banked when a level is cleared: the pending coins picked up in the level,
    the clear bonus (base x level x rank) and the first-clear bonus. A replay pays less."""
    pending: int
    clear_bonus: int
    first_clear: int
    replay: bool

    @property
    def total(self):
        coins = self.pending + self.clear_bonus + self.first_clear
        return int(round(coins * COIN_REPLAY)) if self.replay else coins


def level_payout(pending, level_number, rank, first_clear):
    clear = int(round(COIN_CLEAR_BASE * level_number * RANK_BONUS[rank]))
    return Payout(int(pending), clear, COIN_FIRST_CLEAR if first_clear else 0,
                  replay=not first_clear)
