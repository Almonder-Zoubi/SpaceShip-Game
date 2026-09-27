"""Level definitions as data: waves of asteroids and minions, ship model, background, bosses."""
from dataclasses import dataclass

from .boss import GUNSHIP_SPEC, BossSpec, Carrier, Gunship, Mothership
from .settings import (DEFAULT_DIFFICULTY, LEVEL_LENGTH, MK1, MK2, MK3, NEBULA, NEBULA_ABYSS,
                       NEBULA_CRIMSON, Difficulty, Loadout)


@dataclass(frozen=True)
class BossEntry:
    """One boss of a wave's boss rush: which class, with which balance numbers."""
    boss_class: type
    spec: BossSpec

    def create(self):
        return self.boss_class(self.spec)


@dataclass(frozen=True)
class Wave:
    """Asteroid field (with minions if the level's Difficulty has them), then its bosses."""
    length: float                # seconds of flight through the field
    bosses: tuple = ()           # BossEntry, fought in order after the field
    name: str = ""               # subtitle of the "WAVE n" announcement


@dataclass(frozen=True)
class Level:
    number: int
    name: str
    loadout: Loadout             # ship model the player flies in this level
    difficulty: Difficulty
    nebula: tuple                # background cloud colours
    waves: tuple                 # Wave, played in order; the last boss is the level boss
    upgrade_notes: tuple = ()    # shown on the "level clear" screen before this level


LEVELS = (
    Level(1, "ASTEROID FIELD", MK1, DEFAULT_DIFFICULTY, tuple(NEBULA),
          (Wave(LEVEL_LENGTH, (BossEntry(Gunship, GUNSHIP_SPEC),)),)),
    Level(2, "CRIMSON BELT", MK2,
          Difficulty(spawn_interval=0.55, speed_min=60, speed_max=112, radius_min=4,
                     radius_max=14, drift=18, palettes=("rust", "brown", "grey"),
                     formation_interval=11),
          tuple(NEBULA_CRIMSON),
          (Wave(80, (BossEntry(Gunship, BossSpec("GUNSHIP", strength=1.5, fight_time=20,
                                                 player=MK2)),
                     BossEntry(Carrier, BossSpec("CARRIER", strength=4.0, fight_time=55,
                                                 player=MK2)))),),
          upgrade_notes=(f"HULL  {MK1.max_hp} > {MK2.max_hp}",
                         f"GUN DAMAGE  {MK1.gun_damage} > {MK2.gun_damage}",
                         f"LASER  +{round(MK2.laser_dps / MK1.laser_dps * 100 - 100)}%  RUNS COOLER",
                         "ENGINE  FASTER")),
    # Three waves: minions, minions + the Carrier again (weakened), minions + the final boss.
    Level(3, "DARK NEBULA", MK3,
          Difficulty(spawn_interval=0.5, speed_min=65, speed_max=120, radius_min=4,
                     radius_max=14, drift=20, palettes=("slate", "grey", "rust"),
                     formation_interval=8),
          tuple(NEBULA_ABYSS),
          (Wave(45, name="ASTEROIDS AND DRONES"),
           Wave(40, (BossEntry(Carrier, BossSpec("CARRIER", strength=1.5, fight_time=30,
                                                 player=MK3)),),
                name="THE CARRIER RETURNS"),
           Wave(40, (BossEntry(Mothership, BossSpec("MOTHERSHIP", strength=5.0, fight_time=75,
                                                    player=MK3)),),
                name="FINAL WAVE")),
          upgrade_notes=(f"HULL  {MK2.max_hp} > {MK3.max_hp}    GUN  {MK2.gun_damage} > "
                         f"{MK3.gun_damage}",
                         "NEW: BLAST BEAM",
                         "SHOOT ROCKS + DRONES TO CHARGE",
                         "NEW: ULTIMATE MISSILES - KEY T")),
)
