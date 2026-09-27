"""Drawing a frame: world layers, HUD, and the full-screen overlays of every state."""
import math

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import (ACCENT, BOOST_COLORS, COIN, DANGER, EMPTY, GOOD, INK, RANK_COLORS, SPACE, TEXT,
                              TEXT_DIM, TEXT_SHADOW)
from ..flow.states import Phase, State
from ..levels.data import LEVELS


class ScreensMixin:
    """Game mixin: draw() renders the world and the overlay of the current state."""

    def draw(self):
        c = self.canvas
        c.fill(SPACE)
        self.background.draw(c)
        hazard = self.hazard if self.state not in (State.TITLE, State.HANGAR, State.REWARD,
                                                   State.DEV_MENU) else None
        if hazard:
            hazard.draw_back(c)
        self.smoke.draw(c)
        for rock in self.asteroids:
            rock.draw(c)
        if self.boss:
            self.boss.draw(c)
        for enemy in self.enemies:
            enemy.draw(c)
        for pickup in self.pickups:
            pickup.draw(c)
        if hazard:
            hazard.draw_mid(c)
        if self.state == State.PLAYING and self.ship.alive and self.mouse.aim:
            self._draw_reticle(c, *self.mouse.aim)
        if self.ship.alive and self.state not in (State.DEV_MENU, State.HANGAR, State.REWARD):
            self.ship.draw_flames(c)
            self.ship.draw(c)
            self.draw_wingmen(c)
            if self.shield and self.state == State.PLAYING:
                self._draw_shield(c)
        for weapon in self.weapons + list(self.secondaries.values()):
            weapon.draw(c)
        for x0, y0, x1, y1 in self.refractions:   # split laser beams
            pygame.draw.line(c, self.weapons[1].colors[2], (int(x0), int(y0)), (int(x1), int(y1)))
            c.fill(self.weapons[1].colors[0], (int(x1), int(y1), 2, 2), special_flags=pygame.BLEND_ADD)
        self.blast.draw(c)
        self.ultimate.draw(c)
        self.fire.draw(c)
        blink = int(self.time * 12) % 2 == 0
        for bullet in self.enemy_bullets:
            bullet.draw(c, blink)
        for wave in self.shockwaves:
            wave.draw(c)
        if hazard:
            hazard.draw_front(c)
        if self.hurt_flash > 0:
            v = int(110 * self.hurt_flash / 0.25)
            c.fill((v, 0, 0), special_flags=pygame.BLEND_ADD)
        self._draw_overlay(c)
        if self.flash > 0:
            v = int(255 * min(1.0, self.flash / 0.12))
            c.fill((v, v, v), special_flags=pygame.BLEND_ADD)

    def _draw_shield(self, c):
        """SHIELD bubble: a shimmering ring, one pip per hit it can still take."""
        ship = self.ship
        colors = BOOST_COLORS["SHIELD"]
        r = max(ship.w, ship.h) // 2 + 4 + self.shield_wobble(self.time)
        pygame.draw.circle(c, colors[3], (int(ship.x), int(ship.y)), r + 1, 1)
        pygame.draw.circle(c, colors[2], (int(ship.x), int(ship.y)), r, 1)
        for i in range(self.shield):
            a = self.time * 3 + i * math.tau / 3
            c.fill(colors[0], (int(ship.x + math.cos(a) * r), int(ship.y + math.sin(a) * r), 2, 2))

    def _draw_reticle(self, c, x, y):
        """Mouse target: four small ticks around the point (drawn under the ship)."""
        x, y = int(x), int(y)
        color = DANGER if self.mouse.firing else TEXT_DIM
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.fill(color, (x + dx * 3 - (dx < 0), y + dy * 3 - (dy < 0), 1 + abs(dx), 1 + abs(dy)))

    def _draw_overlay(self, c):
        blink = int(self.time * 2.5) % 2 == 0
        s = self.state
        if s == State.TITLE:
            self._draw_title(c, blink)
            return
        if s == State.DEV_MENU:
            self._draw_dev_menu(c, blink)
            return
        if s in (State.HANGAR, State.REWARD):           # dim the ambient rocks behind the menu
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((*SPACE, 170))
            c.blit(shade, (0, 0))
        if s == State.HANGAR:
            self.hangar_screen.draw(c, self.hangar_view(), self.time, blink)
            return
        if s == State.REWARD:
            self.gift_screen.draw(c, self.gift_options, self.gift_cursor,
                                  self.gift_key.split("-")[1], self.gift_paint, self.time, blink)
            return
        loadout = self.ship.loadout
        self.hud.draw(c, self.ship, self.score, max(self.best, self.score),
                      self.distance / self.wave.length, self.weapon, self.time, boss=self.boss,
                      level=self._level_label(), blast=self.blast if loadout.blast else None,
                      ultimate=self.ultimate if loadout.ultimate else None,
                      galaxy=self.galaxy.number, switchable=len(self.primaries) > 1,
                      secondary=self.secondary.name if self.secondary else None,
                      boosts=(self.boosts, self.shield, self.fever),
                      combo=(self.combo, self.combo_mult, self.combo_ratio(self.combo_time)),
                      coins=None if self.payout else   # results screen counts them
                      (self.save.coins, self.pending_coins, self.coin_flash))
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
        if self.radio and s in (State.PLAYING, State.PAUSED):
            self.radio_view.draw(c, self.radio, self.time)
        if s == State.PAUSED:
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            c.blit(shade, (0, 0))
            self._draw_pause(c, blink)
        elif s == State.GAME_OVER:
            self.hud.banner(c, "GAME OVER", f"R: RETRY LEVEL {self.level.number}",
                            title_color=DANGER, blink_on=blink)
            self.font.draw(c, f"SCORE {self.score}", (LOW_W // 2, LOW_H // 2 + 40),
                           TEXT_DIM, shadow=TEXT_SHADOW, center=True)
            self._draw_record_rank(c, LOW_H // 2 + 52)
            if self.pending_coins:                      # coins only count when a level is won
                self.font.draw(c, f"{self.pending_coins} CREDITS LOST", (LOW_W // 2, LOW_H // 2 + 64),
                               DANGER, shadow=TEXT_SHADOW, center=True)
        elif s in (State.LEVEL_CLEAR, State.WIN) and self.state_time > 0.8:
            self._draw_results(c, blink, win=s == State.WIN)

    def _draw_pause(self, c, blink):
        """PAUSED title and the options menu."""
        f = self.font
        panel = pygame.Rect(60, 52, 200, 120)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((*INK, 200))
        c.blit(shade, panel)
        pygame.draw.rect(c, TEXT_DIM, panel, 1)
        f.draw(c, "PAUSED", (LOW_W // 2, panel.y + 8), TEXT, scale=3, shadow=TEXT_SHADOW,
               center=True)
        for i, (key, label) in enumerate(self.options.ROWS):
            y = panel.y + 42 + i * 13
            selected = i == self.options_cursor
            if selected:
                c.fill(EMPTY, (panel.x + 6, y - 3, panel.w - 12, 12))
                f.draw(c, ">", (panel.x + 9, y), ACCENT, shadow=TEXT_SHADOW)
            f.draw(c, label, (panel.x + 18, y), ACCENT if selected else TEXT, shadow=TEXT_SHADOW)
            value = self.options.text(key)
            if key in ("music", "sound"):
                self.hud._bar(panel.right - 72, y + 1, 50, 4, c, self.options[key] / 10, GOOD)
            color = TEXT if self.options[key] else TEXT_DIM
            f.draw(c, value, (panel.right - 10 - f.size(value)[0], y), color, shadow=TEXT_SHADOW)
        if blink:
            f.draw(c, "P RESUME   ESC MENU   ARROWS OPTIONS", (LOW_W // 2, panel.bottom - 12),
                   TEXT_DIM, shadow=TEXT_SHADOW, center=True)

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
            text = "FINAL BOSS"
        elif last and sum(len(w.bosses) for w in level.waves) > 1:
            text = "LEVEL BOSS"
        else:
            text = "BOSS APPROACHING"
        self._draw_name_card(c, text, name, getattr(self.boss_entry.boss_class, "EPITHET", ""))
        if self.phase_time < 2.0:
            self.font.draw(c, "HULL REPAIRED", (LOW_W // 2, 166), GOOD, shadow=TEXT_SHADOW,
                           center=True)

    def _draw_name_card(self, c, label, name, epithet):
        """Boss name card: slides in from the left during the WARNING."""
        f = self.font
        k = min(1.0, self.phase_time / 0.35)
        w = max(f.size(name, 2)[0], f.size(epithet)[0]) + 30
        card = pygame.Rect(0, 114, w, 42)
        card.centerx = int(LOW_W // 2 - (1 - k) ** 2 * LOW_W)
        shade = pygame.Surface(card.size, pygame.SRCALPHA)
        shade.fill((*INK, 220))
        c.blit(shade, card)
        c.fill(DANGER, (card.x, card.y, 3, card.h))
        c.fill(DANGER, (card.right - 3, card.y, 3, card.h))
        f.draw(c, label, (card.centerx, card.y + 4), DANGER, shadow=TEXT_SHADOW, center=True)
        f.draw(c, name, (card.centerx, card.y + 14), TEXT, scale=2, shadow=TEXT_SHADOW,
               center=True)
        if epithet:
            f.draw(c, epithet, (card.centerx, card.y + 31), TEXT_DIM, shadow=TEXT_SHADOW,
                   center=True)

    def _draw_results(self, c, blink, win):
        """Level results: stats with rating bars, the rank stamp, coins counted into the bank,
        then the ship upgrade waiting in the next level (or the record after a win)."""
        f = self.font
        panel = pygame.Rect(35, 8, 250, 218)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((*INK, 210))
        c.blit(shade, panel)
        pygame.draw.rect(c, TEXT_DIM, panel, 1)
        left, right, mid = panel.left + 10, panel.right - 10, LOW_W // 2
        title = "YOU WIN!" if win else f"LEVEL {self.level.number} CLEAR"
        f.draw(c, title, (mid, 14), GOOD, scale=2, shadow=TEXT_SHADOW, center=True)
        f.draw(c, f"SCORE {self.score}", (mid, 34), TEXT_DIM, shadow=TEXT_SHADOW, center=True)

        stats = self.stats
        ratings = stats.ratings()
        boss = (f"{int(stats.boss_time)}S / {int(stats.boss_par)}S" if stats.boss_par else "-")
        seen = stats.destroyed + stats.escaped
        rows = (("DAMAGE TAKEN", f"{int(stats.damage_taken)} HP", ratings["damage"]),
                ("BOSS TIME", boss, ratings["speed"]),
                ("DESTROYED", f"{round(100 * stats.destroyed / seen) if seen else 100}%",
                 ratings["destroyed"]))
        for i, (label, value, rating) in enumerate(rows):
            y = 48 + i * 10
            f.draw(c, label, (left, y), TEXT, shadow=TEXT_SHADOW)
            f.draw(c, value, (left + 136 - f.size(value)[0], y), TEXT_DIM, shadow=TEXT_SHADOW)
            self.hud._bar(left + 142, y + 1, 40, 4, c, rating, GOOD if rating > 0.6 else ACCENT)
        if self.state_time > self.RANK_TIME:            # the rank lands like a stamp
            scale = 7 if self.state_time < self.RANK_TIME + 0.12 else 5
            color = RANK_COLORS[self.level_rank]
            f.draw(c, self.level_rank, (right - 22, 62 - scale * 7 // 2), color, scale=scale,
                   shadow=TEXT_SHADOW, center=True)
            f.draw(c, "RANK", (right - 22, 84), TEXT_DIM, shadow=TEXT_SHADOW, center=True)

        p = self.payout
        lines = [("PICKED UP", f"+{p.pending}"),
                 (f"CLEAR BONUS {self.level_rank}", f"+{p.clear_bonus}")]
        lines.append(("REPLAY PAYS 50%", "X0.5") if p.replay else ("FIRST CLEAR", f"+{p.first_clear}"))
        for i, (label, value) in enumerate(lines):
            y = 96 + i * 10
            f.draw(c, label, (left, y), TEXT, shadow=TEXT_SHADOW)
            f.draw(c, value, (right - f.size(value)[0], y), COIN[2], shadow=TEXT_SHADOW)
        tally = self.tally()
        f.draw(c, f"TOTAL +{p.total}", (left, 131), TEXT, shadow=TEXT_SHADOW)
        bank = f"CR {self.bank_before + tally}"
        f.draw(c, bank, (right - f.size(bank, 2)[0], 127), TEXT if 0 < tally < p.total else COIN[2],
               scale=2, shadow=TEXT_SHADOW)
        c.fill(TEXT_DIM, (left, 147, right - left, 1))

        if win:
            self._draw_record_rank(c, 160)
            if blink and self.state_time > 1.0:
                f.draw(c, "ENTER: CONTINUE   R: PLAY AGAIN", (mid, 214), TEXT,
                       shadow=TEXT_SHADOW, center=True)
            return
        nxt = LEVELS[self.level_index + 1]
        if nxt.loadout != self.level.loadout:
            f.draw(c, f"SHIP UPGRADE: {self.hull.name} {nxt.loadout.name}", (mid, 154), ACCENT,
                   shadow=TEXT_SHADOW, center=True)
            for i, note in enumerate(self._upgrade_notes(nxt)):
                f.draw(c, note, (mid, 166 + i * 10), TEXT, shadow=TEXT_SHADOW, center=True)
        if blink and self.state_time > 1.0:
            f.draw(c, f"ENTER: LEVEL {nxt.number}", (mid, 214), TEXT, shadow=TEXT_SHADOW,
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
        lines = ("ARROWS / WASD / MOUSE  MOVE",
                 "UP  BOOST     DOWN  RETRO",
                 "SPACE / LEFT CLICK  FIRE",
                 "R  GUN / LASER    T  ULTIMATE",
                 "P PAUSE   C SCANLINES   ESC QUIT")
        for i, line in enumerate(lines):
            f.draw(c, line, (LOW_W // 2, 134 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if self.best:
            f.draw(c, f"HI {self.best}", (LOW_W // 2, 8), ACCENT, shadow=TEXT_SHADOW, center=True)

    def _draw_dev_menu(self, c, blink):
        f = self.font
        f.draw(c, "DEV MODE", (LOW_W // 2, 8), DANGER, scale=2, shadow=TEXT_SHADOW, center=True)
        f.draw(c, "PICK A START POINT", (LOW_W // 2, 28), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        items, rows = self.dev_items(), 10               # scrolls when there are more
        first = max(0, min(self.dev_cursor - rows // 2, len(items) - rows))
        if first > 0:
            pygame.draw.polygon(c, TEXT_DIM, [(LOW_W // 2 - 3, 40), (LOW_W // 2 + 3, 40),
                                              (LOW_W // 2, 37)])
        if first + rows < len(items):
            pygame.draw.polygon(c, TEXT_DIM, [(LOW_W // 2 - 3, 159), (LOW_W // 2 + 3, 159),
                                              (LOW_W // 2, 162)])
        for i, (label, *_) in enumerate(items[first:first + rows], first):
            selected = i == self.dev_cursor
            y = 42 + (i - first) * 12
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
        f.draw(c, "3 REPAIR   4 COINS   G GOD   ESC MENU", (LOW_W // 2, 221), TEXT_DIM,
               shadow=TEXT_SHADOW, center=True)


def _num(value):
    """Stat for display: at most one decimal, no trailing zero."""
    return f"{round(value, 1):g}"
