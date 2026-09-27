"""Player weapons. Each weapon moves its own projectiles and reports hits to the game."""
import math
import random

import pygame

from .settings import (BLAST_DPS, BLAST_PUSH, BLAST_TIME, BLAST_WIDTH, FLAME, GUN_INTERVAL,
                       GUN_PUSH, GUN_SIDE_ANGLE, GUN_SPEED, GUN_SPREAD, LASER, LASER_COOL_RATE,
                       LASER_POWER_BONUS, LASER_POWER_COOL, LASER_PUSH, LASER_RANGE,
                       LASER_RESUME, LOW_H, LOW_W, MK1, POWER, POWER_MAX, SMOKE, SPARK, TRACER,
                       ULT_INTERVAL, ULT_MISSILE_DAMAGE, ULT_MISSILE_SPEED, ULT_TIME, ULT_TURN)


class Hit:
    """One weapon impact: the game applies damage, push and effects.

    (dx, dy) is the shot's direction; push is px/s applied to a radius-4 rock.
    charges=False for hits from BLAST / ULTIMATE, so they don't recharge themselves.
    """
    __slots__ = ("target", "damage", "x", "y", "dx", "dy", "push", "continuous", "charges")

    def __init__(self, target, damage, x, y, dx, dy, push, continuous=False, charges=True):
        self.target, self.damage, self.x, self.y = target, damage, x, y
        self.dx, self.dy, self.push = dx, dy, push
        self.continuous, self.charges = continuous, charges


class Weapon:
    """Base class. Subclasses implement update() and draw().

    loadout -- ship model stats (damage, heat); power -- 0..POWER_MAX, from POWER cores.
    """

    name = "WEAPON"
    heat = 0.0          # 0..1, shown in the HUD for weapons that can overheat
    overheated = False
    loadout = MK1
    power = 0

    def equip(self, loadout):
        self.loadout = loadout

    def power_up(self):
        self.power = min(POWER_MAX, self.power + 1)

    def update(self, dt, firing, ship, targets, fire):
        """Advance the weapon; returns a list of Hit."""
        raise NotImplementedError

    def draw(self, surf):
        raise NotImplementedError

    def reset(self):
        pass


class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "life")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = 1.5


