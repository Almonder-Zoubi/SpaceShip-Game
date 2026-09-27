"""Bosses. Each boss module holds its sprite (drawn on a CharCanvas), muzzle / vent
coordinates and its Boss subclass, so everything about one boss lives in one file.

spec       -- BossSpec: HP and damage derived from the level's ship (damage-race balance)
base       -- Boss base class: enter, fight, phases + roar, dying; drone launch helper
art        -- shared hull colours and build_boss_sprite()
gunship    -- boss 1
carrier    -- boss 2 (3 phases, launches drones)
mothership -- boss 3 (3 phases, sweeping beam)
leviathan  -- boss 4, final boss: a segmented serpent (Segment parts, head weak spot, dives)
"""
