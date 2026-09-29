"""Diver: kamikaze minion (level 4). Drops in, locks on, then dives at the rocket."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER, FLAME_LEAN
from ..config.tuning import (DIVER_ACCEL, DIVER_AIM_FREEZE, DIVER_CONTACT_DAMAGE,
                             DIVER_ENTER_SPEED, DIVER_HP, DIVER_LOCK, DIVER_SPEED, POINTS_DIVER)
from ..core.pixelart import rotate_pixel_art
from .base import Enemy

# Nose down (the direction it dives in when the frame angle is 0).
DIVER_ROWS = (
    "K.........K",
    "KMK.....KMK",
    ".KMK...KMK.",
    ".KMLKKKLMK.",
    "..KLLQLLK..",
    "..KLQqQLK..",
    "...KLQLK...",
    "...KLLLK...",
    "....KLK....",
    "....KWK....",
    ".....K.....",
)
DIVER_COLORS = {
    "K": (18, 14, 30), "M": (58, 70, 112), "L": (150, 168, 206), "W": (240, 244, 255),
    "Q": (255, 64, 64), "q": (255, 214, 200),
}
DIVER_FRAMES = 16                      # rotation steps (22.5 degrees apart)


class Diver(Enemy):
    """Kamikaze: drops in, hovers while it locks on (blinking aim line), then dives in a
    straight line at where the rocket was. No guns: shoot it early or sidestep the dive."""

    points = POINTS_DIVER
    contact_damage = DIVER_CONTACT_DAMAGE
    _frames = None                     # [(image, mask, white)] per rotation step

    @classmethod
    def prebuild(cls):
        """Rotation frames, built once (the game calls this at startup)."""
        if cls._frames is None:
            cls._frames = []
            for i in range(DIVER_FRAMES):
                image = rotate_pixel_art(DIVER_ROWS, DIVER_COLORS, 360 * i / DIVER_FRAMES)
                mask = pygame.mask.from_surface(image)
                white = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
                cls._frames.append((image, mask, white))

    def __init__(self, x, hover_y, delay=0.0):
        Diver.prebuild()
        super().__init__(Diver._frames[0][0], x, -8, DIVER_HP)
        self.hover_y = hover_y
        self.state = "enter"                # enter -> lock -> dive
        self.lock_time = DIVER_LOCK + delay
        self.aim = None                     # (x, y) it will dive at
        self.dx, self.dy, self.speed = 0.0, 1.0, 0.0

    def _face(self, dx, dy):
        """Show the rotation frame closest to direction (dx, dy)."""
        turn = math.atan2(dy, dx) - math.pi / 2          # frame 0 points down
        i = round(turn / math.tau * DIVER_FRAMES) % DIVER_FRAMES
        self.image, self.mask, self.white = Diver._frames[i]
        self.w, self.h = self.image.get_size()

    @property
    def offscreen(self):
        return super().offscreen or (self.state == "dive" and self.y < -20)

    def move(self, dt, world):
        ship = world.ship
        if self.state == "enter":
            self.y += DIVER_ENTER_SPEED * dt
            if self.y >= self.hover_y:
                self.state = "lock"
                world.audio.play("lock_on")
        elif self.state == "lock":
            self.lock_time -= dt
            self.y = self.hover_y + math.sin(self.time * 5) * 1.5
            if ship.alive and (self.aim is None or self.lock_time > DIVER_AIM_FREEZE):
                self.aim = ship.x, ship.y
            if self.aim:
                self._face(self.aim[0] - self.x, self.aim[1] - self.y)
            if self.lock_time <= 0:
                ax, ay = self.aim or (self.x, self.y + 1)
                dist = math.hypot(ax - self.x, ay - self.y) or 1.0
                self.dx, self.dy = (ax - self.x) / dist, (ay - self.y) / dist
                self.state = "dive"
        else:
            self.speed = min(DIVER_SPEED, self.speed + DIVER_ACCEL * dt)
            self.x += self.dx * self.speed * dt
            self.y += self.dy * self.speed * dt
            if random.random() < 40 * dt:                  # cold exhaust trail
                world.fire.emit(self.x - self.dx * 6, self.y - self.dy * 6,
                                -self.dx * 40 + random.uniform(-10, 10),
                                -self.dy * 40 + random.uniform(-10, 10), 0.25, FLAME_LEAN)

    def attack(self, dt, world):
        pass                                               # it IS the attack

    def draw(self, surf):
        if self.state == "lock" and self.aim and int(self.lock_time * 10) % 2 == 0:
            # Dotted aim line: where it's going to dive.
            ax, ay = self.aim
            dist = math.hypot(ax - self.x, ay - self.y)
            for i in range(2, int(dist / 5)):
                k = i * 5 / dist
                surf.fill(DANGER, (int(self.x + (ax - self.x) * k), int(self.y + (ay - self.y) * k),
                                   1, 1))
        super().draw(surf)


def diver_squad(count=3):
    """A few divers spread across the top; they lock on one after another."""
    slots = random.sample(range(count + 2), count)
    step = (LOW_W - 60) / (count + 2)
    return [Diver(30 + step * (slot + 0.5) + random.uniform(-10, 10),
                  hover_y=random.uniform(34, 62), delay=i * 0.4)
            for i, slot in enumerate(slots)]
