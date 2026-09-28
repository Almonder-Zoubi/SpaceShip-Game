"""Progression: coins picked up in a level, level stats, rank and the payout when it is won."""
import math
import random

from ..config.palette import GOOD
from ..config.tuning import (BOSS_ROAR_TIME, COIN_BIG, ELITE_COINS, COIN_BOSS_PHASE, COIN_TALLY_RATE,
                             WRECK_COINS)
from ..levels.data import galaxy_of
from ..pickups.types import BigCoin, Coin
from ..progression.economy import boss_coins, level_payout, minion_coins, rock_coins
from ..progression.results import LevelStats
from ..ui.popup import Popup
from .states import State


class ProgressionMixin:
    """Game mixin: pending coins (lost on death / retry / quit), LevelStats, and on a won
    level the rank + payout into the bank (save file)."""

    RANK_TIME = 1.2               # results screen: the rank stamp lands
    TALLY_DELAY = 1.6             # results screen: seconds before the coins count into the bank

    def _reset_progress(self):
        """Called by new_run(): a fresh attempt starts with no pending coins."""
        self.pending_coins = 0
        self.coin_flash = 0.0                    # HUD counter flashes after a pickup
        self.stats = LevelStats(self.ship.max_hp)
        self.payout = None                       # Payout of the level just won
        self.level_rank = None
        self.bank_before = self.save.coins

    @property
    def galaxy(self):
        return galaxy_of(self.level)

    @property
    def level_key(self):
        return self.galaxy.key(self.level)

    def collect_coins(self, value):
        self.pending_coins += self.coin_bonus(value)
        self.coin_flash = 0.25

    def drop_coins(self, x, y, count, big=False, homing=False):
        """Scatter coins from an explosion."""
        cls = BigCoin if big else Coin
        for _ in range(count):
            a = random.uniform(0, math.tau)
            speed = random.uniform(20, 70)
            self.pickups.append(cls(x, y, math.cos(a) * speed, math.sin(a) * speed - 20,
                                    homing=homing))

    def _drop_rock_coins(self, rock):
        coins = random.randint(*WRECK_COINS) if rock.METAL else rock_coins(rock.radius)
        self.drop_coins(rock.x, rock.y, coins * self.coin_mult)

    def _drop_minion_coins(self, enemy):
        if enemy.drops_coins:
            coins = minion_coins() * self.coin_mult * (ELITE_COINS if enemy.elite else 1)
            self.drop_coins(enemy.x, enemy.y, coins)

    def _drop_boss_coins(self, boss, phase_change=False):
        """Big coins that home in on the ship: a boss's reward can't be missed."""
        coins = COIN_BOSS_PHASE if phase_change else boss_coins(self.level_index + 1,
                                                                 boss.spec.strength)
        self.drop_coins(boss.x, boss.y, max(1, coins // COIN_BIG), big=True, homing=True)

    def _record_boss_time(self, boss):
        """Fight time without the entry and the roars, against the spec's par time."""
        roars = (boss.PHASES - 1) * BOSS_ROAR_TIME
        self.stats.boss_time += max(1.0, self.phase_time - boss.ENTER_TIME - roars)
        self.stats.boss_par += boss.spec.fight_time

    def _bank_level(self):
        """The level is won: coins still on screen are collected, the rank is decided and
        pending coins + clear bonus go into the bank."""
        self.save_brain()
        for pickup in self.pickups:
            if isinstance(pickup, Coin):
                self.pending_coins += pickup.value
        self.pickups = [p for p in self.pickups if not isinstance(p, Coin)]
        self._bank_wingman_xp()
        self.level_rank = self.stats.rank()
        if self.level_rank == "S":
            self.achieve("RANK_S")
        first = not self.save.is_cleared(self.level_key)
        self._hazard_bonus()
        self.pending_coins = self.shift_payout(self.pending_coins)      # a VEIL SHIFT pays more
        self.payout = level_payout(self.pending_coins, self.level_index + 1, self.level_rank, first)
        self.bank_before = self.save.coins
        self.save.clear_level(self.level_key, self.level_rank, self.payout.total)

    def _hazard_bonus(self):
        """A level mechanic that pays when the level is won (a saved brood, a flagship that
        held): hazard.bonus() -> (coins, story beat, popup text, x, y) or None."""
        bonus = getattr(self.hazard, "bonus", None)
        result = bonus() if bonus else None
        if not result:
            return
        coins, beat, text, x, y = result
        self.pending_coins += coins
        if not self.dev:
            self.save.remember("story", beat)
        self.popups.append(Popup(f"{text} +{coins}", x, y, GOOD))

    def tally(self):
        """Coins counted into the bank so far on the results screen (animation)."""
        if not self.payout:
            return 0
        t = max(0.0, self.state_time - self.TALLY_DELAY)
        return min(self.payout.total, int(t * COIN_TALLY_RATE))

    def _update_progress(self, dt):
        self.coin_flash = max(0.0, self.coin_flash - dt)
        if self.state not in (State.LEVEL_CLEAR, State.WIN) or not self.payout:
            return
        before = self.state_time - dt
        if before < self.RANK_TIME <= self.state_time:
            self.audio.play("rank")
            self.shake.add(0.35)
        if 0 < self.tally() < self.payout.total:
            self.audio.play("coin")                  # rate-limited: a ticking counter
