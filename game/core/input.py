"""Keyboard input: held-key set and key groups."""
import pygame

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
