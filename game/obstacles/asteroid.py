"""Asteroids: falling, spinning, destructible rocks (plain rock and brittle ice)."""
import math
import random

from ..config.display import LOW_H, LOW_W
import pygame

from ..config.tuning import (COMET_SPEED, MARROW_REGROW, PHASE_ROCK_CYCLE, ROCK_HP_BASE,
                             ROCK_HP_PER_AREA, ROCK_MIN_FALL, ROCK_SPLIT_RADIUS, WRECK_HP)
from ..core.pixelart import make_glow

HIT_FLASH = 0.06   # seconds a rock shows white after being hit


class Asteroid:
    """A rock drawn from pre-rendered AsteroidArt frames. Bigger rocks have more hp.

    Subclasses change how tough a rock is and how it breaks (see IceRock).
    """

    SPLIT_RADIUS = ROCK_SPLIT_RADIUS   # rocks at least this big break into fragments
    HP_FACTOR = 1.0
    SPARKLE = False                    # glittering shards when it breaks
    EXPLODES = False                   # blows up nearby rocks and minions (magma)
    REFRACTS = False                   # splits a laser beam (crystal)
    METAL = False                      # wreck metal: clangs, drops extra coins
    REGROWS = False                    # reef bone: leaves a marrow core that grows back
    FRAGMENT = None                    # class of its fragments (None = the same class)

    def __init__(self, art, x, y, vx, vy, spin, hp_scale=1.0):
        self.art = art
        self.x, self.y = float(x), float(y)       # centre
        self.vx, self.vy = vx, vy
        self.angle = random.uniform(0, math.tau)
        self.spin = spin
        self.hp_scale = hp_scale                   # the level's rock toughness
        self.max_hp = ((ROCK_HP_BASE + ROCK_HP_PER_AREA * art.radius ** 2) * self.HP_FACTOR
                       * hp_scale)
        self.hp = self.max_hp
        self.flash = 0.0

    @property
    def radius(self):
        return self.art.radius

    @property
    def splits(self):
        return self.radius >= self.SPLIT_RADIUS

    def fragments(self):
        """How it breaks: (count, min radius, max radius, (min, max) kick speed)."""
        r = self.radius
        return 2 if r < 12 else 3, max(4, int(r * 0.4)), max(4, int(r * 0.6)), (25, 55)

    def break_sound(self):
        return "rock_break_big" if self.splits else "rock_break"

    @property
    def bound(self):
        """Radius of a circle that surely contains the rock (for quick rejects)."""
        return self.art.max_r + 1

    @property
    def frame_index(self):
        return int(self.angle / math.tau * self.art.FRAMES) % self.art.FRAMES

    @property
    def topleft(self):
        half = self.art.size // 2
        return int(self.x) - half, int(self.y) - half

    @property
    def mask(self):
        return self.art.masks[self.frame_index]

    @property
    def offscreen(self):
        size = self.art.size
        return self.y - size > LOW_H or self.x < -size or self.x > LOW_W + size

    @property
    def destroyed(self):
        return self.hp <= 0

    def update(self, dt, world_speed):
        self.x += self.vx * dt
        self.y += self.vy * world_speed * dt
        self.angle = (self.angle + self.spin * dt) % math.tau
        self.flash = max(0.0, self.flash - dt)

    def damage(self, amount, flash=True):
        """Continuous damage (laser) passes flash=False, or the rock would stay white."""
        self.hp -= amount
        if flash:
            self.flash = HIT_FLASH

    def push(self, dx, dy, amount):
        """Knock the rock along (dx, dy); bigger rocks are heavier and move less.

        Shots from below slow the fall, but a rock never stops or flies back up.
        """
        k = amount * 4 / self.radius
        self.vx += dx * k
        self.vy = max(ROCK_MIN_FALL, self.vy + dy * k)

    def contains(self, px, py):
        """Pixel-exact point test (used by bullets and the laser)."""
        left, top = self.topleft
        mx, my = int(px) - left, int(py) - top
        size = self.art.size
        return 0 <= mx < size and 0 <= my < size and self.mask.get_at((mx, my))

    def collides_with(self, ship):
        sx, sy = ship.topleft
        ax, ay = self.topleft
        return ship.mask.overlap(self.mask, (ax - sx, ay - sy)) is not None

    def draw(self, surf):
        if self.flash > 0:
            white = self.mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
            surf.blit(white, self.topleft)
        else:
            surf.blit(self.art.frames[self.frame_index], self.topleft)


class IceRock(Asteroid):
    """Brittle ice: less hp, and even medium rocks shatter into a spray of fast shards."""

    SPLIT_RADIUS = 7
    HP_FACTOR = 0.6
    SPARKLE = True

    def fragments(self):
        r = self.radius
        return 3 if r < 11 else 4, 4, max(4, int(r * 0.45)), (45, 85)

    def break_sound(self):
        return "ice_break"


class MagmaRock(Asteroid):
    """Glowing magma: when it breaks it explodes and damages rocks and minions nearby,
    so one shot can set off a chain reaction."""

    EXPLODES = True
    _glows = {}

    def break_sound(self):
        return "magma_burst"

    def draw(self, surf):
        super().draw(surf)
        r = self.radius + 3
        if r not in MagmaRock._glows:
            MagmaRock._glows[r] = make_glow(r, (200, 70, 20), 0.55)
        pulse = 0.6 + 0.4 * math.sin(self.angle * 3 + self.x * 0.05)
        glow = MagmaRock._glows[r]
        if pulse > 0.5:
            surf.blit(glow, (int(self.x) - r, int(self.y) - r), special_flags=pygame.BLEND_ADD)


