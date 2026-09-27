# Roadmap

Goal: turn the simple "dodge falling pictures" prototype into a polished retro arcade shooter
with simple arcade controls, weapons, bosses, three levels, an endless mode and a saved leaderboard.

Status: Phases 1–4 done, Phase 5: all three levels playable (level select + endless missing).
Details and next steps: [PROGRESS.md](PROGRESS.md).

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
- [x] 5x7 bitmap font, HUD (later reworked in Phase 3: HP, progress/boss bar, score, weapon)
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

Decided: both weapons, R switches, SPACE fires where the nose points.

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
- [x] Enemy ship base class for small fighters (`enemies.Enemy`) + `Drone`
- [x] Drone formations (V / line / snake) in the level 2 asteroid field
- [x] Boss intro warning ("WARNING"), health bar, phase changes, big death explosion
- [x] Playtest + tune the Gunship — user: "perfect"
- [x] Multi-phase bosses: `Boss.PHASES`, roar between phases; the player gets bullets cleared,
      a POWER core (weapon power +1) and a repair kit at every phase change
- [ ] Remaining bosses (each a `Boss` subclass + `BossSpec`):
  - [x] Boss 2 — CARRIER (4x, 3 phases): drones, cannons, rain → spiral → bullet walls
  - [x] Boss 3 — MOTHERSHIP (5x, 3 phases, final boss): fans, drones, rings → sweeping beam →
        double spirals

## Phase 5 — Three levels

- [x] `Level` definitions as data: asteroid mix, difficulty, background tint, boss list, ship model
- [x] Ship upgrades per level (`Loadout`): level 2 = MK II (hull 150, gun 7, laser +38%, faster)
- [x] Repair kits: small (+30 HP) and full; in the field and during boss fights
- [x] Levels made of waves (`Wave`): level 3 = minions / minions + Carrier / minions + Mothership
- [x] MK III (level 3): BLAST (charged piercing beam, auto on SPACE when full) and
      ULTIMATE (key T, homing missile storm; charges from hits + every third of boss health)
- [x] Levels 1, 2 and 3 playable
- [x] Structure: asteroids + enemies → boss rush → level boss
  - Level 1: Boss 1
  - Level 2: Boss 1 (weakened) → Boss 2
  - Level 3 (user's wave design): wave 1 → wave 2 + Boss 2 (weakened) → wave 3 + Boss 3
- [ ] Weakened bosses: less HP, slower fire, simpler patterns — a warm-up, not a wall
- [x] Health persists through the level and is refilled to max right before the boss
      (done for the single level; must also refill before each boss in a boss rush)
- [x] Level intro / level clear (upgrade) screens; game over retries the current level
- [x] Level select for unlocked levels (title, LEFT/RIGHT)
- [x] Dev mode (`--dev`): start at any wave / boss, god mode, skip / charge / power / repair keys
- [ ] Endless ("open") mode: difficulty ramps continuously (spawn rate, speed, size, enemy mix)

## Phase 6 — Score, leaderboard & saving

- [ ] Scoring: destroyed rocks, enemies, bosses, time bonus, no-hit bonus, combo multiplier
- [ ] Arcade-style name entry (3 letters) on a new high score
- [x] Minimal records: top 5 (score, level, date) in `save.json`, shown on the title screen
- [ ] Top-10 leaderboard per mode (levels / endless)
- [x] Persist unlocked levels
- [ ] Persist settings

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
