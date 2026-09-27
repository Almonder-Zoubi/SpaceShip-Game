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
| Mouse | Move: the rocket flies to the pointer (an arrow key switches back to the keyboard) |
| Up | Boost — full burn, long flames, the world speeds up |
| Down | Retro — flames die down, the world slows |
| Up + Left / Right | Diagonal — the rocket leans like `\` or `/` and fires that way |
| Space / left click | Fire where the nose points (a click also works as Enter in menus) |
| R | Switch weapon: machine gun / laser (laser overheats) |
| P | Pause |
| C | Toggle CRT scanlines |
| Enter | Start (opens the hangar) / equip or buy in the hangar (again = launch) / restart |
| Left / Right | Title: choose an unlocked level. Hangar: switch tab (ships / weapons). Gift: choose |
| Up / Down | Hangar: pick an item |
| Space | Hangar: launch |
| T | Ultimate missile storm (from level 3) |
| Esc | Back to menu / quit |

You start with the balanced ARROW and a machine gun. Destroyed rocks, drones and bosses drop
**coins**, but they only go into your bank when you win the level. Every cleared level shows
your **rank** (S/A/B/C) and pays out, and the first clear gives a **gift**: choose the LASER or the
tiny fast WASP, get BLAST + ULTIMATE, choose the armoured TITAN or the laser-focused LANCE. The
gift you don't take is sold in the shop. The **hangar** before every level is your inventory:
equip ships, buy items with coins, launch. Every ship is also upgraded between levels
(MK I → MK II → MK III → MK IV). Levels belong to galaxies of 10 (galaxy 1: ORION REACH).

Fly to the end of the asteroid field (progress bar at the top). Asteroids drain your health
bar — bigger rocks hurt more and take longer to destroy; shooting them slows their fall, and big
rocks split into fragments. At the end: **WARNING** — your hull is repaired and the **Gunship**
boss attacks. Four levels, each with its own bosses; in level 4 "FROZEN RIFT" ice rocks shatter,
kamikaze divers lock on, and the LEVIATHAN, a giant space serpent, waits at the end.
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
  minions/       #   drones, kamikaze divers and enemy bullets
  bosses/        #   Gunship, Carrier, Mothership, Leviathan (+ balance maths)
  pickups/       #   repair kits, power cores, coins
  levels/        #   level data, grouped into galaxies
  progression/   #   rank, coins / payout, item catalog + gifts, inventory (pure logic)
  audio/         #   synthesizer, sound effects, music, playback
  ui/            #   HUD, hangar, gift cards, menus and result screens
  flow/          #   the Game: main loop, states, level flow, combat, coins, hangar, sound, dev
tests/smoke.py   # headless smoke test
tools/           # build_audio.py: render sounds and music to WAV
sounds/generated/    # rendered audio cache (git-ignored, rebuilt on first start)
images/, astroids/, sounds/*.wav|mp3   # legacy assets from v1 (no longer used)
docs/GUIDE.md    # developer guide: assets, architecture, workflow, how to add levels / bosses / items
docs/DESIGN.md   # design bible: galaxies, levels 5-10, bosses, weapons, gifts, coins, wingmen, skins
CLAUDE.md        # architecture, conventions and workflow for contributors / Claude
ROADMAP.md       # planned phases (Phase 10 = galaxies + meta progression, G1..G16)
PROGRESS.md      # current snapshot, decisions, log and next steps
```
