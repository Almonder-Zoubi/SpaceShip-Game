# Dodging Asteroid

A retro pixel-art arcade game built with [Pygame](https://www.pygame.org/) for the
"Objektorientierte Skriptsprachen" course (ESA3). Pilot a rocket through a falling asteroid field.

Everything you see — ship, asteroids, planets, nebula, font — is generated in code as real
pixel art on a 320x240 canvas scaled x3, with particle-based engine flames and explosions.

## How to play

| Key | Action |
|---|---|
| Arrows / WASD | Steer (the ship has inertia and banks when turning) |
| Up | **Boost** — full burn, long flames, the world speeds up |
| Down | **Retro** — flames die down, the world slows |
| P | Pause |
| C | Toggle CRT scanlines |
| Enter / R | Start / restart |
| Esc | Back to menu / quit |

Dodge **30** asteroids to win. One hit and your rocket explodes.

## Setup

Requires Python 3.9–3.13 (pygame does not yet ship prebuilt wheels for 3.14).

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 ESA3.py
```

Headless self-test: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test`

## Project structure

```
ESA3.py          # entry point
game/            # the game package (see CLAUDE.md for a module map)
sounds/          # background music and crash sound
images/, astroids/   # legacy clip-art from v1 (no longer used)
ROADMAP.md       # planned phases: levels, endless mode, extras
PROGRESS.md      # current status and next steps
```
