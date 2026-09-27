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
python3 ESA3.py --boss           # skip the asteroid field, straight to the boss
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
| `pixelart.py` | Helpers: sprite-from-strings, `CharCanvas` (shape drawing for big sprites), dithering, noise, glow |
| `sprites.py` | Ship sprite (+ banked and RotSprite lean frames), procedural `AsteroidArt` / `AsteroidLibrary`, boss sprites (`mirrored`, `outlined`) |
| `particles.py` | `ParticleSystem` (flames, smoke, debris), `Shockwave`, `ScreenShake` |
| `background.py` | Dithered nebula, drifting planet, 3-layer parallax starfield with speed streaks |
| `ship.py` | `Ship`: direct arrow controls (always faces up), throttle, health, flames/exhaust/RCS |
| `entities.py` | `Asteroid`: hp, hit flash, pixel-exact `contains()` / `collides_with()` |
| `weapons.py` | `Weapon` base, `MachineGun`, `Laser`, `Hit` (damage + push direction), `raycast()` |
| `boss.py` | `BossSpec` (balance maths), `Boss` base, `Gunship` (boss 1), `EnemyBullet` |
| `spawner.py` | `AsteroidSpawner` — driven by a `Difficulty` |
| `pixelfont.py` | 5x7 bitmap font (no TTF — keeps the retro look) |
| `hud.py` | Health bar, level progress, score/hi-score, weapon + laser heat, banners |
| `audio.py` | Music + SFX, silently degrades when no audio device exists |
| `game.py` | `Game` — main loop, states (TITLE, PLAYING, PAUSED, DYING, GAME_OVER, WIN) and level phases (FIELD, WARNING, BOSS, CLEARED) |

## Conventions

- **Low-res canvas**: all game logic and drawing use `LOW_W x LOW_H` (320x240) pixel coordinates.
  The canvas is scaled x`SCALE` with nearest-neighbour in `Game._present()`. Never draw on the window directly.
- **Frame-rate independent**: every `update(dt)` takes seconds; speeds are px/second.
- **No image files for game art.** Sprites are generated in code (`sprites.py`) so they stay
  consistent in palette and pixel size. Colours come from `settings.py`; don't inline new RGB tuples elsewhere.
- **Surfaces**: sprites use `pygame.SRCALPHA`; anything opaque (canvas, backgrounds, glow) must use
  `pixelart.opaque_surface()`, never a bare `pygame.Surface()`. On macOS the display format has an
  alpha channel and a bare surface turns sprites into black boxes. The headless dummy driver does
  NOT reproduce this — check visual changes in a real window too.
- Flames/glow use additive blending (`BLEND_ADD`); smoke and debris use normal blending.
- Collision is pixel-perfect via `pygame.mask`.
- Tuning numbers belong in `settings.py`, not in logic code.
- **Controls are deliberately simple**: the rocket moves directly with the arrows (diagonal =
  two arrows) and only *leans* up to 30° on UP+LEFT/RIGHT. Drift/360° rotation was tried and
  rejected as too hard — don't reintroduce it. Use `Ship.to_world(lx, ly)` / `Ship.nose()` to place things relative to the ship.
- **Boss balance**: never hand-pick boss HP or bullet damage. Give a `BossSpec(strength,
  fight_time)`; HP and damage are derived so the boss is `strength` times stronger in a damage race.
- Weapons never apply damage themselves: `update()` returns `Hit`s and `Game` applies them,
  so new target types (enemies, bosses) only need `x`, `y`, `bound`, `contains()`.
- Code comments/docstrings in English; keep them short.
- Only runtime dependency is `pygame`. Pure Python otherwise (no numpy).

## Legacy assets

`images/` and `astroids/` hold the original clip-art PNGs from the first version. They are no longer
loaded. `sounds/` is still used.
