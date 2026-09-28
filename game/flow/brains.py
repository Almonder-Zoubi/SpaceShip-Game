"""The enemy's brains on the game side: the player model watches every frame of flight, the
DIRECTOR paces levels that ask for it, learning bosses get their saved bandits, and all of it
is written into the save file (it remembers the player across sessions)."""
import math
import random

from ..brains.bandit import Bandit
from ..brains.director import Director
from ..brains.insight import insights
from ..brains.model import PlayerModel
from ..config.display import LOW_H, LOW_W
from ..config.tuning import BRAIN_THREAT
from .states import Phase, State

MEMORY = 5.0                     # seconds: how far back "recent" damage / kills reach


class BrainsMixin:
    """Game mixin: observe, pace, remember."""

    def load_brain(self):
        data = self.save.brain or {}
        self.player_model = PlayerModel.from_dict(data.get("model", {}), LOW_W, LOW_H)
        self.bandits = {name: Bandit.from_dict(arms)
                        for name, arms in data.get("bandits", {}).items()}

    def save_brain(self):
        self.save.brain = {"model": self.player_model.to_dict(),
                           "bandits": {n: b.to_dict() for n, b in self.bandits.items()}}
        self.save.save()

    def reset_brain(self):
        """The journal's FORGET: they know nothing about you any more."""
        self.player_model = PlayerModel(LOW_W, LOW_H)
        self.bandits = {}
        self.save_brain()

    def bandit_for(self, boss_name):
        return self.bandits.setdefault(boss_name, Bandit())

    def begin_learning(self):
        """A level attempt starts: keep what was learned, weigh old habits a little less,
        and write it down (it survives a quit)."""
        self.player_model.forget()
        self.save_brain()

    def _reset_brains(self):
        self.director = Director()
        self.pressure = 1.0               # the DIRECTOR's spawn-rate multiplier
        self.recent_damage = 0.0          # share of max hull lost per second (smoothed)
        self.recent_kills = 0.0           # kills per second (smoothed)
        self.death_insight = None         # "IT LEARNED: ..." on the game over screen

    @property
    def director_active(self):
        return self.level.director or getattr(self, "force_director", False)

    def telegraph(self):
        """A boss shows an attack coming: the model times how fast the player reacts."""
        self.player_model.telegraph()

    def note_damage(self, amount):
        self.recent_damage += amount / max(1, self.ship.max_hp) / MEMORY

    def note_kill(self):
        self.recent_kills += 1 / MEMORY

    def _threatened(self):
        ship = self.ship
        for b in self.enemy_bullets:
            dx, dy = ship.x - b.x, ship.y - b.y
            if dx * dx + dy * dy < BRAIN_THREAT * BRAIN_THREAT and dx * b.vx + dy * b.vy > 0:
                return True
        return any(math.hypot(ship.x - e.x, ship.y - e.y) < BRAIN_THREAT for e in self.enemies)

    def _update_brains(self, dt, firing):
        decay = math.exp(-dt / MEMORY)
        self.recent_damage *= decay
        self.recent_kills *= decay
        if self.state != State.PLAYING or not self.ship.alive:
            self.pressure = 1.0
            return
        ship = self.ship
        self.player_model.observe(dt, ship.x, ship.y, ship.vx, ship.vy, self._threatened(),
                                  self.weapon.name if firing else None)
        if self.director_active and self.phase == Phase.FIELD:
            self.pressure = self.director.update(dt, ship.hp / ship.max_hp, self.recent_damage,
                                                 self.recent_kills)
        else:
            self.pressure = 1.0

    def learn_from_death(self):
        """GAME OVER in a level with thinking enemies: they say what they noticed."""
        if self.director_active or getattr(self.boss, "learns", False):
            self.death_insight = random.choice(insights(self.player_model)[:2])
        self.save_brain()
