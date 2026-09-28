"""Bandit: pick the attack that has hurt this player most, but keep trying the others."""
import math

from ..config.tuning import BRAIN_EXPLORE, BRAIN_MIN_STEP, BRAIN_UCB


class Bandit:
    """UCB1 with a fixed exploring share. Each arm = an attack pattern; its value = the
    average damage per second it dealt. Recent fights weigh more (a floor on the step size),
    so a player who learns a counter makes the boss switch."""

    def __init__(self, arms=None):
        self.arms = {}                    # name -> [plays, mean reward]
        for name in arms or ():
            self.arms[name] = [0, 0.0]

    def choose(self, options, rng):
        options = list(options)
        for name in options:
            self.arms.setdefault(name, [0, 0.0])
        untried = [n for n in options if self.arms[n][0] == 0]
        if untried:
            return untried[0]
        if rng.random() < BRAIN_EXPLORE:
            return rng.choice(options)
        total = sum(self.arms[n][0] for n in options)
        top = max(self.arms[n][1] for n in options) or 1.0
        def score(n):
            plays, mean = self.arms[n]
            return mean / top + BRAIN_UCB * math.sqrt(math.log(total) / plays)
        return max(options, key=score)

    def reward(self, name, value):
        plays, mean = self.arms.setdefault(name, [0, 0.0])
        plays += 1
        step = max(1.0 / plays, BRAIN_MIN_STEP)
        self.arms[name] = [plays, mean + (value - mean) * step]

    def best(self):
        played = [(m, n) for n, (p, m) in self.arms.items() if p]
        return max(played)[1] if played else None

    def to_dict(self):
        return {n: [p, round(m, 3)] for n, (p, m) in self.arms.items()}

    @classmethod
    def from_dict(cls, data):
        bandit = cls()
        bandit.arms = {str(n): [int(p), float(m)] for n, (p, m) in data.items()}
        return bandit
