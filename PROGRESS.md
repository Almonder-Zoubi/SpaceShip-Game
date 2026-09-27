# Progress

Update this file at the end of every work session: what changed, what's next, open questions.

## Status

**Current phase:** Phase 1 complete → next up **Phase 2 (Levels)**. See [ROADMAP.md](ROADMAP.md).

## Log

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

## Next steps (Phase 2)

1. Add `game/levels.py`: a `Level` dataclass (name, goal, `Difficulty`, palettes, nebula tint)
   and a list of 5–8 levels. `DEFAULT_DIFFICULTY` becomes level 1.
2. New states `LEVEL_INTRO` and `LEVEL_CLEAR` in `game.py`; replace `WIN_SCORE` with `level.goal`.
3. Prebuild asteroid variants per level palette in `AsteroidLibrary` (the "rust" palette is unused so far).
4. Comet hazard (reuse `ParticleSystem` for the trail).
5. Save file (`save.json`) for unlocked levels and best scores.

## Open questions

- Should the old clip-art in `images/` and `astroids/` be deleted, or kept for the assignment history?
- Lives system (Phase 4) vs. one-hit death — one-hit for now, it's the classic feel.
