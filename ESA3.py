#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dodging Asteroid — entry point.
Created on Mon Mar 25
@author: Almonder Zoubi

Usage:
    python3 ESA3.py                 play
    python3 ESA3.py --boss          play, but skip straight to the level boss (boss testing)
    python3 ESA3.py --level 2       start at level 2 (combine with --boss for the Carrier)
    python3 ESA3.py --dev           dev menu: start at any level / wave / boss, god mode,
                                    in-game hotkeys (N skip, 1 charge, 2 power, 3 repair, G god)
    python3 ESA3.py --smoke-test    headless self-test (use SDL_VIDEODRIVER=dummy)
                    [--shots DIR]   ...saving screenshots
                    [--only a,b]    ...running only some sections (see tests/smoke.py)
"""
import sys

from game.flow.game import Game

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        from tests.smoke import run_smoke_test
        shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
        run_smoke_test(shots, only=only)
    else:
        level = int(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else 1
        Game(skip_to_boss="--boss" in sys.argv, start_level=level, dev="--dev" in sys.argv).run()
