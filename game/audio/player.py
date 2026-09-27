"""Audio playback: sound effects, looping engine / laser sounds and the music tracks.

Everything is optional: without an audio device the game is silent, but play() still checks
that the sound name exists, so a typo fails in the smoke test instead of going unnoticed.
"""
import os

import pygame

from . import bank
from .music import JINGLES, SONGS
from .sfx import LOOPS, SOUNDS

# Per-sound volume and the shortest gap between two plays (for sounds that fire in bursts).
VOLUME = {"gun": 0.35, "hit_rock": 0.5, "hit_metal": 0.4, "enemy_shot": 0.45,
          "missile_hit": 0.5, "engine": 0.5, "laser": 0.45, "coin": 0.35}
MIN_GAP = {"gun": 0.06, "hit_rock": 0.05, "hit_metal": 0.06, "enemy_shot": 0.07,
           "missile_hit": 0.05, "rock_break": 0.04, "ice_break": 0.05, "lock_on": 0.25,
           "coin": 0.05}
MUSIC_VOLUME = 0.55


class Audio:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.loop_channels = {}
        self.track = None                         # music track currently playing
        self._last_played = {}
        self.sound_volume = 1.0                   # master volumes from the options (0..1)
        self.music_volume = 1.0
        if self.enabled:
            pygame.mixer.set_num_channels(24)
            pygame.mixer.set_reserved(len(LOOPS))
            for i, name in enumerate(LOOPS):
                self.loop_channels[name] = pygame.mixer.Channel(i)

    def load(self):
        """Render missing WAVs (first start only), then load every sound effect."""
        for path, make in bank.missing():
            bank.render(path, make)
        if not self.enabled:
            return
        for name in SOUNDS:
            try:
                sound = pygame.mixer.Sound(bank.sfx_path(name))
            except (pygame.error, FileNotFoundError):
                continue
            self.sounds[name] = sound
        self.set_volume(self.sound_volume, self.music_volume)

    def set_volume(self, sound, music):
        """Master volumes 0..1 (options menu)."""
        self.sound_volume, self.music_volume = sound, music
        for name, s in self.sounds.items():
            s.set_volume(VOLUME.get(name, 0.7) * sound)
        if self.enabled:
            pygame.mixer.music.set_volume(MUSIC_VOLUME * music)

    # --- sound effects -------------------------------------------------------------------
    def play(self, name):
        assert name in SOUNDS, f"unknown sound {name!r}"
        sound = self.sounds.get(name)
        if not sound:
            return
        now = pygame.time.get_ticks() / 1000
        if now - self._last_played.get(name, -1.0) < MIN_GAP.get(name, 0.0):
            return
        self._last_played[name] = now
        sound.play()

    def loop(self, name, volume):
        """Keep a looping sound (engine, laser) running at a volume; 0 stops it."""
        assert name in LOOPS, f"not a looping sound {name!r}"
        channel, sound = self.loop_channels.get(name), self.sounds.get(name)
        if not channel or not sound:
            return
        if volume <= 0:
            if channel.get_busy():
                channel.fadeout(80)
            return
        if not channel.get_busy():
            channel.play(sound, loops=-1)
        channel.set_volume(volume * self.sound_volume)

    def stop_loops(self):
        for channel in self.loop_channels.values():
            channel.stop()

    # --- music ---------------------------------------------------------------------------
    def music(self, track):
        """Switch the music; calling it every frame with the same track does nothing.
        None fades the music out. Jingles play once."""
        if track == self.track:
            return
        assert track is None or track in SONGS, f"unknown music track {track!r}"
        self.track = track
        if not self.enabled:
            return
        if track is None:
            pygame.mixer.music.fadeout(600)
            return
        path = bank.music_path(track)
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME * self.music_volume)
            pygame.mixer.music.play(0 if track in JINGLES else -1, fade_ms=300)
        except pygame.error:
            pass
