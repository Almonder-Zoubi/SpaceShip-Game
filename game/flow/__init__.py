"""Game flow: the Game class (main loop) and its parts, one mixin per responsibility.

game        -- Game: setup, main loop, update order, presenting the canvas
states      -- State (title, playing, ...) and Phase (field, warning, boss, cleared)
events      -- key handling per state
level_flow  -- runs, levels, waves, level phases, the equipped loadout
world       -- moving rocks / minions / boss / bullets / pickups, hazards to the ship
combat      -- player hits: damage, kills, score, BLAST / ULTIMATE charge
progression -- pending coins, level stats, rank + payout
hangar      -- hangar tabs, buying, weapon slots, gifts
juice       -- juice tiers (shake, hit-stop, slow-mo), boss damage numbers, radio cards
boosts      -- boost timers + drops, shield, combo / FEVER
wingmen     -- the flying wingmen, their hits, knock-outs, XP
skins       -- skins worn, death styles, achievements
options     -- pause-menu options (volume, reduce shake / flashes)
sound       -- music per state, loops
dev         -- dev menu and hotkeys
finale      -- the galaxy finale: WARP cut-scene, galaxy medal
starmap     -- the STAR MAP state: flying, data caches, landing on a planet
"""
