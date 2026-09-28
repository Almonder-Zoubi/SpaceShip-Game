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
GALAXY 1  ORION REACH      levels 1-10   done
GALAXY 2  THE VEIL         levels 1-10   designed in section 4 (approved)
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
scrolls up along its body. *(Built in G15 without a camera scroll: the hive wall spans the
whole top of the screen, then tears open. Boss rush: Mothership, Leviathan, Helios.)*
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

## 4. Galaxy 2 — THE VEIL (design for G16+, approved 2026-09-28)

The user's brief (2026-09-28): galaxy 2 must be **harder** than galaxy 1, with **new kinds of
minions, obstacles and boss shots**, **smarter enemies**, and levels whose **flow** is new and
**unpredictable**, not just "field -> boss" again. On top of that, a **main villain** who ties
all galaxies together: every galaxy's last boss serves the villain, there are dialogs, and the player
gathers **pieces of a puzzle**.

### 4.1 The long story: VANTA and the Dawn Key

**VANTA, THE HOLLOW KING** is the villain of the whole game. It is not a ship and not a
creature: it is a hole in the light, an intelligence that *unmakes* stars and leaves perfect
darkness behind. (The data cache THE HOLLOW on the galaxy 1 map was its first footprint.)

- **What it wants:** the five shards of the **DAWN KEY**. Put together, the key opens THE CORE,
  where every star in the universe is lit from, and VANTA wants to put that light out.
- **The heralds:** each galaxy's finale boss is one of VANTA's five heralds, guarding (or
  hunting for) one shard. Beat the herald and you take its shard first.
- **What galaxy 1 meant, looking back:** the Swarm wasn't invading. It was **fleeing** VANTA
  (the "SIGNAL FROM THE VEIL" cache says so already). The Overmind's heart guarded **shard 1**.
  The player took it without knowing, so a new radio card after galaxy 1 reveals that the
  rocket now carries a shard and VANTA has noticed.
- **The mystery (the puzzle pieces):** who VANTA was. Each galaxy's hidden data caches become
  **ECHOES**, fragments of VANTA's memory. Every echo is one tile of a **pixel mosaic** in the
  new ARCHIVE screen on the star map, plus a line of text. A finished mosaic shows a picture,
  and each picture is a clue:
  - G1 mosaic: two rockets flying side by side (a pilot and a wingmate)
  - G2 mosaic: one rocket turning back into the dark, alone
  - G3 mosaic: an ARROW-shaped silhouette, hollow and black
  - G4 mosaic: COMMANDER VEGA's portrait, younger
  - G5: the answer. **VANTA was the scout before you**, the one who first used the Dawn Key
    to save the Reach. It was hollowed by the Core, and Vega was the wingmate who left it
    behind. The last fight is against a black ARROW that flies with *your* habits (see 4.4).
- **Echo rewards:** finishing a galaxy's mosaic unlocks that galaxy's **secret level** (a
  planet that appears on the star map), with a skin and a lot of credits.

**Dialogs.** The radio cards grow into a small dialog system:
- **Several speakers**, each with a 24x24 portrait: COMMANDER VEGA, the herald of the galaxy,
  VANTA (a black square with two white pixels that blink), and "???" (static).
- **Hijacked transmissions:** VANTA or a herald breaks into Vega's radio mid-level. The card
  glitches (scanline tear, a colour shift, a bit-crushed sound) and the text types in red.
- **Reactive taunts:** heralds comment on what the player does, with lines chosen by game
  state: low hull ("YOU LEAK LIGHT, LITTLE SCOUT."), a long combo ("SO QUICK. SO LOUD."),
  laser spam ("THAT BEAM AGAIN? I REMEMBER IT."), a retry ("BACK ALREADY?"). A line never
  repeats within one level.
- **Level-clear lines:** one story line under the rank, so the plot moves on even for
  players who skip the radio.