class CrystalRock(Asteroid):
    """Crystal: a laser beam hitting it splits into several beams (flow/combat.py)."""

    REFRACTS = True
    SPARKLE = True

    def break_sound(self):
        return "ice_break"

    def draw(self, surf):
        super().draw(surf)
        if int(self.angle * 4 + self.x) % 7 == 0:           # a glint now and then
            x, y = int(self.x) - self.radius // 3, int(self.y) - self.radius // 3
            surf.fill((255, 255, 255), (x, y - 1, 1, 3), special_flags=pygame.BLEND_ADD)
            surf.fill((255, 255, 255), (x - 1, y, 3, 1), special_flags=pygame.BLEND_ADD)


class WreckChunk(Asteroid):
    """A chunk of a dead battleship: tough metal that clangs and drops extra coins."""

    METAL = True
    HP_FACTOR = WRECK_HP

    def fragments(self):
        r = self.radius
        return 2, max(4, int(r * 0.45)), max(4, int(r * 0.6)), (20, 45)

    def break_sound(self):
        return "metal_break"


class Comet(IceRock):
    """A comet: icy, fast, falls at a slant and drags a glowing tail."""

    FRAGMENT = IceRock

    def __init__(self, art, x, y, vx, vy, spin, hp_scale=1.0):
        super().__init__(art, x, y, vx * 3, vy * COMET_SPEED, spin, hp_scale)
        self.tail = []

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.tail.append((self.x, self.y))
        del self.tail[:-10]

    def draw(self, surf):
        for i, (x, y) in enumerate(self.tail[:-1]):
            k = (i + 1) / len(self.tail)
            c = (int(90 * k), int(150 * k), int(220 * k))
            r = max(1, int(self.radius * 0.6 * k))
            pygame.draw.circle(surf, c, (int(x), int(y)), r)
        super().draw(surf)


class BoneRock(Asteroid):
    """Reef bone (galaxy 2): a big one doesn't split. It leaves a pulsing marrow core that
    grows the whole rock back in MARROW_REGROW seconds, unless you finish it."""

    REGROWS = True
    HP_FACTOR = 0.9

    @property
    def splits(self):
        return False


class MarrowCore(Asteroid):
    """What is left of a bone rock: small, soft, and it heals into the rock again."""

    HP_FACTOR = 1.6

    def __init__(self, art, rock):
        super().__init__(art, rock.x, rock.y, rock.vx * 0.5, max(ROCK_MIN_FALL, rock.vy * 0.6),
                         rock.spin * 0.3, rock.hp_scale)
        self.big_art = rock.art
        self.grow = 0.0

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.grow += dt

    def transform(self):
        """The world swaps this in when it returns a rock: the bone has grown back."""
        if self.grow < MARROW_REGROW:
            return None
        return BoneRock(self.big_art, self.x, self.y, self.vx, self.vy, self.spin, self.hp_scale)

    def draw(self, surf):
        super().draw(surf)
        k = self.grow / MARROW_REGROW                        # a ring that closes as it heals
        r = int(self.radius + 14 * (1 - k)) + 2
        if int(self.grow * (4 + 10 * k)) % 2 == 0:
            pygame.draw.circle(surf, (220, 60, 80), (int(self.x), int(self.y)), r, 1)


class PhaseRock(Asteroid):
    """Mirror chrome (galaxy 2): solid for a while, then a ghost that shots and the rocket
    pass through. Its outline blinks for a moment before it turns solid again."""

    def __init__(self, art, x, y, vx, vy, spin, hp_scale=1.0):
        super().__init__(art, x, y, vx, vy, spin, hp_scale)
        self.cycle = random.uniform(0, sum(PHASE_ROCK_CYCLE))

    @property
    def solid(self):
        return self.cycle % sum(PHASE_ROCK_CYCLE) < PHASE_ROCK_CYCLE[0]

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.cycle += dt

    def contains(self, px, py):
        return self.solid and super().contains(px, py)

    def collides_with(self, ship):
        return self.solid and super().collides_with(ship)

    def draw(self, surf):
        if self.solid:
            super().draw(surf)
            return
        t = self.cycle % sum(PHASE_ROCK_CYCLE) - PHASE_ROCK_CYCLE[0]     # seconds a ghost
        soon = PHASE_ROCK_CYCLE[1] - t < 0.45
        ghost = self.art.frames[self.frame_index].copy()
        ghost.fill((255, 255, 255, 60), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(ghost, self.topleft)
        if soon and int(self.cycle * 16) % 2 == 0:
            left, top = self.topleft
            for x, y in self.mask.outline()[::2]:
                surf.fill((255, 255, 255), (left + x, top + y, 1, 1))


ROCK_KINDS = {"ice": IceRock, "magma": MagmaRock,          # palette name -> rock class
              "crystal": CrystalRock, "wreck": WreckChunk, "comet": Comet, "reef": BoneRock,
              "chrome": PhaseRock}


def rock_class(palette_name):
    return ROCK_KINDS.get(palette_name, Asteroid)
