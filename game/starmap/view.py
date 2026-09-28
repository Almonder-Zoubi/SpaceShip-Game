"""Drawing the star map: parallax stars, nebula glows per region, the planets on their route,
the warp gate, hidden caches, the rocket with its trail, and the cards."""
import math
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import (ACCENT, COIN, DANGER, FLAME, GOOD, HIVE_FLESH, HIVE_VEIN, INK,
                              RANK_COLORS, ROCK_PALETTES, STAR_COLORS, TEXT, TEXT_DIM,
                              TEXT_SHADOW)
from ..config.tuning import MAP_CACHE_SEEN, MAP_H, MAP_W
from ..core.pixelart import make_glow, shaded_sphere
from ..ui.medal import draw_medal
from .model import BLACK_HOLE, CACHES, GATE, NODES

PARALLAX = (0.25, 0.5, 1.0)              # star layers, far to near
SUN, HIVE = 4, 9                          # special planets (levels 5 and 10)
LOCKED = [(10, 10, 18), (22, 22, 34), (34, 34, 50), (46, 46, 66)]
SUN_COLORS = [(170, 60, 20), (230, 120, 30), (255, 190, 70), (255, 240, 170), (255, 255, 230)]
ANGLES = 32                               # rotated rocket frames


def boss_name(level):
    """The name of the level's last boss (its card says who waits there)."""
    bosses = [entry for wave in level.waves for entry in wave.bosses]
    return bosses[-1].spec.name if bosses else "-"


