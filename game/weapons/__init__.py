"""Player weapons. Weapons never apply damage: update() returns Hits and the game applies them.

base      -- Hit, Weapon base class, raycast(), is_boss_part()
gun       -- MachineGun (tracer rounds)
laser     -- Laser (beam that overheats)
scatter   -- Scatter (shotgun pellets)
plasma    -- Plasma (piercing orbs)
arc       -- Arc (chain lightning)
specials  -- Charged base, Blast, Ultimate (+ Missile) for the MK III
homing    -- RocketSwarm (homing rockets: HUNTER wingman, ROCKET POD)
bolts     -- Bolts (small straight shots: wingmen, SIDE CANNONS)
secondary -- RocketPod, SideCannons (automatic, rocks + minions only)
"""
