# Roadmap

Goal: turn the simple "dodge falling pictures" prototype into a polished retro arcade game
with levels and an endless mode that keeps getting harder and faster.

## Phase 1 — Retro overhaul (visuals, feel, architecture)

- [x] Split single script into an OOP `game/` package
- [x] Low-res 320x240 canvas scaled x3 (true chunky pixels)
- [x] Hand-drawn pixel-art rocket with banking frames (left/right tilt)
- [x] Procedural pixel-art asteroids: lumpy silhouettes, craters, dithered lighting, outline, rotation frames
- [x] Engine flames driven by a throttle: UP = boost (long, bright flames + smoke), DOWN = retro (flames shrink, cool blue)
- [x] Side RCS puffs when steering, nozzle glow
- [x] Ship physics (acceleration, inertia, friction) instead of fixed steps
- [x] Parallax starfield with speed streaks when boosting, dithered nebula, drifting planet
- [x] Explosion: fire + debris + smoke particles, shockwave ring, screen shake, white flash
- [x] Pixel-perfect collisions (masks)
- [x] 5x7 bitmap font, HUD (score, best, goal progress, throttle gauge)
- [x] States: title, playing, pause, dying, game over, win (ship blasts off)

## Phase 2 — Levels

- [ ] `Level` definitions (data, not code): goal score, `Difficulty`, asteroid palettes, background tint
- [ ] Level intro card ("LEVEL 2 — RUST BELT") and level-complete transition
- [ ] 5–8 handcrafted levels with rising spawn rate, speed and asteroid size
- [ ] New hazards unlocked per level:
  - [ ] Comets (fast, burning trail — uses particle system)
  - [ ] Splitting asteroids (break into smaller rocks)
  - [ ] Sideways drifting / zig-zag rocks
- [ ] Level select from title screen for unlocked levels
- [ ] Persist unlocked levels + best scores in `save.json`

## Phase 3 — Endless ("open") mode

- [ ] Endless mode on the title menu
- [ ] Difficulty ramps continuously with time: spawn interval ↓, speed ↑, bigger rocks, mixed hazards
- [ ] Distance-based score + multiplier for boosting / near misses
- [ ] "Speed up!" warning banners at each tier
- [ ] Separate endless high score (persisted)

## Phase 4 — Juice & extras

- [ ] Shield / slow-mo / magnet power-ups
- [ ] Lives + short invulnerability blink
- [ ] Synthesised chiptune SFX (thrust rumble, near-miss whoosh, pickup blip)
- [ ] Menu: sound on/off, fullscreen toggle
- [ ] Gamepad support
- [ ] Top-10 local leaderboard with 3-letter initials (arcade style)
