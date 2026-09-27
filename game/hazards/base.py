"""Hazard base class: a level-wide mechanic that lives as long as the level."""


class Hazard:
    """The game calls update(dt, game) every frame of the level and draws it in three layers:
    draw_back (behind rocks), draw_mid (over rocks and minions, under the ship and enemy
    bullets) and draw_front (over everything but the HUD)."""

    def update(self, dt, game):
        pass

    def draw_back(self, surf):
        pass

    def draw_mid(self, surf):
        pass

    def draw_front(self, surf):
        pass
