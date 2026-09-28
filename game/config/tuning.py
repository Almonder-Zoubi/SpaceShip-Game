"""Gameplay tuning numbers. Speeds are px/second, times are seconds."""

# --- Ship --------------------------------------------------------------------
# Arrows move the ship directly; two arrows (e.g. UP + RIGHT) move diagonally.
SHIP_ACCEL = 800                 # px/s^2 while a direction key is held
SHIP_MAX_SPEED = 130             # px/s
SHIP_FRICTION = 5.5              # velocity damping per second on released axes
SHIP_MARGIN = 4                  # keep this many px from screen edges
TILT_DEGREES = 30                # UP + LEFT/RIGHT leans the rocket like '\' or '/'
TILT_STEPS = 3                   # frames per side (10 degrees apart)
TILT_RATE = 240                  # degrees per second when leaning / straightening

# Mouse steering: the rocket flies towards the pointer (left click fires).
MOUSE_FOLLOW = 7.0               # wanted speed = distance * this (1/s), capped at max speed
MOUSE_DEADZONE = 1.5             # px: close enough, stop
MOUSE_LEAN = 0.45                # fraction of max speed that counts as "pressing" a direction

THROTTLE_RETRO = 0.12            # DOWN held: flames nearly out
THROTTLE_IDLE = 0.45             # cruising
THROTTLE_BOOST = 1.0             # UP held: full burn
THROTTLE_RESPONSE = 7.0          # how fast throttle follows its target (1/s)

# World scroll speed multiplier at retro / boost throttle
WORLD_SPEED_SLOW = 0.8
WORLD_SPEED_FAST = 1.35

# --- Health ------------------------------------------------------------------
SHIP_MAX_HP = 100
ROCK_DAMAGE_BASE = 8             # damage from a rock = base + per_radius * radius
ROCK_DAMAGE_PER_RADIUS = 2       # (radius 4 -> 16, radius 14 -> 36)
HIT_INVULNERABLE = 1.0           # seconds of blinking after a hit
HIT_KNOCKBACK = 110              # px/s pushed away from the rock
BULLET_KNOCKBACK = 40            # px/s pushed by an enemy bullet

# --- Weapons (R switches, SPACE fires where the nose points) -----------------
GUN_INTERVAL = 0.07              # seconds between bullets
GUN_SPEED = 340                  # px/s
GUN_DAMAGE = 5                   # per bullet (~70 dps if every bullet hits)
GUN_SPREAD = 0.05                # radians of random spread
LASER_DPS = 80                   # damage per second while the beam touches
LASER_RANGE = 360
LASER_HEAT_RATE = 0.4            # heat per second while firing (full in 2.5 s)
LASER_COOL_RATE = 0.35           # heat lost per second when not firing
LASER_RESUME = 0.35              # after overheating, usable again below this heat

# Weapon power (0..POWER_MAX) — collected from POWER cores when a boss changes phase.
POWER_MAX = 2
LASER_POWER_BONUS = 0.35         # +35% laser dps per power level
LASER_POWER_COOL = 0.2           # -20% laser heating per power level
GUN_SIDE_ANGLE = 0.22            # radians, power 2 adds angled side rounds

# --- BLAST and ULTIMATE (MK III) ---------------------------------------------
# Both charge from damage dealt to rocks and minions (+ a bonus per kill, x3 for minions).
BLAST_TIME = 3.0                 # seconds the beam lasts once unleashed
BLAST_DPS = 450                  # to everything inside the beam
BLAST_WIDTH = 11                 # px
BLAST_PUSH = 160                 # rock push per second
BLAST_CHARGE_PER_DAMAGE = 1 / 1400
BLAST_CHARGE_PER_KILL = 0.025
ULT_TIME = 2.4                   # seconds of missile launches
ULT_INTERVAL = 0.05              # seconds between missiles (~48 missiles)
ULT_MISSILE_DAMAGE = 45
ULT_MISSILE_SPEED = 230          # px/s
ULT_TURN = 7.0                   # rad/s homing turn rate
ULT_CHARGE_PER_DAMAGE = 1 / 5000
ULT_CHARGE_PER_KILL = 0.008
ULT_CHARGE_PER_BOSS_THIRD = 0.25 # every 1/3 of a boss's health knocked off

