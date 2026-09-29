"""LATCHERS (galaxy 2, BROOD SANCTUARY): Hollow leeches that fly for the brood pod, cling to
it and drain it until they are shot off. Without a pod they go for the rocket."""
import math
import random

from ..config.display import LOW_W
from ..config.tuning import LATCHER_DRAIN, LATCHER_HP, LATCHER_SPEED, POINTS_LATCHER
from ..core.pixelart import sprite_from_rows
from ..hazards.escort import target_pod
from .base import Enemy

ROWS = (
    ".K...K.",
    "KVK.KVK",
    ".KVVVK.",
    "KVWRWVK",
    ".KVVVK.",
    "..KVK..",
    "...K...",
)
COLORS = {"K": (14, 8, 22), "V": (110, 70, 170), "W": (230, 220, 255), "R": (220, 60, 80)}


class Latcher(Enemy):
    points = POINTS_LATCHER
    contact_damage = 10
    _image = None

    def __init__(self, x, y=-8):
        if Latcher._image is None:
            Latcher._image = sprite_from_rows(ROWS, COLORS)
        super().__init__(Latcher._image, x, y, LATCHER_HP)
        self.latched = None               # (dx, dy) offset on the pod while clinging
        self.wobble = random.uniform(0, math.tau)

    def move(self, dt, world):
        pod = target_pod(world)
        if pod is None:
            self.latched = None
            target = world.ship
        else:
            target = pod
        if self.latched and pod:
            dx, dy = self.latched
            self.x, self.y = pod.x + dx, pod.y + dy
            pod.hurt(LATCHER_DRAIN * dt)
            return
        dx, dy = target.x - self.x, target.y - self.y
        d = math.hypot(dx, dy) or 1.0
        speed = LATCHER_SPEED
        self.x += (dx / d * speed + math.sin(self.time * 5 + self.wobble) * 30) * dt
        self.y += dy / d * speed * dt
        if pod and d < pod.RADIUS + 3:
            a = math.atan2(self.y - pod.y, self.x - pod.x)
            self.latched = (math.cos(a) * (pod.RADIUS + 2), math.sin(a) * (pod.RADIUS + 2))
            world.audio.play("spore")

    @property
    def offscreen(self):
        return self.time > 30

    def attack(self, dt, world):
        pass


def latcher_trio(game):
    x = random.uniform(40, LOW_W - 40)
    return [Latcher(x + dx, -8 - abs(dx)) for dx in (-16, 0, 16)]
