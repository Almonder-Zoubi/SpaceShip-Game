"""Boss 9: THE TWINS, ORA and ZEN (level 9) — two ships linked by a deadly tether that fight
together with the black hole."""
import math
import random

import pygame

from ..config.display import LOW_W
from ..config.palette import DANGER, SPARK
from ..core.particles import Shockwave
from ..core.pixelart import CharCanvas
from ..minions.bullets import bullet, shoot
from ..ui.popup import Popup
from .art import HULL_COLORS, build_boss_sprite
from .base import Boss

TWIN_COLORS = {
    "ORA": {**HULL_COLORS, "E": (80, 220, 255), "e": (30, 110, 170), "Y": (200, 250, 255),
            "y": (80, 160, 220)},
    "ZEN": {**HULL_COLORS, "E": (255, 110, 200), "e": (160, 40, 120), "Y": (255, 220, 240),
            "y": (220, 120, 180)},
}
HALF_W, HALF_H = 15, 28


def _twin_half():
    """A sleek dart: swept wing with a coloured edge, a glowing core near the nose."""
    c = CharCanvas(HALF_W, HALF_H)
    c.poly([(14, 0), (8, 10), (0, 20), (2, 24), (10, 22), (14, 27)], "M")
    c.line(14, 0, 8, 10, "W")
    c.line(8, 10, 0, 20, "L")
    c.line(0, 20, 2, 24, "E")
    c.line(2, 24, 10, 22, "e")
    c.rect(11, 4, 14, 24, "H")
    c.line(12, 5, 12, 23, "L")
    c.rect(12, 14, 14, 19, "G")
    c.rect(13, 15, 14, 18, "E")
    c.set(13, 16, "Y")
    return c.rows()


class Twin:
    """ORA or ZEN: its own health; knocked down, it revives unless the other goes down too."""

    REVIVE = 8.0

    def __init__(self, boss, name, image):
        self.boss, self.name, self.image = boss, name, image
        self.mask = pygame.mask.from_surface(image)
        self.white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.x = self.y = 0.0
        self.hp = self.max_hp = 1.0
        self.down = 0.0                     # seconds until it revives (0 = fighting)
        self.flash = 0.0

    @property
    def alive(self):
        return self.down <= 0

    @property
    def bound(self):
        return max(self.image.get_size()) / 2 + 1

    @property
    def topleft(self):
        return int(self.x - self.image.get_width() / 2), int(self.y - self.image.get_height() / 2)

    def contains(self, px, py):
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        w, h = self.mask.get_size()
        return 0 <= mx < w and 0 <= my < h and self.mask.get_at((mx, my))

    def overlaps(self, ship):
        sx, sy = ship.topleft
        left, top = self.topleft
        return ship.mask.overlap(self.mask, (left - sx, top - sy)) is not None


def _segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - dx * t, py - ay - dy * t)


