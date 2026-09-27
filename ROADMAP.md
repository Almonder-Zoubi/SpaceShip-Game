# Roadmap

Goal: turn the simple "dodge falling pictures" prototype into a polished retro arcade shooter
with drifting flight, weapons, bosses, three levels, an endless mode and a saved leaderboard.

## Phase 1 — Retro overhaul (visuals, feel, architecture) ✅

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
- [x] Fix: sprites rendered as black boxes on macOS (canvas must have no alpha channel)

## Phase 2 — Flight controls ✅ (revised)

Tried drift physics + 360° rotation + spin: too hard to control, reverted at the user's request.
Decided: **direct arcade controls, the rocket always faces up, never rotates.**

- [x] Arrows move the ship directly with light inertia; two arrows (UP + LEFT/RIGHT) = diagonal
- [x] Diagonal lean: UP+RIGHT tilts the rocket like '/', UP+LEFT like '\' (30°, 3 RotSprite
      frames per side); straightens on release. Shots, laser and flames follow the lean
- [x] UP = boost flames + faster world, DOWN = retro flames + slower world (Phase 1 behaviour)
- [x] Weapons fire where the nose points (straight up, or along the diagonal lean)
- [x] ~~Drift, 360° rotation frames, aim lock, SHIFT spin~~ — removed

## Phase 3 — Weapons, destructible asteroids & health ✅

Decided: both weapons, R switches, SPACE fires (straight up).

- [x] Weapon system with a common `Weapon` base class (`weapons.py`)
  - [x] Laser: continuous beam, pixel-exact raycast, overheats (heat gauge + OVERHEAT in HUD)
  - [x] Machine gun: alternating wing barrels, tracer rounds, spread, muzzle flashes
- [x] Asteroids have hit points scaled by area: big rocks need sustained fire
- [x] Hit feedback: white hit flash (bullets), chips, sparks at laser impact, shake on destroy
- [x] Big asteroids (radius >= 8) split into 2–3 fragments
- [x] Hits push rocks back: gun and laser slow a rock's fall (heavier rocks resist, never stops)
- [x] Points for destroying rocks (10 x radius) and for dodging (5)
- [x] Player health bar (100 HP); asteroid hits cost 16–36 HP by size, knockback,
      1 s blinking invulnerability, red screen flash; 0 HP = explosion + game over
- [x] Level progress bar (distance flown) replaces "dodge 30"

## Phase 4 — Enemies & bosses

Balance rule (decided): a boss is **3–5x stronger than the rocket**. Measured as a damage race:
`(boss HP / player DPS) / (player HP / boss DPS)` = strength. Level 1 boss 3x, level 2 boss 4x,
level 3 boss 5x. Rematched earlier bosses are weakened to ~1.5x so they're a warm-up.

- [x] `BossSpec(name, strength, fight_time)` derives boss HP and damage from the player's stats
- [x] `Boss` base class (enter, fight, dying, dead; weapon-target interface; hit flash;
      damage smoke/sparks; vent exhaust) + `EnemyBullet`
- [x] Boss 1 — GUNSHIP (70x48, strength 3x, 40 s fight): strafes; aimed 5-shot fan from the
      nose cannon with charge-up glow; alternating aimed turret shots; below 50% HP it enrages
      (30% faster, adds a 14-bullet ring, damage per bullet scaled so strength stays 3x)
- [x] Level flow: asteroid field → WARNING (hull repaired to full) → boss → explosion sequence → WIN
- [x] Boss health bar with name, ramming damage, bullets fizzle when the boss dies
- [ ] Enemy ship base class for small fighters (movement pattern + weapon + HP)
- [ ] Small enemy fighters in waves between asteroid fields
- [ ] Remaining bosses:
  - [ ] Boss 2 — e.g. carrier that launches drones
  - [ ] Boss 3 — e.g. mothership with multiple phases / weak points
- [x] Boss intro warning ("WARNING"), health bar, phase changes, big death explosion

## Phase 5 — Three levels

- [ ] `Level` definitions as data: asteroid mix, difficulty, background tint, boss list
- [ ] Structure: asteroids + enemies → boss rush → level boss
  - Level 1: Boss 1
  - Level 2: Boss 1 (weakened) → Boss 2
  - Level 3: Boss 1 (weakened) → Boss 2 (weakened) → Boss 3
- [ ] Weakened bosses: less HP, slower fire, simpler patterns — a warm-up, not a wall
- [ ] Health persists through the whole level (asteroids and enemies drain it) and is
      refilled to max right before each boss fight
- [ ] Level intro / level clear screens, level select for unlocked levels
- [ ] Endless ("open") mode: difficulty ramps continuously (spawn rate, speed, size, enemy mix)

## Phase 6 — Score, leaderboard & saving

- [ ] Scoring: destroyed rocks, enemies, bosses, time bonus, no-hit bonus, combo multiplier
- [ ] Arcade-style name entry (3 letters) on a new high score
- [ ] Top-10 leaderboard per mode (levels / endless), saved to `save.json`
- [ ] Persist unlocked levels and settings

## Phase 7 — Asteroid variety & sound

- [ ] More asteroid shapes: elongated, jagged/shattered, round, clustered; ice, metal, crystal types
- [ ] Wider size range including huge slow rocks
- [ ] Sound effects that match the action:
  - [ ] Engine rumble that follows the throttle (boost louder, retro quieter)
  - [ ] Laser hum, machine-gun bursts, hits on rock vs metal
  - [ ] Explosions sized by what explodes (small rock / big rock / ship / boss)
  - [ ] Boss warning siren, UI blips
- [ ] Music per level + boss theme; volume settings

## Later / nice to have

- [ ] Power-ups (shield, weapon upgrade, slow-mo), lives + invulnerability blink
- [ ] Gamepad support, fullscreen toggle, settings menu
