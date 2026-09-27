"""Creates asteroids according to a Difficulty."""
import random

from ..config.display import LOW_W
from .asteroid import Asteroid


class AsteroidSpawner:
    def __init__(self, library, difficulty):
        self.library = library
        self.difficulty = difficulty
        self.timer = 0.5

    def update(self, dt, world_speed):
        """Return a list of new asteroids (usually empty or one)."""
        # Boosting brings rocks in faster, retro gives you breathing room.
        self.timer -= dt * world_speed
        if self.timer > 0:
            return []
        d = self.difficulty
        self.timer = d.spawn_interval * random.uniform(0.55, 1.45)
        art = self.library.pick(d.radius_min, d.radius_max, d.palettes)
        # Big rocks fall slower, small ones faster.
        size_k = (art.radius - d.radius_min) / max(1, d.radius_max - d.radius_min)
        speed = random.uniform(d.speed_min, d.speed_max) * (1.15 - 0.3 * size_k)
        return [Asteroid(
            art,
            x=random.uniform(8, LOW_W - 8),
            y=-art.size / 2,
            vx=random.uniform(-d.drift, d.drift),
            vy=speed,
            spin=random.choice((-1, 1)) * random.uniform(0.4, 2.2),
        )]
