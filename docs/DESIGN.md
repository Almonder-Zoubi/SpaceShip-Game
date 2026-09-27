# Dodging Asteroid — Design Bible

The creative plan for everything after level 4: galaxies, new levels, bosses, weapons,
rewards, coins, wingmen, inventory, skins and the look of the game.

- Status: **approved direction** (branch `design`, 2026-09-27). The user's answers are in
  section 14 and in PROGRESS.md "Decisions". Numbers (prices, HP, timings) are starting
  values to tune in playtests.
- Build order and checkboxes: [ROADMAP.md](../ROADMAP.md) Phase 10.
- How to add a level, boss, minion or hull in code: [GUIDE.md](GUIDE.md) section 6.

---

## 1. Vision and pillars

**Retro on the outside, modern in the hand.** It looks and sounds like a 1987 cartridge
(320x240, chunky pixels, chiptune), but it plays like a game from today: short runs, a reward
after every level, a build the player makes their own, and bosses you want to talk about.

Every new feature has to follow these five pillars:

1. **Easy to learn, deep to master.** Controls stay as they are (arrows or mouse, SPACE, R, T).
   New power comes from *gear*, not from new buttons. Secondary weapons, wingmen and boosts
   work automatically.
2. **Something new every level.** Each level adds one new thing (a minion, an obstacle rule
   or a background event) and gives one reward. A new player never gets everything at once.
