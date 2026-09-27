"""Game states and level phases."""
from enum import Enum, auto


class State(Enum):
    TITLE = auto()
    HANGAR = auto()      # choose a hull, ENTER launches
    DEV_MENU = auto()    # --dev: pick any level / wave / boss to start from
    PLAYING = auto()
    PAUSED = auto()
    DYING = auto()       # explosion plays, then GAME_OVER
    GAME_OVER = auto()
    LEVEL_CLEAR = auto() # rocket blasts off, upgrade screen, ENTER starts the next level
    WIN = auto()         # last level cleared


class Phase(Enum):
    """Stages of a level while PLAYING."""
    FIELD = auto()       # asteroid field, progress bar fills up
    WARNING = auto()     # hull repaired, "WARNING" banner
    BOSS = auto()        # boss fight
    CLEARED = auto()     # boss destroyed, short pause before the next boss / level clear


# Menus with the ambient demo behind them (rocks fall, the ship hovers).
MENU_STATES = (State.TITLE, State.HANGAR, State.DEV_MENU)
