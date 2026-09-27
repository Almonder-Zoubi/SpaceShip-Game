# Progress

Update this file at the end of every work session: what changed, what's next, open questions.

## Status

**Current phase:** Phase 4 in progress — Boss 1 (Gunship) done → next: small enemy fighters, then Bosses 2–3. See [ROADMAP.md](ROADMAP.md).

## Log

### 2026-09-27 — Diagonal lean, rock push-back, Boss 1 (Gunship)
- Lean: UP+RIGHT tilts the rocket '/', UP+LEFT '\' (30°, 3 RotSprite frames per side, masks per
  frame), straightens on release. Guns, laser and flames follow the lean.
- Push-back: `Hit` carries the shot direction; `Asteroid.push()` slows the fall (scaled by 4/radius,
  never below `ROCK_MIN_FALL`).
- `boss.py`: `BossSpec` balance maths (strength 3 = verified in smoke test), `Boss` base,
  `Gunship` boss 1 with spread / turrets / ring (enraged <50%), `EnemyBullet`.
- `pixelart.CharCanvas` + `sprites.mirrored/outlined` to draw big sprites; 70x48 Gunship.
- Level phases FIELD → WARNING (hull repaired) → BOSS → CLEARED → WIN; boss HP bar in HUD;
  ramming damage; boss bullets fizzle out when it dies; 5000 points for the kill.
- `python3 ESA3.py --boss` skips the asteroid field for testing.
- Perf: boss fight worst frame 4.6 ms. Verified in a real macOS window.

### 2026-09-27 — Reverted to direct arcade controls
- User feedback: drift + 360° rotation was too hard to fly. Back to Phase 1 controls: arrows move
  directly, two arrows = diagonal, UP boost / DOWN retro flames, rocket always faces up.
- Removed: RotSprite rotation frames, aim lock, SHIFT spin, spin HUD indicator, drift settings.
- Weapons fire straight up. Everything else from Phase 3 (weapons, rock hp/splitting, health) kept.
- Smoke test checks diagonal movement, quick stop after release, UP boost / DOWN retro throttle.

### 2026-09-27 — Phases 2 + 3: drift flight, 360°, weapons, health
- Decisions: control scheme (b) — arrows push in screen directions, ship faces its thrust;
  both weapons, R switches, SPACE fires; player health bar per level, refilled before bosses;
  bosses 3–5x stronger than the rocket (formula in ROADMAP Phase 4).
- New `ship.py`: momentum + low drag drift, 64 RotSprite rotation frames x 3 banks with masks,
  aim lock while firing, SHIFT spin (invulnerable), exhaust/RCS along the heading, hp + knockback.
  (Flight part reverted later the same day — see entry above.)
- New `weapons.py`: `Weapon` base, `MachineGun` (tracers, spread, muzzle flash), `Laser`
  (pixel-exact raycast, heat/overheat). Weapons return `Hit`s; `Game` applies damage.
- Asteroids: hp by area, white hit flash, chips, destroy explosion, split into 2–3 fragments.
- HUD: HP bar (blinks when low), level progress, 6-digit score + HI, weapon/heat, spin ready.
- Win condition is now distance (`LEVEL_LENGTH` = 75 s of flight) instead of dodge count.
- Fragment art for every palette is prebuilt at startup (was causing ~9 ms hitches).
- Smoke test covers diagonal thrust + heading, drift, weapon switch, spin, laser kill + split,
  gun kill, overheat, damage + invulnerability, death, win, and a 60 s busy combat run.
- Perf: worst frame 3.3 ms in heavy laser combat; startup 0.76 s. Verified in a real macOS window.

### 2026-09-27 — Fix: ship and asteroids drawn as black boxes on macOS
- Cause: `pygame.Surface()` copies the display format, which on macOS has an alpha channel.
  Blitting SRCALPHA sprites onto the canvas wrote alpha 0 in their transparent areas; the window
  showed those pixels as black. The dummy driver (headless tests) has no alpha, so tests missed it.
- Fix: `pixelart.opaque_surface()` (explicit RGB masks, no alpha) for canvas, nebula and glows.
  Smoke test asserts the canvas has no alpha channel. Verified in a real window capture.
- User confirmed movement works. New feature wishes captured as Phases 2–7 in ROADMAP.md.

### 2026-09-27 — Fix: rocket not moving
- Reported: rocket shows flames but doesn't respond to arrows.
- Causes addressed: (1) title screen is an idle demo that ignored arrows and looked like gameplay —
  arrows/WASD/keypad-Enter now start the game; (2) input now comes from KEYDOWN/KEYUP events
  (`Game.held`) instead of `pygame.key.get_pressed()`, cleared on window focus loss.
- Smoke test now posts real key events and asserts the ship moves.
- Awaiting confirmation from a real play session.

### 2026-09-27 — Phase 1: retro overhaul
- Rewrote the single-file prototype into the `game/` package (see module map in CLAUDE.md).
- 320x240 canvas scaled x3 (960x720 window), optional CRT scanlines (C).
- New 17x25 hand-drawn rocket with banked frames; procedural asteroids (harmonic silhouettes,
  sphere lighting with hard terminator, banded dithering, craters with lit rims, 24 rotation frames).
- Throttle system: UP boosts (long white-hot flame + smoke, world x1.35), DOWN retro
  (lean blue flicker, world x0.8). Nozzle glow, side RCS puffs when steering.
- Background: seamless dithered nebula, drifting shaded planets, 3-layer starfield with boost streaks.
- Death: fire/spark/smoke/hull/rock debris particles, two shockwave rings, screen shake, white flash.
- States: TITLE (ambient demo), PLAYING, PAUSED, DYING, GAME_OVER, WIN (autopilot blast-off).
- Pixel-perfect mask collision. 5x7 bitmap font HUD with goal bar and throttle gauge.
- Win target raised from 10 to 30 (`WIN_SCORE`) because the old 10 lasted ~10 seconds.
- Headless `--smoke-test` (optionally `--shots DIR` for screenshots) covers every state.
- Perf: ~1.7 ms/frame avg with 17 rocks + 100 particles.

## Next steps

1. Playtest the Gunship (`--boss`): is 40 s / 3x the right feel? Tune `GUNSHIP_SPEC`,
   bullet speeds and pattern timings in `boss.py`.
2. Small enemy fighters between asteroid fields (reuse `EnemyBullet`, target interface).
3. Boss 2 (carrier launching drones) and Boss 3 (mothership, multiple phases), each via `BossSpec`.
4. Phase 5: `levels.py` with 3 levels and the boss-rush structure (weakened rematches ~1.5x).

## Open questions

- Should the old clip-art in `images/` and `astroids/` be deleted, or kept for the assignment history?
- Should health regenerate slowly, or come from pickups (Phase "later")? Currently neither.
- Should weapons get upgrades between levels?
