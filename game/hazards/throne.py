"""THE HOLLOW THRONE (galaxy 2 finale): what the fights there change about the world.
- A boss that wants the dark (ECLIPSE in the rush, NYX in its third phase) gets it: the
  DARKNESS layer switches on.
- NYX's UNMAKING (phase 4+) lets the void close in from both edges; touching it hurts.
- The ESCAPE wave: the Veil tears apart, the void closes, debris falls, the world rushes.
Walls follow the hive's contract (`width(side, y)`), so the bot and tests handle both."""
import math
import random

from ..config.display import LOW_H, LOW_W
from ..config.tuning import ESCAPE_SPEED, UNMAKING_DAMAGE, UNMAKING_WALL
from ..flow.states import Phase
from ..obstacles.asteroid import rock_class
from .base import Hazard
from .darkness import Darkness

VOID = [(0, 0, 0), (26, 10, 40), (70, 30, 110), (150, 90, 220)]


class HollowThrone(Hazard):
    def __init__(self):
        self.darkness = Darkness()
        self.dark_on = False
        self.close = 0.0                  # 0..1: how far the void has closed in
        self.time = 0.0
        self.world_speed = 1.0
        self.debris_timer = 0.0

    @property
    def dim(self):                        # the Eclipse puts the light out (bosses/eclipse.py)
        return self.darkness.dim

    @dim.setter
    def dim(self, value):
        self.darkness.dim = value

    def width(self, side, y):
        wobble = math.sin(y * 0.06 + self.time * 2 + side) * 5 + math.sin(y * 0.021 - self.time) * 4
        return max(0.0, UNMAKING_WALL * self.close + wobble * self.close)

    def update(self, dt, game):
        self.time += dt
        self.darkness.update(dt, game)
        boss = game.boss
        self.dark_on = bool(boss and getattr(boss, "wants_dark", False) and boss.fighting)
        escape = game.wave.escape and game.phase == Phase.FIELD
        unmaking = bool(boss and getattr(boss, "unmaking", False))
        want = 1.0 if (unmaking or escape) else 0.0
        if escape:
            want = 0.6 + 0.6 * min(1.0, game.distance / max(1.0, game.wave.length))
        self.close += (want - self.close) * min(1.0, 0.8 * dt)
        self.world_speed = ESCAPE_SPEED if escape else 1.0
        if escape:
            self._debris(dt, game)
        ship = game.ship
        if not ship.alive or self.close < 0.05:
            return
        for side in (-1, 1):
            w = self.width(side, ship.y)
            edge = w if side < 0 else LOW_W - w
            if (ship.x - edge) * -side < ship.w / 2 - 2:
                ship.x = edge - side * (ship.w / 2 + 1)
                ship.vx = -side * 60
                game.hurt_ship(ship.max_hp * UNMAKING_DAMAGE, edge, ship.y)

    def _debris(self, dt, game):
        self.debris_timer -= dt
        if self.debris_timer <= 0:
            self.debris_timer = random.uniform(0.25, 0.45)
            name = random.choice(game.level.difficulty.palettes)
            art = game.library.pick(5, 11, (name,))
            game.asteroids.append(rock_class(name)(
                art, random.uniform(70, LOW_W - 70), -art.size / 2, random.uniform(-15, 15),
                random.uniform(120, 170), random.uniform(-2, 2),
                hp_scale=game.level.difficulty.rock_hp))
            if random.random() < 0.3:
                game.shake.add(0.08)

    def draw_mid(self, surf):
        if self.close < 0.02:
            return
        for y in range(0, LOW_H, 2):
            for side in (-1, 1):
                w = int(self.width(side, y))
                if w <= 0:
                    continue
                x0 = 0 if side < 0 else LOW_W - w
                surf.fill(VOID[0], (x0, y, w, 2))
                rim = x0 + w - 2 if side < 0 else x0
                k = int(self.time * 12 + y) % 7
                surf.fill(VOID[3] if k == 0 else VOID[2], (rim, y, 2, 2))
                if (y + int(self.time * 30)) % 11 == 0:
                    surf.fill(VOID[1], (x0 + random.randrange(max(1, w)), y, 1, 1))

    def draw_front(self, surf):
        if self.dark_on:
            self.darkness.draw_front(surf)
