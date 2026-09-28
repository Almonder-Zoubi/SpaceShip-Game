"""ESCORT (galaxy 2, BROOD SANCTUARY): a pod of freed Swarm larvae drifts across the screen.
Latchers try to drain it, the Hollow Reaper wants to harvest it; three freed larvae ride on
it and zap anything that comes close. If the pod survives the level, the brood pays you back
(coins, and something later on). If it dies, the level goes on - without it."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import DANGER, GOOD, HEAL, HIVE_VEIN, TEXT, TEXT_SHADOW
from ..config.tuning import ALLY_DAMAGE, ALLY_INTERVAL, ALLY_RANGE, POD_HP, POD_SPEED
from ..weapons.base import Hit
from .base import Hazard


class BroodPod:
    """The thing to protect: an egg sac with larvae inside. Enemy bullets that touch it hurt
    it (half their damage)."""

    RADIUS = 11

    def __init__(self):
        self.x, self.y = LOW_W / 2, LOW_H - 62
        self.max_hp = self.hp = POD_HP
        self.dir = 1
        self.flash = 0.0
        self.time = 0.0

    @property
    def alive(self):
        return self.hp > 0

    def hurt(self, amount):
        if self.alive:
            self.hp = max(0.0, self.hp - amount)
            self.flash = 0.08

    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        if not self.alive:
            self.y += 20 * dt                             # the husk sinks away
            return
        self.x += self.dir * POD_SPEED * dt
        if not 60 < self.x < LOW_W - 60:
            self.dir = -self.dir
        self.y = LOW_H - 62 + math.sin(self.time * 0.8) * 6


class BroodEscort(Hazard):
    def __init__(self):
        self.pod = BroodPod()
        self.ally_timer = ALLY_INTERVAL
        self.zaps = []                                    # (x0, y0, x1, y1, life)
        self.lost_said = False
        self.time = 0.0

    def allies(self):
        """The three larvae riding on the pod (none once it is lost)."""
        if not self.pod.alive:
            return []
        p = self.pod
        return [(p.x + math.cos(p.time * 2 + i * math.tau / 3) * 16,
                 p.y + math.sin(p.time * 2 + i * math.tau / 3) * 10) for i in range(3)]

    def update(self, dt, game):
        self.time += dt
        pod = self.pod
        pod.update(dt)
        self.zaps = [(x0, y0, x1, y1, t - dt) for x0, y0, x1, y1, t in self.zaps if t > dt]
        if pod.alive:
            for b in list(game.enemy_bullets):            # stray shots hit the pod
                if getattr(b, "solid", True) and math.hypot(b.x - pod.x, b.y - pod.y) < pod.RADIUS:
                    pod.hurt(b.damage * 0.5)
                    game.enemy_bullets.remove(b)
            self.ally_timer -= dt
            if self.ally_timer <= 0:
                self.ally_timer = ALLY_INTERVAL
                self._zap(game)
        elif not self.lost_said:
            self.lost_said = True
            game.explosion(pod.x, pod.y, size=1.5)
            game.radio_say(["THE BROOD... WE LOST THEM.", "KEEP FLYING. MAKE IT COUNT."], delay=0)

    def _zap(self, game):
        """Each larva zaps the nearest minion in reach (the player's side)."""
        for ax, ay in self.allies():
            near = [e for e in game.enemies if math.hypot(e.x - ax, e.y - ay) < ALLY_RANGE]
            if not near:
                continue
            target = min(near, key=lambda e: math.hypot(e.x - ax, e.y - ay))
            self.zaps.append((ax, ay, target.x, target.y, 0.12))
            game._damage_enemy(Hit(target, ALLY_DAMAGE, target.x, target.y, 0, -1, 0))

    def draw_mid(self, surf):
        pod = self.pod
        x, y = int(pod.x), int(pod.y)
        if pod.alive:
            glow = int(60 + 40 * math.sin(pod.time * 3))
            pygame.draw.circle(surf, (20, glow, 30), (x, y), pod.RADIUS + 3)
            pygame.draw.ellipse(surf, (255, 255, 255) if pod.flash > 0 else (90, 160, 90),
                                (x - pod.RADIUS, y - pod.RADIUS + 2, pod.RADIUS * 2, pod.RADIUS * 2 - 4))
            for i in range(3):                            # larvae asleep inside
                a = pod.time + i * 2.1
                surf.fill(HIVE_VEIN, (x + int(math.cos(a) * 5), y + int(math.sin(a) * 3), 2, 2))
            for ax, ay in self.allies():                  # the freed larvae riding on it
                surf.fill(HEAL[2], (int(ax) - 1, int(ay) - 1, 3, 3))
                surf.fill(HEAL[0], (int(ax), int(ay), 1, 1))
        elif y < LOW_H + 10:
            pygame.draw.ellipse(surf, (40, 40, 40), (x - pod.RADIUS, y - 6, pod.RADIUS * 2, 12))
        for x0, y0, x1, y1, _ in self.zaps:
            pygame.draw.line(surf, HEAL[1], (int(x0), int(y0)), (int(x1), int(y1)))

    def draw_bar(self, surf, font):
        """The pod's hull, at the bottom of the screen."""
        pod = self.pod
        x, y, w = LOW_W // 2 - 40, LOW_H - 9, 80             # bottom centre, clear of the HUD
        surf.fill((20, 30, 20), (x, y, w, 4))
        color = GOOD if pod.hp > pod.max_hp * 0.35 else DANGER
        surf.fill(color, (x, y, int(w * pod.hp / pod.max_hp), 4))
        label = "BROOD" if pod.alive else "BROOD LOST"
        font.draw(surf, label, (x - 4 - font.size(label)[0], y - 1),
                  TEXT if pod.alive else DANGER, shadow=TEXT_SHADOW)


def target_pod(game):
    """The pod, if this level has one and it lives."""
    pod = getattr(game.hazard, "pod", None)
    return pod if pod and pod.alive else None

