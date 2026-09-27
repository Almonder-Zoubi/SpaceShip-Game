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
