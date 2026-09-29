"""Keyboard and mouse input: held-key set, key groups and mouse steering."""
import math

import pygame

from ..config.display import SCALE

MOVE_KEYS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
             pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)


class Keys:
    """Set of held keys, indexable like pygame.key.get_pressed().

    The game fills one from KEYDOWN/KEYUP events instead of polling get_pressed(),
    which can report stale state on macOS depending on how the window got focus.
    """

    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def pressed(keys, *codes):
    """True if any of the key codes is held."""
    return any(keys[c] for c in codes)


class Mouse:
    """Mouse steering: the rocket flies towards the pointer, the left button fires.

    Mouse mode starts when the mouse really moves (a few pixels, so a pointer that merely
    rests in the window does nothing) and ends when an arrow key is pressed.
    Positions are canvas pixels (the window shows the canvas scaled by SCALE).
    """

    WAKE_DISTANCE = 6            # window px the mouse must travel to take over

    def __init__(self):
        self.active = False
        self.target = None       # (x, y) on the canvas
        self.firing = False      # left button held
        self._travel = 0.0

    def move(self, window_pos, rel=(0, 0)):
        self.target = (window_pos[0] / SCALE, window_pos[1] / SCALE)
        self._travel += math.hypot(*rel)
        if self._travel >= self.WAKE_DISTANCE:
            self.active = True

    def click(self, window_pos):
        """A click always means mouse mode."""
        self.target = (window_pos[0] / SCALE, window_pos[1] / SCALE)
        self.active = self.firing = True

    def release(self):
        """Keyboard took over (or the window lost focus)."""
        self.active = self.firing = False
        self._travel = 0.0

    @property
    def aim(self):
        """Where the rocket should fly, or None in keyboard mode."""
        return self.target if self.active else None
