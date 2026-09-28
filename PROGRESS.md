# Progress

Update this file at the end of every work session: what changed, what's next, open questions.

## Status

**Branch:** `design` (from `682a781` "level 4 and a complete guide.md"): Phase 10 design,
then G1–G15 (all systems + levels 5–10) and the STAR MAP, one commit per milestone.
**Current phase:** galaxies 1 ORION REACH and 2 THE VEIL are complete — 20 levels. Galaxy 2
(G16–G29): story engine + JOURNAL, the enemy's brains, VEIL SHIFTS, elites, abilities on
SHIFT / right click, the WING BAY, upgrade tiers 6–10, and ten levels with their own flow
(ambush, pursuit, escort, darkness, mirror, rhythm, crossroads, siege, gauntlet, finale), ending
with NYX, the warp, shard 2 and VANTA's face. The user played galaxy 1 L10 ("perfect") and
G2 L1 ("good, not that hard, many weak shots" -> fewer, harder shots). **G2 L2–L10 are not
playtested yet.** Next: the user's playtest of galaxy 2; galaxy 3 BLOOM is designed only as a
herald (MORROW). NEMESIS (Phase 9) is parked.

**Starting a new session?** Read this file's Snapshot + Decisions, then CLAUDE.md (module map,
"where to look when debugging", conventions). Run the smoke test once before changing anything.

## Handoff — next session: the user's galaxy 2 playtest, then galaxy 3 design

(The notes below were written before G19; the log entries above them are current.)

State at hand-off (2026-09-28): branch `design`, everything committed and pushed, full smoke
test green (31 sections), lint clean. Built in long cloud sessions without a real window:
**nothing since G3 was seen on macOS** — ask the user to look (all surfaces are SRCALPHA or
`opaque_surface`; screenshots from `--shots` looked right). The star map is new ground: it
draws its own full screen (`starmap/view.py`), so check it in a real window first.

Decisions I had to make alone are marked **(ask)** in the log entries below — the main ones:
options live in the pause menu (G4); combo coins capped at x2 (G5/G9); OVERDRIVE only drops
once owned (G5); HUNTER / MEDIC are the level 6 / 8 gifts, MAGPIE a shop item (G6);
secondaries never hurt bosses (G7); the Wraith's music keeps playing while it hides (G11);
the level 10 boss rush is Mothership, Leviathan, Helios (not the Twins, G15); the star map
exists at all (a surprise the user asked for, G15+).

