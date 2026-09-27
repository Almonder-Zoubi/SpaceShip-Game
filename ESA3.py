#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dodging Asteroid — entry point.
Created on Mon Mar 25
@author: Almonder Zoubi

Usage:
    python3 ESA3.py                 play
    python3 ESA3.py --boss          play, but skip the asteroid field (boss testing)
    python3 ESA3.py --smoke-test    headless self-test (use SDL_VIDEODRIVER=dummy)
"""
import sys

from game.game import Game, run_smoke_test

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
        run_smoke_test(shots)
    else:
        Game(skip_to_boss="--boss" in sys.argv).run()
