"""A distant planet drifting past."""
from ..config.display import LOW_H, LOW_W
from ..config.palette import PLANET_PALETTES
from ..core.pixelart import shaded_sphere


class Planet:
    """A distant planet that drifts past slowly, then respawns with a new look."""

    SPEED = 6

    def __init__(self, rng):
        self.rng = rng
        self._spawn(initial=True)

    def _spawn(self, initial=False):
        r = self.rng.randint(10, 22)
        palette = self.rng.choice(PLANET_PALETTES)
        self.image = shaded_sphere(r, palette, self.rng, bands=self.rng.choice((0.0, 0.18, 0.28)))
        self.x = self.rng.randint(20, LOW_W - 20 - 2 * r)
        self.y = self.rng.randint(10, LOW_H // 2) if initial else -2 * r - self.rng.randint(40, 400)

    def update(self, dt, world_speed):
        self.y += self.SPEED * world_speed * dt
        if self.y > LOW_H:
            self._spawn()

    def draw(self, surf):
        surf.blit(self.image, (self.x, int(self.y)))
