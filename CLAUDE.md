# CLAUDE.md

Guidance for Claude (and humans) working on this repo.

## What this is

**Dodging Asteroid** — a retro (Atari / NES-style) pixel-art arcade game in Python + pygame,
built for the THB course "Objektorientierte Skriptsprachen" (ESA3). Keep the code object-oriented
and readable: it is graded coursework as well as a game.

- Plan and phases: [ROADMAP.md](ROADMAP.md)
- What's done / what's next: [PROGRESS.md](PROGRESS.md) — **read it first, update it last** in every session.

## Run

```bash
source .venv/bin/activate        # Python 3.9–3.13, pygame >= 2.5
python3 ESA3.py
```

Headless smoke test (no window, no audio) — run after every change:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test [--shots DIR]
```

## Architecture

`ESA3.py` is only the entry point. All code lives in the `game/` package:

| Module | Responsibility |
|---|---|
| `settings.py` | Resolution, tuning constants, colour palettes, `Difficulty` dataclass |
| `pixelart.py` | Helpers: sprite-from-strings, Bayer dithering, value noise, glow sprites |
| `sprites.py` | Hand-drawn ship sprite (+ banked frames), procedural `AsteroidArt` / `AsteroidLibrary`, planet art |
| `particles.py` | `ParticleSystem` (flames, smoke, debris), `Shockwave`, `ScreenShake` |
| `background.py` | Dithered nebula, drifting planet, 3-layer parallax starfield with speed streaks |
| `entities.py` | `Ship` (physics, throttle, flames, RCS puffs) and `Asteroid` |
| `spawner.py` | `AsteroidSpawner` — driven by a `Difficulty` |
| `pixelfont.py` | 5x7 bitmap font (no TTF — keeps the retro look) |
| `hud.py` | Score, best, goal progress, throttle gauge, centred messages |
| `audio.py` | Music + SFX, silently degrades when no audio device exists |
| `game.py` | `Game` — main loop and state machine (TITLE, PLAYING, PAUSED, DYING, GAME_OVER, WIN) |

## Conventions

- **Low-res canvas**: all game logic and drawing use `LOW_W x LOW_H` (320x240) pixel coordinates.
  The canvas is scaled x`SCALE` with nearest-neighbour in `Game._present()`. Never draw on the window directly.
- **Frame-rate independent**: every `update(dt)` takes seconds; speeds are px/second.
- **No image files for game art.** Sprites are generated in code (`sprites.py`) so they stay
  consistent in palette and pixel size. Colours come from `settings.py`; don't inline new RGB tuples elsewhere.
- Flames/glow use additive blending (`BLEND_ADD`); smoke and debris use normal blending.
- Collision is pixel-perfect via `pygame.mask`.
- Tuning numbers belong in `settings.py`, not in logic code.
- Code comments/docstrings in English; keep them short.
- Only runtime dependency is `pygame`. Pure Python otherwise (no numpy).

## Legacy assets

`images/` and `astroids/` hold the original clip-art PNGs from the first version. They are no longer
loaded. `sounds/` is still used.
