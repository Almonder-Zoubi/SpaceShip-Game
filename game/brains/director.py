"""Director: paces a level like a game master. It watches how well the player is doing and
turns up the pressure (faster spawns) in waves: BUILD -> PEAK -> BREATHER -> BUILD ...
It never goes below the level's base difficulty (pressure >= 1)."""
from ..config.tuning import (DIRECTOR_BREATHER, DIRECTOR_MAX, DIRECTOR_PEAK, DIRECTOR_RISE)


class Director:
    BUILD, PEAK, BREATHER = "BUILD", "PEAK", "BREATHER"

    def __init__(self):
        self.state = self.BUILD
        self.pressure = 1.0               # spawn-rate multiplier (1 = the level as designed)
        self.timer = 0.0
        self.skill = 0.5                  # 0..1: how well the player is doing right now

    def update(self, dt, hull, damage_rate, kill_rate):
        """hull: 0..1; damage_rate: share of max hull lost per second (recent);
        kill_rate: kills per second (recent)."""
        doing_well = hull * 0.5 + min(1.0, kill_rate / 1.5) * 0.3 + (1 - min(1.0, damage_rate * 20)) * 0.2
        self.skill += (doing_well - self.skill) * min(1.0, dt * 0.5)
        self.timer += dt
        top = 1.0 + (DIRECTOR_MAX - 1.0) * self.skill
        if self.state == self.BUILD:
            self.pressure = min(top, self.pressure + DIRECTOR_RISE * dt * (0.5 + self.skill))
            if self.pressure >= top - 0.01 and self.timer > 6.0:
                self.state, self.timer = self.PEAK, 0.0
        elif self.state == self.PEAK:
            self.pressure = top
            if self.timer >= DIRECTOR_PEAK or hull < 0.3:
                self.state, self.timer = self.BREATHER, 0.0
        else:
            self.pressure = max(1.0, self.pressure - 2.0 * dt)
            if self.timer >= DIRECTOR_BREATHER:
                self.state, self.timer = self.BUILD, 0.0
        return self.pressure