# --- Asteroids ---------------------------------------------------------------
ROCK_HP_BASE = 6                 # hp = base + per_area * radius^2
ROCK_HP_PER_AREA = 0.8           # (radius 4 -> 19, radius 8 -> 57, radius 14 -> 163)
ROCK_SPLIT_RADIUS = 8            # rocks at least this big break into fragments
# Getting shot slows a rock down: push in px/s for a radius-4 rock, scaled by 4/radius.
GUN_PUSH = 5                     # per bullet
LASER_PUSH = 70                  # per second of beam
ROCK_MIN_FALL = 12               # rocks never get pushed slower than this (px/s)

# --- Enemy drones ------------------------------------------------------------
DRONE_HP = 24
DRONE_SPEED = 62                 # px/s downwards
DRONE_BULLET_SPEED = 95
DRONE_BULLET_DAMAGE = 8
DRONE_CONTACT_DAMAGE = 14

# --- Kamikaze divers (level 4) ----------------------------------------------
DIVER_HP = 18
DIVER_ENTER_SPEED = 75           # px/s while dropping in
DIVER_LOCK = 1.1                 # seconds hovering + aiming before the dive
DIVER_AIM_FREEZE = 0.3           # the aim stops following the rocket this long before the dive
DIVER_SPEED = 250                # px/s top dive speed
DIVER_ACCEL = 650                # px/s^2
DIVER_CONTACT_DAMAGE = 24
POINTS_DIVER = 200

# --- Bosses ------------------------------------------------------------------
# A boss is STRENGTH times stronger than the rocket, measured as a damage race:
#   (boss HP / player DPS) / (player HP / boss DPS) = strength
# where player DPS = the machine gun with every bullet hitting, and boss DPS = the damage
# a rocket that never moves would take. fight_time = seconds to kill the boss at that DPS.
# Both use the ship model of the level (Loadout.gun_dps / max_hp); pickups and power-ups are
# the player's edge on top. See bosses/spec.py.
BOSS_CONTACT_DAMAGE = 20         # ramming the boss hurts
BOSS_ROAR_TIME = 1.6             # a multi-phase boss is invulnerable while changing phase

# --- Pickups -----------------------------------------------------------------
REPAIR_SMALL = 30                # hp restored by a small repair kit
PICKUP_FALL = 26                 # px/s
PICKUP_MAGNET = 34               # px: kits closer than this drift towards the ship
PICKUP_RADIUS = 11               # px: collected when the ship centre is this close
KIT_INTERVAL = (13, 20)          # seconds between kits in the asteroid field (random range)
FULL_KIT_CHANCE = 0.15           # chance a field kit is a full repair
BOSS_KIT_INTERVAL = 15           # seconds between small kits during a boss fight
ROCK_KIT_CHANCE = 0.08           # big rocks (radius >= 10) may drop a small kit
DRONE_KIT_CHANCE = 0.06

# --- Score & rules -----------------------------------------------------------
POINTS_PER_RADIUS = 10           # destroying a rock
POINTS_DODGE = 5                 # a rock leaving the screen
POINTS_DRONE = 150
POINTS_BOSS = 5000
LEVEL_LENGTH = 75                # seconds of flight (at normal speed) to finish
DEATH_DELAY = 1.4                # seconds of explosion before "game over"
WARNING_TIME = 3.0               # "WARNING" before the boss enters

# --- Coins (CREDITS) ----------------------------------------------------------
# Coins picked up in a level are "pending" and only go to the bank when the level is won.
COIN_ROCK_CHANCE = ((10, 0.45), (8, 0.25), (0, 0.06))   # (min radius, chance of 1 coin)
COIN_MINION = (1, 3)             # coins from a destroyed drone / diver (random range)
COIN_BOSS_BASE = 30              # boss death burst: base + per level number
COIN_BOSS_PER_LEVEL = 10
COIN_BOSS_PHASE = 5              # every boss phase change drops one big coin
COIN_BIG = 5                     # value of a big coin
COIN_MAGNET = 46                 # px: coins drift to the ship from a bit further than kits
COIN_CLEAR_BASE = 50             # level clear: base x level number, then x rank multiplier
COIN_FIRST_CLEAR = 100           # one-time bonus for the first clear of a level
COIN_REPLAY = 0.5                # replaying a cleared level pays this share
COIN_TALLY_RATE = 160            # coins per second counted into the bank on the results screen

