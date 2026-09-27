"""Drawing a frame: world layers, HUD, and the full-screen overlays of every state."""
import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import (ACCENT, DANGER, EMPTY, GOOD, INK, SPACE, TEXT, TEXT_DIM,
                              TEXT_SHADOW)
from ..flow.states import Phase, State
from ..levels.data import LEVELS


class ScreensMixin:
    """Game mixin: draw() renders the world and the overlay of the current state."""

    def draw(self):
        c = self.canvas
        c.fill(SPACE)
        self.background.draw(c)
        self.smoke.draw(c)
        for rock in self.asteroids:
            rock.draw(c)
        if self.boss:
            self.boss.draw(c)
        for enemy in self.enemies:
            enemy.draw(c)
        for pickup in self.pickups:
            pickup.draw(c)
        if self.ship.alive and self.state not in (State.DEV_MENU, State.HANGAR):   # menus need room
            self.ship.draw_flames(c)
            self.ship.draw(c)
        for weapon in self.weapons:
            weapon.draw(c)
        self.blast.draw(c)
        self.ultimate.draw(c)
        self.fire.draw(c)
        blink = int(self.time * 12) % 2 == 0
        for bullet in self.enemy_bullets:
            bullet.draw(c, blink)
        for wave in self.shockwaves:
            wave.draw(c)
        if self.hurt_flash > 0:
            v = int(110 * self.hurt_flash / 0.25)
            c.fill((v, 0, 0), special_flags=pygame.BLEND_ADD)
        self._draw_overlay(c)
        if self.flash > 0:
            v = int(255 * min(1.0, self.flash / 0.12))
            c.fill((v, v, v), special_flags=pygame.BLEND_ADD)

    def _draw_overlay(self, c):
        blink = int(self.time * 2.5) % 2 == 0
        s = self.state
        if s == State.TITLE:
            self._draw_title(c, blink)
            return
        if s == State.DEV_MENU:
            self._draw_dev_menu(c, blink)
            return
        if s == State.HANGAR:
            self._draw_hangar(c, blink)
            return
        loadout = self.ship.loadout
        self.hud.draw(c, self.ship, self.score, max(self.best, self.score),
                      self.distance / self.wave.length, self.weapon, self.time, boss=self.boss,
                      level=self._level_label(), blast=self.blast if loadout.blast else None,
                      ultimate=self.ultimate if loadout.ultimate else None)
        if self.dev:                                    # dev runs are marked, never recorded
            self.font.draw(c, "DEV GOD" if self.god else "DEV", (6, 24), DANGER,
                           shadow=TEXT_SHADOW)
        for popup in self.popups:
            popup.draw(c, self.font)
        if s == State.PLAYING and self.phase == Phase.WARNING:
            self._draw_warning(c)
        elif s == State.PLAYING and self.alert:
            title, subtitle, color, _ = self.alert
            self.hud.alert(c, title, subtitle, color, blink_on=int(self.time * 5) % 3 != 0)
        if s == State.PAUSED:
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            c.blit(shade, (0, 0))
            self.hud.banner(c, "PAUSED", "P TO RESUME  -  ESC FOR MENU", blink_on=blink)
        elif s == State.GAME_OVER:
            self.hud.banner(c, "GAME OVER", f"R: RETRY LEVEL {self.level.number}",
                            title_color=DANGER, blink_on=blink)
            self.font.draw(c, f"SCORE {self.score}", (LOW_W // 2, LOW_H // 2 + 40),
                           TEXT_DIM, shadow=TEXT_SHADOW, center=True)
            self._draw_record_rank(c, LOW_H // 2 + 52)
        elif s == State.LEVEL_CLEAR and self.state_time > 0.8:
            self._draw_level_clear(c, blink)
        elif s == State.WIN and self.state_time > 0.8:
            self.hud.banner(c, "YOU WIN!", "PRESS R TO PLAY AGAIN", title_color=GOOD, blink_on=blink)
            self._draw_record_rank(c, LOW_H // 2 + 40)

    def _draw_warning(self, c):
        """Classic boss alert: blinking red stripes and WARNING, 'hull repaired' note."""
        on = int(self.phase_time * 4) % 2 == 0
        if on:
            for y in (70, 142):
                for x in range(-16, LOW_W, 16):
                    offset = int(self.phase_time * 40) % 16
                    pygame.draw.polygon(c, DANGER, [(x + offset, y), (x + offset + 8, y),
                                                    (x + offset + 12, y + 6), (x + offset + 4, y + 6)])
            self.font.draw(c, "WARNING", (LOW_W // 2, 88), DANGER, scale=4, shadow=TEXT_SHADOW,
                           center=True)
        level, bosses = self.level, self.wave.bosses
        name = self.boss_entry.spec.name
        last = self.wave_index == len(level.waves) - 1 and self.boss_index == len(bosses) - 1
        if self.is_final_boss():
            text = f"FINAL BOSS: {name}"
        elif last and sum(len(w.bosses) for w in level.waves) > 1:
            text = f"LEVEL BOSS: {name}"
        else:
            text = f"BOSS APPROACHING: {name}"
        self.font.draw(c, text, (LOW_W // 2, 124), TEXT, shadow=TEXT_SHADOW, center=True)
        if self.phase_time < 2.0:
            self.font.draw(c, "HULL REPAIRED", (LOW_W // 2, 160), GOOD, shadow=TEXT_SHADOW,
                           center=True)

    def _draw_level_clear(self, c, blink):
        """'LEVEL 1 CLEAR' and the ship upgrade waiting in the next level."""
        f = self.font
        nxt = LEVELS[self.level_index + 1]
        panel = pygame.Rect(0, 0, 220, 128)
        panel.midtop = (LOW_W // 2, 44)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((*INK, 200))
        c.blit(shade, panel)
        pygame.draw.rect(c, TEXT_DIM, panel, 1)
        f.draw(c, f"LEVEL {self.level.number} CLEAR", (LOW_W // 2, 52), GOOD, scale=2,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, f"SCORE {self.score}", (LOW_W // 2, 72), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if nxt.loadout != self.level.loadout:
            f.draw(c, f"SHIP UPGRADE: {self.hull.name} {nxt.loadout.name}", (LOW_W // 2, 88),
                   ACCENT, shadow=TEXT_SHADOW, center=True)
            for i, note in enumerate(self._upgrade_notes(nxt)):
                f.draw(c, note, (LOW_W // 2, 102 + i * 10), TEXT, shadow=TEXT_SHADOW, center=True)
        if blink and self.state_time > 1.0:
            f.draw(c, f"ENTER: LEVEL {nxt.number}", (LOW_W // 2, 158), TEXT, shadow=TEXT_SHADOW,
                   center=True)

    def _upgrade_notes(self, nxt):
        """Stat changes of the chosen hull from this level's ship model to the next, plus the
        level's own notes (new features)."""
        old, new = self.loadout_for(self.level), self.loadout_for(nxt)
        laser = round(new.laser_dps / old.laser_dps * 100 - 100)
        cooler = "  RUNS COOLER" if new.laser_heat_rate < old.laser_heat_rate else ""
        return (f"HULL {old.max_hp} > {new.max_hp}   GUN {_num(old.gun_damage)} > "
                f"{_num(new.gun_damage)}",
                f"LASER +{laser}%{cooler}") + nxt.upgrade_notes

    def _draw_hangar(self, c, blink):
        self.hangar_screen.draw(c, self.hangar_cursor, LEVELS[self.start_level].loadout,
                                LEVELS[self.start_level].number, self.time, blink)

    def _draw_record_rank(self, c, y):
        if self.record_rank == 1:
            text, color = "NEW HIGH SCORE!", ACCENT
        elif self.record_rank:
            text, color = f"RECORD #{self.record_rank}", GOOD
        else:
            return
        if int(self.time * 4) % 2 == 0:
            self.font.draw(c, text, (LOW_W // 2, y), color, shadow=TEXT_SHADOW, center=True)

    def _draw_title(self, c, blink):
        f = self.font
        f.draw(c, "DODGING", (LOW_W // 2, 24), ACCENT, scale=4, shadow=DANGER, center=True)
        f.draw(c, "ASTEROID", (LOW_W // 2, 58), TEXT, scale=4, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(c, "PRESS ENTER", (LOW_W // 2, 100), TEXT, scale=2, shadow=TEXT_SHADOW, center=True)
        if self.selectable_levels > 1:                  # unlocked levels: choose with LEFT/RIGHT
            level = LEVELS[self.start_level]
            f.draw(c, f"<  LEVEL {level.number}: {level.name}  >", (LOW_W // 2, 119), ACCENT,
                   shadow=TEXT_SHADOW, center=True)
        records = self.save.records
        if records and int(self.time / 6) % 2 == 1:     # attract mode: alternate with controls
            f.draw(c, "TOP SCORES", (LOW_W // 2, 134), ACCENT, shadow=TEXT_SHADOW, center=True)
            for i, r in enumerate(records):
                line = f"{i + 1}. {r['score']:06d}  LEVEL {r['level']}  {r['date']}"
                f.draw(c, line, (LOW_W // 2, 147 + i * 10), TEXT if i == 0 else TEXT_DIM,
                       shadow=TEXT_SHADOW, center=True)
            return
        lines = ("ARROWS / WASD  MOVE",
                 "UP  BOOST     DOWN  RETRO",
                 "SPACE  FIRE    R  GUN / LASER",
                 "T  ULTIMATE  (LEVEL 3)",
                 "P PAUSE   C SCANLINES   ESC QUIT")
        for i, line in enumerate(lines):
            f.draw(c, line, (LOW_W // 2, 134 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if self.best:
            f.draw(c, f"HI {self.best}", (LOW_W // 2, 8), ACCENT, shadow=TEXT_SHADOW, center=True)

    def _draw_dev_menu(self, c, blink):
        f = self.font
        f.draw(c, "DEV MODE", (LOW_W // 2, 8), DANGER, scale=2, shadow=TEXT_SHADOW, center=True)
        f.draw(c, "PICK A START POINT", (LOW_W // 2, 28), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        for i, (label, *_) in enumerate(self.dev_items()):
            selected = i == self.dev_cursor
            y = 42 + i * 12
            if selected:
                c.fill(EMPTY, (60, y - 2, LOW_W - 120, 11))
                f.draw(c, ">", (66, y), ACCENT, shadow=TEXT_SHADOW)
            f.draw(c, label, (78, y), ACCENT if selected else TEXT, shadow=TEXT_SHADOW)
        f.draw(c, f"<  SHIP: {self.hull.name}  >", (LOW_W // 2, 166), ACCENT,
               shadow=TEXT_SHADOW, center=True)
        god = "ON" if self.god else "OFF"
        f.draw(c, f"G  GOD MODE: {god}", (LOW_W // 2, 178), DANGER if self.god else TEXT,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "UP/DOWN SELECT  LEFT/RIGHT SHIP  ENTER START", (LOW_W // 2, 194), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "IN GAME:  N SKIP   1 CHARGE   2 POWER", (LOW_W // 2, 210), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)
        f.draw(c, "3 REPAIR   G GOD   ESC MENU", (LOW_W // 2, 221), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)


def _num(value):
    """Stat for display: at most one decimal, no trailing zero."""
    return f"{round(value, 1):g}"
