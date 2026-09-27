# CLAUDE.md

Guidance for Claude (and humans) working on this repo.

## What this is

**Dodging Asteroid** — a retro (Atari / NES-style) pixel-art arcade game in Python + pygame,
built for the THB course "Objektorientierte Skriptsprachen" (ESA3). Keep the code object-oriented
and readable: it is graded coursework as well as a game.

- Plan and phases: [ROADMAP.md](ROADMAP.md)
- What's done / what's next: [PROGRESS.md](PROGRESS.md) — **read it first, update it last** in every session.
  Its "Snapshot" section describes the current game in one screen; the "Decisions" section is binding.

## Working with the user

- The user playtests on macOS and reports how it *feels*. Ask before adding control complexity.
- Show visual changes: `--smoke-test --shots DIR` saves screenshots of every state (headless), but
  also capture a **real window** frame (see "Verify in a real window" below) — some bugs only show there.
- Commit only when asked. Work happens on feature branches (e.g. `levels`), `main` is stable.

## Run

```bash
source .venv/bin/activate        # Python 3.9–3.13, pygame >= 2.5
python3 ESA3.py
python3 ESA3.py --boss           # skip the asteroid field, straight to the level boss
python3 ESA3.py --level 2        # start at level 2 (with --boss: straight to the Carrier)
python3 ESA3.py --level 3 --boss # final boss (Mothership)
python3 ESA3.py --dev            # dev menu: any level / wave / boss, god mode, hotkeys
```

Headless smoke test (no window, no audio) — run after every change. It drives every state and
mechanic (movement, lean, weapons, push, damage, death, boss flow, balance maths, 60 s combat):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test [--shots DIR]
python3 -m pyflakes ESA3.py game/     # lint (pyflakes is installed in .venv only)
```

### Verify in a real window

The dummy video driver has a different surface format than macOS, so render checks need a real
window. Script pattern (run with `PYTHONPATH=.`, saves what the window shows):

```python
import sys, pygame
from game.game import Game, Keys
g = Game(); g.start(); g.ship.hp = 10**9          # g.distance = 10**9 to jump to the boss
for i in range(180):
    g.handle_events(); dt = g.clock.tick(60) / 1000
    g.update(dt, Keys(pygame.K_SPACE, pygame.K_UP)); g.draw(); g._present()
pygame.image.save(g.window, sys.argv[1]); pygame.quit()
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
| `ship.py` | `Ship`: direct arrow controls, diagonal lean (±30°), throttle, health, flames/exhaust/RCS |
| `entities.py` | `Asteroid`: hp, hit flash, pixel-exact `contains()` / `collides_with()` |
| `weapons.py` | `Weapon` base, `MachineGun`, `Laser`, `Charged` base → `Blast`, `Ultimate` (+`Missile`), `Hit` (damage + push direction), `raycast()` |
| `boss.py` | `BossSpec` (balance maths), `Boss` base (multi-phase + roar, drone launch), `Gunship` (boss 1), `Carrier` (boss 2), `Mothership` (boss 3, beam) |
| `enemies.py` | `EnemyBullet`, `shoot()`, `Enemy` base, `Drone`, `drone_formation()` |
| `pickups.py` | `Pickup` base, `RepairKit`, `FullRepair`, `PowerCore` |
| `levels.py` | `Level` → `Wave` → `BossEntry` data, `LEVELS` (asteroid mix, ship model, nebula, waves) |
| `spawner.py` | `AsteroidSpawner` — driven by a `Difficulty` |
| `pixelfont.py` | 5x7 bitmap font (no TTF — keeps the retro look) |
| `hud.py` | Health bar, level progress, score/hi-score, weapon + laser heat, banners |
| `storage.py` | `SaveData` — records + unlocked levels in `save.json` (git-ignored); `path=None` = memory only |
| `audio.py` | Music + SFX, silently degrades when no audio device exists |
| `game.py` | `Game` — main loop, states (TITLE, PLAYING, PAUSED, DYING, GAME_OVER, LEVEL_CLEAR, WIN), level phases (FIELD, WARNING, BOSS, CLEARED), boss rush, pickups, damage/explosions, `Keys`, `run_smoke_test()` |

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
  fight_time, player=<Loadout of that level>)`; HP and damage are derived so the boss is `strength`
  times stronger in a damage race. Pickups and POWER levels are the player's edge on top.
- **Levels are data** (`levels.py`). A new level = a `Level` entry; a new ship model = a `Loadout`
  in settings + a palette in `sprites.SHIP_PALETTES`.
- Weapons never apply damage themselves: `update()` returns `Hit`s and `Game` applies them,
  so new target types (enemies, bosses) only need `x`, `y`, `bound`, `contains()` (+ `damage()`).
- Input: `Game.held` (a `Keys` set filled from KEYDOWN/KEYUP) — not `pygame.key.get_pressed()`,
  which is unreliable on macOS. Tests pass `Keys(...)` directly to `Game.update()`.
- Big sprites (bosses) are drawn as a left half on a `CharCanvas`, then `mirrored()` + `outlined()`.
  Keep muzzle/vent coordinates next to the sprite definition in `sprites.py`.
- Heading/lean: angles in radians clockwise from "nose up"; `Ship.angle`, `forward`, `right`.
- Code comments/docstrings in English; keep them short.
- Never write the player's `save.json` from tests or scripts: pass `save_path=` (temp file) or
  use `dev=True` (memory only). The smoke test already does this.
- Only runtime dependency is `pygame`. Pure Python otherwise (no numpy).

## Legacy assets

`images/` and `astroids/` hold the original clip-art PNGs from the first version. They are no longer
loaded. `sounds/` is still used.
