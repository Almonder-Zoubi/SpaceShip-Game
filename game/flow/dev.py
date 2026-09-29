"""Dev mode (--dev): menu of every start point, god mode, in-game hotkeys."""
import pygame

from ..config.palette import DANGER
from ..config.tuning import WARNING_TIME
from ..levels.data import LEVELS
from ..ui.popup import Popup
from ..weapons.base import Hit
from .states import Phase


class DevMixin:
    """Game mixin: debugging aids. Dev runs never write the save file."""

    @staticmethod
    def dev_items():
        """Every start point in the game: (label, level index, wave index, boss index)."""
        items = []
        for li, level in enumerate(LEVELS):
            for wi, wave in enumerate(level.waves):
                tag = f"{level.number}-{wi + 1}" if len(level.waves) > 1 else f"{level.number}"
                items.append((f"LEVEL {tag}  FIELD", li, wi, None))
                for bi, entry in enumerate(wave.bosses):
                    spec = entry.spec
                    items.append((f"LEVEL {tag}  {spec.name} {spec.strength:g}X", li, wi, bi))
        return items

    def dev_key(self, key):
        """Dev hotkeys while playing. Returns True if the key was one of them."""
        if key == pygame.K_g:
            self.god = not self.god
            self.popups.append(Popup(f"GOD MODE {'ON' if self.god else 'OFF'}", self.ship.x,
                                     self.ship.y - 24, DANGER))
        elif key == pygame.K_n:
            self.dev_skip()
        elif key == pygame.K_1:
            self.blast.charge = self.ultimate.charge = 1.0
        elif key == pygame.K_2:
            for weapon in self.weapons:
                weapon.power_up()
        elif key == pygame.K_3:
            self.ship.hp = self.ship.max_hp
        elif key == pygame.K_4:
            self.collect_coins(50)
        elif key == pygame.K_d:                        # the DIRECTOR on any level
            self.force_director = not getattr(self, "force_director", False)
            self.popups.append(Popup(f"DIRECTOR {'ON' if self.force_director else 'OFF'}",
                                     self.ship.x, self.ship.y - 24, DANGER))
        else:
            return False
        return True

    def dev_skip(self):
        """End the field, finish the warning / boss entry, or knock the boss into its next
        phase (the last phase: kill it). Goes through the normal damage path, so rewards
        and charges happen as in a real fight."""
        b = self.boss
        if self.phase == Phase.FIELD:
            self.distance = self.wave.length
        elif self.phase == Phase.WARNING:
            self.phase_time = WARNING_TIME
        elif self.phase == Phase.BOSS and b.state == "enter":
            b.state_time = b.ENTER_TIME
        elif self.phase == Phase.BOSS and b.fighting:
            b.roar = 0
            floor = b.max_hp * (b.PHASES - 1 - b.phase) / b.PHASES if b.phase < b.PHASES - 1 else 0
            self._damage_boss(Hit(b, b.hp - floor + 1e-6, b.x, b.y, 0, -1, 0, charges=False))
