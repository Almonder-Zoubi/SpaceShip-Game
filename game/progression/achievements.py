"""Achievements: goals that unlock a skin. Pure data; the game checks them (flow/skins.py)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    text: str                    # how to earn it
    reward: str                  # skin item id


ACHIEVEMENTS = (
    Achievement("NO_HIT", "UNTOUCHABLE", "BEAT A BOSS WITHOUT A HIT", "GOLD TRIM"),
    Achievement("FEVER", "FEVER PITCH", "REACH FEVER (COMBO 25)", "RAINBOW"),
    Achievement("RANK_S", "TOP OF THE CLASS", "CLEAR A LEVEL WITH RANK S", "NEON"),
    Achievement("MINIONS", "DRONE HUNTER", "DESTROY 100 MINIONS", "TOXIC"),
    Achievement("PACIFIST", "PACIFIST", "FLY A WHOLE FIELD WITHOUT FIRING", "HEARTS"),
    Achievement("CHAMPION", "CHAMPION", "WIN THE GAME", "SUPERNOVA"),
    Achievement("EXPLORER", "EXPLORER", "FIND EVERY DATA CACHE ON THE MAP", "STARDUST"),
)
BY_ID = {a.id: a for a in ACHIEVEMENTS}
MINIONS_GOAL = 100
