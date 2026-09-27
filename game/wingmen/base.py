"""Wingman base class: formation flying, knock-out + reboot, XP levels."""
import math
import random

from ..config.palette import FLAME, SMOKE, SPARK
from ..config.tuning import WINGMAN_KO_TIME, WINGMAN_XP
from .art import wingman_sprite


def level_for(xp):
    """Level 1..5 for a total XP."""
    return sum(1 for need in WINGMAN_XP if xp >= need)


class Wingman:
    """A small ship beside the rocket, never controlled directly and never destroyed:
    a hit knocks it out (it spins and smokes) and it reboots after WINGMAN_KO_TIME.

    Subclasses set name / rows / role and implement act(dt, game, firing) -> [Hit].
    Hooks the game calls: block(bullet) (GUARDIAN), heal/revive (MEDIC), magnet (MAGPIE).
    """

    name = "WINGMAN"
    rows = ()
    role = ""
    perk = ""                          # what level 5 adds (hangar text)
    temporary = False                  # TWIN boost copy

    def __init__(self, level=1, side=-1):
        self.level = level
        self.side = side               # -1 = left of the ship, 1 = right
        self.x = self.y = 0.0
        self.placed = False
        self.ko = 0.0                  # seconds until it reboots (0 = flying)
        self.time = random.uniform(0, 5)
        self.frames = self.build_frames()

    def build_frames(self):
        return wingman_sprite(self.name, self.rows)

    @property
    def flying(self):
        return self.ko <= 0

    @property
    def bound(self):
        return 5

    def slot(self, ship):
        """Where it wants to be: beside the ship, following the lean."""
        return ship.to_world(self.side * (ship.w / 2 + 9), 5)

    def update(self, dt, game, firing):
        self.time += dt
        ship = game.ship
        tx, ty = self.slot(ship)
        if not self.placed:
            self.x, self.y, self.placed = tx, ty, True
        k = min(1.0, (4 if self.ko > 0 else 10) * dt)
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k
        if self.ko > 0:
            self.ko = max(0.0, self.ko - dt)
            if random.random() < 20 * dt:
                game.smoke.emit(self.x, self.y, random.uniform(-10, 10), random.uniform(10, 30),
                                0.6, SMOKE, size=2, drag=1.2)
            if self.ko == 0:
                game.audio.play("wingman_up")
                game.fire.burst(self.x, self.y, 8, 50, 0.3, SPARK, size=(1, 1))
            return []
        if random.random() < 30 * dt:          # tiny engine flame
            game.fire.emit(self.x + random.uniform(-1, 1), self.y + 6, 0, random.uniform(30, 60),
                           0.08, FLAME)
        if not ship.alive:
            return []
        return self.act(dt, game, firing)

    def act(self, dt, game, firing):
        return []

    def touches(self, x, y, radius=0):
        return self.flying and math.hypot(x - self.x, y - self.y) < 4 + radius

    def knock_out(self, game):
        """Hit: spin, smoke, reboot later."""
        if not self.flying:
            return
        self.ko = WINGMAN_KO_TIME
        game.fire.burst(self.x, self.y, 14, 70, 0.4, FLAME, size=(1, 2))
        game.audio.play("wingman_down")

    def block(self, bullet, game):
        """An enemy bullet touches it. Returns True if the bullet is used up."""
        self.knock_out(game)
        return True

    def reset(self):
        self.ko = 0.0
        self.placed = False

    def draw(self, surf):
        frame = self.frames[int(self.time * 12) % 4] if self.ko > 0 else self.frames[0]
        if self.ko > 0 and self.ko < 1.0 and int(self.ko * 10) % 2:
            return                                   # blinks back to life
        surf.blit(frame, (int(self.x) - frame.get_width() // 2,
                          int(self.y) - frame.get_height() // 2))

    def draw_shots(self, surf):
        """Hook: bolts, rockets, shields."""