# --- Level rank ---------------------------------------------------------------
# Three ratings 0..1, weighted: took little damage, killed bosses fast, destroyed what came.
RANK_WEIGHTS = {"damage": 0.45, "speed": 0.30, "destroyed": 0.25}
RANK_DAMAGE_ZERO = 1.5           # damage taken (in multiples of max HP) that rates 0
RANK_DESTROYED_FULL = 0.6        # share of rocks + minions destroyed that rates 1
RANK_THRESHOLDS = (("S", 0.85), ("A", 0.65), ("B", 0.45), ("C", 0.0))
RANK_BONUS = {"S": 2.0, "A": 1.5, "B": 1.0, "C": 0.5}

# --- Upgrades (hangar, bought with coins) ---------------------------------------
# 5 tracks x 5 tiers, a capped edge on top of the level's par ship model (BossSpec keeps
# using par). ARMOR x GUNS at full tiers = 1.15 x 1.15 = POWER 132%: a 5x boss feels ~3.8x.
UPGRADE_TIERS = 10
UPGRADE_COSTS = (100, 200, 350, 550, 800,     # price of tier 1 .. 5 (galaxy 1)
                 1100, 1400, 1800, 2300, 2900)  # tiers 6 .. 10: galaxy 2 tech
GALAXY1_TIERS = 5                # tiers that count in galaxy 1 levels (and that can be bought
                                 # before galaxy 1 is beaten): galaxy 1's balance stays as is
UPGRADE_BONUS = {                             # per tier, as a share of the par value
    "ARMOR": 0.03,                            # max HP
    "GUNS": 0.03,                             # machine-gun damage
    "LASER": 0.03,                            # laser dps
    "ENGINE": 0.04,                           # top speed
    "CHARGE": 0.10,                           # BLAST / ULTIMATE charge rate
}

# --- Juice (game feel) -----------------------------------------------------------
# Tier -> (shake trauma, hit-stop seconds, extra embers, screen flash seconds).
JUICE = {
    "small": (0.05, 0.0, 0, 0.0),        # bullet on rock, coin
    "medium": (0.3, 0.04, 6, 0.0),       # minion kill, big rock, the ship is hit
    "large": (0.8, 0.12, 24, 0.1),       # boss phase, boss kill, the ship explodes
}
SLOWMO_TIME = 0.5                # a large event also slows the world down this long
SLOWMO_SCALE = 0.35              # world speed during slow-mo
REDUCED_SHAKE = 0.3              # options: "reduce shake" multiplies all shake by this
REDUCED_FLASH = 0.25             # options: "reduce flashes" multiplies screen flashes by this
DAMAGE_NUMBER_EVERY = 0.2        # seconds: boss damage is summed and shown this often

# --- Radio cards ---------------------------------------------------------------------
RADIO_CHARS_PER_S = 45           # typing speed
RADIO_HOLD = 3.0                 # seconds a card stays after the text is complete

# --- Boosts (pickups, automatic) + combo / FEVER ---------------------------------------
BOOST_INTERVAL = (20, 30)        # seconds between boost drops in the field (random range)
BOSS_BOOST_INTERVAL = 22         # ... and during boss fights
BOOST_MINION_CHANCE = 0.05       # a destroyed minion may drop one
OVERDRIVE_TIME = 6.0             # fire rate x OVERDRIVE_RATE, white flames
OVERDRIVE_RATE = 2.0
SHIELD_HITS = 3                  # the bubble absorbs this many hits
SHIELD_GRACE = 0.6               # seconds of invulnerability after the bubble takes a hit
MAGNET_TIME = 8.0                # every coin and pickup on screen flies to the ship
SLOWDOWN_TIME = 4.0              # SLOW-MO boost: enemies, rocks and bullets at half speed
SLOWDOWN_SCALE = 0.5
COMBO_WINDOW = 1.5               # seconds: a kill within this keeps the combo going
COMBO_STEP = 3                   # kills per multiplier step: 3 kills = x2 ... 21 kills = x8
COMBO_MAX = 8                    # score multiplier cap
COMBO_COIN_CAP = 2               # coins are multiplied too, but at most x2 (economy, playtest)
FEVER_AT = 25                    # combo that starts FEVER
FEVER_TIME = 5.0                 # OVERDRIVE + rainbow trail

