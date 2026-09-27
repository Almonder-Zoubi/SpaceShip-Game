"""Music and sound effects. Everything is optional: no audio device = silent game."""
import pygame

from .settings import asset


class Audio:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.crash = None
        if not self.enabled:
            return
        try:
            self.crash = pygame.mixer.Sound(asset("sounds", "crash.wav"))
            pygame.mixer.music.load(asset("sounds", "nes.mp3"))
            pygame.mixer.music.set_volume(0.6)
        except pygame.error:
            self.enabled = False

    def play_music(self):
        if self.enabled:
            pygame.mixer.music.play(-1)

    def play_crash(self):
        if self.crash:
            self.crash.play()
