# Roadmap

Goal: turn the simple "dodge falling pictures" prototype into a polished retro arcade shooter
with simple arcade controls, weapons, bosses, four levels, an endless mode and a saved leaderboard.

Status: Phases 1–4 done, Phase 5: all four levels playable (endless missing), Phase 7: sound done,
mouse control added. Next big feature (proposed): Phase 9 — NEMESIS, a boss that learns.
Code restructured into one package per area (see CLAUDE.md).
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
- [x] Mouse control: the rocket flies to the pointer (eases in), left click fires, R / T as
      before; an arrow key hands control back to the keyboard. Click = ENTER in menus
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
- [x] Level 4 "FROZEN RIFT" (MK IV): ice rocks that shatter into shards, kamikaze DIVERS
      (lock on, then dive), Mothership rematch 1.5x, final boss LEVIATHAN 5x — a segmented
      space serpent (every plate is a target, head = weak spot x1.5, locks on and lunges,
      ripple fire tail->head, 4-way bursts, spiral + shedding scales in phase 3)
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
- [x] Sound effects that match the action (synthesized in code, `game/audio/`):
  - [x] Engine rumble that follows the throttle (boost louder, retro quieter)
  - [x] Laser hum, machine-gun bursts, hits on rock vs metal
  - [x] Explosions sized by what explodes (small rock / big rock / drone / ship / boss)
  - [x] Boss warning siren, boss roar, Mothership beam, UI blips, pickups
- [x] Music per level + boss theme + final boss theme, title theme, jingles (clear / game over / win)
- [ ] Volume settings

## Ships

- [x] Four hulls with their own shape and size, picked in a hangar screen (remembered in the save):
      ARROW (balanced), WASP (small + fast, fragile), TITAN (wide, heavy armour, slow),
      LANCE (long + thin, laser specialist). `hp * firepower == 1` keeps boss balance exact
- [x] Playtest the hull trade-offs — user: "so creative", no changes
- [ ] Unlockable hulls / paint jobs (achievements), hull abilities on SHIFT (ask first)

## Phase 8 — Polish ideas (suggested, see PROGRESS.md "Next steps")

- [ ] Options menu: music / SFX volume, scanlines, fullscreen (saved)
- [ ] Game feel: hit-stop and slow-mo on boss kills, state transitions, boss damage numbers
- [ ] Level results screen with rank (S/A/B/C), combo multiplier, no-hit bonus
- [ ] New minions: kamikaze diver, mine layer, shielded interceptor, rock turret
- [ ] Architecture doc with UML class diagram; pytest unit tests for pure logic
- [ ] Gamepad support, packaged app (PyInstaller)

## Phase 9 — NEMESIS: a boss that learns (proposed, needs the user's go)

The user's idea: a separate endless mode where the player is thrown straight into a boss
fight, the boss gets stronger every round, and it **learns from the player** like a human
opponent who studies you — different each time, so the player wants "one more try".

**Honest scope note:** no neural network. Training one (reinforcement learning) needs numpy /
torch, hours of offline training and would not adapt to *one* player in real time; the game's
rule is "pygame only". Instead: online learning in pure Python that updates during and between
fights, is saved in `save.json`, and can be *shown* to the player. This is real learning
(a player model + a multi-armed bandit), explainable, and testable — good for the coursework too.

How the NEMESIS learns:
1. **Player model** (recorded every frame, persisted): where the rocket spends its time
   (8x6 heatmap), which way it dodges when a bullet comes close (L/R/U/D counts), gun vs laser
   share, reaction time to telegraphs (lock-on -> first move), how often T is used.
2. **Attack choice = multi-armed bandit** (epsilon-greedy or UCB1): every attack pattern keeps
   an average "damage dealt per second". The boss picks what works on *you*, still exploring
   ~10% of the time. The values persist between runs = its memory.
3. **Aiming from the model:** leads shots by your velocity, biases fans toward your usual dodge
   side, drops bullet walls / mines on your heatmap hot spots, times dives to your reaction time.
4. **Counters** (unlocked by generation): hug the bottom -> floor sweepers; laser-heavy ->
   a mirror shield only the gun breaks; ULT spam -> decoy drones that soak missiles.
5. **Generations:** each round won by the player -> the boss evolves (strength +8% via
   `BossSpec`, one new ability from an unlock tree). Rounds = the leaderboard number.
6. **Make the learning visible** (the addictive part): before a round an ANALYSIS card —
   "NEMESIS GEN 7 / YOU DODGE LEFT 68% / YOU CAMP BOTTOM-LEFT / NEW: PREDICTIVE AIM";
   after a death: "IT LEARNED: ...". Between rounds the player picks 1 of 3 perks.
7. **Fairness rails:** capped learning rate, strength ramp per round only through `BossSpec`,
   always-telegraphed attacks, a "RESET NEMESIS BRAIN" menu option.

Code plan: `game/nemesis/` (`brain.py`: `PlayerModel`, `Bandit` — pure logic, unit-testable;
`boss.py`: `Nemesis(Boss)` + attack library; `perks.py`), `flow/arena.py` (`ArenaMixin`: rounds,
perks, analysis), `ui/analysis.py`, states `ARENA_INTRO` / `ARENA_PERK`, `SaveData.nemesis`
(brain + arena leaderboard). Smoke section `nemesis` + seeded tests for the bandit.

- [ ] N1 Arena shell: title menu entry, straight into a boss, rounds with rising `BossSpec`
      strength, own leaderboard (best round + score) — no learning yet
- [ ] N2 Player model recording + ANALYSIS card ("it watches you")
- [ ] N3 Bandit attack choice + predictive aim (adapts within and across runs)
- [ ] N4 Counter abilities, generations / unlock tree, perks between rounds
- [ ] N5 Playtest tuning, reset-brain option, polish (own music + NEMESIS sprite that
      visibly changes per generation)

## Later / nice to have

- [ ] Power-ups (shield, weapon upgrade, slow-mo), lives + invulnerability blink
- [ ] Gamepad support, fullscreen toggle, settings menu