# --- Wingmen (one slot in galaxy 1) ----------------------------------------------------
# Never destroyed: a hit knocks one out for a few seconds. XP from kills, levels 1..5.
WINGMAN_KO_TIME = 5.0
WINGMAN_XP = (0, 40, 120, 250, 450)      # total XP needed for level 1 .. 5
WINGMAN_XP_KILL = 1                      # any kill while it flies
WINGMAN_XP_OWN = 3                       # extra for a kill of its own
WINGMAN_XP_BOSS = 25                     # a boss destroyed while it flies
WINGMAN_TRAIN_XP = 60                    # hangar: TRAIN buys this much XP ...
WINGMAN_TRAIN_COST = 150                 # ... for this many coins
# Its damage is part of the capped player edge (with upgrades): the smoke test checks that
# a maxed build + a level 5 PIP still faces a 5x boss as >= 3.5x.
PIP_SHARE = (0.035, 0.045, 0.055, 0.065, 0.075)   # of the player's gun DPS, per level
PIP_INTERVAL = 0.14
GUARDIAN_COOLDOWN = (2.0, 1.7, 1.4, 1.2, 1.0)  # seconds between blocked bullets
GUARDIAN_ORBIT = 19                      # px from the ship
GUARDIAN_SPIN = 2.6                      # rad/s
MEDIC_RATE = (0.004, 0.006, 0.008, 0.01, 0.012)   # share of max HP repaired per second
MEDIC_DELAY = 3.0                        # ... once no damage was taken for this long
MEDIC_REVIVE = 0.25                      # level 5: revives once per level with this much HP
HUNTER_INTERVAL = 2.0
HUNTER_ROCKETS = (1, 1, 2, 2, 3)         # rockets per volley, per level
HUNTER_DAMAGE = 2.5                      # x the player's gun damage per rocket (never bosses)
MAGPIE_RADIUS = (60, 75, 90, 105, 120)   # px: coins and pickups this close fly to the ship
MAGPIE_BONUS = 0.1                       # level 5: chance that a coin counts twice
TWIN_TIME = 10.0                         # TWIN boost: a copy of the ship flies along ...
TWIN_SHARE = 0.25                        # ... firing at this share of the gun's DPS

# --- More primaries (2 slots, R switches) and secondaries (1 slot, automatic) -----------
# Every primary does about the machine gun's DPS (Loadout.gun_dps), so BossSpec holds.
SCATTER_INTERVAL = 0.28          # 5 pellets per shot, strong up close
SCATTER_PELLETS = 5              # + 2 per POWER level (same damage per pellet)
SCATTER_SPREAD = 0.36            # radians, total fan width
SCATTER_SPEED = 280
SCATTER_RANGE = 0.42             # seconds a pellet lives (~120 px)
PLASMA_INTERVAL = 0.25           # slow, big orbs that pierce
PLASMA_SPEED = 170
PLASMA_PIERCE = 3                # targets per orb (a boss stops it)
PLASMA_POWER_BONUS = 0.2         # +20% damage per POWER level
ARC_SHARE = 0.77                 # first target gets this x gun DPS (55 of 71 at MK I) ...
ARC_JUMP = 0.6                   # ... every jump this much of the previous one
ARC_JUMPS = 2                    # jumps after the first target (+1 per POWER level)
ARC_RANGE = 130                  # px from the nose to the first target
ARC_CONE = 0.6                   # radians either side of the nose
ARC_CHAIN = 64                   # px between two targets of a chain
SECONDARY_SHARE = 0.2            # secondaries: this x gun DPS, only on rocks and minions
ROCKET_POD_INTERVAL = 1.8        # 2 homing rockets
SIDE_CANNON_INTERVAL = 0.22      # both sides, only when something is beside the ship

# --- Level 5 SOLAR FORGE ------------------------------------------------------------------
MAGMA_BLAST = 26                 # px + the rock's radius: a magma rock's blast reach
MAGMA_BLAST_DAMAGE = 70          # to rocks and minions in reach (chain reactions)
MINELAYER_HP = 25
MINELAYER_SPEED = 55             # px/s across the screen
MINELAYER_DROP = 1.2             # seconds between mines
MINE_HP = 1
MINE_ARM = 1.0                   # seconds before a mine is armed
MINE_FALL = 22                   # px/s
MINE_DAMAGE = 30                 # an armed mine touching the ship
MINE_BLAST = 26                  # a mine shot down blows up: px reach ...
MINE_BLAST_DAMAGE = 45           # ... damage to rocks and minions (never the ship)
POINTS_MINELAYER = 250
POINTS_MINE = 20

