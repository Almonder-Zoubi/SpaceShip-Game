"""Weapon base class, the Hit record and the pixel-exact raycast."""
from ..config.loadouts import MK1
from ..config.tuning import POWER_MAX


class Hit:
    """One weapon impact: the game applies damage, push and effects.

    (dx, dy) is the shot's direction; push is px/s applied to a radius-4 rock.
    charges=False for hits from BLAST / ULTIMATE, so they don't recharge themselves.
    source: who fired it when that matters (a wingman gets XP for its kills).
    """
    __slots__ = ("target", "damage", "x", "y", "dx", "dy", "push", "continuous", "charges",
                 "source")

    def __init__(self, target, damage, x, y, dx, dy, push, continuous=False, charges=True,
                 source=None):
        self.target, self.damage, self.x, self.y = target, damage, x, y
        self.dx, self.dy, self.push = dx, dy, push
        self.continuous, self.charges, self.source = continuous, charges, source


class Weapon:
    """Base class. Subclasses implement update() and draw().

    loadout -- ship model stats (damage, heat); power -- 0..POWER_MAX, from POWER cores.
    """

    name = "WEAPON"
    heat = 0.0          # 0..1, shown in the HUD for weapons that can overheat
    overheated = False
    loadout = MK1
    power = 0
    rate = 1.0          # fire-rate multiplier (OVERDRIVE boost), set by the game each frame

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


def is_boss_part(target):
    """A boss, or a piece of one (the Leviathan's segments know their boss)."""
    return hasattr(target, "PHASES") or hasattr(target, "boss")
