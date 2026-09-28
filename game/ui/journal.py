"""The JOURNAL screen: the logbook of scout ARROW-01, in four pages (PILOT, BOSSES, ECHOES,
LOG). The data comes from flow/journal.py as a JournalPage; this only draws."""
import random

import pygame

from ..config.display import LOW_H, LOW_W
from ..config.palette import (ACCENT, COIN, DANGER, GOOD, INK, TEXT, TEXT_DIM, TEXT_SHADOW)
from ..config.tuning import UPGRADE_TIERS
from ..player.art import SHIP_PALETTES, build_ship_frames
from ..player.hulls import ARROW
from ..story.lore import MOSAIC
from .medal import draw_medal
from .portraits import Portraits

TABS = ("PILOT", "BOSSES", "ECHOES", "LOG")
PAPER = (14, 12, 26)
NOTE = (230, 70, 80)             # the margin notes: someone else's hand
VIOLET = (170, 110, 255)
LOG_ROWS = 18
PICTURE = (84, 58)               # boss picture box


class JournalView:
    def __init__(self, font, item_art):
        self.font, self.art = font, item_art
        self.portraits = Portraits()
        self._pictures = {}
        self.mosaic = self._build_mosaic()

    # --- pictures -------------------------------------------------------------------------
    def _picture(self, entry, known):
        """The boss's own sprite, fitted into the box (a black silhouette until defeated)."""
        key = (entry.spec.name, known)
        if key not in self._pictures:
            image = entry.create().image
            if not known:
                mask = pygame.mask.from_surface(image)
                image = mask.to_surface(setcolor=(34, 30, 52), unsetcolor=(0, 0, 0, 0))
            w, h = image.get_size()
            k = min(PICTURE[0] / w, PICTURE[1] / h, 1.0)
            self._pictures[key] = pygame.transform.scale(image, (max(1, int(w * k)),
                                                                 max(1, int(h * k))))
        return self._pictures[key]

    @staticmethod
    def _build_mosaic():
        """Galaxy 1's echo picture: two rockets leaving side by side at dawn (48x32).
        One of them is an ARROW in MK I paint: the player's own first ship."""
        surf = pygame.Surface((48, 32), pygame.SRCALPHA)
        for y in range(32):
            k = y / 31
            surf.fill((int(40 + 150 * k), int(20 + 60 * k), int(60 - 20 * k)), (0, y, 48, 1))
        rng = random.Random(3)
        for _ in range(26):
            surf.set_at((rng.randrange(48), rng.randrange(18)), (230, 230, 255))
        pygame.draw.circle(surf, (255, 220, 150), (24, 33), 9)          # the dawn
        mine = build_ship_frames(ARROW.rows, SHIP_PALETTES["mk1"])[0]
        other = build_ship_frames(ARROW.rows, SHIP_PALETTES["mk2"])[0]
        for image, x in ((mine, 9), (other, 25)):
            small = pygame.transform.scale(image, (image.get_width() * 2 // 3,
                                                   image.get_height() * 2 // 3))
            surf.blit(small, (x, 6))
            surf.fill((255, 200, 90), (x + small.get_width() // 2 - 1, 6 + small.get_height(), 2, 3))
        return surf

    # --- frame ----------------------------------------------------------------------------
    def draw(self, surf, page, time, blink):
        surf.fill(PAPER)
        for y in range(0, LOW_H, 4):                                   # ruled lines
            surf.fill((20, 18, 36), (0, y, LOW_W, 1))
        f = self.font
        f.draw(surf, f"LOGBOOK OF SCOUT {page.callsign}", (8, 4), ACCENT, shadow=TEXT_SHADOW)
        x = 8
        for i, name in enumerate(TABS):
            w = f.size(name)[0] + 10
            rect = pygame.Rect(x, 15, w, 11)
            if i == page.tab:
                surf.fill(INK, rect)
                pygame.draw.rect(surf, ACCENT, rect, 1)
            f.draw(surf, name, (x + 5, 17), TEXT if i == page.tab else TEXT_DIM)
            x += w + 4
        surf.fill(TEXT_DIM, (8, 27, LOW_W - 16, 1))
        getattr(self, "_draw_" + TABS[page.tab].lower())(surf, page, time)
        if blink:
            f.draw(surf, "LEFT/RIGHT PAGE   UP/DOWN SELECT   ESC BACK", (LOW_W // 2, LOW_H - 9),
                   TEXT_DIM, center=True)

    def _note(self, surf, text, pos, time):
        """A margin note: red, a little crooked, as if written by hand."""
        x, y = pos
        for i, ch in enumerate(text):
            dy = (i * 7 + i // 3) % 3 - 1
            self.font.draw(surf, ch, (x + i * 6, y + dy), NOTE)

    # --- PILOT ----------------------------------------------------------------------------
    def _draw_pilot(self, surf, page, time):
        f = self.font
        image = self.art.image(page.hull, page.paint)
        surf.blit(image, image.get_rect(center=(44, 60)))
        f.draw(surf, page.hull, (84, 36), TEXT, shadow=TEXT_SHADOW)
        f.draw(surf, f"POWER {page.power}%", (84, 47), ACCENT, shadow=TEXT_SHADOW)
        for i, (label, value) in enumerate(page.stats):
            y = 96 + i * 10
            f.draw(surf, label, (10, y), TEXT_DIM)
            f.draw(surf, value, (146 - f.size(value)[0], y), TEXT)
        for i, (track, tier) in enumerate(page.tiers.items()):
            y = 160 + i * 9
            f.draw(surf, track, (10, y), TEXT_DIM)
            for t in range(UPGRADE_TIERS):
                color = ACCENT if t < tier else (40, 36, 60)
                surf.fill(color, (70 + t * 8, y + 1, 6, 5))
        # right column: achievements, gear, medals, the Dawn Key
        f.draw(surf, "ACHIEVEMENTS", (160, 32), ACCENT)
        for i, (name, text, earned, reward) in enumerate(page.achievements):
            y = 43 + i * 10
            if i == page.cursor:
                surf.fill(INK, (158, y - 2, 154, 10))
            f.draw(surf, ("+ " if earned else "- ") + name, (160, y), GOOD if earned else TEXT_DIM)
        name, text, earned, reward = page.achievements[page.cursor]
        y = 45 + len(page.achievements) * 10
        f.draw(surf, text[:25], (160, y), TEXT)
        f.draw(surf, f"SKIN: {reward}"[:25], (160, y + 9), COIN[2] if earned else TEXT_DIM)
        y += 24
        for i, (label, owned, total) in enumerate(page.gear):
            f.draw(surf, f"{label} {owned}/{total}", (160 + (i % 2) * 78, y + (i // 2) * 10),
                   TEXT)
        y += 34
        f.draw(surf, "MEDALS", (160, y), TEXT_DIM)
        for i, _ in enumerate(page.medals):
            draw_medal(surf, 210 + i * 18, y + 3, time)
        if not page.medals:
            f.draw(surf, "-", (210, y), TEXT_DIM)
        self._draw_key(surf, page.shards, (160, y + 18))

    def _draw_key(self, surf, shards, pos, stacked=False):
        """The DAWN KEY: five shards, lit where carried (stacked: label above the shards)."""
        f = self.font
        x, y = pos
        f.draw(surf, "DAWN KEY", (x, y), TEXT_DIM)
        if stacked:
            x, y = x - 58, y + 12
        for i in range(5):
            lit = (i + 1) in shards
            color = (255, 230, 150) if lit else (40, 36, 60)
            points = [(x + 58 + i * 12, y + 7), (x + 63 + i * 12, y - 1), (x + 68 + i * 12, y + 7)]
            pygame.draw.polygon(surf, color, points)
            if lit:
                surf.fill((255, 255, 255), (x + 63 + i * 12, y + 2, 1, 1))
        f.draw(surf, f"{len(shards)}/5", (x + 124, y), COIN[2] if shards else TEXT_DIM)

    # --- BOSSES ---------------------------------------------------------------------------
    def _draw_bosses(self, surf, page, time):
        f = self.font
        colors = {"defeated": TEXT, "unknown": TEXT_DIM, "herald": VIOLET, "vanta": VIOLET}
        for i, boss in enumerate(page.bosses):
            y = 32 + i * 11
            if i == page.cursor:
                surf.fill(INK, (6, y - 2, 106, 11))
                pygame.draw.rect(surf, ACCENT, (6, y - 2, 106, 11), 1)
            f.draw(surf, boss.name[:16], (9, y), colors[boss.status])
        boss = page.bosses[page.cursor]
        box = pygame.Rect(118, 32, PICTURE[0] + 6, PICTURE[1] + 6)
        surf.fill(INK, box)
        pygame.draw.rect(surf, colors[boss.status], box, 1)
        if boss.entry:
            picture = self._picture(boss.entry, boss.status == "defeated")
            surf.blit(picture, picture.get_rect(center=box.center))
            if boss.status == "unknown":
                f.draw(surf, "?", box.center, TEXT_DIM, scale=3, center=True)
        elif boss.status == "vanta" and boss.lines and boss.epithet:
            big = pygame.Surface((24, 24), pygame.SRCALPHA)
            self.portraits.draw(big, "VANTA", (0, 0), time)
            big = pygame.transform.scale(big, (48, 48))
            surf.blit(big, big.get_rect(center=box.center))
        else:
            f.draw(surf, "?", box.center, VIOLET, scale=4, center=True)
        x = box.right + 6
        f.draw(surf, boss.name[:13], (x, 34), colors[boss.status], shadow=TEXT_SHADOW)
        for i, part in enumerate(_wrap(boss.epithet, 13)[:3]):
            f.draw(surf, part, (x, 45 + i * 9), TEXT_DIM)
        f.draw(surf, boss.where, (x, 80), ACCENT)
        for i, line in enumerate(boss.lines):
            color = VIOLET if line == "VANTA:" else TEXT
            f.draw(surf, line, (118, 100 + i * 10), color)
        if boss.note:
            self._note(surf, boss.note, (118, 100 + (len(boss.lines) + 1) * 10), time)

    # --- ECHOES ---------------------------------------------------------------------------
    def _draw_echoes(self, surf, page, time):
        f = self.font
        found = {echo.tile for echo, got in page.echoes if got}
        frame = pygame.Rect(10, 34, 100, 68)
        surf.fill(INK, frame)
        for tile in range(6):
            tx, ty = tile % 3, tile // 3
            dest = (frame.x + 2 + tx * 32, frame.y + 2 + ty * 32)
            if tile in found:
                part = self.mosaic.subsurface((tx * 16, ty * 16, 16, 16))
                surf.blit(pygame.transform.scale(part, (32, 32)), dest)
            else:
                surf.fill((8, 6, 14), (*dest, 31, 31))
                f.draw(surf, "?", (dest[0] + 16, dest[1] + 13), (50, 46, 70), center=True)
        pygame.draw.rect(surf, GOOD if len(found) == 6 else TEXT_DIM, frame, 1)
        caption = MOSAIC if len(found) == 6 else f"MOSAIC {len(found)}/6"
        for i, part in enumerate(_wrap(caption, 16)):
            f.draw(surf, part, (10, 108 + i * 9), GOOD if len(found) == 6 else TEXT_DIM)
        f.draw(surf, "DECODER", (10, 134), TEXT_DIM)
        f.draw(surf, "ONLINE" if page.decoder else "FIND ALL 6", (10, 144),
               GOOD if page.decoder else DANGER)
        if page.decoder:
            f.draw(surf, "SEE THE LOG.", (10, 154), TEXT)
        self._draw_key(surf, page.shards, (10, 172), stacked=True)
        for i, (echo, got) in enumerate(page.echoes):
            y = 34 + i * 26
            if i == page.cursor:
                surf.fill(INK, (118, y - 2, 196, 23))
                pygame.draw.rect(surf, ACCENT, (118, y - 2, 196, 23), 1)
            f.draw(surf, f"ECHO {echo.tile + 1}", (121, y), ACCENT if got else TEXT_DIM)
            text = echo.text if got else "- SIGNAL LOST -"
            f.draw(surf, text, (121, y + 10), TEXT if got else (60, 56, 84))

    # --- LOG ------------------------------------------------------------------------------
    def _draw_log(self, surf, page, time):
        f = self.font
        rows = page.log[page.cursor:page.cursor + LOG_ROWS]
        for i, (kind, text, highlight) in enumerate(rows):
            y = 32 + i * 10
            if kind == "head":
                f.draw(surf, text, (8, y), ACCENT)
            elif kind == "decoded":
                f.draw(surf, text, (8, y), GOOD, shadow=TEXT_SHADOW)
            elif kind == "speaker":
                speaker = text.split(":")[0]
                f.draw(surf, text[:50], (14, y), VIOLET if speaker != "COMMANDER VEGA" else TEXT)
            elif highlight:                                       # the hidden letter
                f.draw(surf, text[0], (14, y), GOOD, shadow=TEXT_SHADOW)
                f.draw(surf, text[1:50], (20, y), TEXT)
            else:
                f.draw(surf, text[:50], (14, y), TEXT)
        if len(page.log) > LOG_ROWS:                               # scroll bar
            h = LOW_H - 48
            top = 32 + int(h * page.cursor / len(page.log))
            size = max(4, int(h * LOG_ROWS / len(page.log)))
            surf.fill((40, 36, 60), (LOW_W - 5, 32, 2, h))
            surf.fill(ACCENT, (LOW_W - 5, top, 2, size))


def _wrap(text, width):
    """Words into lines of at most width characters."""
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])
