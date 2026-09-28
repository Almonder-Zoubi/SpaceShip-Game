"""The galaxy finale: after the last level's escape, the rocket jumps to hyperspace, the
galaxy medal is awarded and the next galaxy is teased; then the win results."""
import math
import random

from ..config.display import LOW_H, LOW_W
from ..config.palette import FLAME_WHITE
from ..config.tuning import WARP_TIME
from ..levels.data import galaxy_of
from .states import State


class FinaleMixin:
    """Game mixin: the WARP state (begin, update, speed); drawn by ui/screens.py."""

    WARP_JUMP = 0.55              # share of WARP_TIME when the rocket jumps

    def begin_warp(self):
        """The galaxy is beaten: medal, clean screen, cut-scene."""
        self.medal_new = self.save.add_medal(galaxy_of(self.level).number)
        self.asteroids.clear()
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.boss = None
        self.radio = None
        self._warp_flashed = False
        self.set_state(State.WARP)
        self.audio.play("warp")

    @property
    def warp_progress(self):
        return min(1.0, self.state_time / WARP_TIME)

    def warp_speed(self):
        """The stars stretch: slow build-up, then a hyperspace rush."""
        k = self.warp_progress
        return 1.0 + 30 * max(0.0, k - 0.15) ** 2

    def _update_warp(self, dt):
        """The rocket lines up in the centre, then jumps (streaks + flash)."""
        ship = self.ship
        k = self.warp_progress
        cx, cy = LOW_W / 2, LOW_H * 0.62
        if k < self.WARP_JUMP:
            ship.x += (cx - ship.x) * min(1.0, 2.5 * dt)
            ship.y += (cy - ship.y) * min(1.0, 2.5 * dt)
            ship.y += math.sin(self.time * 30) * 0.2 * k           # the hull shivers
        elif ship.y > -40:
            ship.y -= (200 + 900 * (k - self.WARP_JUMP)) * dt
            if not self._warp_flashed:
                self._warp_flashed = True
                self.screen_flash(0.2)
                self.shake.add(0.4)
        for _ in range(3):                                       # engine glow
            self.fire.emit(ship.x + random.uniform(-2, 2), ship.y + ship.h / 2,
                           random.uniform(-8, 8), random.uniform(80, 140), 0.25, FLAME_WHITE,
                           size=2)
        if self.state_time >= WARP_TIME:
            self.finish_warp()

    def finish_warp(self):
        self.ship.x, self.ship.y = self.SHIP_START
        self.set_state(State.WIN)
