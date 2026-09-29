"""THE COURT OF NYX (galaxy 2, GAUNTLET + DUEL): four arenas, each with its own rolled rule
(a VEIL SHIFT per wave, Wave.reroll). CHAINED ROCKS swing through them: two rocks on a
tether that turns as they fall. The tether hurts; break one rock and the other flies free."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.tuning import CHAIN_DAMAGE, CHAIN_INTERVAL, CHAIN_LENGTH, CHAIN_SPIN
from ..flow.states import Phase
from ..obstacles.asteroid import rock_class
from .base import Hazard

LINK = (150, 140, 170)


class Chain:
    def __init__(self, a, b, x):
        self.a, self.b = a, b
        self.cx, self.cy = x, -CHAIN_LENGTH
        self.angle = random.uniform(0, math.pi)
        self.spin = random.choice((-1, 1)) * CHAIN_SPIN
        self.speed = random.uniform(30, 45)

    def ends(self):
        dx, dy = math.cos(self.angle) * CHAIN_LENGTH / 2, math.sin(self.angle) * CHAIN_LENGTH / 2
        return (self.cx - dx, self.cy - dy), (self.cx + dx, self.cy + dy)


def _segment_distance(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


class CourtOfNyx(Hazard):
    def __init__(self):
        self.chains = []
        self.timer = 3.0
        self.time = 0.0

    def update(self, dt, game):
        self.time += dt
        if game.phase == Phase.FIELD and game.distance < game.wave.length - 4:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = CHAIN_INTERVAL * random.uniform(0.8, 1.2)
                self._spawn(game)
        ship = game.ship
        for chain in list(self.chains):
            alive = [r for r in (chain.a, chain.b) if r in game.asteroids]
            if len(alive) < 2:                               # broken: the other flies free
                for rock in alive:
                    rock.vx = -math.sin(chain.angle) * chain.spin * CHAIN_LENGTH
                    rock.vy = chain.speed + 40
                self.chains.remove(chain)
                continue
            chain.cy += chain.speed * dt
            chain.angle += chain.spin * dt
            for rock, (x, y) in zip((chain.a, chain.b), chain.ends()):
                rock.x, rock.y, rock.vx, rock.vy = x, y, 0.0, 0.0
            if chain.cy - CHAIN_LENGTH > LOW_H:
                for rock in (chain.a, chain.b):
                    if rock in game.asteroids:
                        game.asteroids.remove(rock)
                self.chains.remove(chain)
                continue
            if ship.alive and _segment_distance(ship.x, ship.y, *chain.ends()) < ship.w * 0.35:
                game.hurt_ship(ship.max_hp * CHAIN_DAMAGE, ship.x, ship.y)

    def _spawn(self, game):
        palettes = game.level.difficulty.palettes
        x = random.uniform(50, LOW_W - 50)
        rocks = []
        for _ in range(2):
            name = random.choice(palettes)
            art = game.library.pick(7, 10, (name,))
            rocks.append(rock_class(name)(art, x, -40, 0, 0, random.uniform(-2, 2),
                                          hp_scale=game.level.difficulty.rock_hp))
        game.asteroids += rocks
        self.chains.append(Chain(rocks[0], rocks[1], x))

    def draw_mid(self, surf):
        for chain in self.chains:
            (ax, ay), (bx, by) = chain.ends()
            for k in range(1, 9):                            # links
                t = k / 9
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                surf.fill(LINK, (int(x) - 1, int(y) - 1, 2, 2))
            pygame.draw.line(surf, (60, 50, 80), (int(ax), int(ay)), (int(bx), int(by)))
