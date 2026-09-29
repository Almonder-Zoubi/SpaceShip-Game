"""Particles and screen effects: flames, smoke, debris, shockwaves, shake."""
import math
import random

import pygame

from .pixelart import ramp


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "colors", "size", "drag")

    def __init__(self, x, y, vx, vy, life, colors, size, drag):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.colors, self.size, self.drag = colors, size, drag


class ParticleSystem:
    """A pool of square pixel particles whose colour follows a ramp over their life."""

    def __init__(self, additive=False):
        self.additive = additive
        self.particles = []

    def emit(self, x, y, vx, vy, life, colors, size=1, drag=0.0):
        self.particles.append(Particle(x, y, vx, vy, life, colors, size, drag))

    def burst(self, x, y, count, speed, life, colors, size=(1, 2), drag=2.0):
        """Radial explosion of `count` particles with randomised speed and life."""
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(speed * 0.2, speed)
            self.emit(x, y, math.cos(a) * s, math.sin(a) * s,
                      random.uniform(life * 0.4, life), colors,
                      random.randint(*size), drag)

    def update(self, dt, scroll=0.0):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            damp = max(0.0, 1 - p.drag * dt)
            p.vx *= damp
            p.vy *= damp
            p.x += p.vx * dt
            p.y += (p.vy + scroll) * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surf):
        flags = pygame.BLEND_ADD if self.additive else 0
        for p in self.particles:
            age = 1 - p.life / p.max_life
            size = p.size if age < 0.6 else max(1, p.size - 1)
            surf.fill(ramp(p.colors, age), (int(p.x), int(p.y), size, size), special_flags=flags)

    def clear(self):
        self.particles.clear()


class Shockwave:
    """Expanding pixel ring."""

    def __init__(self, x, y, max_radius=40, duration=0.45, color=(255, 230, 170)):
        self.x, self.y = x, y
        self.max_radius, self.duration, self.color = max_radius, duration, color
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.duration

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        k = self.t / self.duration
        radius = int(2 + self.max_radius * (1 - (1 - k) ** 3))
        fade = 1 - k
        color = tuple(int(c * fade) for c in self.color)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), radius, 1)


class ScreenShake:
    """Trauma-based shake: add trauma on impact, offset grows with trauma^2."""

    def __init__(self, max_offset=6, decay=1.6):
        self.trauma = 0.0
        self.max_offset, self.decay = max_offset, decay
        self.scale = 1.0          # options: "reduce shake" lowers this

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount * self.scale)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - self.decay * dt)

    def offset(self):
        k = self.trauma ** 2 * self.max_offset
        return round(random.uniform(-k, k)), round(random.uniform(-k, k))
