# Progress

Update this file at the end of every work session: what changed, what's next, open questions.

## Status

**Branch:** `design` (from `682a781` "level 4 and a complete guide.md"): Phase 10 design,
then G1–G3 (coins + rank, gifts + HANGAR 2.0, upgrades).
**Current phase:** 4 levels playable + mouse control. New direction from the user: **galaxies of
10 levels + meta progression** (gifts per level, coins, upgrades, wingmen, inventory, skins,
new weapons, bosses and effects). Designed in [docs/DESIGN.md](docs/DESIGN.md), milestones
G0–G15 in [ROADMAP.md](ROADMAP.md) Phase 10.
Design approved (answers in DESIGN.md section 14). G1 (coins, rank) playtested: "feels ok",
215–250 CR per level is good. G2 done (gifts 1 of 2, HANGAR 2.0 + shop, new players start
with ARROW + gun), not playtested yet. **G3 done** (upgrades: 5 tracks x 5 tiers, UPGRADES
tab, POWER %), waiting for the user's playtest together with G2. Next: **G4 game feel pass**.
Systems first, then a full playtest of levels 1–4, then level 5.
NEMESIS (Phase 9) is parked behind Phase 10.

**Starting a new session?** Read this file's Snapshot + Decisions, then CLAUDE.md (module map,
"where to look when debugging", conventions). Run the smoke test once before changing anything.

## Handoff — next session: playtest G2 + G3, then G4 (game feel)

State at hand-off (2026-09-27): branch `design`, G1–G3 committed and pushed, full smoke test
green, lint clean. **G2 and G3 are not playtested yet**: ask the user how the gift screen,
hangar controls (ENTER equip / buy, ENTER again confirms, SPACE launch), prices and the
upgrade feel (+3% per tier is deliberately small, see DESIGN 6.3) are before tuning anything.
The real macOS window check of the UPGRADES tab was **not** done (cloud session, headless
only): the screen uses only SRCALPHA icons and `fill`s on the canvas, but ask the user to look.

Working headless (cloud): `pip install -r requirements.txt pyflakes`, then
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test [--only a,b]
[--shots DIR]` and `python3 -m pyflakes ESA3.py game/ tests/ tools/`. The first start renders
the sounds into `sounds/generated/` (git-ignored, ~9 s).

G4 (ROADMAP Phase 10, DESIGN section on juice tiers): shake / hit-stop / particles per tier,
boss damage numbers, boss name cards, radio cards, options (volume, reduce shake / flashes).
Options need a place in the menus: ask the user where (title? pause?) before adding keys.

## Snapshot — what the game is right now

- **Code layout:** one package per area under `game/` (config, core, background, player, weapons,
  obstacles, minions, bosses, pickups, levels, audio, ui, flow); `Game` = mixins, one per
  responsibility. Module map + "where to look when debugging" in CLAUDE.md.
- **Flow:** title → HANGAR (pick a hull, ENTER launches) → LEVEL 1 (asteroid field 75 s → WARNING, hull repaired → Gunship) → LEVEL 1 CLEAR
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
  LANCE 13x33 (laser x1.3, speed x0.95, one big engine). They multiply the level's MK model and
  get its paint job; `hp * firepower == 1` keeps every boss's strength exact. Level-clear screen
  computes the upgrade numbers for the chosen hull.
- **Ship models** (`Loadout` in `config/loadouts.py`): MK I 100 HP / gun 5 / laser 80; MK II (level 2, blue
  paint) 150 HP / gun 7 / laser 110 dps, cooler laser, faster; MK III (level 3, violet) 200 HP /
  gun 9 / laser 140 + BLAST + ULTIMATE; MK IV (level 4, gold on gunmetal, ice-blue canopy)
  250 HP / gun 11 / laser 170, speed 155, BLAST + ULTIMATE. Boss balance uses the level's model.
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
  leans `\` / `/` (30°), straightening on release. SPACE fires along the nose, R switches gun/laser,
  P pause, C scanlines, Esc menu/quit, Enter/R restart. `--boss` flag skips to the boss.
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
- Player has a **health bar** for the whole level; it is **refilled to max before every boss**.
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