Ask the user first: how levels 5–10 feel (the bot needs ~5–6.5 min for level 10 vs the
designed 3–4; the Overmind's hive phase is the slowest part for the bot), whether the star
map is fun or should be skippable (ENTER on the title could go straight to the hangar),
whether +3% upgrade tiers feel worth it, wingman strength, prices.

G16+ plan: DESIGN section 4 (galaxy 2 THE VEIL, the villain VANTA, level flows, the
DIRECTOR) and ROADMAP G16–G29. The user played level 10 ("perfect") and asked for this;
the answers are in DESIGN section 15 (design approved). The warp gate on the
star map (`starmap/model.GATE`) is where galaxy 2's map would begin.

Working headless (cloud): `pip install -r requirements.txt pyflakes`, then
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test [--only a,b]
[--shots DIR]` and `python3 -m pyflakes ESA3.py game/ tests/ tools/`. The first start renders
the sounds into `sounds/generated/` (git-ignored, ~14 s now).

## Snapshot — what the game is right now

- **Code layout:** one package per area under `game/` (config, core, background, player, weapons,
  obstacles, minions, bosses, hazards, wingmen, pickups, levels, progression, audio, ui, flow);
  `Game` = mixins, one per responsibility. Module map + "where to look when debugging" in
  CLAUDE.md.
- **Levels 5–9 (G10–G14)**, each 3 waves (field 45 s; field 40 s -> the previous level boss at
  1.5x; field 40 s -> the level boss at 5x), own music, radio lines, gift:
  5 SOLAR FORGE (MK V): magma rocks explode (chain reactions), mine layers, sun corona ->
  HELIOS (pods detach, solar flares with gaps, magma rain). 6 GHOST NEBULA (MK VI): fog banks
  hide rocks + minions (never the ship / enemy bullets), lightning, phantoms -> WRAITH
  (teleports, decoys, fogged screen + curving shots). 7 CRYSTAL VEIL (MK VII): crystals split
  the laser into 3 beams, prism turrets ride crystals -> KALEIDOS (mirror shards reflect the
  laser, light lattice, 7-colour spirals). 8 IRON GRAVEYARD (MK VIII): wreck chunks (tough,
  coins), salvagers steal pickups, battleship silhouettes -> SCRAPJAW (assembles itself,
  throws its armour back, magnet claw, skeleton). 9 EVENT HORIZON (MK IX): the BLACK HOLE
  pulls everything incl. the ship (thrust escapes), curves shots, SLINGSHOT ring (x3 score +
  coins, x2 charge, gun shots +50%), WHITE HOLE flip every 25 s; comets, interceptors (front
  shield) -> THE TWINS (tether, revive in 8 s unless both go down, orbit / swap / propeller).
- **Level 10 SWARM HEART (G15, galaxy finale, MK X 550 HP):** a living HIVE TUNNEL — flesh
  walls on both sides that breathe (touching = 5% max HP + a push back); spore pods (swell
  0.7 s with a closing red ring, then a ring of 8 slow bullets; shot early they just pop),
  larva flocks (boids: cohesion, alignment, separation + hunting the rocket, leave after 9 s).
  4 waves: field 45 s; field 30 s -> BOSS RUSH Mothership, Leviathan, Helios (1.5x each);
  field 30 s -> THE OVERMIND 5x (`bosses/overmind.py`): P1 a hive WALL across the top with
  4 GLANDS (only they take hits, spit + spore pods + larvae; the last one tears the wall), P2
  the heart descends (Gunship fans, larvae, rings), P3 x1.2 the TENTACLE (lock-on crosshair,
  lashes to that spot = the Leviathan's lunge), P4 x1.4 the BIO-BEAM (Mothership's beam,
  tracks the rocket slowly) + spirals; a heartbeat SFX follows its rage. Then ESCAPE! (20 s,
  own music, countdown, the walls close in, debris rains, the world rushes x1.5). Then WARP:
  a 9 s cut-scene (streaks, the rocket jumps, "GALAXY 1 COMPLETE", the galaxy medal, "NEXT:
  GALAXY 2 THE VEIL"; ENTER skips) -> WIN -> SWARMBANE paint (gift) -> the star map with the
  warp gate open. CHAMPION on the win; medals saved (`save.medals`).
- **STAR MAP (G15+, the surprise):** title ENTER -> a 720x520 map of the ORION REACH; fly the
  rocket (arrows / mouse, drifts, rotates to its heading) along the route of 10 level planets
  (rock / sun / black hole / hive looks, rank badges, a ring on the frontier, locked ones dark
  with "?"); a card shows level, boss and best rank, ENTER lands = that level's hangar. Six
  hidden DATA CACHES (Vega's log, a pirate ledger, the Hollow, a forge blueprint, the Twins'
  story, a signal from the Veil): invisible until 46 px, a scanner ring + beep gets faster
  nearby; each pays 100–200 CR once and shows its story; all six = EXPLORER (STARDUST trail).
  The black hole planet pulls the rocket; the warp gate opens with the galaxy medal. Parallax
  stars, a nebula glow per level region, own music (`starmap`, F lydian). Hangar ESC -> map,
  map ESC -> title.
- **Game feel (G4):** juice tiers (medium: minion / big rock kill, ship hit = shake + 0.04 s
  hit-stop + embers; large: boss phase / kill / death = 0.12 s hit-stop + 0.5 s slow-mo +
  flash), boss damage numbers, boss name cards with an epithet, radio cards (COMMANDER VEGA,
  ENTER skips), pause menu = options (music / sound volume, reduce shake / flashes).
- **Boosts + combo (G5):** OVERDRIVE (fire rate x2), SHIELD (3 hits), MAGNET, SLOW-MO (enemy
  side at 50%), TWIN (a copy of the ship for 10 s) fall every 20–30 s; combo x2..x8 on score
  (coins x2 max), FEVER at 25.
- **Wingmen (G6):** PIP, GUARDIAN (level 4 gift), HUNTER (6), MEDIC (8), MAGPIE (shop);
  knocked out 5 s, never destroyed; XP levels 1–5, TRAIN in the hangar.
- **Weapons (G7):** 2 primary slots (R) from GUN, LASER, SCATTER, PLASMA, ARC + an automatic
  secondary (ROCKET POD, SIDE CANNONS: rocks + minions only). New primaries ~ gun DPS.
- **Skins (G8):** paint jobs, engine trails, tracer / beam colours, death styles; 6
  achievements unlock some of them.
- **Flow:** title → STAR MAP (land on a planet) → HANGAR (pick a hull, ENTER launches) → LEVEL 1 (asteroid field 75 s → WARNING, hull repaired → Gunship) → LEVEL 1 CLEAR
  screen (ship upgrade to MK II, ENTER) → LEVEL 2 "CRIMSON BELT" (rust rocks + drone formations,
  80 s → Gunship rematch 1.5x → WARNING → CARRIER 4x) → LEVEL 2 CLEAR (MK III) → LEVEL 3
  "DARK NEBULA" in 3 waves (HUD "LEVEL 3-1"): wave 1 rocks + drones 45 s; wave 2 rocks + drones
  40 s → Carrier 1.5x; wave 3 rocks + drones 40 s → LEVEL BOSS MOTHERSHIP 5x → LEVEL 3 CLEAR
  (MK IV) → LEVEL 4 "FROZEN RIFT" (frost nebula, ice + slate rocks, drones + kamikaze DIVERS):
  wave 1 45 s; wave 2 40 s → Mothership 1.5x; wave 3 40 s → FINAL BOSS LEVIATHAN 5x → WIN.
  Score carries over. 0 HP → GAME OVER → R retries the *current* level with its starting score.
  Levels are data in `levels.py` (`Level` → `Wave`s → `BossEntry`s).
- **Hulls** (`player/hulls.py`, picked in the hangar, remembered in `save.json`): ARROW 17x25
  (the original rocket, x1), WASP 13x17 (hp x0.8, firepower x1.25, speed x1.15, one engine),
  TITAN 27x25 (hp x1.4, firepower x0.71, speed x0.85, 3 engines, barrels on the pods),
  LANCE 13x33 (laser x1.3, speed x0.95, one big engine), SPECTER 15x18 (secret, level 9
  gift: hp x0.9, firepower x1.11, speed x1.1). They multiply the level's MK model and
  get its paint job; `hp * firepower == 1` keeps every boss's strength exact. Level-clear screen
  computes the upgrade numbers for the chosen hull.
- **Ship models** (`Loadout` in `config/loadouts.py`): MK I 100 HP / gun 5 / laser 80; MK II (level 2, blue
  paint) 150 HP / gun 7 / laser 110 dps, cooler laser, faster; MK III (level 3, violet) 200 HP /
  gun 9 / laser 140 + BLAST + ULTIMATE; MK IV (level 4, gold on gunmetal, ice-blue canopy)
  250 HP / gun 11 / laser 170, speed 155, BLAST + ULTIMATE; MK V–IX (levels 5–9) +50 HP,
  +2 gun, +30 laser per level up to 500 / 21 / 320. Boss balance uses the level's model.
- **Boss 4 Leviathan** (`bosses/leviathan.py`, final boss): a space serpent — rotating head
  (16 RotSprite frames x 3 phases) + 11 armour plates that follow the head's trail. Every piece
  is a weapon target (`Boss.parts()`), the head takes x1.5 (announced: "ITS HEAD IS THE WEAK
  SPOT!"). Swims to random waypoints with a slither. P1: RIPPLE (plates fire aimed shots tail
  -> head), head fans, one DIVE (1 s lock-on: red crosshair + dotted line, frozen 0.25 s
  before, then a straight lunge through that spot; contact = 4x bullet damage); P2 x1.2: more
  dives, BURSTS (every other plate fires a 4-way cross); P3 x1.4, cracked: head spiral, dives
  shed bullets sideways. Dies plate by plate from the tail. Sprites prebuilt at startup (0.6 s).
- **Level 4 extras:** `IceRock` (hp x0.6, splits from radius 7 into 3–4 fast shards, glitter +
  glassy `ice_break` sound). `Diver` (kamikaze, 18 HP, 200 pts): drops in, hovers ~1.1 s while
  its aim line follows the rocket (frozen for the last 0.3 s), then dives in a straight line;
  squads of 2–4 every ~9 s (`Difficulty.diver_interval`). New music `level4` (glassy B minor)
  and `leviathan` (E phrygian, double kicks); SFX `lock_on`, `dive`, `ice_break`.
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
  leans `\` / `/` (30°), straightening on release. SPACE fires along the nose, R switches the
  2 equipped primaries, T ultimate, ENTER skips a radio card, P pause (+ options), C scanlines, Esc menu/quit, Enter/R restart. `--boss` flag skips to the boss.
  **Mouse:** the rocket flies to the pointer (wanted speed = distance x 7, capped, eases in,
  1.5 px dead zone) and its velocity counts as the arrows it would press (boost / retro / bank
  / lean all work); left button = fire; R / T unchanged. Takes over after the pointer moves
  6 px or on a click; any arrow key or ENTER hands back to the keyboard. System cursor hidden
  while playing, a small reticle (red while firing) marks the target. Click = ENTER in menus.
- **Weapons:** machine gun (5 dmg / 0.07 s ≈ 71 DPS, spread, tracers) and laser (80 DPS beam,
  overheats after 2.5 s, usable again below 35% heat). Hits push rocks back (slow their fall).
- **Asteroids:** radius 4–14, hp = 6 + 0.8·r², split into 2–3 fragments at r ≥ 8, ram damage
  8 + 2·r, 10·r points per kill, 5 per dodge. Procedural art in 4 palettes (grey/brown/slate used,
  rust unused).
- **Boss 1 Gunship:** `BossSpec("GUNSHIP", strength=3, fight_time=40)` → ~2857 HP; a motionless
  rocket dies in ~13 s. Patterns: aimed 5-shot fan (charge glow), alternating turret shots,
  enraged below 50% (+30% speed, 14-bullet ring, per-bullet damage scaled to keep 3x). Ramming 20.
- **Dev mode** (`--dev`): DEV MENU (scrolls, 10 rows) lists every start point (each wave's field and each boss,
  e.g. "LEVEL 3-2 CARRIER 1.5X"), LEFT/RIGHT picks the hull, G god mode. In game: N skip (field end / warning / entry /
  next boss phase through the normal damage path), 1 fill BLAST+ULT, 2 power up, 3 repair, 4 +50 coins,
  G god, Esc back to the menu. R after game over retries the same start point. "DEV" badge in
  the HUD; dev runs keep records in memory only (never written).
- **Coins + rank** (G1): coins drop from rocks, minions and bosses, count as *pending* (HUD
  "CR 1240 +86") and go into the bank only when the level is won. The results screen rates
  damage taken, boss time vs par and share destroyed -> rank S/A/B/C, then pays pending +
  50 x level x rank bonus (+100 on the first clear, a replay pays 50%). Levels are grouped
  into galaxies (`GALAXIES`, galaxy 1 = ORION REACH).
- **Inventory + gifts** (G2): a new player owns ARROW + machine gun. First clear of level 1:
  choose LASER or WASP; level 2: BLAST + ULTIMATE; level 3: TITAN or LANCE; the gift not
  taken is sold in the shop (200–350 CR). Between levels (and from the title) the HANGAR
  shows SHIPS / WEAPONS tabs: equip, buy with coins, see how locked items unlock, SPACE
  launches.
- **Upgrades** (G3): hangar tab UPGRADES — ARMOR (+3% HP), GUNS (+3% gun damage), LASER
  (+3% laser DPS), ENGINE (+4% speed), CHARGE (+10% BLAST / ULT charge), 5 tiers each for
  100 / 200 / 350 / 550 / 800 CR (ENTER asks, ENTER buys). Applied after the hull on every
  level's ship model; bosses stay balanced on par. Header shows `POWER n%` = HP x better
  weapon bonus (max 132%: a 5x boss feels ~3.8x).
- **Save** (`storage.SaveData`, `save.json` in the project root, git-ignored): top 5 records
  (score, level reached, date) + unlocked levels. Written on game over / win (records) and
  level clear (unlock). Title: LEFT/RIGHT picks any unlocked level; TOP SCORES alternate with
  the controls every 6 s; GAME OVER / WIN show "NEW HIGH SCORE!" or "RECORD #n".
- **Audio** (`game/audio/`, all synthesized in pure Python): music per state — title theme,
  one track per level (A minor heroic / D minor gallop / E minor spacey), boss theme, final boss
  theme (Mothership), silence during WARNING, jingles for level clear / game over / win.
  25 SFX: gun, laser hum loop, overheat, switch, BLAST, ULTIMATE, missile hits, rock/metal hits,
  small/big rock breaks, drone / ship / boss explosions, ship hurt, enemy shots, boss roar,
  Mothership beam, warning siren, pickup, power-up, menu blips, engine loop (follows the throttle).
  Rendered to `sounds/generated/` (git-ignored) on first start (~9 s) or by `tools/build_audio.py`.
- **Tech:** 320x240 canvas ×3, all art generated in code, pixel-perfect masks, startup ~1.2 s,
  worst frame ~4.6 ms (Gunship), 2.0 ms (Mothership + BLAST + ULTIMATE, real window). Smoke test covers everything above
  (`run_smoke_test(seed=N)` for a reproducible run).

## Decisions (binding — from the user)

- **Controls stay simple.** No drift, no 360° rotation, no spin move (tried, rejected as too hard).
  Only the ±30° diagonal lean is allowed.
- Both weapons; **R** switches, **SPACE** fires (or the left mouse button).
- **Mouse control** (user's request): move by tracking the mouse, left click fires, R / T stay.
- Player has a **health bar** for the whole level; it is **refilled to max before every boss**
  in galaxy 1, **to 50% in galaxy 2** (2026-09-28).
- **Abilities (galaxy 2): one new key, SHIFT or the right mouse button** (2026-09-28).
- **Learning bosses remember the player across sessions** (saved, resettable); **VANTA's
  twist is kept** (the scout before you, left behind by Vega) (2026-09-28).
- Bosses are **3–5x stronger than the rocket** (damage race, see `BossSpec`): level 1 boss 3x,
  level 2 boss 4x, level 3 boss 5x. Earlier bosses re-appear **weakened (~1.5x)** as a warm-up.
- **3 levels**: L1 = Boss 1; L2 = Boss 1 (weak) → Boss 2; L3 = Boss 1 (weak) → Boss 2 (weak) → Boss 3.
  Then the user asked for a level 4 ("surprise me"): L4 = Boss 3 (weak) → Boss 4 Leviathan 5x.
- **Code layout is one package per area** (bosses, minions, obstacles, background, flow ...),
  `Game` split into mixins — keep new code in that shape (user wants easy debugging / extending).
- **4 hulls + hangar approved as they are** (ARROW, WASP, TITAN, LANCE; stats unchanged after the
  playtest). Keep `hp * firepower == 1`.
- **Synthesized audio approved** (music per level / boss, SFX, engine loop). Keep audio as code
  recipes in `game/audio/`, not hand-made files.
- Later: leaderboard with saved scores, more asteroid shapes/sizes.
- **Galaxies + meta progression** (Phase 10, [docs/DESIGN.md](docs/DESIGN.md)): 10 levels per
  galaxy. After each level the player **chooses 1 of 2 gifts**, the other goes to the shop.
  **New players start with ARROW + machine gun only** (existing saves keep their unlocks).
  **Coins count only when the level is won** (pending coins lost on death / retry / quit; the
  bank is never lost). Wingmen are **knocked out for a few seconds, never destroyed** (may
  change after playtests). Upgrades and wingmen are a capped edge on top of the level's par
  loadout; `BossSpec` stays. **Build order: systems first, then playtest levels 1–4 with all
  systems, then level 5 onward.**
- **Black hole (level 9) may pull the ship** (user: "make it insane"): an extra velocity on top
  of the direct controls, capped so thrust always escapes. This is not the rejected drift.
- Camera scroll is allowed for the Overmind fight (level 10).
- **Abilities later:** advanced levels (galaxy 2+) unlock abilities / features that help win;
  the key is decided then.

## Log

### 2026-09-28 — G26–G29: galaxy 2 levels 7–10 and its story (THE VEIL is complete)
- Flow plumbing: `Wave.fork` / `Wave.route` (the bosses are alternatives; `Game.wave_bosses`
  picks the hazard's `route`), `Wave.reroll` (a new VEIL SHIFT per arena), bosses may
  retreat (`update()` returns "escaped" -> `_boss_escaped()`: the wave is won, no journal
  file), hazards may pay on a won level (`bonus()` -> coins + story beat; the brood uses it).
- L7 HOLLOW MAZE (`hazards/maze.py`, `minions/egg.py`, `bosses/grinder.py`,
  `bosses/spinner.py`): void holes erase bullets of both sides; the gates open at 55% of the
  first field; no choice = the maze picks. **(ask: is a fork of two bosses fun, or should
  both be fought?)**
- L8 LAST LIGHT (`hazards/siege.py`, `minions/leader.py`): 3 x 30 s, no boss. Flagship hull
  1600, its turrets shoot minions; losing it destroys the rocket (the attempt is lost);
  above half its hull = +500 CR and `FLAGSHIP_HELD`.
- L9 THE COURT OF NYX (`hazards/court.py`, `bosses/nyx.NyxCourt`): four arenas, a new
  shift each, chained rocks (tether hurts, break one rock to free the other), NYX at 3x / 4x
  leaves at half its hull.
- L10 THE HOLLOW THRONE (`hazards/throne.py`, `bosses/nyx.Nyx`): the rush at 2x, NYX 7x /
  90 s in 5 phases; the hazard switches its darkness on for Eclipse and NYX phase 3, closes
  the void walls for NYX phase 4+ and the escape; then the warp (medal 2, shard 2,
  `G2_WARP`), the NYX paint, the Veil's map.
- Story: galaxy 2's first radio lines spell LOOK BEHIND (`ACROSTIC_2`); 6 caches on the
  Veil's map = mosaic 2 ("ONE SHIP TURNS BACK") and decoder 2; VANTA's file adds lines for
  medal 2 / decoder 2; the warp transmission shows VANTA UNMASKED (its portrait is Vega's
  helmet and collar, darkened - a clue); NYX (new speaker + portrait) greets you with what the
  enemy's player model learned and taunts every phase; heralds = the wingmates who did not
  turn back (added to the answer in `story/lore.py`). Dossiers: GRINDER, SPINNER, NYX.
- Gifts 2-6..2-10 are skins (BONE / ECHO TRAIL, RIFT TRACERS / TEAL BEAM, VEGA, HOLLOW,
  NYX). The design's RAIL / MINE TRAIL / VESPER / LUMEN are not built **(ask)**.
- 7 new tracks (maze, grinder, spinner, siege, court, nyx, throne).
- Bot (maxed, tank): L7 146 s A, L8 97 s S, L9 168 s A, L10 307 s B (rush + NYX 171 s vs
  par 150). The siege is about the flagship, not the rocket: the maxed bot (which never
  hunts leaders) ends with 300–500 of 1600 hull, a tier-5 bot lost it once in 3 runs
  **(ask: siege too hard / too easy?)**.
- Smoke: new section `veil3`; the `veil` boomerang check no longer flakes (rifts closed).

### 2026-09-28 — G19 + G21–G25: abilities, WING BAY, tiers 6–10, levels 2–6 of THE VEIL
- User feedback on G2 L1: "not that hard, but so many shots" -> galaxy 2 bosses fire
  **fewer, harder shots** (the Warden's fans every 0.8 s; the new bosses the same way), and
  galaxy 2 bosses are 6–6.5x (the Warden 5.5 -> 6.0).
- G19: `flow/abilities.py` — one ability on SHIFT / right click with a cooldown ring (PHASE
  dash + i-frames, FLARE, TIME SLIP, REPAIR DRONE, DECOY; `aim_target()` is what aimed shots
  chase). Abilities are items (`slot=ABILITY`), equipped in the hangar. The WING BAY flies a
  second wingman (`save.wingman2`). Upgrade tiers 6–10 (buyable after galaxy 1's medal;
  galaxy 1 levels count at most 5, so its balance is unchanged). MK XII–XX.
- G21 BONE REEF (`hazards/pursuit.py`, `minions/stalker.py`, `bosses/leechmaw.py`): the maw
  rises from below while you idle, UP pushes it back, a bite drops it back 30 px (no bite
  chains); big bone rocks leave a marrow core that grows back.
- G22 BROOD SANCTUARY (`hazards/escort.py`, `minions/latcher.py`, `bosses/reaper.py`): a pod
  to protect (bar at the bottom), its riders zap minions; the Reaper's harvest drains it
  unless you hit the scythe. A saved brood: +400 CR and `story` BROOD_SAVED **(ask: should
  the brood help later, e.g. in level 10?)**.
- G23 THE DARK VEIL (`hazards/darkness.py`, `minions/lurker.py`, `bosses/eclipse.py`).
- G24 MIRROR SEA (`hazards/mirror.py`, `minions/mirror.py`, `bosses/mimic.py`; `PhaseRock`;
  `ship_at()` = the ship's last 12 s).
- G25 PULSE NEBULA (`hazards/pulse.py`: `time_scale` on the enemy side, 0.25..2.25 on a
  120 bpm beat; `bosses/tempo.py`; `veil_bullets.cage()`).
- 10 new tracks, 5 dossiers; galaxy 2's first radio lines spell LOOKBEHIND (so far LOOKBE).
- Bot (maxed, all 10 tiers, tank): L1–L6 all won, bosses 18–67 s vs par 45–50. The bot
  ignores darkness and the beat, so L4 / L6 read easier for it than for a pilot.
- Smoke: new sections `abilities`, `veil2`; the cap tests are per galaxy (galaxy 2 >= 3.2x
  with all 10 tiers + PIP). **Not seen in a real window yet** (darkness uses BLEND_RGBA_SUB).

### 2026-09-28 — G18 + G20: galaxy 2 plumbing and level 1 VEIL GATE
- Multi-galaxy: `GALAXIES` has THE VEIL (`boss_repair=0.5`); `level_title()` ("G2 LEVEL 1");
  records / coins / unlocks use the global level index; a `finale` level warps even when
  more levels follow; after galaxy 1: WARP -> WIN -> gift -> the Veil's star map (arriving
  at its gate). Star map per galaxy (`MAPS`, `GalaxyMap`), warp gates both ways.
- ELITES (`Enemy.make_elite`), VEIL SHIFTS (`levels/shifts.py`, `flow/shifts.py`; start card
  + HUD label), the Veil's bullets (`minions/veil_bullets.py`; the world swaps in `burst()`
  children and skips non-solid marks), AMBUSH waves (`Wave.ambush`).
- VEIL GATE: MK XI, bone + veil rocks, WISPS (`minions/wisp.py`), RIFT PORTALS
  (`hazards/rifts.py`), THE WARDEN (`bosses/warden.py`, `Learner`), music `veil` + `warden`,
  gift VEIL paint, THE WARDEN's journal file.
- Bot tuning: the ring first blocked everything (bot 229 s vs par 60) -> wider gaps, the
  default gap faces the rocket, the inner ring swings across the outer gap (a rhythm), a
  ring hit passes 25%, fewer rocks during an ambush fight; now maxed 43–74 s vs par 45.
  A zero-upgrade pilot needs ~200 s **(ask: is galaxy 2 hard enough / too hard?)**.
- Fix: a learning boss now fetches its bandit fresh (a reloaded brain left it stale).
- Smoke: new `veil` section (+ 5 seeds); level 10 now ends on the Veil's map.

### 2026-09-28 — G17: the enemy's brains (player model, bandit, DIRECTOR)
- `game/brains/` (pure Python, saved in `save.brain`): `PlayerModel` (8x6 heatmap of
  seconds, dodge directions counted once per dodge under threat, weapon seconds, reaction
  times after a telegraph, `forget()` 0.9 per level attempt), `Bandit` (UCB1 + 15% exploring,
  step >= 0.2 so it re-learns when the player adapts), `Director` (BUILD -> PEAK 9 s ->
  BREATHER 5 s; pressure 1.0..1.6 scaled by how well the player is doing; never below 1),
  `insights()` (short lines, only claims what the numbers show).
- `flow/brains.py`: observes every frame of flight in every level; DIRECTOR only where
  `Level.director` is set (none in galaxy 1; dev key D forces it); `pressure` multiplies the
  rock spawner and the minion timers; saved at level start, win, title and quit.
- `bosses/learning.Learner` (for galaxy 2 bosses): `begin_attack()` via the saved bandit,
  `credit()` from `hurt_ship`, `lead_aim()`, `counters()`. Leviathan, Mothership and
  Overmind now call `world.telegraph()` (reaction timing; no gameplay change).
- Game over in a thinking level: "IT LEARNED: YOU HIDE AT THE BOTTOM." Journal page KNOWN
  (heatmap, dodges, weapons, reaction, notes; BACKSPACE twice = forget).
- Bot check (level 5, DIRECTOR forced): pressure cycles 1.0 -> 1.5 -> 1.0 about every 20 s;
  worst frame 1.6 ms. Smoke: new `brains` section (+ 3 seeds).

### 2026-09-28 — G16: story engine + the JOURNAL (the user's idea)
- The user asked for a board to read the story in peace (achievements, strength, defeated
  bosses and their link to VANTA, future ones blacked out, the puzzle pieces) and for a
  twisted story that makes sense at the end. Built:
- `story/` (pure data): `dialog.Line` + `cards()` (a card per speaker, 3 lines max, VANTA /
  ??? hijack), `lore.py` (boss DOSSIERS with margin notes, HERALDS, VANTA_FILE, ECHOES,
  ACROSTIC, TRANSMISSIONS, GHOST_RECORD; the docstring states the answer to the mystery).
- JOURNAL state (`flow/journal.py` + `ui/journal.py`): J on the title / star map; pages
  PILOT, BOSSES (the boss's own sprite or a silhouette), ECHOES (mosaic 3x2 + decoder), LOG
  (every radio line + intercepted transmissions, scrolls). Music: `starmap`.
- Radio: speakers with portraits (`ui/portraits.py`: VEGA, VANTA, ??? static), a queue for
  conversations, hijacked cards tear, flicker and type in red (SFX `hijack`); `page` SFX.
- The warp after galaxy 1 now carries a transmission (???, VANTA, Vega; 15 s, ENTER skips
  card by card) and hands out Dawn Key **shard 1** (`save.shards`); beaten bosses go into
  `save.bosses`; `save.story` remembers beats. The title shows the ghost record after
  galaxy 1. **(ask)** The first radio line of levels 1–10 was reworded for the acrostic
  (same meaning); the pirate ledger cache now names the job (wake what sleeps at the rift).
- Font: `#` is a solid block (redactions).
- Smoke test: new `journal` section (acrostic, line lengths, every boss has a file, cards,
  unknown -> defeated file, herald redaction, VANTA's file growing, decoder, log highlight,
  star map J, hijacked conversation); `level10` checks shard 1 + the transmission.

### 2026-09-28 — G16.0: galaxy 2 THE VEIL designed (docs only)
- The user tested level 10: "perfect". Their brief for galaxy 2: creative new minions,
  obstacles and boss shots, smarter enemies, harder levels, new and unpredictable level
  flows, and a main villain with followers, dialogs and puzzle pieces across galaxies.
- DESIGN.md section 4 rewritten: VANTA, THE HOLLOW KING and the DAWN KEY (5 shards, one per
  galaxy herald; the Overmind retroactively held shard 1); ECHO caches build a pixel
  mosaic per galaxy (the mystery of who VANTA was, a secret level per galaxy); a dialog
  system (several speakers, hijacked transmissions, reactive taunts); harder-but-fair
  levers; 10 level FLOWS (ambush, pursuit, escort, darkness, duel, siege, crossroads,
  gauntlet, mirror, rhythm) + a random VEIL SHIFT per attempt; the DIRECTOR and learning
  bosses (the NEMESIS plan); new minions / obstacles / bullet types; the 10 levels and NYX,
  THE FIRST HERALD; abilities; heralds of galaxies 3–5.
- ROADMAP: G16–G29 plan. The user answered DESIGN 4.8 (all four recommended options):
  SHIFT / right click for abilities, 50% repair before galaxy 2 bosses, learning bosses
  remember across sessions, VANTA's twist kept (DESIGN section 15, PROGRESS Decisions).

### 2026-09-28 — G15: level 10 SWARM HEART, THE OVERMIND, the warp finale + the STAR MAP
- `hazards/hive.HiveTunnel`: breathing flesh walls (width by row and time), contact hurts +
  pushes back; during an `escape` wave it collapses (walls close in to 70 px by the end,
  chitin debris, the world x1.5). `Game._world_speed()` multiplies a hazard's `world_speed`.
- `minions/swarm.py`: `SporePod`, `Larva` (boids) + spawners; `bosses/overmind.py` (4 phases,
  `Gland`s as `parts()` in phase 1, `Tentacle`, bio-beam, heartbeat, prebuilt wall surface).
- Level flow: `_finish_wave()` (next wave / level clear / win), `Wave(music, escape)`,
  `Level(finale)`; `is_final_boss()` looks at the last wave with bosses. New state WARP
  (`flow/finale.py`: medal, cut-scene, ENTER skips) and STAR_MAP (`flow/starmap.py`,
  `starmap/model.py` pure logic, `starmap/view.py` drawing). After a win: gift -> star map.
- Save: `medals`, `caches` (old saves load with empty lists). Items: SWARMBANE (gift of 1-10),
  STARDUST trail (EXPLORER achievement). MK X loadout + paint; `chitin` rocks; hive palette.
- Audio: songs `level10` (D minor heartbeat), `overmind` (A minor, 170 bpm), `escape` (E minor,
  196 bpm), `starmap` (F lydian); SFX `spore`, `heartbeat`, `warp`, `data_cache`.
- Found with the bot: the wall contact test was inverted (the rocket counted as touching
  whenever it was *inside* the tunnel) — fixed, and the smoke test now checks the middle is
  safe. The boss rush had the Twins; at 1.5x their revive made the rush drag (270 s for the
  bot) **(ask)**: swapped for Helios. The bot now respects the hive walls like a player.
- Bot playtest level 10 (`--tank`): maxed 317 s, boss 136/165 s, rank B; new player 394 s,
  boss 209/165 s, rank B. Worst frame 15 ms once (first Mothership), draw ~1.5 ms.
- Smoke test: new sections `level10` (walls, spores, larvae, rush, all Overmind phases,
  escape, warp, medal, CHAMPION, SWARMBANE, map with the gate open) and `starmap` (flying,
  landing, locked planets, bounds, black hole pull, scanner, caches pay once, EXPLORER, save);
  `level9` now ends in LEVEL_CLEAR -> ARC / SPECTER -> hangar of level 10; `menus` / `mouse`
  go through the map.

### 2026-09-27 — G14: level 9 EVENT HORIZON (+ fixes found by the bot)
- `hazards/blackhole.BlackHole`: drifts across the top third; pulls rocks, enemy bullets, the
  player's gun / scatter / plasma shots and pickups (accelerations), minions and the ship
  (the ship: an extra velocity, capped at 60% of its top speed, so thrust always escapes —
  checked in the smoke test). Event horizon: 20% max HP per hit. SLINGSHOT ring: x3 score and
  coins, x2 BLAST / ULT charge, gun shots through it +30% speed and +50% damage
  (`Bullet.boost`). Spaghettification: rocks that fall in stream out as orbiting shards.
  WHITE HOLE every 25 s (2 s warning: the disc blinks white, a red ring): 3 s of pushing
  everything out, a shockwave, swallowed enemy bullets come back as a ring. Lensing rings +
  accretion disc drawn behind the rocks.
- `Comet` (fast, slanted, a glowing tail; breaks into ice). `Interceptor` (pairs every 9 s):
  lines up with a dotted lock line, dashes, cools down 0.8 s; a front shield blocks shots
  that hit it head-on (`Enemy.armour(hit)`), open from the side and while cooling.
- THE TWINS (`bosses/twins.py`): ORA + ZEN, half the boss HP each (phases and death work on
  the sum), a laser TETHER between them hurts; a twin that goes down revives after 8 s with
  35% unless the other goes down too ("ORA REVIVES 7" over it). P1 orbit the black hole
  (their shots curve), P2 swap sides through the ring and feed bullets into the hole, P3 the
  tether spins like a propeller and the hole grows x1.35. Music `level9` (B phrygian drift),
  `twins` (C# minor chase, 176 bpm); SFX white_hole.
- SPECTER hull (15x18, secret: hp x0.9, firepower x1/0.9, speed x1.1). Gift after level 9:
  ARC | SPECTER. Level 9 is the last level: WIN -> ENTER -> gift -> title.
- Found with `tools/playtest.py` (now also prints boss time vs par):
  - a 245 ms frame when a rock size / colour wasn't prebuilt (prism crystals, magma rain):
    `AsteroidLibrary.pick()` now falls back to the nearest prebuilt size;
  - adding 4 rock palettes had thinned out the big rocks of levels 1–4 (the prebuild
    round-robin spreads 11 sizes over all palettes): levels 1–4 get exactly their old set
    again; later palettes get 3 big signature sizes built in the background during the
    menus (`queue` / `build_step`, <= 3.4 ms a frame, ~5 s) — startup stays 2.8 s;
  - bosses 6–9 ran 1.2–1.9x their par time: Kaleidos shards pass 60% of gun damage to the
    hive and regrow after 10 s, Scrapjaw's junk 25 HP and skeleton x1.5, the Twins revive at
    35%, the Wraith jumps faster (0.7 s, 0.4 s static). Now ~1.0–1.4x for the bot.
  - a phase change in the middle of a Wraith jump left stale jump state (no decoys).
- Hangar ship stats tightened (5 hulls). README / GUIDE (recipes: extras spawners, rock flags,
  hazards + event layers) / CLAUDE.md updated.
- Smoke test: new `level9` section (incl. every radio line fits its card); 6 extra seeds for
  levels 5–9 pass.

### 2026-09-27 — G13: level 8 IRON GRAVEYARD
- `WreckChunk` (palette "wreck"): 2.5x tougher, clangs (`hit_metal`, new `metal_break`),
  always drops 1–2 coins. Wrecks event layer: dark battleship silhouettes drifting past.
- `Salvager` minion (every 10 s): flies to the nearest pickup / coin, grabs up to 3 (or 7 s),
  then flees upwards; shot down, everything it stole drops twice.
- SCRAPJAW (`bosses/scrapjaw.py`): assembles itself on entry (its armour plates fly in from
  the edges). P1 six plates (4% boss HP each; hits count for the boss too, so the damage
  race is unchanged) can be shot off; it THROWS junk back (`JunkShot`: big, slow, can be
  shot apart, worth 3 bullets), cannon pairs, scrap spreads. P2 MAGNET CLAW pulls rocks and
  coins (never the ship; dotted field lines), crushed rocks become ammunition. P3 the armour
  falls off: a fast skeleton spraying sparks. Music `level8` (grinding C minor), `scrapjaw`
  (G minor metal, 160 bpm).
- Level 8 waves: field 45 s (+ divers); field 40 s -> Kaleidos 1.5x; field 40 s -> SCRAPJAW
  5x. Gift after level 8: SIDE CANNONS | MEDIC.
- Smoke test: new `level8` section.

### 2026-09-27 — G12: level 7 CRYSTAL VEIL
- `CrystalRock`: a LASER hit (`Hit.source` is the Laser now) splits into beams to the 3
  nearest rocks / minions within 90 px (80% damage each, never a boss); drawn as thin beams.
  CrystalSparkle event layer (faceted crystal moon + glinting star crosses).
- `PrismTurret` minion (every 11 s): rides a big crystal rock (1.5x tougher), fires 3-way
  shots; break the crystal and the turret falls (counts as a kill). The world now destroys
  any enemy whose hp dropped to 0 outside of combat.
- KALEIDOS (`bosses/kaleidos.py`): faceted hive + 6 shards. P1 the shards form a MIRROR
  towards the ship: laser hits on a shard bounce back (0.6 bullets of damage, the boss is
  unharmed), other weapons break shards (2.5% boss HP each; regrow after 8 s). P2 the shards
  spread and a turning LATTICE of 3 light beams blinks 0.8 s, then burns. P3 7-arm prism
  spirals in 7 hot colours (`ColoredBullet`, readability rule kept). `hit_part()` got a
  `source` argument (all bosses). Music `level7` (glassy E major), `kaleidos` (F# minor 164).
- Level 7 waves: field 45 s; field 40 s -> Wraith 1.5x; field 40 s -> KALEIDOS 5x. Gift
  after level 7: PLASMA | SOLAR paint (gift cards draw skins; a gifted skin is worn at once).
- Smoke test: new `level7` section.

### 2026-09-27 — G11: level 6 GHOST NEBULA
- `hazards/fog.FogBanks`: dithered grey-green fog banks drift down every 4–7 s and are drawn
  over rocks, minions and pickups but under the ship and enemy bullets (fairness rule).
  Lightning event layer (a dim flash + bolt deep in the nebula every 2.5–7 s).
- `Phantom` minion (pairs every 8 s): only a shimmering outline; fades in over 0.6 s, fires
  a 3-shot burst, cloaks again (2 bursts, then leaves).
- WRAITH (`bosses/wraith.py`): nearly invisible stealth frigate (alpha + shimmer outline,
  afterimages). P1 teleports between 5 spots (0.5 s of static at the arrival spot first,
  untargetable while it jumps), aimed fans + a stream. P2 two decoys per jump (only the real
  one has the blinking red light; a decoy pops in one hit, no damage to the boss). P3 the
  screen fogs over, a white flare on its muzzle before each shot, curving shots
  (`minions/bullets.CurvedBullet`). Music `level6` (haunted D minor), `wraith` (A minor,
  158 bpm); SFX teleport. Music does not drop out while it hides (a track switch restarts
  the song) **(ask)**.
- Level 6 waves: field 45 s; field 40 s -> Helios 1.5x; field 40 s -> WRAITH 5x. Gift after
  level 6: ROCKET POD | HUNTER.
- Smoke test: new `level6` section.

### 2026-09-27 — G10: level 5 SOLAR FORGE (+ level plumbing for 5–9)
- Plumbing: `Difficulty.extras` (minion spawners as data), `rock_hp` / `enemy_hp` (later ship
  models hit 2–4x harder than MK I, so fields stay meaningful), `Level.event` (background
  event layer, `background/events.py`), `Level.hazard` (new package `game/hazards/`: a
  level-wide mechanic with update + back / mid / front draw layers). `Enemy.armour(hit)`,
  `on_death()`, `drops_coins`, `stat`. `CombatMixin.area_blast()` (explosions that hurt rocks
  and minions, never the ship; their kills count, so they chain into combos).
- MK V..MK IX loadouts + paints (levels 5–9), nebulas and rock palettes for 5–9.
- Level 5: `MagmaRock` (glows, explodes: chain reactions), `MineLayer` (crosses the upper
  screen, drops a mine every 1.2 s) + `Mine` (arms after 1 s; shot = blast that clears
  rocks and minions), SunCorona event layer (dim sun at the right edge, corona arcs, heat
  shimmer). Waves: field 45 s; field 40 s -> Leviathan 1.5x; field 40 s -> HELIOS 5x.
  Radio lines, upgrade notes; music `level5` (G minor forge) and `helios` (E minor, 170 bpm);
  SFX magma_burst, flare. Gift after level 5: SCATTER | OVERDRIVE.
- HELIOS (`bosses/helios.py`): core + 4 pods on a spinning ring. P1 pods fire aimed bursts,
  SOLAR FLARE (ring glows 1 s, then a wall of fire with 1–2 gaps sweeps down). P2 pods
  detach, circle the rocket with their own armour (6% of the boss HP each; killing one drops
  coins and ends its attacks; hits on pods don't count for the core). P3 core open (x1.3),
  flares from both sides, magma rain. Balance: `AIMED_RATE` from bursts + one flare.
- Level 4 is no longer the last level: its clear goes to the results -> gift -> hangar.
- Smoke test: new `level5` section; level4 / wingmen sections work with more levels.

### 2026-09-27 — G9 (automated part): bot playtest of levels 1–4 with every system
- No human playtest possible from the cloud session, so `tools/playtest.py`: a headless
  autopilot (fires, lines up under targets, sidesteps what will cross its row, presses T)
  plays whole levels for a new player or a maxed profile; `--tank` refills the hull at
  half so every level completes and "damage taken" compares difficulty. ~3–6 s per level.
- Findings (4 runs each): every level completes with every system active, no crash; level
  times 3.5–4.5 min (design: 3–4); worst update ~16 ms headless incl. a draw (the dummy
  driver's `music.load` stalls ~600 ms on a track change — headless only, ignored).
- Coins: the G5 combo coin multiplier (x3) inflated levels 3–4 to 600–700 CR per level
  (BLAST makes combos of 50–150). Without it levels 3–4 pay ~450–550 (bosses, clear bonus
  grows with the level). **Cap lowered to x2** (+10–20%). Level 1 still pays ~170, level 2
  ~280 for this bot (rank C).
- The bot dodges badly (5–10 hull refills per level as a new player), so rank / damage
  numbers are an upper bound on difficulty, not a human's experience. **The user's playtest
  of levels 1–4 with all systems is still open (G9 not ticked).**

### 2026-09-27 — G8: skins + achievements
- Skins are inventory items (`kind=SKIN`, `slot` PAINT / TRAIL / TRACER / BEAM / DEATH,
  `look` = the palette key), so gifts, shop and locks work as for everything else. Never
  stats. Defaults (MK PAINT, CLASSIC TRAIL, GOLD TRACERS, BLUE BEAM, CLASSIC BOOM) are
  starter items; `Inventory` adds missing starter items to old saves.
- Paint jobs SOLAR (level 7 gift option later), RETRO + STEALTH (shop 400), NEON, GOLD TRIM;
  trails PLASMA BLUE (shop), TOXIC, RAINBOW, HEARTS; tracers CYAN / WHITE / EMERALD, beams
  EMERALD / VIOLET (shop 150); death styles PIXEL SHATTER (shop 200), SUPERNOVA. Shop skins
  appear after level 1 / 2 (`sold_after`). A paint skin replaces the level's MK paint
  (`loadout_for()`).
- Achievements (`progression/achievements.py`, `flow/skins.py`): UNTOUCHABLE (a boss
  without a hit) -> GOLD TRIM, FEVER PITCH -> RAINBOW, TOP OF THE CLASS (rank S) -> NEON,
  DRONE HUNTER (100 minions, lifetime) -> TOXIC, PACIFIST (a whole field without firing,
  shown as "???") -> HEARTS, CHAMPION (win) -> SUPERNOVA. Popup + fanfare; saved.
- Hangar SKINS tab (5 tabs now, spacing adapts): live previews per slot (ship in the paint,
  trail flames, tracer streaks, beam, death burst), WEARING / OWNED / price / LOCKED with the
  achievement hint, ACHIEVEMENTS n/6.
- Smoke test: new `skins` section.

### 2026-09-27 — G7: weapon slots, SCATTER / PLASMA / ARC, ROCKET POD / SIDE CANNONS
- 2 primary slots (R switches, `save.primaries`, default GUN + LASER) + 1 automatic
  secondary slot (`save.secondary`). `Game.weapons` keeps every primary in a fixed order;
  `Game.primaries` / `Game.secondary` are what the player equipped (and owns).
- New primaries, all balanced off `Loadout.gun_dps` (so hull, upgrades and `BossSpec`
  apply unchanged; smoke test checks each is 0.6–1.35x the gun's DPS on a target):
  SCATTER (5 pellets / 0.28 s, short range, +2 pellets per POWER), PLASMA (orb / 0.25 s,
  pierces 3 targets; a boss soaks it up), ARC (continuous lightning to the nearest target
  ahead, jumps 2x at 60%, +1 jump per POWER; never chains along one boss).
- Secondaries (automatic, no key) at 20% of gun DPS, **rocks and minions only** — bosses
  shrug them off so the capped edge stays intact **(ask)**: ROCKET POD (2 homing rockets
  every 1.8 s), SIDE CANNONS (fire sideways when something flies beside the ship).
- Hangar WEAPONS tab: list scrolls (6 rows), tags SLOT 1 / SLOT 2 / SECONDARY / OWNED /
  ON BOARD; ENTER on an owned primary puts it in a free slot (or slot 2), on an equipped one
  takes it out (one always stays); ENTER on a secondary toggles it. Gifts / purchases go into
  a free slot automatically. HUD shows "+ ROCKET POD" over the weapon.
- `weapons/bolts.py` (moved from wingmen), `is_boss_part()`; SFX scatter, plasma, arc
  (loop), rocket; font "^".
- Smoke test: new `arsenal` section.

### 2026-09-27 — G6: wingmen
- New package `game/wingmen/`: `Wingman` base (eases into a slot beside the ship, follows
  the lean; a bullet or rock knocks it out for 5 s: it spins + smokes, then reboots; never
  destroyed), `Bolts` (its shots, `Hit.source` = the wingman). Types: PIP (fires with you:
  3.5% -> 7.5% of your gun DPS, LV5 angled shots), GUARDIAN (orbits, blocks a bullet every
  2.0 -> 1.0 s, LV5 reflects it), MEDIC (repairs 0.4% -> 1.2% max HP/s after 3 s without
  damage, LV5 revives once per level at 25%), HUNTER (homing rockets at minions / rocks every
  2 s, 1 -> 3 per volley, never at bosses), MAGPIE (pickup radius 60 -> 120 px, LV5 10%
  double coins). TWIN boost = a copy of your ship on the other side for 10 s (25% gun DPS).
- XP: +1 per kill while it flies, +3 for its own kill, +25 per boss; levels at 0/40/120/
  250/450 XP; banked when the level ends (won or lost). Hangar TRAIN: +60 XP for 150 CR.
- `flow/wingmen.py` `WingmenMixin`; `weapons/homing.RocketSwarm` (shared with ROCKET POD
  later); `Hit.source`; save: `wingman`, `wingmen_xp`.
- Gifts: level 4 = PIP | GUARDIAN (the wingman slot opens). HUNTER / MEDIC become the level
  6 / 8 gifts **(ask)**; until then they're "COMING LATER". MAGPIE: shop (300 CR) once level
  4 is cleared (`Item.sold_after`). Level 4 is the last level for now, so the WIN screen
  got ENTER = gift -> title (R still restarts). A cleared level whose gift was never taken
  (e.g. the user's save: level 4 was cleared before the gift existed) is offered when the
  hangar opens.
- Hangar: WINGMEN tab (FLIES LV n / LV n, role, XP bar, level 5 perk); ENTER equips, ENTER
  on the flying one = TRAIN (asks first). Gift cards say NEW WINGMAN.
- Balance: wingman damage is part of the capped edge. Smoke test: maxed upgrades + a LV5
  PIP still face every 5x boss as >= 3.5x with every hull (3.52 worst, TITAN).
- Smoke test: new `wingmen` section. New SFX: wingman_down, wingman_up.

### 2026-09-27 — G5: boosts + combo / FEVER
- `pickups/boosts.py`: `Boost` pickups OVERDRIVE (fire rate x2, white flames, 6 s), SHIELD
  (bubble absorbs 3 hits, 0.6 s grace after each), MAGNET (everything on screen flies in,
  8 s), SLOW-MO (rocks, minions, bosses and enemy bullets at 50%, the ship at 100%, 4 s).
  Drops every 20–30 s in the field, every 22 s in boss fights, 5% from minions.
  OVERDRIVE is an item (WEAPONS tab, 250 CR in the shop later) = the level 5 gift; until the
  player owns it, it doesn't drop **(ask)**.
- `flow/boosts.py` `BoostsMixin`: timers, `enemy_dt()`, `fire_rate` -> `Weapon.rate`,
  `absorb_hit()`, combo: kills within 1.5 s; every 3 kills +1 multiplier (x2 .. x8) on
  score; **coins x min(combo, 3)** so the economy can't run away **(ask; design said x8)**.
  Combo 25 = FEVER 5 s (OVERDRIVE + rainbow trail + alert). A hull hit ends the combo, a
  shield hit doesn't. Music layering for FEVER not done (a `fever` jingle plays instead).
- HUD: active boosts with draining bars (left, under the level), `X4 / COMBO 12` + timer
  (right, under the coins); shield ring with a pip per hit left. New SFX: boost, shield,
  combo, fever. `hurt_ship()` now ignores calls while the ship blinks (no double shake).
- Note: gun cooldowns are whole frames, so x2 fire rate is ~x1.7 at 60 fps (base gun timing
  left as is: changing it would silently rebalance every boss).
- Smoke test: new `boosts` section.

### 2026-09-27 — G4: game feel (juice tiers, damage numbers, name cards, radio, options)
- User: G3 "runs perfectly", "continue developing until you reach G14". Working through
  G4 -> G14 in order, one commit per milestone; decisions I had to make alone are marked
  **(ask)** so the user can overrule them.
- `flow/juice.py` `JuiceMixin`: `juice("small"|"medium"|"large", x, y)` = shake + hit-stop +
  embers + flash (`tuning.JUICE`); large events (boss phase / kill, ship explodes) add 0.5 s
  slow-mo at x0.35. `Game.update()` runs the world on `world_dt(dt)`; popups, shake, alerts
  and the radio use real time. Medium: minion kill, big rock kill, ship hit.
- Boss damage numbers (`ui/popup.DamageNumber`): damage summed per 0.2 s, pops where it hit
  (gold from 60 up). Boss name card on WARNING (slides in; `Boss.EPITHET` per class).
- Radio cards (`ui/radio.py`): COMMANDER VEGA portrait (24x24 rows), types out under the HUD
  after the level title, ENTER finishes / closes. `Level.radio`, `Wave.radio` = data.
- Options **(ask: placement)**: in the pause menu (P, UP/DOWN, LEFT/RIGHT): music + sound
  volume 0–10, screen shake full / reduced (x0.3), flashes full / reduced (x0.25). Saved in
  `save.json` `options`. `Audio.set_volume()`, `ScreenShake.scale`.
- Font: `( ) = *` glyphs (brackets showed as "?" before).
- Smoke test: new `feel` section; waits after a boss kill got `JUICE_PAD` (slow-mo stretches
  world time).

### 2026-09-27 — G3: upgrades (5 tracks x 5 tiers), POWER %
- User: "continue to complete G3". G2 still not playtested (no feedback yet).
- Numbers: the handoff suggested +6% per tier, but ARMOR x GUNS at +30% each = 1.69 would
  make a 5x boss feel ~3.0x, below the roadmap's ">= ~3.5x" check and DESIGN's "about 3.8x".
  Chose **+3% HP / gun / laser per tier** (max 1.15 x 1.15 = POWER 132%, 5x boss -> 3.78x),
  ENGINE +4% speed, CHARGE +10% charge rate (utility, not in POWER). Costs 100/200/350/550/800
  (10,000 CR for everything). DESIGN 6.3 updated. Tell the user if +3% feels too small.
- `config/tuning.py` `UPGRADE_TIERS`, `UPGRADE_COSTS`, `UPGRADE_BONUS`; `Loadout.charge_rate`
  (default 1, read by `CombatMixin._charge()` / `_charge_ultimate()`, incl. boss thirds).
- `progression/upgrades.py`: `Track`, `TRACKS`, `cost()`, `apply(loadout, tiers)`,
  `power_ratio(tiers)` (HP x the better weapon; gun and laser don't stack).
- `SaveData.upgrades` {track: tier}, clamped 0..5 on load, missing = {} (old saves).
  `Inventory.tier()` / `tiers` / `upgrade_cost()` / `buy_upgrade()`; `grant_all()` leaves
  tiers at 0 (tests stay exact).
- `loadout_for()` applies upgrades after the hull; `BossSpec` untouched (par).
- Hangar: third tab UPGRADES (`items.UPGRADE`; list of tracks with 5 pips + next price or
  MAX, preview = 3x track icon + big pips + TIER n/5, details "HULL +6% > +9%" and the value
  on the next level's model). ENTER asks "ARMOR TIER 3 FOR 350 CR? ENTER", ENTER buys; not
  enough credits / maxed are refused. `POWER n%` in the header on every tab. Ship stat bars
  and weapon numbers now show the equipped hull + upgrades (weapon lines used par before).
- Smoke test: new `upgrades` section (costs, apply, power, cap vs every boss and hull, hangar
  ask / buy / saved / refused / maxed, ship flies the upgraded model, boss HP stays par,
  CHARGE x1.5 fill, old + broken saves). Full test + seeds 1–3 pass, lint clean. Real macOS
  window not checked (cloud session).

### 2026-09-27 — G2: gifts, HANGAR 2.0, shop, starter inventory
- User playtested G1: "feels ok", coins per level (215–250) good. Asked for G2.
- `progression/items.py`: `Item` catalog (ids = hull / weapon names, 2 blurb lines <= 21
  chars, price), `STARTER` = ARROW + GUN, `GIFTS`: L1 LASER | WASP, L2 BLAST + ULTIMATE
  (fixed; level 3 is built around them — moved from L3 in the draft), L3 TITAN | LANCE, L4 none
  until wingmen (G6). DESIGN.md table updated. Prices LASER 200, WASP 250, TITAN / LANCE 350.
- `progression/inventory.py` `Inventory`: owns / status (OWNED, SHOP, LOCKED) / unlock hint /
  gift options / claim (other option -> shop) / buy / grant_all. A save without an inventory
  (v1, or v2 from G1) gets STARTER + every gift of the levels before `unlocked` (the user's
  save: everything, WASP kept). `SaveData` stores `owned`, `shop`, `gifts`.
- Gating: `loadout_for()` drops BLAST + ULT without SPECIALS; `switch_weapon()` only cycles
  owned weapons (HUD hides "R SWITCH" without the laser); the hangar only equips owned hulls.
- Flow: results -> ENTER -> `State.REWARD` (gift cards, first clear only) -> HANGAR before the
  next level (was: straight into the level). Title -> HANGAR as before.
- HANGAR 2.0 (`ui/hangar.py` + `flow/hangar.py` `HangarMixin`): tabs SHIPS / WEAPONS
  (LEFT/RIGHT), list (UP/DOWN), preview box (live ship with flames / 3x weapon icon / dark
  silhouette when locked), ship stat bars or weapon numbers, blurb, bank. ENTER: equip; ENTER on
  the equipped ship launches; shop item asks "BUY X FOR N CR? ENTER", then buys; locked says
  "GIFT AFTER LEVEL N". SPACE launches. Menu background dimmed. New SFX `denied`.
- `ui/item_art.py` (shared by hangar and gift screen), `ui/gifts.py`.
- Smoke test: every section starts with all items (`grant_all`); `next_level()` helper (results
  -> gift -> hangar -> launch); new `inventory` section (starter gating, gift choice, shop
  refused / confirm / buy + saved, locked hint, launch, fixed gift, old-save migration).
  Full test + 4 seeds pass, lint clean. Real macOS window: hangar (locked silhouette) and gift
  cards render correctly.

### 2026-09-27 — G1: galaxies, coins, rank + results screen, save file v2
- `levels`: `Galaxy` (number, name, levels, `key(level)` -> "1-3"); `GALAXIES`, `LEVELS` = all
  levels in play order, `galaxy_of()`. HUD shows "G1 LEVEL 3-2". `save.unlocked` now counts
  levels in play order (same numbers for galaxy 1).
- New pure-logic package `game/progression/`: `results.LevelStats` (damage taken, boss time vs
  `BossSpec.fight_time`, share destroyed -> weighted score -> S/A/B/C), `economy` (drops,
  `Payout`: pending + 50 x level x rank bonus + 100 first clear; replay pays 50%).
- `pickups`: spinning `Coin` (1) / `BigCoin` (5); `Pickup.sound` / `fanfare` replace the
  isinstance checks in `world.py`. Rocks (6–45% by size), minions (1–3), boss phase change (5),
  boss death (30 + 10 x level, half for a rematch) drop coins; boss coins home in; coins still
  on screen when the level is won are collected.
- `flow/progression.py` `ProgressionMixin`: pending coins (lost on death / retry / quit, shown as
  "N CREDITS LOST" on game over), stats hooks, `_bank_level()`, results tally + stamp sound.
- Results screen (level clear + win): 3 rated stats with bars, rank stamp, picked up / clear
  bonus / first clear or replay, bank counting up. SFX `coin`, `rank`. Dev hotkey 4 = +50 coins.
- `SaveData` v2: `version`, `coins`, `cleared` {key: best rank}; v1 files load with an empty
  bank (so the user's current save starts at 0 CR, levels and records kept); broken values ->
  fresh save. The first clear with the coin system pays the first-clear bonus.
- Smoke test: new `economy` section (rank maths, payout, v1 migration, pending lost on death,
  retry, win banks + results, replay half). Full test passes (6 seeds for economy); lint clean.
  Real macOS window: coins + results render correctly, worst frame 5.5 ms.

### 2026-09-27 — Design branch: galaxies, progression, new content (docs only)
- User's direction (new branch `design`): design levels 5–10 so that every 10 levels form a
  galaxy; creative bosses + minions; backgrounds, colours, planets, hit and fire effects; new
  guns / lasers / rockets; each cleared level unlocks one thing (a skill, ship or gun), with
  what already exists coming as gifts the player can choose from; temporary boosts (e.g. faster
  fire) and new features per galaxy; wingmen that level up; an inventory to equip and improve
  gear; coins collected during and after levels to spend on upgrades; skins and gear effects.
  Goal: retro feel, modern expectations, "exciting so it does not bore them".
- Wrote [docs/DESIGN.md](docs/DESIGN.md): pillars, galaxy structure + story (IRON FLEET ->
  LEVIATHAN -> the SWARM), levels 5–10 (SOLAR FORGE / HELIOS, GHOST NEBULA / WRAITH, CRYSTAL
  VEIL / KALEIDOS, IRON GRAVEYARD / SCRAPJAW, EVENT HORIZON / THE TWINS, SWARM HEART /
  OVERMIND), 6 minions, galaxies 2–5 sketch, weapons (SCATTER, PLASMA, ARC, RAIL + automatic
  secondaries), gift table per level, coins economy, upgrades on top of the *par* loadout
  (keeps `BossSpec` valid, capped +30%), boosts + combo/FEVER, 5 wingmen, HANGAR 2.0 mock-up,
  skins, colour/readability rules, juice tiers, code map, 8 open questions.
- ROADMAP: new Phase 10 with milestones G0–G15. CLAUDE.md links the design doc.
- Skills: searched for agent skills. The official plugin marketplace has nothing for
  pygame / 2D arcade design (the `unity` plugin is Unity-only). Vetted
  `gamedev-skills/awesome-gamedev-agent-skills` (Apache-2.0): `game-feel` and
  `level-design` are useful (engine-neutral principles, Godot code); `pygame-core`
  contradicts this repo (`key.get_pressed()`, image files, pygame-ce), `roguelike` is
  turn-based, `game-ui-ux` is about responsive layouts. Copying the two good ones into
  `.claude/skills/` was **blocked by the permission check** — left for the user to decide.
  Their key ideas (juice tiers, sawtooth pacing, teach -> test) are in DESIGN.md anyway.
- User answered the 8 design questions (see Decisions). DESIGN.md updated: coins banked only
  on a win (pending counter), black hole redesigned "insane" (pulls the ship too, curved
  shots, SLINGSHOT x3 zone, WHITE HOLE flip, Twins fight around it), abilities for galaxy 2+.
  ROADMAP Phase 10 reordered: systems G1–G8, playtest levels 1–4 (G9), levels 5–10 (G10–G15).

### 2026-09-27 — Mouse control, level 4 "FROZEN RIFT", LEVIATHAN; NEMESIS design
- User: game "working wonderfully". Asked for mouse control (move by tracking the mouse, left
  click fires, R / T unchanged), then level 4 ("surprise me"), and floated an endless mode vs a
  boss that learns from the player — to be developed and tracked separately.
- Mouse: `core.input.Mouse`; `Game.update(dt, keys, mouse=None)`; `Ship.update(target=...)`
  (`_follow` = wanted velocity, `_stick` = the arrows it corresponds to); events for motion /
  buttons, click = ENTER in menus, cursor hidden while playing, reticle in `ui/screens.py`.
- Level 4: `MK4`, `mk4` paint, `NEBULA_FROST`, `ICE_SHARDS`; `IceRock` + `rock_class()` (split
  rules moved from `combat.py` onto the rock class: `splits`, `fragments()`, `break_sound()`);
  `minions/diver.py`; `Difficulty.diver_interval`; `bosses/leviathan.py` (`Segment`, trail
  layout). `Boss` base got `parts()`, `hit_part()`, `contact_damage`, `enter(k)`, `prebuild()`.
- Title controls rewritten to 5 lines (mouse added; "(LEVEL 3)" showed as "?LEVEL 3?" because
  the font has no brackets). Dev menu scrolls.
- Smoke test: new `mouse` and `level4` sections; campaign now ends with level 3 clear -> level 4;
  busy covers level 4 + Leviathan. 12/12 seeds pass for mouse/level4/campaign.
- Real macOS window checked (Leviathan fight, mouse steering, dev menu): renders correctly,
  worst update+draw 9.8 ms. Startup +0.6 s for the Leviathan's rotated heads.
- Wrote [docs/GUIDE.md](docs/GUIDE.md) on request: where assets come from (all generated in
  code, audio WAV cache), what is fixed vs random, architecture, workflow, recipes. README
  updated (mouse, level 4).
- NEMESIS: written up as ROADMAP Phase 9 (player model + bandit, generations, analysis card,
  milestones N1–N5). Not started — waiting for the user's go and answers.

### 2026-09-27 — Restructure into packages, 4 hulls + hangar, synthesized soundtrack + SFX
- User asked for: every area in its own folder (bosses, minions, background, obstacles, flow ...)
  for easier debugging and development; new sound effects and background music; new rocket
  ships with different shapes and dimensions.
- Restructure (behaviour unchanged, verified by the smoke test before adding features):
  `settings.py` → `config/` (display, palette, tuning, loadouts); `sprites.py` split to where
  each sprite is used (each boss file = sprite + muzzles + class); `game.py` (1445 lines) →
  `flow/game.py` + mixins (events with one `_keys_<state>` handler per state, level_flow, world,
  combat, sound, dev) + `ui/screens.py`; smoke test → `tests/smoke.py` in 14 named sections
  (`--only a,b`). Largest module now ~300 lines.
- Hulls: `Hull` dataclass (rows, nozzles, barrels, multipliers, `apply(loadout)`); `Ship.equip`
  takes a hull; gun barrels / nose / missile launch points read from the hull. `State.HANGAR`,
  `ui/hangar.py` (2x previews, stat bars vs the other hulls), `SaveData.ship`.
- Audio: `synth.py` (pulse/triangle/saw/sine/noise, ADSR, echo, DC block, step sequencer,
  seamless loops), `sfx.py`, `music.py` (songs as chord progressions + 8th-note melodies),
  `bank.py` (WAV cache), `player.py` (`play`, `loop`, `music`; rate limits for bursty sounds).
  `Level.music` / `BossEntry.music` are data. Old `nes.mp3` / `crash.wav` no longer used.
- Fixed a flaky smoke check that existed on `main` (4/150 runs): the "gun kills a small rock"
  rock sat between the two barrel streams; it's now on a barrel's line (0/450 failures).
- Perf: startup 1.2 s (same as `main` on this machine), boss fights 0.8 ms worst update+draw.
  Verified in a real macOS window (hangar, TITAN vs Carrier, LANCE), audio enabled.
- User playtest: "so perfect" — sounds great, ships creative. No balance or mix changes asked
  for. User commits the branch and continues on a new one.

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

Suggestions, roughly in order of value for effort. Items marked **ask** change controls or
rules, so check with the user first (see "Working with the user" in CLAUDE.md). The user will
bring their own ideas too — those come first.

**Now: Phase 10 (the user's direction, design approved).** Follow ROADMAP Phase 10:
systems G1 -> G8, playtest G9, then levels G10 -> G15. Several items below are now part of it:
level results screen + rank (G1), unlocks (G2), game feel + options (G4), new minions /
obstacles (G8–G13), score combo (G5).

**Quick wins (polish)**
1. **Options menu** (from title + pause): music volume, SFX volume, scanlines, fullscreen;
   saved in `save.json` (`SaveData` already has the pattern). Closes the last Phase 6/7 items.
2. **Game feel:** short hit-stop + slow-motion on a boss kill, a flash/zoom on phase changes,
   screen transitions (wipe) between states, damage numbers on bosses (reuse `ui/popup.py`).
3. **Level results screen:** time, accuracy, damage taken, kills → rank S/A/B/C and bonus points.

**Bigger features**
0. **NEMESIS mode** (the user's idea, ROADMAP Phase 9) — **ask**: start with N1 (arena shell).
4. **Endless mode** (ROADMAP Phase 5): `Difficulty` ramps over time, a random boss (weakened →
   stronger) every few minutes, own leaderboard. The level/wave data model already fits:
   generate `Wave`s on the fly instead of reading `LEVELS`.
5. **Score depth:** combo multiplier for kills in quick succession (resets on hit), no-hit boss
   bonus, 3-letter arcade name entry for records (Phase 6).
6. **New obstacles** (`obstacles/`): ~~ice rocks~~ (done, level 4), metal rocks (tough,
   drop POWER), explosive rocks (chain blast hurts nearby rocks and drones), huge slow rocks,
   comet with a trail. Each = art palette + `Asteroid` subclass.
7. **New minions** (`minions/`): ~~kamikaze diver~~ (done, level 4), mine layer, shielded interceptor (only
   vulnerable from the side), turret on a big rock. Each = sprite + `Enemy` subclass + a
   formation; mix them into levels via `Difficulty`.
8. **Unlocks / progression:** hulls or paint jobs unlocked by achievements (e.g. TITAN after
   level 1, gold paint for a no-hit boss) — stored in `save.json`, shown locked in the hangar.
9. **Hull abilities** — **ask** (adds a key): one special per hull on SHIFT, e.g. WASP short
   dash with i-frames, TITAN shield bubble, LANCE overcharged beam, ARROW repair drone.
10. ~~**Level 4 / new boss**~~ — done (FROZEN RIFT + LEVIATHAN). A level 5 works the same way.

**For the coursework / quality**
11. **Architecture doc with a UML class diagram** (Mermaid in a `docs/ARCHITECTURE.md`):
    inheritance (`Boss` → Gunship/Carrier/Mothership, `Enemy` → Drone, `Weapon` → ...,
    `Pickup` → ...) and the `Game` mixins. Shows the OOP design at a glance for grading.
12. **Unit tests** (pytest) for pure logic next to the smoke test: `BossSpec`, `Hull.apply`,
    `SaveData`, synth (`chord`, `freq`, `Song` lengths), `raycast`.
13. **Gamepad support** (pygame joystick → the same `Keys` set) and a **packaged build**
    (PyInstaller app for macOS/Windows, so it runs without installing Python).

## Open questions

- Skills: allow copying `game-feel` + `level-design` from awesome-gamedev-agent-skills
  (Apache-2.0) into `.claude/skills/`? The permission check blocked it.
- Playtest: does mouse steering feel right? Knobs in `config/tuning.py`: `MOUSE_FOLLOW` (how
  eagerly it chases the pointer), `MOUSE_LEAN` (how fast a move must be to boost / lean).
  Should the pointer mark the ship's centre (now) or sit above the nose? Right click = switch?
- Level 4 balance: Leviathan 5x / 80 s, dive contact 4x bullet damage, divers 24 contact damage.
- NEMESIS (Phase 9): go ahead with N1? Rounds with the chosen hull at MK IV, or start at MK I
  and upgrade through perks?
- Should `sounds/generated/` be committed (7.6 MB, instant first start) instead of rendered on
  first start (~9 s)? Currently git-ignored.
- Delete the unused `sounds/crash.wav` + `sounds/nes.mp3` and the old clip-art in `images/` /
  `astroids/`, or keep them for the assignment history?
- Decided: health comes from repair-kit pickups (small + full); weapons upgrade per level.
- Decided (playtests): Gunship 3x, level 2 balance, level 3, hulls and audio all approved.
