"""Game flow: the Game class (main loop) and its parts, one mixin per responsibility.

game       -- Game: setup, main loop, update order, presenting the canvas
states     -- State (title, playing, ...) and Phase (field, warning, boss, cleared)
events     -- key handling per state
level_flow -- runs, levels, waves, level phases
world      -- moving rocks / minions / boss / bullets / pickups, hazards to the ship
combat     -- player hits: damage, kills, score, BLAST / ULTIMATE charge
dev        -- dev menu and hotkeys
"""
