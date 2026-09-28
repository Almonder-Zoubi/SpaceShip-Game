"""SIEGE (galaxy 2, LAST LIGHT): no boss. Vega's flagship limps along the bottom of the
screen and the Hollow throw everything at it for three waves. Rocks, minions that reach it
and stray enemy bullets hurt its hull; its turrets shoot the minions nearest to it. Lose
the flagship and the attempt is lost. Hold it above half its hull for a bonus."""
import math

import pygame

from ..bosses.art import build_boss_sprite
from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, GOOD, TEXT, TEXT_SHADOW
from ..config.tuning import (FLAGSHIP_GUN, FLAGSHIP_GUN_DAMAGE, FLAGSHIP_HULL, FLAGSHIP_RAM,
                             FLAGSHIP_ROCK, FLAGSHIP_SAVED_COINS)
from ..core.pixelart import CharCanvas
from ..weapons.base import Hit
from .base import Hazard

COLORS = {"K": (8, 10, 16), "H": (150, 160, 180), "h": (90, 100, 120), "d": (50, 56, 70),
          "B": (90, 170, 255), "W": (240, 250, 255), "Y": (255, 204, 64)}


def _half():
    c = CharCanvas(64, 18)
    c.poly([(63, 1), (40, 2), (14, 6), (2, 12), (10, 16), (63, 16)], "h")
    c.poly([(63, 3), (40, 4), (16, 8), (8, 12), (14, 14), (63, 14)], "H")
    c.rect(30, 0, 36, 5, "d")                               # a turret
    c.rect(32, 0, 34, 1, "W")
    for x in range(18, 62, 6):                              # windows
        c.set(x, 10, "B")
    c.line(40, 12, 63, 12, "d")
    c.rect(56, 5, 63, 8, "Y")                               # Vega's crest on the bridge
    return c.rows()


class Flagship:
    def __init__(self):
        self.image = build_boss_sprite(_half(), COLORS)
        self.w, self.h = self.image.get_size()
        self.x, self.y = LOW_W / 2, LOW_H - self.h / 2 + 2
        self.max_hp = self.hp = FLAGSHIP_HULL
        self.flash = 0.0
        self.time = 0.0

    @property
    def alive(self):
        return self.hp > 0

    @property
    def top(self):
        return self.y - self.h / 2 + 4

    def over(self, x, y):
        return abs(x - self.x) < self.w / 2 - 6 and y > self.top

    def hurt(self, amount):
        if self.alive:
            self.hp = max(0.0, self.hp - amount)
            self.flash = 0.06

    def turrets(self):
        return [(self.x - 30, self.top), (self.x + 30, self.top)]


class Siege(Hazard):
    def __init__(self):
        self.flagship = Flagship()
        self.gun_timer = FLAGSHIP_GUN
        self.tracers = []                                   # (x0, y0, x1, y1, life)
        self.lost_time = None
        self.time = 0.0

    def update(self, dt, game):
        self.time += dt
        ship = self.flagship
        ship.time += dt
        ship.flash = max(0.0, ship.flash - dt)
        self.tracers = [(a, b, c, d, t - dt) for a, b, c, d, t in self.tracers if t > dt]
        if not ship.alive:
            self._lost(dt, game)
            return
        for rock in list(game.asteroids):                    # rocks crash into its hull
            if ship.over(rock.x, rock.y + rock.radius):
                ship.hurt(FLAGSHIP_ROCK * max(0.5, rock.radius / 10))
                game.asteroids.remove(rock)
                game.explosion(rock.x, ship.top, size=0.6)
        for enemy in list(game.enemies):                     # minions ram it
            if ship.over(enemy.x, enemy.y + enemy.h / 2):
                ship.hurt(FLAGSHIP_RAM)
                game.enemies.remove(enemy)
                game.explosion(enemy.x, ship.top, size=0.8)
        kept = []
        for b in game.enemy_bullets:                         # and stray shots
            if getattr(b, "solid", True) and ship.over(b.x, b.y):
                ship.hurt(b.damage * 0.6)
            else:
                kept.append(b)
        game.enemy_bullets = kept
        self.gun_timer -= dt
        if self.gun_timer <= 0:
            self.gun_timer = FLAGSHIP_GUN
            self._fire(game)

    def _fire(self, game):
        """Each turret shoots the minion nearest to the flagship (the player's side)."""
        ship = self.flagship
        targets = sorted((e for e in game.enemies if 0 < e.y < ship.top - 10),
                         key=lambda e: math.hypot(e.x - ship.x, e.y - ship.y))
        for (tx, ty), target in zip(ship.turrets(), targets):
            self.tracers.append((tx, ty, target.x, target.y, 0.1))
            game._damage_enemy(Hit(target, FLAGSHIP_GUN_DAMAGE, target.x, target.y, 0, -1, 0))
        if targets:
            game.audio.play("gun")

    def _lost(self, dt, game):
        if self.lost_time is None:
            self.lost_time = 0.0
            for i in range(6):
                game.explosion(self.flagship.x + (i - 2.5) * 20, self.flagship.y, size=1.4)
            game.shake.add(0.8)
            game.radio_say(["THE FLAGSHIP... VEGA! VEGA, ANSWER!"], delay=0)
        self.lost_time += dt
        if self.lost_time > 1.5 and game.ship.alive and not game.god:
            game._ship_destroyed()                          # the line did not hold

    def bonus(self):
        ship = self.flagship
        if ship.hp > ship.max_hp * 0.5:
            return FLAGSHIP_SAVED_COINS, "FLAGSHIP_HELD", "FLAGSHIP HELD", ship.x, ship.top - 20
        return None

    def draw_mid(self, surf):
        ship = self.flagship
        if not ship.alive and (self.lost_time or 0) > 1.0:
            return
        x, y = int(ship.x - ship.w / 2), int(ship.y - ship.h / 2)
        surf.blit(ship.image, (x, y))
        if ship.flash > 0:
            surf.fill((80, 40, 40), (x, y, ship.w, ship.h), special_flags=pygame.BLEND_ADD)
        for k in (-1, 1):                                    # engine glow
            glow = 120 + int(60 * math.sin(self.time * 9 + k))
            surf.fill((glow // 3, glow // 2, glow), (int(ship.x + k * 56), int(ship.y) + 4, 3, 2),
                      special_flags=pygame.BLEND_ADD)
        for x0, y0, x1, y1, _ in self.tracers:
            pygame.draw.line(surf, (255, 230, 150), (int(x0), int(y0)), (int(x1), int(y1)))

    def draw_bar(self, surf, font):
        ship = self.flagship
        x, y, w = LOW_W // 2 - 40, LOW_H - 30, 80
        surf.fill((20, 24, 34), (x, y, w, 3))
        color = GOOD if ship.hp > ship.max_hp * 0.5 else DANGER
        surf.fill(color, (x, y, int(w * ship.hp / ship.max_hp), 3))
        font.draw(surf, "VEGA", (x + w + 4, y - 2), TEXT if ship.alive else DANGER,
                  shadow=TEXT_SHADOW)
