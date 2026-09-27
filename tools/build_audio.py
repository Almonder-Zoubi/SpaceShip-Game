#!/usr/bin/env python3
"""Render the game's sound effects and music (game/audio/sfx.py + music.py) to WAV files.

    python3 tools/build_audio.py              render everything
    python3 tools/build_audio.py boss gun     render only these (sound or track names)

The game also renders missing files on its first start; run this after changing a recipe.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.audio import bank  # noqa: E402


def main(names):
    files = bank.all_files()
    if names:
        files = [(p, r) for p, r in files if os.path.splitext(os.path.basename(p))[0] in names]
        if not files:
            sys.exit(f"no sound or track named {', '.join(names)}")
    total = 0
    for path, render in files:
        start = time.time()
        if not bank.render(path, render):
            sys.exit(f"cannot write {path}")
        size = os.path.getsize(path)
        total += size
        print(f"{os.path.relpath(path):40s} {size / 1024:7.0f} KB  {time.time() - start:4.1f} s")
    print(f"{len(files)} files, {total / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
