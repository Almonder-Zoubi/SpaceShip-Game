# Dodging Asteroid

A retro pixel-art arcade game built with [Pygame](https://www.pygame.org/) for the
"Objektorientierte Skriptsprachen" course (ESA3). Pilot a rocket through a falling asteroid field.

Everything you see — ship, asteroids, planets, nebula, font — is generated in code as real
pixel art on a 320x240 canvas scaled x3, with particle-based engine flames and explosions.

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
| Enter | Start / restart |
| Esc | Back to menu / quit |

Fly to the end of the asteroid field (progress bar at the top). Asteroids drain your health
bar — bigger rocks hurt more and take longer to destroy; shooting them slows their fall, and big
rocks split into fragments. At the end: **WARNING** — your hull is repaired and the **Gunship**
boss attacks. Destroy it to win. (`python3 ESA3.py --boss` skips straight to the boss.)

## Setup

Requires Python 3.9–3.13 (pygame does not yet ship prebuilt wheels for 3.14).

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 ESA3.py
```

Headless self-test: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test`

Skip to the boss for testing: `python3 ESA3.py --boss`

## Project structure

```
ESA3.py          # entry point
game/            # the game package (see CLAUDE.md for a module map)
sounds/          # background music and crash sound
images/, astroids/   # legacy clip-art from v1 (no longer used)
CLAUDE.md        # architecture, conventions and workflow for contributors / Claude
ROADMAP.md       # planned phases: bosses, levels, endless mode, leaderboard, sound
PROGRESS.md      # current snapshot, decisions, log and next steps
```