class StarMapView:
    """Built once (sprites are pre-rendered); draw(surf, starmap, ...) every frame."""

    def __init__(self, font, levels):
        self.font = font
        rng = random.Random(7)
        self.layers = [self._star_layer(rng, p, 70 + i * 60) for i, p in enumerate(PARALLAX)]
        self.glows = []                   # (x, y, surface) at parallax 0.6
        for level, (x, y) in zip(levels, NODES):
            color = level.nebula[-1]
            bright = tuple(min(255, c * 3) for c in color)
            self.glows.append((x, y, make_glow(70, bright, 0.55)))
        self.planets, self.locked = [], []
        for i, level in enumerate(levels):
            r = 7 if i < 4 else 8 + (i == HIVE) * 3
            if i == SUN:
                palette = SUN_COLORS
            elif i == HIVE:
                palette = HIVE_FLESH
            else:
                palette = ROCK_PALETTES[level.difficulty.palettes[0]][1:]
            self.planets.append(shaded_sphere(r, palette, rng, bands=0.25 if i % 3 == 1 else 0))
            self.locked.append(shaded_sphere(r, LOCKED, rng))
        self.sun_glow = make_glow(28, (255, 150, 50), 0.9)
        self.gate_glow = make_glow(30, (150, 80, 255), 0.8)
        self.cache_glow = make_glow(12, (80, 200, 255), 0.9)
        self.rocket = []
        self.trail = []                   # [x, y, life] in map coordinates

    @staticmethod
    def _star_layer(rng, parallax, count):
        w = int(LOW_W + (MAP_W - LOW_W) * parallax)
        h = int(LOW_H + (MAP_H - LOW_H) * parallax)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(int(count * w * h / (LOW_W * LOW_H))):
            color = rng.choice(STAR_COLORS)
            k = 0.35 + 0.65 * parallax
            surf.set_at((rng.randrange(w), rng.randrange(h)), tuple(int(c * k) for c in color))
        return surf

    def set_rocket(self, image):
        """Rotated frames of the player's rocket (the hangar may have changed it)."""
        self.rocket = [pygame.transform.rotate(image, -math.degrees(math.tau * i / ANGLES))
                       for i in range(ANGLES)]

    @staticmethod
    def camera(starmap):
        ship = starmap.ship
        cx = min(MAP_W - LOW_W, max(0, ship.x - LOW_W / 2))
        cy = min(MAP_H - LOW_H, max(0, ship.y - LOW_H / 2))
        return int(cx), int(cy)

    # --- per frame ------------------------------------------------------------------------
    def update(self, dt, starmap):
        ship = starmap.ship
        if ship.thrusting:
            bx = ship.x - math.sin(ship.angle) * 5
            by = ship.y + math.cos(ship.angle) * 5
            self.trail.append([bx + random.uniform(-1, 1), by + random.uniform(-1, 1), 0.5])
        for p in self.trail:
            p[2] -= dt
        self.trail = [p for p in self.trail if p[2] > 0]

    def draw(self, surf, starmap, time, coins, blink):
        cam = self.camera(starmap)
        surf.fill((6, 4, 14))
        for layer, parallax in zip(self.layers, PARALLAX):
            surf.blit(layer, (-int(cam[0] * parallax), -int(cam[1] * parallax)))
        for x, y, glow in self.glows:
            gx, gy = x - cam[0] * 0.6 - glow.get_width() // 2, y - cam[1] * 0.6 - glow.get_height() // 2
            surf.blit(glow, (int(gx), int(gy)), special_flags=pygame.BLEND_ADD)
        self._draw_route(surf, starmap, cam, time)
        self._draw_gate(surf, starmap, cam, time)
        for i in range(len(self.planets)):
            self._draw_planet(surf, starmap, i, cam, time)
        self._draw_caches(surf, starmap, cam, time)
        self._draw_rocket(surf, starmap, cam, time)
        self._draw_hud(surf, starmap, time, coins, blink)

    def _draw_route(self, surf, starmap, cam, time):
        """Dotted lines from planet to planet: lit where the route is open."""
        for i in range(len(self.planets) - 1):
            (x0, y0), (x1, y1) = NODES[i], NODES[i + 1]
            n = int(math.hypot(x1 - x0, y1 - y0) / 6)
            lit = starmap.is_open(i + 1)
            for j in range(1, n):
                if lit and (j - int(time * 8)) % 6 == 0:
                    color = ACCENT
                else:
                    color = (90, 84, 120) if lit else (36, 34, 52)
                x = x0 + (x1 - x0) * j / n - cam[0]
                y = y0 + (y1 - y0) * j / n - cam[1]
                surf.fill(color, (int(x), int(y), 1, 1))

    def _draw_planet(self, surf, starmap, i, cam, time):
        x, y = NODES[i][0] - cam[0], NODES[i][1] - cam[1]
        if not (-40 < x < LOW_W + 40 and -40 < y < LOW_H + 40):
            return
        open_ = starmap.is_open(i)
        image = self.planets[i] if open_ else self.locked[i]
        r = image.get_width() // 2
        if open_ and i == SUN:
            surf.blit(self.sun_glow, (int(x) - 28, int(y) - 28), special_flags=pygame.BLEND_ADD)
        if i == BLACK_HOLE and open_:                        # the black hole: a spinning disk
            for k in range(28):
                a = time * 1.6 + k * math.tau / 28
                d = 10 + (k % 3) * 2
                color = (255, 220, 170) if k % 4 == 0 else (200, 110, 60)
                surf.fill(color, (int(x + math.cos(a) * d), int(y + math.sin(a) * d * 0.45), 1, 1))
            pygame.draw.circle(surf, (0, 0, 0), (int(x), int(y)), 6)
            pygame.draw.circle(surf, (120, 170, 255), (int(x), int(y)), 7, 1)
        else:
            surf.blit(image, (int(x) - r, int(y) - r))
        if i == HIVE and open_ and int(time * 2) % 2 == 0:  # the hive's veins pulse
            pygame.draw.circle(surf, HIVE_VEIN, (int(x), int(y)), r + 2, 1)
        f = self.font
        label = str(i + 1) if open_ else "?"
        f.draw(surf, label, (int(x), int(y) + r + 3), TEXT if open_ else TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        rank = starmap.ranks.get(i)
        if rank:
            f.draw(surf, rank, (int(x) + r + 3, int(y) - r - 3), RANK_COLORS[rank],
                   shadow=TEXT_SHADOW)
        if open_ and not starmap.ranks.get(i) and int(time * 3) % 2 == 0:   # the frontier
            pygame.draw.circle(surf, ACCENT, (int(x), int(y)), r + 5, 1)

    def _draw_gate(self, surf, starmap, cam, time):
        x, y = GATE[0] - cam[0], GATE[1] - cam[1]
        if starmap.medal:
            surf.blit(self.gate_glow, (int(x) - 30, int(y) - 30), special_flags=pygame.BLEND_ADD)
        for k in range(20):
            a = (time * (1.2 if starmap.medal else 0.2)) + k * math.tau / 20
            color = (190, 140, 255) if starmap.medal else (60, 50, 90)
            if k % 5 == 0:
                color = (255, 255, 255) if starmap.medal else (90, 80, 120)
            surf.fill(color, (int(x + math.cos(a) * 12), int(y + math.sin(a) * 12), 2, 2))

    def _draw_caches(self, surf, starmap, cam, time):
        for cache in CACHES:
            x, y = cache.x - cam[0], cache.y - cam[1]
            if cache.id in starmap.found:
                surf.fill((70, 90, 110), (int(x), int(y), 1, 1))
                continue
            if not starmap.visible(cache):
                continue
            d = math.hypot(cache.x - starmap.ship.x, cache.y - starmap.ship.y)
            k = 1 - d / MAP_CACHE_SEEN
            if k > 0.3:
                surf.blit(self.cache_glow, (int(x) - 12, int(y) - 12), special_flags=pygame.BLEND_ADD)
            if int(time * 6) % 2 == 0 or k > 0.5:
                points = [(x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)]
                pygame.draw.polygon(surf, (150, 230, 255), points)
                surf.fill((255, 255, 255), (int(x), int(y), 1, 1))

    def _draw_rocket(self, surf, starmap, cam, time):
        for x, y, life in self.trail:
            color = FLAME[min(len(FLAME) - 1, int((0.5 - life) * 10))]
            surf.fill(color, (int(x - cam[0]), int(y - cam[1]), 1, 1), special_flags=pygame.BLEND_ADD)
        ship = starmap.ship
        x, y = ship.x - cam[0], ship.y - cam[1]
        signal = starmap.signal()
        if signal > 0:                                       # the scanner rings
            period = 1.4 - signal
            k = (time % period) / period
            color = tuple(int(c * (1 - k)) for c in (80, 200, 255))
            pygame.draw.circle(surf, color, (int(x), int(y)), int(8 + k * 26), 1)
        if self.rocket:
            frame = self.rocket[int(round(ship.angle / math.tau * ANGLES)) % ANGLES]
            surf.blit(frame, frame.get_rect(center=(int(x), int(y))))

    # --- cards + HUD ----------------------------------------------------------------------
    def _panel(self, surf, rect):
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((*INK, 215))
        surf.blit(shade, rect)
        pygame.draw.rect(surf, TEXT_DIM, rect, 1)

    def _draw_hud(self, surf, starmap, time, coins, blink):
        f = self.font
        f.draw(surf, "STAR MAP  ORION REACH", (6, 6), TEXT, shadow=TEXT_SHADOW)
        found = len(starmap.found)
        f.draw(surf, f"DATA CACHES {found}/{len(CACHES)}", (6, 16),
               GOOD if found == len(CACHES) else TEXT_DIM, shadow=TEXT_SHADOW)
        text = f"CR {coins}"
        f.draw(surf, text, (LOW_W - 6 - f.size(text)[0], 6), COIN[2], shadow=TEXT_SHADOW)
        if starmap.medal:
            draw_medal(surf, LOW_W - 14, 30, time)
        if starmap.card:
            self._draw_cache_card(surf, starmap.card, blink)
            return
        node = starmap.near_node()
        if node is not None:
            self._draw_node_card(surf, starmap, node, blink)
        elif starmap.near_gate():
            rect = pygame.Rect(40, LOW_H - 44, LOW_W - 80, 38)
            self._panel(surf, rect)
            if starmap.medal:
                f.draw(surf, "THE VEIL GATE IS OPEN", (LOW_W // 2, rect.y + 6), (190, 140, 255),
                       shadow=TEXT_SHADOW, center=True)
                f.draw(surf, "GALAXY 2 IS BEING CHARTED...", (LOW_W // 2, rect.y + 18), TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
            else:
                f.draw(surf, "A SEALED WARP GATE", (LOW_W // 2, rect.y + 6), TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
                f.draw(surf, "BEAT THE GALAXY TO OPEN IT", (LOW_W // 2, rect.y + 18), TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
        elif blink:
            f.draw(surf, "FLY TO A PLANET   ENTER: HANGAR   ESC: TITLE", (LOW_W // 2, LOW_H - 12),
                   TEXT_DIM, shadow=TEXT_SHADOW, center=True)

    def _draw_node_card(self, surf, starmap, i, blink):
        f = self.font
        level = starmap.levels[i]
        rect = pygame.Rect(40, LOW_H - 48, LOW_W - 80, 42)
        self._panel(surf, rect)
        mid = LOW_W // 2
        if not starmap.is_open(i):
            f.draw(surf, f"LEVEL {level.number}  ???", (mid, rect.y + 6), TEXT_DIM,
                   shadow=TEXT_SHADOW, center=True)
            f.draw(surf, f"CLEAR LEVEL {level.number - 1} TO OPEN THE ROUTE", (mid, rect.y + 18),
                   DANGER, shadow=TEXT_SHADOW, center=True)
            return
        f.draw(surf, f"LEVEL {level.number}  {level.name}", (mid, rect.y + 5), ACCENT,
               shadow=TEXT_SHADOW, center=True)
        rank = starmap.ranks.get(i)
        info = f"BOSS: {boss_name(level)}   BEST: {rank or '-'}"
        f.draw(surf, info, (mid, rect.y + 16), TEXT, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(surf, "ENTER: HANGAR", (mid, rect.y + 28), GOOD, shadow=TEXT_SHADOW, center=True)

    def _draw_cache_card(self, surf, cache, blink):
        f = self.font
        rect = pygame.Rect(30, 56, LOW_W - 60, 118)
        self._panel(surf, rect)
        mid = LOW_W // 2
        f.draw(surf, "DATA CACHE FOUND", (mid, rect.y + 6), (150, 230, 255), shadow=TEXT_SHADOW,
               center=True)
        f.draw(surf, cache.title, (mid, rect.y + 20), ACCENT, shadow=TEXT_SHADOW, center=True)
        for k, line in enumerate(cache.lines):
            f.draw(surf, line, (mid, rect.y + 38 + k * 11), TEXT, shadow=TEXT_SHADOW, center=True)
        f.draw(surf, f"+{cache.coins} CR", (mid, rect.y + 86), COIN[2], shadow=TEXT_SHADOW,
               center=True)
        if blink:
            f.draw(surf, "ENTER: CLOSE", (mid, rect.y + 102), TEXT_DIM, shadow=TEXT_SHADOW,
                   center=True)
