"""Game states and level phases."""
from enum import Enum, auto


class State(Enum):
    TITLE = auto()
    STAR_MAP = auto()    # fly between the level planets, find data caches, land = hangar
    HANGAR = auto()      # inventory before every level: equip, buy, SPACE launches
    REWARD = auto()      # gift after a first level clear: choose 1 of 2
    DEV_MENU = auto()    # --dev: pick any level / wave / boss to start from
    PLAYING = auto()
    PAUSED = auto()
    DYING = auto()       # explosion plays, then GAME_OVER
    GAME_OVER = auto()
    LEVEL_CLEAR = auto() # rocket blasts off, upgrade screen, ENTER starts the next level
    WIN = auto()         # last level cleared
    WARP = auto()        # galaxy finale: the warp cut-scene before the results


class Phase(Enum):
    """Stages of a level while PLAYING."""
    FIELD = auto()       # asteroid field, progress bar fills up
    WARNING = auto()     # hull repaired, "WARNING" banner
    BOSS = auto()        # boss fight
    CLEARED = auto()     # boss destroyed, short pause before the next boss / level clear


# Menus with the ambient demo behind them (rocks fall, the ship hovers).
MENU_STATES = (State.TITLE, State.HANGAR, State.REWARD, State.DEV_MENU)
