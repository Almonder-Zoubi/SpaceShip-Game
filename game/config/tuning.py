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
UPGRADE_TIERS = 5
UPGRADE_COSTS = (100, 200, 350, 550, 800)     # price of tier 1 .. 5
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
