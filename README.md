# Dodging Asteroid

A retro pixel-art arcade game built with [Pygame](https://www.pygame.org/) for the
"Objektorientierte Skriptsprachen" course (ESA3). Pilot a rocket through a falling asteroid field.

Everything you see and hear is generated in code: ships, asteroids, bosses, planets, nebula and
font as real pixel art on a 320x240 canvas scaled x3, and a chiptune soundtrack + sound effects
from a small pure-Python synthesizer.

## How to play

| Key | Action |
|---|---|
| Arrows / WASD | Move (UP + LEFT/RIGHT = diagonal) |
| Up | Boost — full burn, long flames, the world speeds up |
| Down | Retro — flames die down, the world slows |
| Up + Left / Right | Diagonal — the rocket leans like `\` or `/` and fires that way |
| Space | Fire where the nose points |
| R | Switch weapon: machine gun / laser (laser overheats) |
| P | Pause |
| C | Toggle CRT scanlines |
| Enter | Start (opens the hangar) / launch / restart |
| Left / Right | Title: choose an unlocked level. Hangar: choose your ship |
| T | Ultimate missile storm (level 3) |
| Esc | Back to menu / quit |

Pick a ship in the **hangar**: the balanced ARROW, the tiny fast WASP, the heavily armoured
TITAN or the laser-focused LANCE. Every ship is upgraded between levels (MK I → MK II → MK III).

Fly to the end of the asteroid field (progress bar at the top). Asteroids drain your health
bar — bigger rocks hurt more and take longer to destroy; shooting them slows their fall, and big
rocks split into fragments. At the end: **WARNING** — your hull is repaired and the **Gunship**
boss attacks. Three levels, each with its own bosses; the Mothership waits at the end.
(`python3 ESA3.py --boss` skips straight to the boss, `--dev` opens a menu of every start point.)

## Setup

Requires Python 3.9–3.13 (pygame does not yet ship prebuilt wheels for 3.14).

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 ESA3.py
```

The first start takes ~10 s longer: the game renders its music and sound effects into
`sounds/generated/` (after that they load instantly). `python3 tools/build_audio.py` renders
them again after changing a sound recipe.

Headless self-test: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test`
(add `--only hulls,audio` to run single sections)

Skip to the boss for testing: `python3 ESA3.py --boss`

## Project structure

```
ESA3.py          # entry point
game/            # the game package, one folder per area (see CLAUDE.md for the module map)
  config/        #   resolution, colours, tuning numbers, ship models
  core/          #   pixel-art helpers, font, particles, input, save file
  background/    #   nebula, planet, starfield
  player/        #   hulls (ship shapes), ship art, the Ship
  weapons/       #   machine gun, laser, BLAST, ULTIMATE
  obstacles/     #   asteroids and their spawner
  minions/       #   drones and enemy bullets
  bosses/        #   Gunship, Carrier, Mothership (+ balance maths)
  pickups/       #   repair kits, power cores
  levels/        #   level data
  audio/         #   synthesizer, sound effects, music, playback
  ui/            #   HUD, hangar, menus and result screens
  flow/          #   the Game: main loop, states, level flow, combat, sound, dev mode
tests/smoke.py   # headless smoke test
tools/           # build_audio.py: render sounds and music to WAV
sounds/generated/    # rendered audio cache (git-ignored, rebuilt on first start)
images/, astroids/, sounds/*.wav|mp3   # legacy assets from v1 (no longer used)
CLAUDE.md        # architecture, conventions and workflow for contributors / Claude
ROADMAP.md       # planned phases: bosses, levels, endless mode, leaderboard, sound
PROGRESS.md      # current snapshot, decisions, log and next steps
```
