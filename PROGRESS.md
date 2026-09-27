# Progress

Update this file at the end of every work session: what changed, what's next, open questions.

## Status

**Branch:** `levels` (branched from `main` at `33cb7a0 "end level boss to win"`). Levels 2+3 uncommitted.
**Current phase:** all 3 levels playable (user: "perfect"), dev mode + minimal save done →
next: see "Next steps". See [ROADMAP.md](ROADMAP.md).

## Snapshot — what the game is right now

- **Flow:** title → LEVEL 1 (asteroid field 75 s → WARNING, hull repaired → Gunship) → LEVEL 1 CLEAR
  screen (ship upgrade to MK II, ENTER) → LEVEL 2 "CRIMSON BELT" (rust rocks + drone formations,
  80 s → Gunship rematch 1.5x → WARNING → CARRIER 4x) → LEVEL 2 CLEAR (MK III) → LEVEL 3
  "DARK NEBULA" in 3 waves (HUD "LEVEL 3-1"): wave 1 rocks + drones 45 s; wave 2 rocks + drones
  40 s → Carrier 1.5x; wave 3 rocks + drones 40 s → FINAL BOSS MOTHERSHIP 5x → WIN.
  Score carries over. 0 HP → GAME OVER → R retries the *current* level with its starting score.
  Levels are data in `levels.py` (`Level` → `Wave`s → `BossEntry`s).
- **Ship models** (`Loadout` in settings): MK I 100 HP / gun 5 / laser 80; MK II (level 2, blue
  paint) 150 HP / gun 7 / laser 110 dps, cooler laser, faster; MK III (level 3, violet) 200 HP /
  gun 9 / laser 140 + BLAST + ULTIMATE. Boss balance uses the level's model.
- **BLAST (MK III):** meter fills from damage to rocks/drones (+kill bonus, x3 for drones).
  Full + SPACE held → 3 s piercing beam from the nose (450 dps to everything in it, gold for
  gun / blue for laser), normal weapon pauses, meter drains, then recharges. Automatic, no key.
- **ULTIMATE (MK III, key T):** charges the same way (slower) + 0.25 per third of a boss's
  health. T → 2.4 s missile storm (~48 homing missiles, 45 dmg each) spread over every target on
  screen, bigger targets get more. Hits from BLAST/ULTIMATE don't recharge them (`Hit.charges`).
- **Boss 3 Mothership:** 126x60, 3 phases. P1 aimed 3-shot fans from 4 turrets, drones, bullet
  rings; P2 x1.2 + sweeping BEAM (0.9 s red warning line, then a column down that follows the
  ship slowly) + spiral; P3 x1.4, cracked, double counter-spirals, 5-shot fans. Lights
  green → orange → red. Same phase rewards as the Carrier.
- **Pickups:** small repair kit (+30 HP) every 13–20 s in the field and every 15 s in boss fights,
  sometimes from big rocks / drones; gold FULL REPAIR (15% of field kits, phase-3 reward);
  POWER core (weapon power +1, max 2, homes in on the ship). Kits near the ship drift to it.
- **Boss 2 Carrier:** 3 phases at 2/3 and 1/3 HP. Between phases it roars 1.6 s (invulnerable,
  flashes red, bullets cleared, drops POWER core + repair kit, "PHASE 2 / CARRIER IS ANGRY!").
  P1 drones + aimed cannons + bullet rain; P2 x1.25 speed, spiral + cannon fans + more drones;
  P3 x1.5, cracked hull, bullet walls with a gap + 3-arm spiral. Lights cyan → orange → red.
- **Power levels:** gun P1 adds a nose round every other shot, P2 every shot + angled side
  rounds; laser +35% dps / -20% heat per level, wider beam. Reset at every level start.
