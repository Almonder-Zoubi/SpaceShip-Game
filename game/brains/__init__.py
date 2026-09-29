"""The enemy's brains (pure Python, no pygame, saved with the profile). This is real online
learning, small enough to explain: no neural network, just counting and averaging.

model    -- PlayerModel: where the rocket lives (8x6 heatmap), which way it dodges, which
            weapon it fires, how fast it reacts to a telegraph
bandit   -- Bandit: a learning boss picks the attack that hurts *you* most (UCB1 + a fixed
            share of exploring)
director -- Director: paces a level with peaks and breathers, never below the base difficulty
insight  -- insights(): what they learned, in words ("YOU ALWAYS BREAK LEFT.")
"""
