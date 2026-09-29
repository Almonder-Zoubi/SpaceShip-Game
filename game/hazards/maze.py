"""CROSSROADS (galaxy 2, HOLLOW MAZE): drifting VOID HOLES erase every bullet that flies into
them (yours and theirs: safe spots and blind spots at once). Late in the first field two
gates open, RED and BLUE; the one you fly into picks the route - and the boss at its end.
Choose nothing and the maze chooses for you."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, TEXT, TEXT_SHADOW
from ..config.tuning import FORK_AT, FORK_GATE, VOID_HOLES, VOID_RADIUS, VOID_SPEED
from ..core.particles import Shockwave
from ..flow.states import Phase
from .base import Hazard

GATES = ((80, "RED", (230, 60, 70)), (240, "BLUE", (70, 140, 255)))


class VoidHole:
    def __init__(self, y=None):
        self.r = random.uniform(*VOID_RADIUS)
        self.x = random.uniform(30, LOW_W - 30)
        self.y = random.uniform(-40, LOW_H) if y is None else y
        self.drift = random.uniform(-8, 8)
        self.time = random.uniform(0, 10)

    def update(self, dt):
        self.time += dt
        self.y += VOID_SPEED * dt
        self.x += self.drift * dt
        if self.y - self.r > LOW_H or not -self.r < self.x < LOW_W + self.r:
            self.__init__(-self.r - random.uniform(0, 60))

    def contains(self, x, y):
        return (x - self.x) ** 2 + (y - self.y) ** 2 < self.r ** 2


class HollowMaze(Hazard):
    def __init__(self):
        self.holes = [VoidHole() for _ in range(VOID_HOLES)]
        self.time = 0.0
        self.route = None                 # 0 = RED, 1 = BLUE (read by Game.wave_bosses)
        self.gates_y = None               # the fork's gates (None = closed)
        self.erased = 0

    def update(self, dt, game):
        self.time += dt
        for hole in self.holes:
            hole.update(dt)
        self._erase(game)
        wave = game.wave
        if wave.fork and game.phase == Phase.FIELD and self.route is None:
            if game.distance >= wave.length * FORK_AT:
                self._fork(dt, game)
            if game.distance >= wave.length - 0.5 and self.route is None:
                self._choose(random.randrange(2), game, forced=True)
        elif self.gates_y is not None and self.route is not None:
            self.gates_y -= 90 * dt                       # the gates close upwards
            if self.gates_y < -40:
                self.gates_y = None

    def _erase(self, game):
        """Bullets inside a void hole are gone - enemy bullets and the rocket's own shots."""
        def outside(b):
            return not any(h.contains(b.x, b.y) for h in self.holes)
        before = len(game.enemy_bullets)
        game.enemy_bullets = [b for b in game.enemy_bullets if outside(b)]
        self.erased += before - len(game.enemy_bullets)
        for weapon in game.weapons:
            bullets = getattr(weapon, "bullets", None)
            if isinstance(bullets, list):
                bullets[:] = [b for b in bullets if outside(b)]

    def _fork(self, dt, game):
        if self.gates_y is None:
            self.gates_y = -30.0
            game.audio.play("teleport")
            game.radio_say(["TWO GATES! RED OR BLUE - PICK ONE!"], delay=0)
        self.gates_y = min(96.0, self.gates_y + 60 * dt)
        ship = game.ship
        for i, (x, _, _) in enumerate(GATES):
            if ship.alive and math.hypot(ship.x - x, ship.y - self.gates_y) < FORK_GATE + 4:
                self._choose(i, game)

    def _choose(self, route, game, forced=False):
        self.route = route
        x, name, color = GATES[route]
        game.shockwaves.append(Shockwave(x, self.gates_y or 0, max_radius=60, duration=0.5,
                                         color=color))
        game.audio.play("switch")
        if forced:
            game.radio_say([f"THE MAZE CHOSE FOR YOU: {name}."], delay=0)
        else:
            game.radio_say([f"{name} ROUTE. NO WAY BACK NOW."], delay=0)

    def draw_back(self, surf):
        for hole in self.holes:
            x, y, r = int(hole.x), int(hole.y), int(hole.r)
            pygame.draw.circle(surf, (2, 0, 6), (x, y), r)
            for i in range(10):                            # a ring of motes sinking in
                a = hole.time * 1.3 + i * math.tau / 10
                k = (hole.time * 0.7 + i * 0.1) % 1
                rr = r + 4 - k * 6
                surf.fill((90, 60, 140), (x + int(math.cos(a) * rr), y + int(math.sin(a) * rr), 1, 1))
            pygame.draw.circle(surf, (50, 30, 80), (x, y), r, 1)

    def draw_front(self, surf):
        if self.gates_y is None:
            return
        y = int(self.gates_y)
        for i, (x, name, color) in enumerate(GATES):
            if self.route is not None and self.route != i:
                continue
            spin = self.time * (2 if i else -2)
            for k in range(12):
                a = spin + k * math.tau / 12
                r = FORK_GATE + math.sin(self.time * 5 + k) * 2
                surf.fill(color, (x + int(math.cos(a) * r), y + int(math.sin(a) * r), 2, 2),
                          special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(surf, color, (x, y), FORK_GATE - 6, 1)

    def draw_bar(self, surf, font):
        """Names under the open gates (and a warning if the rocket has not chosen)."""
        if self.gates_y is None or self.route is not None:
            return
        y = int(self.gates_y) + FORK_GATE + 4
        for x, name, color in GATES:
            boss = "GRINDER" if name == "RED" else "SPINNER"
            font.draw(surf, name, (x, y), color, shadow=TEXT_SHADOW, center=True)
            font.draw(surf, boss, (x, y + 9), TEXT, shadow=TEXT_SHADOW, center=True)
        if int(self.time * 3) % 2:
            font.draw(surf, "CHOOSE", (LOW_W // 2, y), DANGER, shadow=TEXT_SHADOW, center=True)
