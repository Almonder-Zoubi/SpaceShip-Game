"""The concrete pickups: small repair kit, full repair, power core, coins."""
import math

from ..config.palette import COIN, POWER
from ..config.tuning import COIN_BIG, COIN_MAGNET, PICKUP_FALL, REPAIR_SMALL
from ..core.pixelart import sprite_from_rows
from .art import (BIG_COIN_FRAMES, COIN_FRAMES, KIT_FULL_ROWS, KIT_SMALL_ROWS, PICKUP_COLORS,
                  POWER_ROWS)
from .base import Pickup


class RepairKit(Pickup):
    """Small repair: restores REPAIR_SMALL hull points."""

    rows = KIT_SMALL_ROWS

    def apply(self, game):
        return f"+{int(game.ship.heal(REPAIR_SMALL))} HP"


class FullRepair(Pickup):
    """Rare gold kit: restores the hull completely."""

    rows = KIT_FULL_ROWS

    def apply(self, game):
        game.ship.heal(game.ship.max_hp)
        return "FULL REPAIR"


class PowerCore(Pickup):
    """Weapon power +1 for both weapons. Always homes in on the ship (never lost)."""

    rows = POWER_ROWS
    glow = POWER
    magnet = 400
    sound = "power_up"

    def apply(self, game):
        for weapon in game.weapons:
            weapon.power_up()
        return "POWER UP!"


class Coin(Pickup):
    """One coin (CREDIT). Pending until the level is won. homing=True: flies to the ship
    from anywhere (boss rewards)."""

    FRAMES = COIN_FRAMES
    value = 1
    glow = COIN
    sound = "coin"
    fanfare = False
    magnet = COIN_MAGNET
    _frames = {}

    def __init__(self, x, y, vx=0.0, vy=PICKUP_FALL, homing=False):
        super().__init__(x, y, vx, vy)
        if homing:
            self.magnet = 400
        cls = type(self)
        if cls not in Coin._frames:
            faces = [sprite_from_rows(rows, PICKUP_COLORS) for rows in cls.FRAMES]
            Coin._frames[cls] = (faces[0], faces[1], faces[2], faces[1])
        self.frames = Coin._frames[cls]

    def apply(self, game):
        game.collect_coins(self.value)
        return None

    def draw(self, surf):
        image = self.frames[int(self.time * 8) % 4]
        x = int(self.x) - image.get_width() // 2
        y = int(self.y) - image.get_height() // 2 + int(math.sin(self.time * 4))
        surf.blit(image, (x, y))


class BigCoin(Coin):
    """Worth COIN_BIG coins: boss rewards."""

    FRAMES = BIG_COIN_FRAMES
    value = COIN_BIG