# --- Level 6 GHOST NEBULA -------------------------------------------------------------------
FOG_INTERVAL = (4.0, 7.0)        # seconds between fog banks
FOG_SPEED = 26                   # px/s (x world speed)
PHANTOM_HP = 20
PHANTOM_FADE = 0.6               # seconds it takes to fade in before it fires
PHANTOM_CLOAK = 1.6              # seconds it stays hidden between bursts
PHANTOM_BURST = 3                # shots per burst
PHANTOM_BULLET_DAMAGE = 9
PHANTOM_BULLET_SPEED = 120
POINTS_PHANTOM = 220

# --- Level 7 CRYSTAL VEIL -------------------------------------------------------------------
REFRACT_RANGE = 90               # px: a lasered crystal splits the beam to up to 3 targets ...
REFRACT_BEAMS = 3
REFRACT_SHARE = 0.8              # ... each getting this share of the laser's damage
PRISM_HP = 40
PRISM_INTERVAL = 1.8             # seconds between 3-way refracted shots
PRISM_BULLET_DAMAGE = 10
PRISM_BULLET_SPEED = 110
POINTS_PRISM = 300

# --- Level 8 IRON GRAVEYARD -----------------------------------------------------------------
WRECK_HP = 2.5                   # wreck chunks are this much tougher than rocks
WRECK_COINS = (1, 2)             # coins a destroyed wreck chunk drops (before the combo)
SALVAGER_HP = 30
SALVAGER_SPEED = 90              # px/s towards the pickup it wants
SALVAGER_GREED = 3               # pickups it grabs before it flees
SALVAGER_TIME = 7.0              # ... or seconds before it flees anyway
POINTS_SALVAGER = 260
JUNK_HP = 25                     # Scrapjaw's thrown armour: can be shot apart

# --- Level 9 EVENT HORIZON: the black hole -------------------------------------------------
BH_RANGE = 230                   # px: how far the pull reaches
BH_PULL = 160                    # px/s^2 on rocks, bullets and shots at the core (falls off)
BH_SHIP_PULL = 95                # px/s extra ship velocity at the core (falls off with range)
BH_SHIP_PULL_MAX = 0.6           # ... never more than this x the ship's top speed (escapable)
BH_CORE = 10                     # event horizon radius (px); inside it hurts a lot
BH_CORE_DAMAGE = 0.2             # share of max HP per hit at the event horizon
BH_RING = (22, 38)               # SLINGSHOT ring: inner and outer radius
SLINGSHOT_SCORE = 3              # score and coins x3 inside the ring ...
SLINGSHOT_CHARGE = 2             # ... BLAST / ULT charge x2
SLINGSHOT_SHOT = 1.5             # a gun shot through the ring: +50% damage
WHITE_HOLE_EVERY = 25.0          # seconds between WHITE HOLE flips
WHITE_HOLE_WARN = 2.0
WHITE_HOLE_TIME = 3.0            # it pushes everything out (x2 the pull) this long
INTERCEPTOR_HP = 35
INTERCEPTOR_AIM = 1.2            # seconds it lines up before a dash
INTERCEPTOR_DASH = 260           # px/s
INTERCEPTOR_DASH_TIME = 0.5
INTERCEPTOR_COOLDOWN = 0.8       # vulnerable from every side after a dash
INTERCEPTOR_DAMAGE = 28
POINTS_INTERCEPTOR = 320
COMET_SPEED = 1.8                # comets fall this much faster than rocks

# --- Level 10 SWARM HEART -----------------------------------------------------------------
HIVE_WALL = (14, 34)             # px: the hive walls' width at both sides (min, max)
HIVE_WALL_DAMAGE = 0.05          # share of max HP when the ship touches a wall
ESCAPE_WALL = 70                 # walls close in to this width during the escape
ESCAPE_SPEED = 1.5               # the world rushes past this much faster during the escape
SPORE_HP = 12
SPORE_FALL = 32                  # px/s
SPORE_RIPEN = 105                # y where a pod starts to swell ...
SPORE_SWELL = 0.7                # ... for this long (the telegraph), then bursts
SPORE_SHOTS = 8                  # bullets in the burst ring
SPORE_BULLET_SPEED = 62
SPORE_BULLET_DAMAGE = 12
POINTS_SPORE = 60
LARVA_HP = 4
LARVA_SPEED = 115                # px/s top speed
LARVA_DAMAGE = 8
LARVA_TIME = 9.0                 # seconds a flock hunts before it leaves
POINTS_LARVA = 30
WARP_TIME = 15.0                 # the galaxy finale's cut-scene (ENTER skips)
WARP_CALL = 2.0                  # seconds into it when the hijacked transmission starts

