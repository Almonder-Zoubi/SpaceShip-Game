"""Ship models the player flies. Each level hands out one (MK I -> MK II -> MK III -> MK IV)."""
from dataclasses import dataclass

from .tuning import GUN_DAMAGE, GUN_INTERVAL, LASER_DPS, LASER_HEAT_RATE, SHIP_MAX_HP, SHIP_MAX_SPEED


@dataclass(frozen=True)
class Loadout:
    """Player ship model: hull, speed and weapon strength."""
    name: str
    max_hp: int
    max_speed: float
    gun_damage: float
    laser_dps: float
    laser_heat_rate: float
    colors: str = "mk1"           # key into player.hulls paint jobs
    blast: bool = False           # charged BLAST beam (MK III)
    ultimate: bool = False        # T: missile storm (MK III)

    @property
    def gun_dps(self):
        """Machine gun with every bullet hitting (no power-ups) — the boss balance baseline."""
        return self.gun_damage / GUN_INTERVAL


MK1 = Loadout("MK I", max_hp=SHIP_MAX_HP, max_speed=SHIP_MAX_SPEED, gun_damage=GUN_DAMAGE,
              laser_dps=LASER_DPS, laser_heat_rate=LASER_HEAT_RATE)
MK2 = Loadout("MK II", max_hp=150, max_speed=145, gun_damage=7, laser_dps=110,
              laser_heat_rate=0.32, colors="mk2")
MK3 = Loadout("MK III", max_hp=200, max_speed=150, gun_damage=9, laser_dps=140,
              laser_heat_rate=0.28, colors="mk3", blast=True, ultimate=True)
MK4 = Loadout("MK IV", max_hp=250, max_speed=155, gun_damage=11, laser_dps=170,
              laser_heat_rate=0.25, colors="mk4", blast=True, ultimate=True)