class Twins(Boss):
    """Boss 9. Two ships, one health bar (each has half); a laser TETHER links them.
    If one goes down, the other revives it within 8 s — unless it goes down too.

    Phase 1 (calm)    -- they orbit the black hole on opposite sides; their aimed shots bend
                         around it
    Phase 2 (angry)   -- x1.2; they SWAP sides in a crossing dash through the SLINGSHOT
                         ring, and fire bullets into the hole (they come back out when it
                         flips to a WHITE HOLE)
    Phase 3 (furious) -- x1.4; the tether spins like a propeller around the hole, and the
                         hole grows
    The idea: damage has to be balanced, and gravity is both their weapon and yours.
    """

    EPITHET = "ORA AND ZEN"
    PHASES = 3
    ENTER_TIME = 3.0
    RAGE = (1.0, 1.2, 1.4)
    PATTERNS = (
        (("volley", 3.0), ("spread", 2.4), ("rest", 1.0)),
        (("swap", 1.2), ("volley", 2.6), ("feed", 2.0), ("spread", 2.2), ("rest", 0.6)),
        (("propeller", 4.0), ("volley", 2.2), ("spread", 2.0), ("rest", 0.4)),
    )
    ORBIT_X, ORBIT_Y = 76, 34
    VOLLEY_INTERVAL, VOLLEY_SPEED = 0.7, 125
    SPREAD_INTERVAL, SPREAD_SHOTS, SPREAD_SPEED = 0.8, 5, 100
    FEED_INTERVAL = 0.25
    TETHER_X = 1.5                   # touching the tether hurts like this many bullets
    REVIVE_SHARE = 0.35              # a revived twin comes back with this much of its health
    # Phase 1 aimed shots per second at a rocket sitting still: every volley shot of both
    # twins and the middle shot of each spread.
    AIMED_RATE = ((3.0 / VOLLEY_INTERVAL) * 2 + (2.4 / SPREAD_INTERVAL) * 2) / (3.0 + 2.4 + 1.0)

    _sprites = None

    @classmethod
    def prebuild(cls):
        if cls._sprites is None:
            cls._sprites = {name: build_boss_sprite(_twin_half(), colors)
                            for name, colors in TWIN_COLORS.items()}
        return cls._sprites

    def __init__(self, spec):
        sprites = self.prebuild()
        super().__init__(spec, sprites["ORA"], {}, [(10, 1), (21, 1)])
        self.bullet_damage = spec.dps / self.AIMED_RATE
        self.twins = [Twin(self, name, sprites[name]) for name in ("ORA", "ZEN")]
        for twin in self.twins:
            twin.hp = twin.max_hp = self.max_hp / 2
        self.orbit = 0.0
        self.swap_from = 0.0
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.6
        self.turn = 0
        self.center = (LOW_W / 2, 72.0)
        self._went_down = None           # a twin went down this frame (effects in update)
        self._layout()

    # --- pieces -------------------------------------------------------------------------
    def parts(self):
        return [t for t in self.twins if t.alive]

    def hit_part(self, part, amount, flash=True, source=None):
        if not part.alive or self.state != "fight" or self.roar > 0:
            return
        before = self.hp
        self.damage(min(amount, part.hp), flash)     # phases and death work on the sum
        part.hp -= before - self.hp
        part.flash = 0.05 if flash else part.flash
        if part.hp <= 0.5 and self.state == "fight":
            part.hp = 0.0
            part.down = Twin.REVIVE
            self._went_down = part

    def contains(self, px, py):
        return any(t.contains(px, py) for t in self.parts())

    def collides_with(self, ship):
        return any(t.overlaps(ship) for t in self.parts())

    def random_hull_point(self):
        t = random.choice(self.twins)
        return t.x + random.uniform(-10, 10), t.y + random.uniform(-10, 10)

    @property
    def revive_text(self):
        """(text, x, y) over a twin that is down, or None (the screen draws it)."""
        down = [t for t in self.twins if not t.alive]
        if not down or not self.fighting:
            return None
        t = down[0]
        return f"{t.name} REVIVES {int(t.down) + 1}", t.x, t.y - 22

    def tether(self):
        a, b = self.twins
        return (a.x, a.y, b.x, b.y) if a.alive and b.alive else None

    def on_phase(self):
        self.pattern_index = 0
        self.attack_time = 0.0
        self.fire_timer = 0.5

    def _pattern(self):
        pattern = self.PATTERNS[self.phase]
        return pattern[self.pattern_index % len(pattern)]

    def _layout(self):
        cx, cy = self.center
        name, _ = self._pattern() if self.state == "fight" else ("", 0)
        rx = 58 if name == "propeller" else self.ORBIT_X
        ry = 58 if name == "propeller" else self.ORBIT_Y
        for i, twin in enumerate(self.twins):
            a = self.orbit + math.pi * i
            twin.x = cx + math.cos(a) * rx
            twin.y = cy + math.sin(a) * ry
        self.x, self.y = cx, cy

    # --- update -------------------------------------------------------------------------
    def update(self, dt, world):
        hole = world.hazard if hasattr(world.hazard, "grow") else None
        if hole:
            self.center = (hole.x, hole.y)
            hole.grow = 1.35 if self.phase == 2 and self.fighting else 1.0
        went_down = self._went_down
        if went_down:
            self._went_down = None
            world.explosion(went_down.x, went_down.y, size=1.4)
            world.popups.append(Popup(f"{went_down.name} IS DOWN!", went_down.x,
                                      went_down.y - 20, DANGER))
        for twin in self.twins:
            twin.flash = max(0.0, twin.flash - dt)
            if twin.down > 0 and self.fighting:
                twin.down = max(0.0, twin.down - dt)
                if twin.down == 0:                     # revived by the other
                    twin.hp = twin.max_hp * self.REVIVE_SHARE
                    self.hp += twin.hp
                    world.shockwaves.append(Shockwave(twin.x, twin.y, max_radius=30,
                                                      duration=0.4, color=SPARK[1]))
                    world.audio.play("power_up")
        tether = self.tether()
        ship = world.ship
        if tether and self.fighting and ship.alive:
            if _segment_distance(ship.x, ship.y, *tether) < 2 + ship.w * 0.3:
                world.hurt_ship(self.bullet_damage * self.TETHER_X, ship.x, ship.y)
        result = super().update(dt, world)
        if self.state != "fight":
            self._layout()
        return result

    def enter(self, k):
        cx, cy = self.center
        self.orbit = -math.pi / 2 * (1 - k)
        self.center = (cx, cy)
        self._layout()
        for twin in self.twins:                        # they fly in from above
            twin.y -= (1 - k) ** 2 * 150

    def fight(self, dt, world):
        rate = self.RAGE[self.phase]
        name, duration = self._pattern()
        self.attack_time += dt
        if name == "swap":                             # dash across through the ring
            k = min(1.0, self.attack_time / duration)
            self.orbit = self.swap_from + math.pi * (k * k * (3 - 2 * k))
        elif name == "propeller":
            self.orbit += 1.3 * dt * rate
        else:
            self.orbit += 0.45 * dt * rate
        self._layout()
        if self.attack_time >= duration:
            self.attack_time = 0.0
            self.pattern_index += 1
            self.fire_timer = 0.3
            self.swap_from = self.orbit
            return
        self.fire_timer -= dt * rate
        if self.fire_timer > 0 or name in ("rest", "swap", "propeller"):
            return
        getattr(self, "_" + name)(world)

    # --- attacks ------------------------------------------------------------------------
    def _volley(self, world):
        self.fire_timer = self.VOLLEY_INTERVAL
        for twin in self.parts():
            shoot(world, twin.x, twin.y + 8, math.atan2(world.ship.y - twin.y, world.ship.x - twin.x),
                  self.VOLLEY_SPEED, self.bullet_damage)

    def _spread(self, world):
        self.fire_timer = self.SPREAD_INTERVAL
        for twin in self.parts():
            aim = math.atan2(world.ship.y - twin.y, world.ship.x - twin.x)
            for i in range(self.SPREAD_SHOTS):
                world.enemy_bullets.append(bullet(twin.x, twin.y + 8,
                                                  aim + (i - self.SPREAD_SHOTS // 2) * 0.22,
                                                  self.SPREAD_SPEED, self.bullet_damage))
        world.audio.play("enemy_shot")

    def _feed(self, world):
        """Fire into the hole: those bullets come back out with the next WHITE HOLE."""
        self.fire_timer = self.FEED_INTERVAL
        cx, cy = self.center
        for twin in self.parts():
            world.enemy_bullets.append(bullet(twin.x, twin.y,
                                              math.atan2(cy - twin.y, cx - twin.x), 90,
                                              self.bullet_damage))

    # --- draw ---------------------------------------------------------------------------
    def draw(self, surf):
        if self.state == "dead":
            return
        tether = self.tether()
        if tether and self.state in ("fight", "enter"):
            ax, ay, bx, by = tether
            wobble = int(self.attack_time * 30) % 2
            pygame.draw.line(surf, (200, 40, 150), (int(ax), int(ay)), (int(bx), int(by)), 3)
            pygame.draw.line(surf, (255, 220, 250) if wobble else (255, 160, 230),
                             (int(ax), int(ay)), (int(bx), int(by)))
        for twin in self.twins:
            left, top = twin.topleft
            if self.state == "dying" or self.roar > 0:
                left += random.randint(-1, 1)
            if not twin.alive:
                if int(twin.down * 6) % 2 == 0:                    # blinking wreck
                    surf.blit(twin.image, (left, top), special_flags=pygame.BLEND_MULT)
                continue
            if self.roar > 0 and int(self.roar * 10) % 2:
                surf.blit(self.red, (left, top))
            else:
                surf.blit(twin.white if twin.flash > 0 else twin.image, (left, top))