# --- Star map (the explorable galaxy map between title and hangar) --------------------------
MAP_W, MAP_H = 720, 520          # px: the map is bigger than the screen, the camera follows
MAP_ACCEL = 320                  # px/s^2
MAP_SPEED = 130                  # px/s top speed
MAP_DRAG = 2.2                   # velocity lost per second (drifts to a stop)
MAP_REACH = 22                   # px: close enough to a planet to open its card
MAP_CACHE_SEEN = 46              # px: a hidden data cache becomes visible this close
MAP_GRAVITY = 240                # the black hole planet's pull (px/s^2 at its core, fades out)

# --- Brains (galaxy 2: the player model, learning bosses, the DIRECTOR) --------------------
BRAIN_GRID = (8, 6)              # heatmap cells over the screen
BRAIN_DODGE_SPEED = 40           # px/s: moving faster than this under threat = a dodge
BRAIN_REACTIONS = 20             # reaction times kept
BRAIN_FORGET = 0.9               # at each level start old habits keep this weight
BRAIN_THREAT = 34                # px: an enemy bullet / body this close (and coming) = a threat
BRAIN_EXPLORE = 0.15             # a learning boss still tries a random attack this often
BRAIN_UCB = 0.35                 # how much it values trying rarely used attacks
BRAIN_MIN_STEP = 0.2             # recent fights weigh at least this much (it can re-learn)
BRAIN_MIN_SECONDS = 20           # seconds watched before it claims to know anything
BRAIN_MIN_DODGES = 8
DIRECTOR_MAX = 1.6               # spawn rate at the peak for a player doing very well
DIRECTOR_RISE = 0.05             # pressure gained per second while building up
DIRECTOR_PEAK = 9.0              # seconds a peak lasts
DIRECTOR_BREATHER = 5.0          # seconds of breathing room after a peak
LEAD_AIM = 0.8                   # learning bosses aim this much of the way to where you'll be

# --- Galaxy 2: THE VEIL ------------------------------------------------------------------
BOSS_REPAIR_G2 = 0.5             # share of max hull repaired before a galaxy 2 boss
ELITE_HP = 3.0                   # elites: x3 hull ...
ELITE_SPEED = 1.2                # ... move faster ...
ELITE_COINS = 3                  # ... and drop x3 coins
ELITE_GUARD = 2.5                # an elite shrugs off one hit every this many seconds
SHIFT_BONUS = 1.2                # clearing a level under a VEIL SHIFT pays x1.2 coins
SHIFT_ROCK_SPEED = 1.35          # ROCKS FAST
SHIFT_GLASS = 1.5                # GLASS CANNON: damage dealt and taken
SPLIT_TIME = 0.6                 # splitter bullets swell, then burst into 3
BOOMERANG_TIME = 1.6             # a boomerang is back where it started after this long
RUNE_TIME = 0.8                  # a rune mark blooms into a ring after this long
RUNE_SHOTS = 8
WISP_HP = 10
WISP_SPEED = 26                  # px/s drifting down
WISP_DODGE = 150                 # px/s side-step when a shot is lined up on it
WISP_DODGE_COOLDOWN = 0.9
WISP_FIRE = 1.8                  # seconds between its lead shots
WISP_BULLET_SPEED = 95
WISP_BULLET_DAMAGE = 16
POINTS_WISP = 160
RIFT_RADIUS = 10
RIFT_LIFE = 9.0                  # seconds a pair of rift portals stays open
RIFT_OPEN = 1.0                  # shimmer before it carries anything
RIFT_INTERVAL = (6.0, 9.0)
AMBUSH_ROCKS = 0.6                # rocks keep falling during an ambush fight, a bit thinner