- **Controls:** arrows/WASD move directly (light inertia, stops fast). UP = boost (long flames,
  world x1.35), DOWN = retro (small blue flame, world x0.8). UP+LEFT/RIGHT = diagonal and the rocket
  leans `\` / `/` (30°), straightening on release. SPACE fires along the nose, R switches gun/laser,
  P pause, C scanlines, Esc menu/quit, Enter/R restart. `--boss` flag skips to the boss.
- **Weapons:** machine gun (5 dmg / 0.07 s ≈ 71 DPS, spread, tracers) and laser (80 DPS beam,
  overheats after 2.5 s, usable again below 35% heat). Hits push rocks back (slow their fall).
- **Asteroids:** radius 4–14, hp = 6 + 0.8·r², split into 2–3 fragments at r ≥ 8, ram damage
  8 + 2·r, 10·r points per kill, 5 per dodge. Procedural art in 4 palettes (grey/brown/slate used,
  rust unused).
- **Boss 1 Gunship:** `BossSpec("GUNSHIP", strength=3, fight_time=40)` → ~2857 HP; a motionless
  rocket dies in ~13 s. Patterns: aimed 5-shot fan (charge glow), alternating turret shots,
  enraged below 50% (+30% speed, 14-bullet ring, per-bullet damage scaled to keep 3x). Ramming 20.
- **Dev mode** (`--dev`): DEV MENU lists every start point (each wave's field and each boss,
  e.g. "LEVEL 3-2 CARRIER 1.5X"), G god mode. In game: N skip (field end / warning / entry /
  next boss phase through the normal damage path), 1 fill BLAST+ULT, 2 power up, 3 repair,
  G god, Esc back to the menu. R after game over retries the same start point. "DEV" badge in
  the HUD; dev runs keep records in memory only (never written).
- **Save** (`storage.SaveData`, `save.json` in the project root, git-ignored): top 5 records
  (score, level reached, date) + unlocked levels. Written on game over / win (records) and
  level clear (unlock). Title: LEFT/RIGHT picks any unlocked level; TOP SCORES alternate with
  the controls every 6 s; GAME OVER / WIN show "NEW HIGH SCORE!" or "RECORD #n".
- **Tech:** 320x240 canvas ×3, all art generated in code, pixel-perfect masks, startup ~1.0 s,
  worst frame ~4.6 ms (Gunship), 2.0 ms (Mothership + BLAST + ULTIMATE, real window). Smoke test covers everything above
  (`run_smoke_test(seed=N)` for a reproducible run).

## Decisions (binding — from the user)

- **Controls stay simple.** No drift, no 360° rotation, no spin move (tried, rejected as too hard).
  Only the ±30° diagonal lean is allowed.
- Both weapons; **R** switches, **SPACE** fires.
- Player has a **health bar** for the whole level; it is **refilled to max before every boss**.
- Bosses are **3–5x stronger than the rocket** (damage race, see `BossSpec`): level 1 boss 3x,
  level 2 boss 4x, level 3 boss 5x. Earlier bosses re-appear **weakened (~1.5x)** as a warm-up.
- **3 levels**: L1 = Boss 1; L2 = Boss 1 (weak) → Boss 2; L3 = Boss 1 (weak) → Boss 2 (weak) → Boss 3.
- Later: leaderboard with saved scores, more asteroid shapes/sizes, realistic sound effects.

## Log

### 2026-09-27 — Dev mode + minimal storage
- User: level 3 "really perfect and sweet". Asked for a dev mode to start any level for
  debugging, then minimal storage for records and levels.
- `Game(dev=..., save_path=...)`, `State.DEV_MENU`, `Game.dev_items()`, `dev_key()`,
  `dev_skip()`; `start(level, score, wave, boss)` generalises `--boss`; `retry_point`.
- New `storage.py` (`SaveData`: JSON, atomic write via temp file + `os.replace`, corrupt or
  missing file = fresh start, `path=None` = memory only). `SAVE_FILE` in settings.
- Smoke test uses a temp save file (never the player's), checks reload / corrupt file / title
  level select / dev menu flow / god mode / hotkeys / dev runs not saved.

### 2026-09-27 — Level 3: waves, BLAST, ULTIMATE, Mothership final boss
- User: level 2 "really nice". Level 3 spec from the user: ultimate that hits all targets on
  screen; 3 waves (minions / minions + previous boss / minions + final boss); a gun that charges
  by hitting rocks and minions and then fires a big blast for a few seconds; ultimate charges the
  same way, key T, +0.25 per 0.3 of boss health.
- Interpretation (tell the user if wrong): BLAST fires automatically when full and SPACE is
  held; the wave-2 boss is the Carrier at 1.5x (no Gunship in level 3); both specials only on MK III.
- `levels.Wave`; `Difficulty.wave_interval` renamed `formation_interval` (drone formations).
- `weapons.Charged` base → `Blast`, `Ultimate` (+ `Missile`); `Hit.charges`.
- `boss.Mothership`; `Boss._launch_drones()` shared by Carrier and Mothership; `Game.hurt_ship()`
  is public (the beam uses it).
- HUD: "LEVEL 3-2" label, BLAST / ULT meters (bottom right, "HOLD SPACE" / "PRESS T" hints),
  boss name shortened to "MOTHERSHIP 2/3". WARNING says FINAL BOSS / LEVEL BOSS as appropriate.
- Smoke test: level 3 flow, charging, blast, missiles, boss-third charge, beam; `kill()` helper
  (one hit can't skip a phase), stray-rock-proof gun test. 16/16 seeds pass.

### 2026-09-27 — Level 2: ship upgrade, repair kits, drones, Carrier boss (3 phases)
- User playtested level 1: "perfect". Asked for: stronger ship + guns in level 2, two repair kit
  types (also in boss fights), end boss with 3 health phases that gets angrier while the player
  gets advantages.
- New `levels.py` (Level data, boss rush), `pickups.py` (RepairKit, FullRepair, PowerCore),
  `enemies.py` (`Enemy` base, `Drone`, `drone_formation`, `EnemyBullet` moved here).
- `settings.Loadout` (MK1/MK2); `Ship.equip()` switches sprites/hull/speed; `Weapon.equip()` +
  `power_up()`. `BossSpec.player` = ship model the balance is computed for.
- `Boss` base: `PHASES`, phase thresholds clamp damage, `roar`, `on_phase()`, `phase_marks`.
  `Carrier` sprite (94x58, 3 recoloured variants) via `CharCanvas` + `mirrored()` + `outlined()`.
- HUD: longer HP bar for MK II, LEVEL n, PWR pips, boss PHASE n/3 with phase ticks, floating
  popups (+30 HP, POWER UP!), mid-screen alerts. Font got `+` and `%`.
- States: LEVEL_CLEAR (upgrade screen). CLI: `--level 2`, `--boss` now = the level's last boss.
- Crimson nebula for level 2 (darkened after a screenshot showed bullets were hard to read).

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

1. Phase 6 extras (ask the user): 3-letter name entry for records, per-mode tables once
   endless mode exists, saved settings (scanlines).
2. Endless mode (Phase 5), Phase 7 (asteroid variety, sound effects).

## Open questions

- Is the Gunship fight fun at 3x / 40 s? (needs the user's playtest)
- Should the old clip-art in `images/` and `astroids/` be deleted, or kept for the assignment history?
- Decided: health comes from repair-kit pickups (small + full); weapons upgrade per level (MK II).
- Level 2 balance (Carrier 4x, kit frequency, POWER bonuses) needs the user's playtest.