class MachineGun(Weapon):
    """Rapid tracer rounds from alternating wing barrels. No overheating, some spread."""

    name = "GUN"
    BARRELS = ((-5.0, 1.0), (5.0, 1.0))      # ship-local positions (x right, y down)
    NOSE = (0.0, -12.0)

    def __init__(self):
        self.bullets = []
        self.reset()

    def reset(self):
        self.bullets.clear()
        self.cooldown = 0.0
        self.barrel = 0
        self.shots = 0
        self.power = 0

    def update(self, dt, firing, ship, targets, fire):
        self.cooldown -= dt
        if firing and self.cooldown <= 0:
            self.cooldown = GUN_INTERVAL
            self._volley(ship, fire)
        return self._move_bullets(dt, targets, fire)

    def _volley(self, ship, fire):
        """Power 0: alternating wing barrels. Power 1: + nose round every other shot.
        Power 2: + nose round every shot and angled side rounds every other shot."""
        self.shots += 1
        self._shoot(ship, fire, self.BARRELS[self.barrel], 0.0)
        self.barrel = 1 - self.barrel
        if self.power >= 2 or (self.power == 1 and self.shots % 2 == 0):
            self._shoot(ship, fire, self.NOSE, 0.0)
        if self.power >= 2 and self.shots % 2 == 1:
            for side, barrel in ((-1, self.BARRELS[0]), (1, self.BARRELS[1])):
                self._shoot(ship, fire, barrel, side * GUN_SIDE_ANGLE)

    def _shoot(self, ship, fire, barrel, offset):
        bx, by = ship.to_world(*barrel)
        a = ship.angle + offset + random.uniform(-GUN_SPREAD, GUN_SPREAD)   # 0 = straight up
        dx, dy = math.sin(a), -math.cos(a)
        self.bullets.append(Bullet(bx, by, dx * GUN_SPEED + ship.vx, dy * GUN_SPEED + ship.vy))
        for _ in range(3):   # muzzle flash
            fire.emit(bx + dx * 2, by + dy * 2, dx * random.uniform(20, 60) + ship.vx,
                      dy * random.uniform(20, 60) + ship.vy, random.uniform(0.03, 0.07), SPARK)

    def _move_bullets(self, dt, targets, fire):
        hits, alive = [], []
        for b in self.bullets:
            b.life -= dt
            hit = None
            for step in (0.5, 1.0):        # two sub-steps so fast bullets can't skip small rocks
                x, y = b.x + b.vx * dt * step, b.y + b.vy * dt * step
                for t in targets:
                    if abs(x - t.x) < t.bound and abs(y - t.y) < t.bound and t.contains(x, y):
                        speed = math.hypot(b.vx, b.vy) or 1.0
                        hit = Hit(t, self.loadout.gun_damage, x, y, b.vx / speed, b.vy / speed, GUN_PUSH)
                        break
                if hit:
                    break
            if hit:
                hits.append(hit)
                continue
            b.x += b.vx * dt
            b.y += b.vy * dt
            if b.life > 0 and -8 < b.x < LOW_W + 8 and -8 < b.y < LOW_H + 8:
                alive.append(b)
        self.bullets = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        head = POWER[1] if self.power else TRACER[0]
        for b in self.bullets:
            speed = math.hypot(b.vx, b.vy) or 1
            dx, dy = b.vx / speed, b.vy / speed
            surf.fill(head, (int(b.x) - 1, int(b.y) - 1, 2, 2), special_flags=add)        # hot head
            for i in range(1, 5):                                                          # fading tail
                color = TRACER[min(len(TRACER) - 1, i // 2 + 1)]
                surf.fill(color, (int(b.x - dx * i * 1.2), int(b.y - dy * i * 1.2), 1, 1),
                          special_flags=add)


class Laser(Weapon):
    """Continuous beam from the nose: instant, precise, but it overheats."""

    name = "LASER"

    def __init__(self):
        self.reset()

    def reset(self):
        self.power = 0
        self.heat = 0.0
        self.overheated = False
        self.active = False
        self.start = self.end = (0, 0)
        self.time = 0.0

    def update(self, dt, firing, ship, targets, fire):
        self.time += dt
        self.active = firing and not self.overheated
        if self.active:
            rate = self.loadout.laser_heat_rate * (1 - LASER_POWER_COOL * self.power)
            self.heat = min(1.0, self.heat + rate * dt)
            if self.heat >= 1.0:
                self.overheated = True
        else:
            self.heat = max(0.0, self.heat - LASER_COOL_RATE * dt)
            if self.overheated and self.heat <= LASER_RESUME:
                self.overheated = False
        if not self.active:
            return []

        ox, oy = ship.nose()
        dx, dy = ship.forward
        dist, target = raycast(ox, oy, dx, dy, LASER_RANGE, targets)
        self.start, self.end = (ox, oy), (ox + dx * dist, oy + dy * dist)
        if target is None:
            return []
        ex, ey = self.end
        for _ in range(2):   # sparks spray back from the impact point
            a = math.atan2(-dy, -dx) + random.uniform(-1.1, 1.1)
            s = random.uniform(30, 110)
            fire.emit(ex, ey, math.cos(a) * s, math.sin(a) * s, random.uniform(0.08, 0.2), LASER)
        dps = self.loadout.laser_dps * (1 + LASER_POWER_BONUS * self.power)
        return [Hit(target, dps * dt, ex, ey, dx, dy, LASER_PUSH * dt, continuous=True)]

    def draw(self, surf):
        if not self.active:
            return
        (sx, sy), (ex, ey) = self.start, self.end
        length = max(1, int(math.hypot(ex - sx, ey - sy)))
        dx, dy = (ex - sx) / length, (ey - sy) / length
        px, py = -dy, dx
        wobble = 1 if int(self.time * 30) % 2 else 0
        add = pygame.BLEND_ADD
        for i in range(length):
            x, y = sx + dx * i, sy + dy * i
            surf.fill(LASER[0], (int(x), int(y), 1, 1), special_flags=add)
            for side in (-1, 1):
                surf.fill(LASER[2], (int(x + px * side), int(y + py * side), 1, 1), special_flags=add)
                if self.power:                                 # powered beam is wider
                    surf.fill(LASER[1 + (self.power == 1)],
                              (int(x + px * side * 2), int(y + py * side * 2), 1, 1),
                              special_flags=add)
                if wobble and i % 3 == 0:
                    surf.fill(LASER[3], (int(x + px * side * 2), int(y + py * side * 2), 1, 1),
                              special_flags=add)
        pygame.draw.circle(surf, LASER[1], (int(sx), int(sy)), 1)               # muzzle
        pygame.draw.circle(surf, LASER[1], (int(ex), int(ey)), 2 + wobble, 1)   # impact ring


def raycast(ox, oy, dx, dy, max_dist, targets):
    """Distance to the first target pixel along a ray, and that target (or None)."""
    best, hit = max_dist, None
    for t in targets:
        rx, ry = t.x - ox, t.y - oy
        along = rx * dx + ry * dy
        if along < -t.bound or along - t.bound > best:
            continue
        if abs(rx * dy - ry * dx) > t.bound:          # perpendicular distance
            continue
        s = max(0.0, along - t.bound)
        stop = min(best, along + t.bound)
        while s < stop:
            if t.contains(ox + dx * s, oy + dy * s):
                best, hit = s, t
                break
            s += 1.0
    return best, hit


class Charged(Weapon):
    """Base for special weapons that fill a 0..1 meter from damage dealt, then fire."""

    duration = 1.0

    def __init__(self):
        self.reset()

    def reset(self):
        self.charge = 0.0
        self.active_time = 0.0
        self.time = 0.0

    @property
    def active(self):
        return self.active_time > 0

    @property
    def ready(self):
        return self.charge >= 1 and not self.active

    def add_charge(self, amount):
        """Returns True if this made the weapon ready."""
        if self.active or self.charge >= 1:
            return False
        self.charge = min(1.0, self.charge + amount)
        return self.charge >= 1

    def activate(self):
        if not self.ready:
            return False
        self.active_time = self.duration
        return True

    def _tick(self, dt):
        self.time += dt
        if self.active:
            self.active_time = max(0.0, self.active_time - dt)
            self.charge = self.active_time / self.duration      # meter drains while it fires


class Blast(Charged):
    """BLAST: when charged, holding fire unleashes a huge piercing beam from the nose for
    BLAST_TIME seconds. It destroys everything in front of the rocket, then recharges.
    Its colour follows the active weapon (golden plasma for the gun, blue for the laser)."""

    name = "BLAST"
    duration = BLAST_TIME

    def reset(self):
        super().reset()
        self.colors = TRACER
        self.start = self.end = (0, 0)

    def update(self, dt, firing, ship, targets, fire):
        self._tick(dt)
        if firing and self.charge >= 1 and not self.active:
            self.activate()
        if not self.active:
            return []
        ox, oy = ship.nose()
        dx, dy = ship.forward
        self.start, self.end = (ox, oy), (ox + dx * LASER_RANGE, oy + dy * LASER_RANGE)
        for _ in range(3):                                    # recoil sparks at the nose
            a = math.atan2(-dy, -dx) + random.uniform(-1.2, 1.2)
            fire.emit(ox, oy, math.cos(a) * 90, math.sin(a) * 90, 0.15, self.colors)
        hits = []
        for t in targets:
            rx, ry = t.x - ox, t.y - oy
            along = rx * dx + ry * dy
            if along < -t.bound or abs(rx * dy - ry * dx) > BLAST_WIDTH / 2 + t.bound * 0.8:
                continue
            hx, hy = ox + dx * along, oy + dy * along
            if random.random() < 0.5:
                fire.emit(hx, hy, random.uniform(-80, 80), random.uniform(-80, 80), 0.2, SPARK)
            hits.append(Hit(t, BLAST_DPS * dt, hx, hy, dx, dy, BLAST_PUSH * dt,
                            continuous=True, charges=False))
        return hits

    def draw(self, surf):
        if not self.active:
            return
        start, end = self.start, self.end
        grow = min(1.0, (self.duration - self.active_time) / 0.15)    # beam opens up quickly
        fade = min(1.0, self.active_time / 0.3)                       # and narrows at the end
        width = max(1, int(BLAST_WIDTH * grow * fade)) + (int(self.time * 30) % 2)
        pygame.draw.line(surf, self.colors[-1], start, end, width + 4)
        pygame.draw.line(surf, self.colors[-2], start, end, width)
        pygame.draw.line(surf, self.colors[1], start, end, max(1, width - 4))
        pygame.draw.line(surf, (255, 255, 255), start, end, max(1, width - 8))
        pygame.draw.circle(surf, self.colors[1], (int(start[0]), int(start[1])), width // 2 + 2)


class Missile:
    __slots__ = ("x", "y", "vx", "vy", "target", "life")

    def __init__(self, x, y, vx, vy, target):
        self.x, self.y, self.vx, self.vy, self.target = x, y, vx, vy, target
        self.life = 3.0


class Ultimate(Charged):
    """ULTIMATE (key T): a storm of homing missiles spread over every target on screen.
    Bigger targets (bosses) draw more missiles."""

    name = "ULTIMATE"
    duration = ULT_TIME

    def reset(self):
        super().reset()
        self.missiles = []
        self.timer = 0.0
        self.side = 1
        self.assigned = {}

    def activate(self):
        if super().activate():
            self.timer = 0.0
            self.assigned = {}
            return True
        return False

    def update(self, dt, firing, ship, targets, fire):
        self._tick(dt)
        visible = [t for t in targets if -t.bound < t.y < LOW_H and -t.bound < t.x < LOW_W + t.bound]
        if self.active and ship.alive:
            self.timer -= dt
            while self.timer <= 0:
                self.timer += ULT_INTERVAL
                self._launch(ship, visible, fire)
        return self._move(dt, visible, fire)

    def _pick(self, visible):
        """Spread missiles over all targets; each gets a share by its size."""
        if not visible:
            return None
        target = min(visible, key=lambda t: self.assigned.get(id(t), 0) / max(1.0, t.bound / 6))
        self.assigned[id(target)] = self.assigned.get(id(target), 0) + 1
        return target

    def _launch(self, ship, visible, fire):
        self.side = -self.side
        x, y = ship.to_world(self.side * 7, 2)
        rx, ry = ship.right
        fx, fy = ship.forward
        speed = random.uniform(90, 140)
        self.missiles.append(Missile(x, y, rx * self.side * speed + fx * 60,
                                     ry * self.side * speed + fy * 60, self._pick(visible)))
        fire.burst(x, y, 3, 40, 0.1, FLAME[:3], size=(1, 1))

    def _move(self, dt, visible, fire):
        hits, alive = [], []
        ids = {id(t) for t in visible}
        for m in self.missiles:
            m.life -= dt
            if m.target is None or id(m.target) not in ids:
                m.target = min(visible, key=lambda t: (t.x - m.x) ** 2 + (t.y - m.y) ** 2,
                               default=None)
            angle = math.atan2(m.vy, m.vx)
            if m.target is not None:
                want = math.atan2(m.target.y - m.y, m.target.x - m.x)
                turn = (want - angle + math.pi) % math.tau - math.pi
                angle += max(-ULT_TURN * dt, min(ULT_TURN * dt, turn))
            speed = min(ULT_MISSILE_SPEED, math.hypot(m.vx, m.vy) + 400 * dt)
            m.vx, m.vy = math.cos(angle) * speed, math.sin(angle) * speed
            m.x += m.vx * dt
            m.y += m.vy * dt
            fire.emit(m.x - m.vx * 0.02, m.y - m.vy * 0.02, -m.vx * 0.2 + random.uniform(-10, 10),
                      -m.vy * 0.2 + random.uniform(-10, 10), 0.18, FLAME[1:])
            hit = None
            for t in visible:
                if abs(m.x - t.x) < t.bound and abs(m.y - t.y) < t.bound and t.contains(m.x, m.y):
                    hit = Hit(t, ULT_MISSILE_DAMAGE, m.x, m.y, math.cos(angle), math.sin(angle),
                              25, charges=False)
                    break
            if hit:
                hits.append(hit)
                fire.burst(m.x, m.y, 12, 90, 0.35, FLAME, size=(1, 2))
                fire.burst(m.x, m.y, 4, 60, 0.6, SMOKE, size=(1, 2))
            elif m.life > 0 and -20 < m.x < LOW_W + 20 and -20 < m.y < LOW_H + 20:
                alive.append(m)
        self.missiles = alive
        return hits

    def draw(self, surf):
        add = pygame.BLEND_ADD
        for m in self.missiles:
            speed = math.hypot(m.vx, m.vy) or 1
            dx, dy = m.vx / speed, m.vy / speed
            for i in range(1, 5):                          # hot body fading back to orange
                surf.fill(FLAME[min(i, 3)], (int(m.x - dx * i), int(m.y - dy * i), 2, 2),
                          special_flags=add)
            surf.fill((255, 255, 255), (int(m.x), int(m.y), 2, 2), special_flags=add)