# --- Abilities (galaxy 2: one slot, SHIFT or the right mouse button) ------------------------
ABILITY_COOLDOWN = {"PHASE": 7.0, "FLARE": 14.0, "TIME SLIP": 16.0, "REPAIR DRONE": 20.0,
                    "DECOY": 15.0}
PHASE_TIME = 0.45                # PHASE: i-frames ...
PHASE_DASH = 80                  # ... and a dash this far (px) where the rocket is heading
FLARE_TIME = 5.0                 # FLARE: the darkness lifts, lurkers show
TIME_SLIP_TIME = 2.5             # TIME SLIP: the enemy side runs at ...
TIME_SLIP_SCALE = 0.35           # ... this speed
REPAIR_TIME = 5.0                # REPAIR DRONE: heals ...
REPAIR_SHARE = 0.18              # ... this share of the hull over REPAIR_TIME
DECOY_TIME = 3.5                 # DECOY: aimed shots go for a copy of the rocket

# --- G2 L2 BONE REEF (PURSUIT) -----------------------------------------------------------
MARROW_REGROW = 3.0              # seconds until a marrow core grows its bone rock back
MARROW_MIN_RADIUS = 7            # bone rocks this big leave a marrow core
PURSUIT_RISE = 9.0               # px/s the maw's bite line creeps up the screen ...
PURSUIT_FALL = 26.0              # ... and falls back while the rocket boosts (UP)
PURSUIT_START = 40               # px above the bottom edge where the bite line starts
PURSUIT_BITE = 0.1               # share of max hull a bite takes
PURSUIT_SATED = 30               # px the jaws drop back after a bite (no bite chains)
PURSUIT_SPEED = 1.3              # the world rushes past during the chase
STALKER_HP = 16
STALKER_SPEED = 70
STALKER_DASH = 260               # px/s: the striker's dash across the screen
STALKER_WARN = 0.7               # its dotted line shows this long first
STALKER_DAMAGE = 22
POINTS_STALKER = 220

# --- G2 L3 BROOD SANCTUARY (ESCORT) ------------------------------------------------------
POD_HP = 600                     # the brood pod's hull (its own bar)
POD_SPEED = 18                   # px/s it drifts from side to side
LATCHER_HP = 9
LATCHER_SPEED = 80
LATCHER_DRAIN = 14               # pod hull per second while a latcher is on it
POINTS_LATCHER = 120
ALLY_DAMAGE = 9                  # a freed larva's zap
ALLY_INTERVAL = 1.1
ALLY_RANGE = 90
POD_SAVED_COINS = 400            # the brood survives: its gift of credits
REAPER_DRAIN = 55                # pod hull per second while the Reaper harvests
REAPER_BREAK = 0.035             # share of the Reaper's max hp on its scythe breaks a harvest

# --- G2 L4 THE DARK VEIL (DARKNESS) ------------------------------------------------------
DARK_ALPHA = 238                 # how black the dark is (0..255)
LIGHT_SHIP = 58                  # px: the rocket's light
LIGHT_SHOT = 12                  # px: every tracer carries a little light
LIGHT_BOOM = 34                  # px: explosions light the field for a moment
LURKER_HP = 14
LURKER_SPEED = 38
LURKER_FIRE = 2.0
POINTS_LURKER = 200

# --- G2 L5 MIRROR SEA (MIRROR) -----------------------------------------------------------
REFLECTION_HP = 40               # your mirror image's hull; it reforms ...
REFLECTION_BACK = 8.0            # ... after this long
REFLECTION_FIRE = 0.3            # it fires when you fire, this often
PHASE_ROCK_CYCLE = (2.2, 1.6)    # seconds solid, seconds ghost
ECHO_DELAY = 3.0                 # an echo flies where you were this long ago ...
ECHO_DROP = 0.3                  # ... and leaves a mine there this often
ECHO_HP = 12
POINTS_ECHO = 180
HISTORY_SECONDS = 12.0           # how much of the rocket's path the game remembers

# --- G2 L6 PULSE NEBULA (RHYTHM) ---------------------------------------------------------
PULSE_BPM = 120                  # the level's music; the enemy side moves on its beat
PULSE_LOW = 0.25                 # speed between beats ...
PULSE_HIGH = 2.25                # ... and on the beat (cos^2 pulse: averages 1)
CAGE_SPEED = 55                  # px/s the cage walls close in
CAGE_GAP = 46                    # px: the gap in each wall