- Lines stay <= 43 characters (the card width, checked by the smoke test). ENTER skips.

**Built in G16 (2026-09-28): the JOURNAL and the hidden layers.** The user asked for a board
to read the story in peace. `J` on the title or the star map opens the **LOGBOOK OF SCOUT
ARROW-01**:
- **PILOT:** the ship as it flies now (model, hull, gun, laser, speed, POWER %), upgrade tiers,
  gear owned, achievements (with the skin they give), medals and the DAWN KEY (shards).
- **BOSSES:** every boss's file with its own sprite: what the fleet knows, its link to
  VANTA, and a **red margin note in someone else's hand**. Unbeaten bosses are black
  silhouettes, future heralds black bars (N##), VANTA's file opens line by line.
- **ECHOES:** the mosaic (6 tiles from the star map caches) and the decoder.
- **LOG:** every radio line heard, level by level, plus the intercepted transmissions.

The hidden layers (the "mind-blowing" part: each one is small, and together they point to
one answer that the `story/lore.py` docstring states):
1. **Vega's acrostic:** the first letters of Vega's first line in levels 1–10 spell
   `YOU ARE NEXT`. The decoder (all 6 echoes) lights them up in the LOG.
2. **The margin notes** were written by the previous owner of the callsign ARROW-01 ("THAT
   PLATE IS MINE." on Scrapjaw, whose jaw holds a plate stamped ARROW-01).
3. **The ghost record:** after galaxy 1 the title's score board shows `0. 999999 LEVEL 50
   ARROW-01`, a finished game by your own callsign. It glitches.
4. **The mosaic** shows two ships leaving side by side, and one is your MK I ARROW.
5. **The hijacked transmission** in the warp: VANTA says "WE HAVE DONE THIS BEFORE." Vega
   says the signal is a lie.

### 4.2 Harder, but fair

Galaxy 2 raises difficulty through **new pressure**, not just bigger numbers. Pillar 4 still
holds: everything is telegraphed.

| Lever | Galaxy 1 | Galaxy 2 |
|---|---|---|
| Level boss strength | 5x | 5.5–6x, 4 phases (galaxy 1 has 3) |
| Returning boss (warm-up) | 1.5x | 2x, and it has learned one new trick |
| Galaxy boss | 5x | 7x, 5 phases |
| Enemy bullets | one pattern at a time | from phase 3, **two patterns overlap** |
| Bullet speed | base | +15% |
| Repair kits in the field | every 13–20 s | every 22–30 s, and elites can steal them |
| Repair before a boss | full | **50%** (decided, 4.8) |
| Minions | fixed stats | **ELITES** (4.5) and the DIRECTOR (4.4) |
| Rank S | no-hit is rare | needs a no-hit boss phase and a combo of 40 or more |

The player keeps growing too: ship models **MK XI–XX** add +30 HP / +2 gun per level
(galaxy 1: +50 / +2), upgrade tracks get **tiers 6–10**, and the new gear (4.7) is the
player's edge. The `BossSpec` rule stays: every boss is exactly `strength` times the
level's par ship.

### 4.3 Level flows: no two levels play the same way

Galaxy 1 levels all follow the same shape: field → WARNING → boss (times 2–3 waves).
In galaxy 2 **every level has its own flow**, taken from this list and shown on the star map
card (e.g. "FLOW: PURSUIT"):

| Flow | What happens | Why it feels new |
|---|---|---|
| **AMBUSH** | the boss arrives *without* a WARNING, somewhere in the middle of the field (only radio static warns you) | the safe rhythm breaks |
| **PURSUIT** | something huge chases you *from the bottom*; the world scrolls faster; stay low and it bites, then the path closes and you turn to fight | you are the prey |
| **ESCORT** | protect a slow ally (a Swarm brood pod) crossing the screen; its HP bar sits under yours | your attention is split |
| **DARKNESS** | the screen is black, with a light cone around the ship; your tracers light the dark, enemy bullets glow | you read the space instead of seeing it |
| **DUEL** | the herald hunts you across the level, fights a phase, *retreats*, and ambushes again | a rivalry, not one fight |
| **SIEGE** | survive 90 s defending Vega's flagship at the bottom; no progress bar, only a timer | defence instead of travel |
| **CROSSROADS** | halfway through, two portals: RED (harder, elites, x2 coins, mini-boss A) or BLUE (safer, mini-boss B) | a real choice; replays differ |
| **GAUNTLET** | 4 short arenas; before each one a slot-machine card rolls a random **rule** (4.6) | nobody knows the next 30 s |
| **MIRROR** | a shadow of your own ship flies mirrored across the centre and shoots back with your weapons | you fight yourself |
| **RHYTHM** | everything moves on the beat of the music: bullets advance in steps, and the gaps open on the off-beat | you listen to dodge |

On top of the flow, every attempt of a level rolls one **VEIL SHIFT**, a small random
modifier shown on a card at the start: "ROCKS FAST", "DOUBLE MINIONS", "BULLETS SPLIT",
"NO KITS, DOUBLE COINS", "ELITE SQUAD", "HEAVY GRAVITY", "BLIND SPOTS" (dark patches)...
A retry is never the same level twice. Clearing a level under a hard shift pays a bonus.

### 4.4 Smart enemies: the DIRECTOR and learning bosses

This is the "intelligence" the user asked for, built from the NEMESIS plan (ROADMAP Phase 9):
pure-Python online learning, no neural network, visible to the player, and tested.

1. **The DIRECTOR** (like an AI game master): watches the player (hull %, combo, damage per
   minute, deaths) and paces the level with **peaks and breathers**. It spawns harder when the
   player is doing well and gives a short breather after a peak. It never goes below the
   level's base difficulty, so it only makes things harder or keeps them the same.
2. **The PLAYER MODEL** (saved, and shared across all of galaxy 2): where on the screen the
   rocket spends its time, which way it dodges, gun vs laser share, reaction time to
   telegraphs.
3. **Learning bosses:** every galaxy 2 boss chooses its attacks with a **bandit** (it keeps
   the patterns that hurt *you* and still tries others ~15% of the time), aims **ahead** of
   your velocity, and gets **counters**: hug the bottom → floor sweepers, circle left →
   cut-offs on the left, laser-heavy → a mirror shield only the gun breaks.
4. **You can see what it learned:** after a death, the boss says what it noticed in one
   line ("YOU ALWAYS BREAK LEFT."). Before the galaxy boss, an ANALYSIS card shows what it
   learned about you.
5. **Squad AI for minions:** leaders and followers (kill the leader and the squad
   scatters), flanking pairs (one draws your fire, one strikes from the side), dodgers that
   step out of a shot lined up on them.
6. **Fairness rails:** a capped learning rate, `BossSpec` strength unchanged, every attack
   telegraphed, and a "RESET WHAT THEY LEARNED" option.

**Built in G17 (2026-09-28):** `game/brains/` (player model, bandit, DIRECTOR, insights),
saved in `save.json` and shown on the journal's **KNOWN** page ("WHAT THEY KNOW ABOUT YOU":
a heatmap of where you fly, dodge directions, weapon shares, reaction time, their notes,
BACKSPACE twice to make them forget). A death in a thinking level shows "IT LEARNED: ...".
The model already watches galaxy 1 play, so galaxy 2 starts out knowing the player.

**Built in G18 (2026-09-28): galaxy 2 plumbing + level 1 VEIL GATE.** Galaxy 2 has its own
star map (the warp gate joins the two maps; the way back is always open), MK XI, ELITES
(golden, x3 hull, faster, the shell bounces a hit every 2.5 s, x3 coins), VEIL SHIFTS
(ROCKS FAST, DOUBLE MINIONS, NO KITS + COINS X2, ELITE SQUAD, GLASS CANNON, BLIND SPOTS;
x1.2 coins when cleared), the bullet types (splitter, boomerang, rune, lead shot, shadow,
twinned), 50% repair before bosses. VEIL GATE (AMBUSH flow): WISPS side-step lined-up
shots, RIFT PORTALS carry rocks, bullets and your own shots, and THE WARDEN strikes
mid-field: a learning boss behind shield rings (a ring hit does 25%, the gap 100%), the gap
turns away from your favourite side, an inner ring swings across it in phase 2, the rings
spin and spray in phase 3, the outer ring saws loose in phase 4. The level-1 gift is the
VEIL paint (the 2nd wingman slot moves to G19 with the ability key).

### 4.5 New minions, obstacles and boss shots

**Minions (the HOLLOW, VANTA's army, plus Swarm remnants):**

| Minion | Behaviour | Counterplay |
|---|---|---|
| WISP | light, fast; **side-steps** when a shot is lined up on it | fire where it will dodge to, or spread shots |
| STALKER pair | flankers: one hovers in front, the other circles and strikes from the side | kill the circler first |
| HOLLOW LEADER + squad | squad in formation; the leader gives orders (they focus fire) | kill the leader and they panic, scatter and stop shooting for 3 s |
| LURKER | invisible in darkness; your tracers or a flare reveal it | light it up |
| THIEF | steals a repair kit or boost and runs up | chase it for the item x2 |
| ECHO | replays the path you flew 3 s ago as a trail of bullets | don't go back to where you were |
| SWARM ALLY (level 3 on) | freed larvae that fight **for** you for a while | protect them in ESCORT |
| **ELITE** version of any minion | golden aura, x3 HP, one extra trick (shield, dash, splits in two on death, reflects one shot), x3 coins | a mini-fight worth it |

**Obstacles:**
- **BONE ROCKS**: break into a marrow core that **regrows** the rock in 3 s unless you
  finish it.
- **RIFT PORTALS**: pairs of tears; rocks, bullets (yours too) and minions that enter one
  come out of the other. They open with a 1 s shimmer, so nothing comes out unseen.
- **VOID HOLES**: patches that **erase bullets** from both sides; they make safe spots and
  blind spots.
- **PHASE ROCKS**: real half the time, ghosts the other half (the outline blinks before
  they turn solid).
- **EGG CLUSTERS**: hatch minions after 6 s unless destroyed.
- **CHAINED ROCKS**: two rocks on a tether that swings; shoot the chain to split them.

**Boss shots (new bullet types, all telegraphed):**
- **SPLITTERS**: break into 3 after 0.6 s (the bullet swells before it splits)
- **BOOMERANGS**: fly out, stop, come back along a curve
- **RUNES**: a marker appears on the floor, and 0.8 s later a bullet ring blooms from it
- **SHADOW BULLETS**: dark cores with bright rims (for the DARKNESS levels)
- **TWINNED**: two bullets that orbit each other while they travel
- **CAGE**: 4 slow walls close in from the sides and leave one gap that moves
- **LEAD SHOTS**: aimed where you *will* be (from the player model), drawn with a thin
  line to where they are heading

### 4.6 The ten levels of THE VEIL

Palette family: purple, teal, bone white, with void black. Each level: one new minion or
obstacle, one flow, one boss (or none), one gift.

| # | Level | Flow | New thing | Boss | Idea |
|---|---|---|---|---|---|
| 1 | VEIL GATE | AMBUSH | WISP (dodges), RIFT PORTALS | THE WARDEN: a rotating shield ring; the gap takes full damage (the ring 25%), and it turns the gap away from your favourite side | "the door knows you're coming" (built) |
| 2 | BONE REEF | PURSUIT | BONE ROCKS, STALKER pairs | LEECH MAW: chases you up the screen, then turns and fights in the reef | "you are the prey" |
| 3 | BROOD SANCTUARY | ESCORT | SWARM ALLIES, THIEF | HOLLOW REAPER: hunts the brood pod, not you; keep it busy | "the enemy of my enemy" |
| 4 | THE DARK VEIL | DARKNESS | LURKER, SHADOW BULLETS | ECLIPSE: puts out the light; only the rim of its body glows | "fight what you can't see" |
| 5 | MIRROR SEA | MIRROR | ECHO minions, PHASE ROCKS | THE MIMIC: copies your weapons and wingman; in phase 4 it replays your last 10 s as bullets | "your own worst enemy" |
| 6 | PULSE NEBULA | RHYTHM | beat-locked everything, CAGE | TEMPO: a metronome boss; each phase raises the BPM | "listen to dodge" |
| 7 | HOLLOW MAZE | CROSSROADS | VOID HOLES, EGG CLUSTERS | RED route: GRINDER / BLUE route: SPINNER (two mini-bosses); then the maze's heart | "choose your pain" |
| 8 | LAST LIGHT | SIEGE | HOLLOW LEADER squads, ELITE waves | none: a 90 s DIRECTOR siege of Vega's flagship; its guns help you | "hold the line" |
| 9 | THE COURT OF NYX | GAUNTLET + DUEL | CHAINED ROCKS, random rules | NYX appears in arenas 2 and 4, retreats, taunts; the 4 arena rules are rolled | "it is testing you" |
| 10 | THE HOLLOW THRONE | finale | everything | boss rush (THE WARDEN, ECLIPSE, THE MIMIC at 2x) → **NYX, FIRST HERALD** (7x, 5 phases) → collapse | "the first herald falls" |

**NYX, THE FIRST HERALD (galaxy 2 boss, level 10):**
1. **The duel:** a sleek black ship with a white mask. Lead shots, and it dodges *your*
   lined-up shots like a WISP. It uses everything the player model learned in galaxy 2.
2. **Portals:** it opens rift portals around the screen and fires *through* them, from
   behind and from the sides.
3. **Eclipse:** the lights go out (DARKNESS); only its mask and its SHADOW BULLETS glow.
4. **Unmaking:** void closes in from the screen edges (the arena shrinks); two patterns
   overlap.
5. **VANTA takes over:** the transmission is hijacked, and VANTA speaks through NYX
   ("KEEP THE SHARD. I WILL TAKE IT FROM YOUR LIGHT."). A last desperate phase: runes
   everywhere, cages.
- After the win: **SHARD 2** of the DAWN KEY, the galaxy 2 medal, an ESCAPE through the
  Veil as it tears apart, then the warp to galaxy 3, BLOOM. For the first time VANTA shows
  its face on the radio.

**Built in G21–G29 (2026-09-28): all ten levels.** As in the table, with these choices:
the maw's jaws rise while you idle and UP pushes them back (a bite drops them 30 px); a saved
brood / a flagship held above half pays a bonus and is remembered as a story beat; the
MIRROR level uses phase rocks (chrome) and echo ghosts; PULSE moves the whole enemy side on
a 120 bpm beat (0.25x between beats, 2.25x on them); CROSSROADS gates open at 55% of the
first field (no choice = the maze picks); LAST LIGHT is 3 x 30 s, and losing the flagship
loses the attempt; the COURT's NYX leaves at half its hull; the finale's darkness and void
walls come from its hazard (`hazards/throne.py`), switched on by the boss. The story adds:
heralds are the wingmates who did **not** turn back (NYX was one); galaxy 2's first radio
lines spell LOOK BEHIND; its caches say every hull in the Bone Reef reads ARROW-01; the
warp transmission shows VANTA's face - Vega's fleet helmet, darkened.

**Gifts (one per level, choose 1 of 2 as before):** the 2nd wingman slot (level 1), the
first **ABILITY** (level 2, see 4.7), RAIL (primary), MINE TRAIL (secondary), new hull
**VESPER** (a thin, dark scout), wingman **LUMEN** (lights up the dark, marks lurkers),
upgrade tiers 6–10, and paints NYX / VEIL / BONE.

### 4.7 Abilities (decision 7: "advanced levels unlock abilities")

One ability slot, on **one new key**. That's a control change, so the user decides it first.
The proposal: **SHIFT** (or right click), with a cooldown ring around the rocket.
- **PHASE**: 0.4 s through bullets (i-frames), 8 s cooldown. Gift of level 2.
- **FLARE**: lights up the dark and reveals lurkers for 4 s (DARKNESS levels).
- **TIME SLIP**: enemy side at 40% for 2 s.
- **REPAIR DRONE**: heals 15% over 5 s.
- **DECOY**: a copy of the rocket that enemies and learning bosses aim at for 3 s.
Without a key, abilities could instead fire **automatically** (PHASE when a hit would land,
once per 12 s): simpler, but less skill.

### 4.8 Decisions (the user's answers, 2026-09-28)

1. **Ability key: SHIFT or right click**, with a cooldown ring. 2. **Repair before bosses:
50% in galaxy 2** (galaxy 1 stays full). 3. **The learning bosses remember across sessions**
(saved, with a reset option). 4. **VANTA's twist stays** (the scout before you, left behind
by Vega). 5. Build order not asked: default is story engine + brains first (G16, G17).

The questions as they were asked:

1. **Ability key:** SHIFT / right click, or automatic abilities?
2. **Repair before bosses** (binding decision now: always full): keep it, or 50% in galaxy 2
   so the fields matter more?
3. **The learning bosses' memory:** per player save (it knows you across sessions) or
   reset every run?
4. **VANTA's twist** (it was the scout before you, and Vega left it behind): OK, or keep the
   villain a pure alien evil?
5. **Build order:** story + dialog system and the DIRECTOR first (they change every level),
   then the levels one by one — or level 1 first to feel the new flow early?

### 4.9 Galaxies 3+ (sketch, the heralds)

| Galaxy | Theme | Palette | Galaxy mechanic | Herald (galaxy boss) |
|---|---|---|---|---|
| 3 BLOOM | living nebula, plant creatures | green, pink, gold | **route map**: after each level choose 1 of 2 next levels | MORROW, THE WITHERING: rot spreads over the screen |
| 4 CHRONO RIFT | time-bending ancients | cyan, white, black | **time zones**: bullets slow down or speed up | KAIROS, WHO STOLE TIME: rewinds its own damage unless you break the clock |
| 5 THE CORE | everything returns | all palettes | remixes of every flow | **VANTA**: a black ARROW that flies with your habits |

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

**Built (G3):** per tier ARMOR +3% HP, GUNS +3% gun damage, LASER +3% laser DPS, ENGINE +4%
top speed, CHARGE +10% BLAST / ULT charge rate. POWER = HP bonus x the better weapon bonus
(gun and laser don't stack, one fires at a time): full ARMOR + GUNS = 1.15 x 1.15 =
**POWER 132%**, so a 5x boss feels like ~3.8x (the smoke test asserts >= 3.5x for every hull).
ENGINE and CHARGE are utility and don't count in POWER. Buying all 25 tiers costs 10,000 CR
(~40 good level runs); one run (215–250 CR) buys 1–2 early tiers, as targeted in 6.2.

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

## 15. Decisions for galaxy 2 (the user's answers, 2026-09-28)

1. **Abilities use one new key: SHIFT or the right mouse button** (cooldown ring on the rocket).
2. **Galaxy 2 repairs the hull to 50% before a boss** (galaxy 1 keeps the full repair).
3. **Learning bosses remember the player across sessions** (saved; a reset option exists).
4. **VANTA's twist is kept:** it was the scout before you, left behind by Vega.
