"""Rendered sounds on disk: sounds/generated/sfx/*.wav and sounds/generated/music/*.wav.

The recipes in sfx.py and music.py are the source; the WAV files are a cache so the game
starts fast. Anything missing is rendered on demand (tools/build_audio.py renders all).
"""
import os

from ..config.display import asset
from .music import SONGS
from .sfx import LOOPS, SOUNDS
from .synth import dc_block, limit, write_wav

GENERATED = asset("sounds", "generated")


def sfx_path(name):
    return os.path.join(GENERATED, "sfx", f"{name}.wav")


def music_path(name):
    return os.path.join(GENERATED, "music", f"{name}.wav")


def all_files():
    """(path, render function) for every sound and track."""
    return ([(sfx_path(n), lambda n=n, fn=fn: _finish(fn(), loop=n in LOOPS))
             for n, fn in SOUNDS.items()]
            + [(music_path(n), lambda fn=fn: fn().render()) for n, fn in SONGS.items()])


def _finish(samples, loop):
    """One-shot effects lose their DC offset (loops keep theirs: filtering breaks the seam)."""
    return limit(samples if loop else dc_block(samples))


def missing():
    return [(path, render) for path, render in all_files() if not os.path.exists(path)]


def render(path, make_samples):
    """Render one sound to its WAV file. Returns False if the folder isn't writable."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        write_wav(tmp, make_samples())
        os.replace(tmp, path)                   # never leave half a file behind
        return True
    except OSError:
        return False
