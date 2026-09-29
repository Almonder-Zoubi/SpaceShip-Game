"""VEIL SHIFTS (galaxy 2): every attempt of a level rolls one modifier, so a retry is never
the same level twice. Clearing a level under a shift pays SHIFT_BONUS coins. Pure data; the
game applies them in flow/shifts.py."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Shift:
    id: str
    name: str
    text: str                    # one line on the level's start card (<= 32 characters)


SHIFTS = (
    Shift("ROCKS FAST", "ROCKS FAST", "ROCKS FALL 35% FASTER."),
    Shift("DOUBLE MINIONS", "DOUBLE MINIONS", "TWICE THE MINIONS."),
    Shift("NO KITS", "NO KITS, DOUBLE COINS", "NO REPAIR KITS. COINS X2."),
    Shift("ELITE SQUAD", "ELITE SQUAD", "THREE TIMES THE ELITES."),
    Shift("GLASS CANNON", "GLASS CANNON", "YOU HIT AND GET HIT X1.5."),
    Shift("BLIND SPOTS", "BLIND SPOTS", "DARK PATCHES HIDE THINGS."),
)
BY_ID = {s.id: s for s in SHIFTS}
