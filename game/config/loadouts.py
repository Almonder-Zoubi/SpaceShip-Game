"""Ship models the player flies. Each level hands out one (MK I -> MK II -> ... -> MK X)."""
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
    charge_rate: float = 1.0      # BLAST / ULTIMATE charge multiplier (CHARGE upgrade)

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
MK5 = Loadout("MK V", max_hp=300, max_speed=158, gun_damage=13, laser_dps=200,
              laser_heat_rate=0.24, colors="mk5", blast=True, ultimate=True)
MK6 = Loadout("MK VI", max_hp=350, max_speed=160, gun_damage=15, laser_dps=230,
              laser_heat_rate=0.23, colors="mk6", blast=True, ultimate=True)
MK7 = Loadout("MK VII", max_hp=400, max_speed=162, gun_damage=17, laser_dps=260,
              laser_heat_rate=0.22, colors="mk7", blast=True, ultimate=True)
MK8 = Loadout("MK VIII", max_hp=450, max_speed=164, gun_damage=19, laser_dps=290,
              laser_heat_rate=0.21, colors="mk8", blast=True, ultimate=True)
MK9 = Loadout("MK IX", max_hp=500, max_speed=166, gun_damage=21, laser_dps=320,
              laser_heat_rate=0.2, colors="mk9", blast=True, ultimate=True)
MK10 = Loadout("MK X", max_hp=550, max_speed=168, gun_damage=23, laser_dps=350,
               laser_heat_rate=0.19, colors="mk10", blast=True, ultimate=True)
# Galaxy 2: +30 HP / +2 gun per level (galaxy 1 grew +50 / +2): the enemy grows faster.
MK11 = Loadout("MK XI", max_hp=580, max_speed=170, gun_damage=25, laser_dps=375,
               laser_heat_rate=0.19, colors="mk11", blast=True, ultimate=True)
MK12 = Loadout("MK XII", max_hp=610, max_speed=171, gun_damage=27, laser_dps=400,
               laser_heat_rate=0.18, colors="mk12", blast=True, ultimate=True)
MK13 = Loadout("MK XIII", max_hp=640, max_speed=172, gun_damage=29, laser_dps=425,
               laser_heat_rate=0.18, colors="mk13", blast=True, ultimate=True)
MK14 = Loadout("MK XIV", max_hp=670, max_speed=173, gun_damage=31, laser_dps=450,
               laser_heat_rate=0.18, colors="mk14", blast=True, ultimate=True)
MK15 = Loadout("MK XV", max_hp=700, max_speed=174, gun_damage=33, laser_dps=475,
               laser_heat_rate=0.17, colors="mk15", blast=True, ultimate=True)
MK16 = Loadout("MK XVI", max_hp=730, max_speed=175, gun_damage=35, laser_dps=500,
               laser_heat_rate=0.17, colors="mk16", blast=True, ultimate=True)
MK17 = Loadout("MK XVII", max_hp=760, max_speed=176, gun_damage=37, laser_dps=525,
               laser_heat_rate=0.17, colors="mk17", blast=True, ultimate=True)
MK18 = Loadout("MK XVIII", max_hp=790, max_speed=177, gun_damage=39, laser_dps=550,
               laser_heat_rate=0.16, colors="mk18", blast=True, ultimate=True)
MK19 = Loadout("MK XIX", max_hp=820, max_speed=178, gun_damage=41, laser_dps=575,
               laser_heat_rate=0.16, colors="mk19", blast=True, ultimate=True)
MK20 = Loadout("MK XX", max_hp=850, max_speed=180, gun_damage=43, laser_dps=600,
               laser_heat_rate=0.16, colors="mk20", blast=True, ultimate=True)