3. **Bosses are the stars.** Each boss has one idea you remember ("the one that hides in
   fog", "the one made of junk"), a name card, 3 phases and its own music.
4. **Fair and readable.** Every attack is telegraphed. Enemy bullets always stand out from
   the background. No damage from something the player couldn't see coming.
5. **Your ship, your style.** Coins, upgrades, wingmen and skins let the player find the build
   that suits them and show it off.

What stays binding (PROGRESS "Decisions"): simple controls without drift or 360° rotation,
the `BossSpec` damage-race balance, `hp * firepower == 1` for hulls, all art and audio made in
code, and pygame as the only dependency.

---

## 2. Structure: galaxies of 10 levels

```
GALAXY 1  ORION REACH      levels 1-10   (1-4 done)
GALAXY 2  THE VEIL         levels 1-10   sketch below
GALAXY 3  BLOOM            levels 1-10   sketch below
...
```

- Levels are numbered **inside** the galaxy: HUD "G1 L5-2" (galaxy 1, level 5, wave 2).
- Each galaxy has a **palette family**, a **faction** (enemy style), a **new game mechanic**
  and a **finale**: level 10 is a boss rush plus the galaxy boss, followed by a warp
  cut-scene into the next galaxy.
- Boss strength follows the existing rule: level bosses 3–5x, returning bosses about 1.5x
  as a warm-up. Galaxy bosses are 5x, with more phases rather than more HP.
- Level length: 3–4 minutes (2–3 waves). A whole galaxy is about 40 minutes.

### Story (short, told in text cards and radio lines)

The pilot is a scout on the frontier of the ORION REACH. The pirates of the **IRON FLEET**
(Gunship, Carrier, Mothership) are only the first problem. Their mining woke the
**LEVIATHAN** in the ice (level 4), and its cry called the **SWARM**, a hive of living ships
from beyond the Veil. Galaxy 1 ends at the **SWARM HEART**. When it dies, a warp gate opens
and the pilot follows the Swarm home (galaxy 2).

How the story is told (all in the 5x7 font, skippable with ENTER):
- a 2–3 line **radio card** with a pixel portrait (COMMANDER VEGA, 24x24) before each level
- a **boss name card** on WARNING, e.g. `SCRAPJAW  -  THE JUNK KING`
- the **level-clear screen** shows the reward and one line of story

---

## 3. Galaxy 1 — ORION REACH, levels 5–10

Levels 1–4 stay as they are. Each new level follows the pattern: **field (teach the new
thing) → returning boss (warm-up) → level boss**. Balance comes from `BossSpec` against the
level's par loadout (section 6.3).

| # | Name | New obstacle / hazard | New minion | Level boss (5x) | Background |
|---|---|---|---|---|---|
| 5 | SOLAR FORGE | **Magma rocks**: glowing cracks; they explode when destroyed and damage nearby rocks and drones (chain reactions) | **Mine layer**: drops blinking mines that arm after 1 s | **HELIOS** | a huge sun at the right edge, corona flares, heat shimmer |
| 6 | GHOST NEBULA | **Fog banks** drift down and dim everything inside them (never the ship or enemy bullets) | **Phantom**: cloaked, fades in 0.6 s before it fires | **WRAITH** | grey-green fog in 3 parallax layers, lightning flashes |
| 7 | CRYSTAL VEIL | **Crystal rocks**: a laser hit refracts into 3 beams (reward for using the laser) | **Prism turret**: sits on a big crystal and fires refracted shots | **KALEIDOS** | violet/teal nebula, glittering stars, a crystal moon |
| 8 | IRON GRAVEYARD | **Wreck chunks**: big, tough metal, drop coins | **Salvager**: steals pickups and coins and flies away (kill it to get them back) | **SCRAPJAW** | rust orange, silhouettes of dead battleships drifting past |
| 9 | EVENT HORIZON | **Black hole** that pulls *everything*, the ship too; shots curve, a SLINGSHOT danger zone, a WHITE HOLE flip (see below); **comets** with trails | **Interceptor**: front shield, vulnerable only from the side or after its dash | **THE TWINS** | accretion disc, stars stretched by lensing |
| 10 | SWARM HEART | **Spore pods** burst into a small telegraphed bullet ring | **Larvae**: tiny, fast, move in flocks (boids) | **OVERMIND** (galaxy boss) | organic hive walls scrolling at both sides (tunnel) |

Returning bosses (1.5x): L5 Leviathan, L6 Helios, L7 Wraith, L8 Kaleidos, L9 Scrapjaw, and L10
a boss rush of Mothership, Leviathan and the Twins before Overmind.

### Boss designs

Each boss has one **big idea**, 3 phases (the usual roar, POWER core and repair kit between
phases) and its own track.

**HELIOS — the living forge (L5).** A round forge-station, 90x90, with 4 turret pods on a
slowly spinning ring.
- P1: pods fire aimed bursts; every 6 s a **SOLAR FLARE** sweeps the screen as a wall of fire
  with 1–2 gaps, telegraphed by an orange glow on the ring 1 s before.
- P2: pods **detach** and orbit the ship as separate targets (`parts()`). Killing a pod gives
  coins and removes that pod's attacks.
- P3: core exposed, flares come from two sides, plus magma rain (falling magma rocks).
- Idea: *choose to kill the pods first or burn the core.*

**WRAITH — the stealth frigate (L6).** It is invisible except for a shimmer outline and
afterimages.
- P1: teleports between 5 points, always 0.5 s of static at the arrival point first.
- P2: makes **2 decoys**. Only the real one has a blinking red running light, and decoys pop
  in one hit.
- P3: the whole screen fogs, the Wraith lights a flare on itself before each attack, and
  shots bend in a curve.
- Idea: *read the tells, not the sprite.* Music drops out while it is hidden.

**KALEIDOS — the prism queen (L7).** A crystal hive with 6 shards orbiting it.
- P1: shards form a **mirror shield** facing the ship. Laser hits bounce back as a thin
  harmless-looking beam (reduced damage to the player); the gun breaks shards.
- P2: shards spread out and shoot light beams between them (lines to stay out of) that
  rotate slowly.
- P3: the queen splits white light into 7 coloured spirals (rainbow bullet patterns, tuned
  to be readable).
- Idea: *the laser, the player's favourite, now needs thinking.*

**SCRAPJAW — the junk king (L8).** A mech-ship built from wrecks.
- Enters by **assembling itself**: wreck chunks fly in and snap onto the frame.
- P1: shooting off armour pieces is possible; Scrapjaw **throws them back** (big slow
  projectiles that can be shot apart).
- P2: a magnet claw pulls rocks and coins toward it (visible field lines; the ship is *not*
  pulled).
- P3: armour gone, a fast skeleton that fires sparks everywhere.
- Idea: *the arena is its ammunition.*

**THE BLACK HOLE (L9 hazard, the user asked for "insane to try").** The whole level is played
next to a gravity well, which slowly drifts across the top third of the screen.
- **It pulls everything**: rocks, minions, enemy bullets, the player's shots, coins, and the
  ship. The controls stay direct (arrows or mouse move the ship as always); the pull is an
  extra velocity added on top, strongest near the core, capped so full thrust always
  escapes. A tuning knob sets its strength.
- **Curved shots**: bullets bend around it. Enemy fans become curving arcs, and your gun
  stream wraps around it and can hit things *behind* the hole.
- **SLINGSHOT zone**: a glowing ring around the core. While the ship is inside it, score and
  coins x3 and BLAST/ULT charge x2, with blue-shifted speed lines. The risk is real: the
  **event horizon** in the middle deals heavy damage per second. Shots that pass through
  the ring come out faster and deal +50% damage.
- **Spaghettification**: rocks that fall in stretch into lines and burst into shards that
  orbit it once and then fly out.
- **WHITE HOLE flip** (every ~25 s, 2 s warning: the disc turns white and the music
  reverses): for 3 s it **pushes** everything outward. Every bullet on screen scatters,
  rocks are thrown at the edges, and a shockwave ring expands.
- **Lensing**: the background stars and the planet warp around it (a cheap trick:
  pre-rendered distortion rings).

**THE TWINS — ORA and ZEN (L9).** Two ships linked by an energy tether (a boss made of 2
bosses, one HP bar each). They fight *with* the black hole.
- The tether is a moving laser line; don't touch it.
- If one twin dies, the other **revives it within 8 s** unless it is killed too. A "REVIVE
  8..7..6" timer is shown.
- P1: they orbit the black hole on opposite sides, so their shots curve in from two
  directions.
- P2: they swap sides in a crossing dash *through* the slingshot zone (they come out
  faster), and they fire bullets into the hole that come out in the next white-hole flip.
- P3: the tether spins like a propeller around the black hole, and the hole grows.
- Idea: *damage has to be balanced, and gravity is both their weapon and yours.*

**OVERMIND — the Swarm heart (L10, galaxy boss).** Bigger than the screen; the camera
scrolls up along its body.
- Stage A: the hive wall. Destroy 4 spore glands to open the way.
- Stage B: the heart. 3 phases that each reuse **one attack from an earlier boss**, now in
  organic form (Gunship fan, Leviathan dive, Mothership beam). A boss-rush callback.
- Stage C, **ESCAPE**: 20 s timer, the hive collapses, and the player flies up through
  falling debris. Surviving opens the warp gate.
- Idea: *a finale that remembers the whole galaxy.*

### Minions (details)

| Minion | HP | Behaviour | Counterplay |
|---|---|---|---|
| Mine layer | 25 | crosses the screen horizontally, drops a mine every 1.2 s | mines arm after 1 s; shooting one sets off a small blast that hurts enemies too |
| Phantom | 20 | cloaked, fades in 0.6 s before it fires a 3-shot burst | watch the shimmer |
| Prism turret | 40 | fixed to a crystal rock, fires refracted shots | kill the crystal and the turret falls |
| Salvager | 30 | flies to pickups and coins, then flees upward | kill it before it leaves to get everything back x2 |
| Interceptor | 35 | front shield, dashes at the ship | flank it, or hit it during its 0.8 s cool-down after a dash |
| Larvae | 4 | flocks of 8–16, boids | spread weapons, ULTIMATE |

---

## 4. Galaxies 2+ — sketch (details later)

Each galaxy adds **one new mechanic for the whole galaxy** and one gear slot.

| Galaxy | Theme / faction | Palette | New mechanic | New slot |
|---|---|---|---|---|
| 2 THE VEIL | the Swarm's home: bio-mechanical | purple, teal, bone | **Elite enemies** (golden aura, drop more coins); galaxy modifiers per level (e.g. "rocks fast", "double minions") | 2nd wingman |
| 3 BLOOM | living nebula, plant-like creatures | green, pink, gold | **Route map**: after each level choose 1 of 2 next levels (Star Fox style) | 2nd secondary weapon |
| 4 CHRONO RIFT | time-bending ancients | cyan, white, black | **Time zones**: areas where bullets slow down or speed up | more abilities |

**Abilities (decided: later, unlocked in advanced levels).** From galaxy 2 on, some gifts
are *abilities and features* that help to win levels: e.g. a hull special per ship (WASP
dash with i-frames, TITAN shield bubble, LANCE overcharge, ARROW repair drone), time slow,
a phase shift through bullets, a second life per level. They get designed when galaxy 1 is
done. The key (probably SHIFT) is decided then, keeping the "simple controls" rule in mind.
| 5 THE CORE | everything returns | all palettes | remixes plus a true final boss | — |

---

## 5. Weapons

Controls stay as they are: **SPACE fires the primary, R switches between the 2 primaries
picked in the hangar.** Everything else is automatic.

### Primary weapons (2 equipped, R switches)

| Weapon | Feel | Numbers (at MK I, balanced to about the gun's DPS) | Unlock |
|---|---|---|---|
| MACHINE GUN | reliable stream | 71 DPS (exists) | start |
| LASER | beam, overheats | 80 DPS (exists) | gift |
| SCATTER | 5-pellet shotgun, strong up close | 5 x 4 dmg every 0.28 s, ~71 DPS at close range | L5 |
| PLASMA | slow, big orbs that pierce | 18 dmg every 0.25 s, pierces 3 targets | L7 |
| ARC | lightning that jumps to 3 nearby targets | 55 DPS on the first target, 60% per jump | L9 |
| RAIL | hold to charge (0.8 s), instant piercing line | 60 dmg per full charge | galaxy 2 |

Every primary gets POWER levels 1–2 from POWER cores, like the gun and laser do today.
Weapon damage is balanced with `Loadout.gun_dps` as the baseline, so no weapon breaks
`BossSpec`.

### Secondary weapons (1 slot, fire automatically, no key)

| Secondary | Behaviour | Unlock |
|---|---|---|
| ROCKET POD | 2 homing rockets every 1.8 s at the nearest target | L6 |
| SIDE CANNONS | 2 small guns firing sideways (hits divers and interceptors) | L8 |
| MINE TRAIL | drops a mine behind the ship every 2 s | galaxy 2 |

Secondaries do about 20% of the primary's DPS, as a steady extra.

### Specials (exist, unlocked as gifts)

- BLAST (charged beam) and ULTIMATE (T, missile storm) stay as they are.

---

## 6. Progression: rewards, coins, upgrades

### 6.1 Level rewards ("gifts")

After every cleared level the level-clear screen becomes a **reward screen**: **CHOOSE YOUR
GIFT, 1 of 2.** The gift not chosen goes into the shop, where it can be bought later with
coins. What exists today (hulls, laser, BLAST, ULTIMATE) becomes the first gifts, so a new
player unlocks it step by step.

| After level | Gift A | Gift B | Automatic |
|---|---|---|---|
| 1 | LASER | WASP hull | shop opens |
| 2 | BLAST + ULTIMATE (always: level 3 is built around them) | — | — |
| 3 | TITAN hull | LANCE hull | — |
| 4 | wingman **PIP** | wingman **GUARDIAN** | wingman slot opens (G6; until then no gift) |
| 5 | SCATTER | OVERDRIVE boost (section 7) | — |
| 6 | ROCKET POD | wingman **HUNTER** | — |
| 7 | PLASMA | skin "SOLAR" | — |
| 8 | SIDE CANNONS | wingman **MEDIC** | — |
| 9 | ARC | new hull **SPECTER** (galaxy 1 secret hull) | — |
| 10 | galaxy medal + skin "SWARMBANE" | — | warp to galaxy 2 |

Built in G2 (`progression/items.py` `GIFTS`). Changed from the first draft: BLAST + ULTIMATE
moved to level 2 (level 3 is designed around them) and TITAN / LANCE became the level 3 choice.
Shop prices: LASER 200, WASP 250, TITAN / LANCE 350 CR.

**Decided:** choose 1 of 2, the other goes to the shop. A **new player starts with ARROW + the
machine gun only**; everything else comes as gifts or from the shop.

**Existing save files:** a player who has already unlocked level N gets every gift up to N
(no one loses what they had).

### 6.2 Coins ("CREDITS")

Sources (faucets):
- rocks: 0–1 coin (bigger rocks more often), drones and minions 1–3, elites x3
- bosses: a burst of coins on death (30 + 10 per level); every phase change drops 5
- level clear: `50 x level` + **rank bonus** (S x2, A x1.5, B x1, C x0.5)
- first clear of a level: a one-time bonus of 100
- replaying an old level pays 50% (farming is possible, but slower)

Coins fly to the ship when it is close (like repair kits), with a satisfying "tink" and a
counter pop in the HUD.

**Decided: coins only count if you win.** Coins picked up during a level are *pending* (the HUD
shows `+86` next to the bank). They go into the bank only when the level is cleared, together
with the clear bonus. Death, retry or quitting loses the pending coins, but never the bank.
This makes every coin in a hard boss fight feel at stake: the level-clear screen counts the
pending coins into the bank one by one ("ka-ching"). The MAGPIE wingman and the MAGNET boost
don't change this rule.

Sinks: upgrades (6.3), shop items (gifts not chosen), wingman levels, skins.

Target: one good run of a level pays for 1–2 upgrade tiers. That's enough to feel it without
having to grind.

**Rank** (level results screen, new): time, accuracy, damage taken, kills. S/A/B/C, shown
with a stamp animation.

### 6.3 Upgrades and how they fit the boss balance

Upgrades in the hangar: **ARMOR, GUNS, LASER, ENGINE, CHARGE** (BLAST/ULT fill speed), each
with 5 tiers. Costs: 100 / 200 / 350 / 550 / 800.

The balance rule stays: `BossSpec` is still computed against the level's **par loadout**
(today's MK per level: MK I–IV, then MK V ... MK X for levels 5–10). Par is what the game
assumes a player *without* upgrades has, and the ship still grows by one MK every level for
free. Upgrades are **the player's edge on top of par**, capped at about **+30% power at full
tiers** (e.g. ARMOR +6% HP per tier). With everything maxed, a 5x boss feels like about 3.8x.
That's the reward for investing, and it can never become trivial.

The hangar shows `POWER 112%` next to the ship (100% = par for the next level).

---

## 7. Temporary boosts and combo

New pickups (all automatic, no key), which fall like repair kits:

| Boost | Effect | Duration |
|---|---|---|
| OVERDRIVE | fire rate x2, flames turn white | 6 s |
| SHIELD | bubble that absorbs 3 hits | until broken |
| MAGNET | pulls in every coin and pickup on screen | 8 s |
| SLOW-MO | enemies and bullets at 50% speed (the ship at 100%) | 4 s |
| TWIN | a temporary wingman copy of the player's ship | 10 s |

**COMBO / FEVER** (new-generation hook, no key): kills within 1.5 s of each other build a
combo (x2, x3 ... up to x8 score *and* coins). At combo 25 the ship enters **FEVER** for 5 s
(OVERDRIVE plus a rainbow trail plus music layered one octave up). Getting hit resets the
combo.

Galaxy features: galaxy 1 introduces boosts and combo; galaxy 2 adds elite enemies and
modifiers; later galaxies are in section 4.

---

## 8. Wingmen

A small ship (9x11 px) that flies in formation beside the rocket (left or right, follows the
lean and eases into place). It is **never controlled directly**.

- **Can't die.** A hit knocks it out for 5 s (it spins, smokes, then reboots), so there's no
  frustration.
- Gains XP from kills it takes part in, up to level 5 (coins can speed this up).
- Wingman DPS counts as player edge (about 15% of par DPS at level 5), so `BossSpec` stays
  intact.

| Wingman | Role | Level-up path |
|---|---|---|
| PIP | gunner: copies the player's primary at 25% | +damage, then fires angled shots at level 5 |
| GUARDIAN | orbits the ship and blocks enemy bullets (1 every 2 s) | +blocks, at level 5 a reflected bullet deals damage |
| MEDIC | repairs 1 HP/s while no damage is taken for 3 s | +rate, at level 5 revives once per level with 25% HP |
| HUNTER | homing micro-missile at minions every 2 s | +missiles |
| MAGPIE | collects coins and pickups within a large radius | +radius, +10% coins |

One slot in galaxy 1, two from galaxy 2.

---

## 9. Inventory: HANGAR 2.0

The current hangar grows into the player's base. It opens before every level and from the
title. It works fully with the keyboard (LEFT/RIGHT tabs, UP/DOWN items, ENTER equip or buy)
and the mouse.

```
+--------------------------------------------------------------+
| HANGAR            SHIPS  WEAPONS  WINGMEN  UPGRADES  SKINS   |
|                                                   CR 1 240   |
|  +------------+   ARROW  [equipped]                          |
|  |            |   HP      ########..                         |
|  |  ship      |   POWER   #######...                         |
|  |  preview   |   SPEED   ######....                         |
|  |  (animated,|   ------------------------------------       |
|  |  wingman,  |   > WASP        owned                        |
|  |  flames)   |     TITAN       300 CR                       |
|  +------------+     LANCE       locked  (clear level 4)      |
|  LOADOUT: ARROW  GUN+LASER  ROCKET POD  PIP  SKIN:MK         |
|                                     POWER 112%   LAUNCH >    |
+--------------------------------------------------------------+
```

- Tabs: SHIPS (hulls), WEAPONS (2 primaries + 1 secondary), WINGMEN, UPGRADES, SKINS.
- Locked items show *how* to unlock them (a goal pulls the player on).
- **TEST FLIGHT** (stretch goal): a 20 s sandbox with target dummies to try a build.
- The preview is live (flames, lean, wingman beside the ship, skin), not a static picture.

---

## 10. Skins and cosmetic effects

Skins never change stats. Each one is a palette key in `player/art.py` plus optional effects.

- **Paint jobs**: the MK paints that exist today, plus SOLAR (gold/red), NEON (magenta/cyan,
  80s), STEALTH (black/grey), RETRO (NES blue/red), SWARMBANE (galaxy 1 medal).
- **Engine trails**: classic orange, plasma blue, toxic green, rainbow (FEVER look), pixel
  hearts (secret).
- **Tracer colours** for the gun, **beam colours** for the laser (readability rule: never the
  enemy bullet colour).
- **Death explosion** styles: classic, pixel shatter, supernova.
- Sources: gifts, achievements (e.g. "no-hit boss" gives GOLD TRIM), coins.

---

## 11. Look and feel

### Colour and readability rules

- **Enemy bullets** stay in the hot range (magenta, orange, red, pink) with a white core, in
  every galaxy. Backgrounds never use that range at high brightness.
- **Player shots** stay cool or gold (cyan, blue, white, gold).
- **Pickups** have a slow bob plus a sparkle; coins are yellow and round (instantly
  recognisable).
- Every level's background is at most 40% brightness so sprites pop (lesson from the level 2
  crimson nebula).

### Backgrounds (one new "event layer" per level)

Today there are three layers: nebula, planet and starfield. New: an **event layer** per
level that makes it memorable. Examples: L5 sun corona with flares, L6 lightning in fog,
L7 crystal sparkle, L8 wreck silhouettes, L9 lensing around the black hole, L10 scrolling
organic walls. It is a new `background/` module per effect, chosen by a field on `Level`.

### Hit and fire effects ("juice")

Juice is sorted into **3 tiers** so it stays proportional:

| Tier | Events | Shake | Hit-stop | Particles | Extra |
|---|---|---|---|---|---|
| small | bullet on rock, coin | none / 0.1 | – | 2–4 | tink |
| medium | kill minion, big rock, player hit | 0.3 | 0.04 s | 8–12 | white flash, damage number |
| large | boss phase, boss kill, player death | 0.8 | 0.12 s | 30+ | flash, zoom punch, slow-mo 0.5 s |

New effects: muzzle flash per weapon, impact sparks in the weapon's colour, lingering embers
after explosions, **damage numbers** on bosses (reuses `ui/popup.py`), shield ripple, a charge
glow on weapons that charge.

Accessibility: options for **reduce shake** and **reduce flashes** (options menu, Phase 8).

### Audio

- A track for each new level and boss (recipes in `game/audio/music.py`); the galaxy boss has
  a 2-part track (hive, then escape).
- Layered FEVER music (same song plus an octave layer).
- New SFX: coin, combo up, fever, shield, wingman down/up, mine, teleport, tether, magma burst,
  crystal refract, hangar buy, gift reveal.

---

## 12. "New generation" hooks (what keeps players coming back)

- Short levels with a reward every 3–4 minutes (gift, coins, rank)
- A build that becomes yours: hull, weapons, wingman, skin
- Coins are banked on a win: every cleared level pays out, and every boss fight has coins at stake
- Visible goals: locked items say how to unlock them; ranks S/A/B/C per level
- Boss name cards, radio lines, a finale that remembers the galaxy
- Later: **daily challenge** (fixed seed, one attempt, own leaderboard), achievements, and
  NEMESIS (ROADMAP Phase 9)

---

## 13. How it maps to code (plan, not built yet)

| New thing | Where |
|---|---|
| `Galaxy` (name, palette family, levels, mechanic) | `levels/model.py`; data in `levels/galaxy1.py`, `levels/data.py` → `GALAXIES` |
| Rewards, shop items, unlock rules, prices | new package `game/progression/` (`rewards.py`, `economy.py`, `inventory.py`), pure logic that can be unit-tested |
| Coins (pickup), boosts | `pickups/types.py` (`Coin`, `Overdrive`, `Shield`, ...) |
| Combo / FEVER, rank | `flow/scoring.py` (new mixin `ScoringMixin`) |
| Wingmen | new package `game/wingmen/` (`base.py` `Wingman`, one file per type) |
| New primaries / secondaries | `weapons/scatter.py`, `plasma.py`, `arc.py`, `secondary.py` |
| Upgrades on top of par | `config/loadouts.py` (`Loadout.upgraded(tiers)`), tier numbers in `config/tuning.py` |
| Hangar 2.0 | `ui/hangar.py` → `ui/inventory/` (one module per tab); keys in `flow/events.py` `_keys_hangar` |
| Reward screen, radio cards | `ui/screens.py` + `State.REWARD`; `flow/meta.py` (`MetaMixin`) |
| Save file v2 | `core/storage.py`: `version` field, profile = coins, owned items, tiers, loadout, skins, galaxy progress; migration from v1 |
| New bosses / minions / obstacles | one file each, as in GUIDE.md section 6 |
| Event background layers | `background/<effect>.py` + `Level.event` |

Tests: a smoke-test section for each area (`economy`, `rewards`, `wingmen`, `boosts`,
`galaxy`) plus pytest unit tests for `progression/`.

---

## 14. Decisions (the user's answers, 2026-09-27)

1. **Gifts:** choose 1 of 2 after each level; the other goes to the shop.
2. **New players start with ARROW + machine gun only.** Hulls, laser, BLAST/ULT come as gifts.
   Existing saves keep what they have unlocked.
3. **Coins only count when the level is won.** Pending coins are lost on death / retry / quit;
   the bank is never lost (section 6.2).
4. **Black hole: make it insane.** It pulls everything including the ship (capped so thrust
   always escapes), curves all shots, SLINGSHOT zone, WHITE HOLE flip (section 3).
5. **Wingmen are knocked out for a few seconds, never destroyed.** May be revisited after
   playtests.
6. **Camera scroll for the Overmind fight: OK.**
7. **Abilities later:** advanced levels unlock new abilities and features that help win
   levels (section 4); designed after galaxy 1.
8. **Build order: systems first** (save v2, coins, rank, gifts, hangar/inventory, upgrades,
   juice, boosts, wingmen, weapons, skins), **then a full playtest from level 1 to 4 with all
   systems, then level 5** onward (ROADMAP Phase 10).
