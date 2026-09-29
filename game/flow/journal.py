"""The JOURNAL (logbook of scout ARROW-01): pilot strength + achievements, boss files and
their link to VANTA (future heralds stay black), the ECHO mosaic, and every radio line heard.
Opened with J from the title or the star map, so the story can be read in peace."""
from dataclasses import dataclass

from ..levels.data import LEVEL_KEYS, LEVELS, galaxy_of, level_title
from ..progression.achievements import ACHIEVEMENTS
from ..progression.items import ITEMS, SHIP, SKIN, WEAPON, WINGMAN, items_of
from ..progression.upgrades import TRACKS, power_ratio
from ..brains.insight import insights
from ..story.dialog import VEGA, as_line
from ..story.lore import (CALLSIGN, DECODED, DECODED_2, DOSSIER_BY_BOSS, ECHOES, ECHOES_2,
                          HERALDS, TRANSMISSIONS, VANTA_FILE, redact)
from .states import State

TABS = ("PILOT", "BOSSES", "ECHOES", "LOG", "KNOWN")


@dataclass
class BossFile:
    """One row of the BOSSES tab."""
    name: str                     # shown name (redacted while unknown)
    where: str                    # "G1 L4" or "GALAXY 2"
    status: str                   # "defeated", "unknown", "herald", "vanta"
    epithet: str = ""
    lines: tuple = ()             # facts + link to VANTA (or the herald's lines)
    note: str = ""                # the margin note (red), once defeated
    entry: object = None          # the BossEntry (for its picture)


@dataclass
class JournalPage:
    """Everything the journal screen shows this frame (built by JournalMixin)."""
    tab: int
    cursor: int
    callsign: str
    hull: str
    paint: str
    stats: tuple                  # (label, value) rows
    power: int                    # POWER %
    tiers: dict
    gear: tuple                   # (label, owned, total)
    achievements: tuple           # (name, text, earned)
    medals: tuple
    shards: tuple
    bosses: tuple                 # BossFile
    echoes: tuple                 # (Echo, found)
    decoder: bool
    log: tuple                    # (kind, text, highlight): kind "head" / "line" / "speaker"
    known: dict = None            # KNOWN: what the enemy's player model says about you
    decoder2: bool = False        # galaxy 2's echoes all found


class JournalMixin:
    """Game mixin: open / navigate / close the journal and build what it shows."""

    def open_journal(self):
        self.journal_back = self.state
        self.journal_tab = 0
        self.journal_cursor = {tab: 0 for tab in TABS}
        self.journal_forget = False           # KNOWN: BACKSPACE asked once already
        self.audio.play("page")
        self.set_state(State.JOURNAL)

    def close_journal(self):
        self.set_state(self.journal_back)

    def journal_switch(self, step):
        self.journal_tab = (self.journal_tab + step) % len(TABS)
        self.audio.play("page")

    def journal_move(self, step):
        tab = TABS[self.journal_tab]
        size = {"PILOT": len(ACHIEVEMENTS), "BOSSES": len(self._boss_files()),
                "ECHOES": len(self._echoes()), "LOG": len(self._journal_log()), "KNOWN": 1}[tab]
        self.journal_cursor[tab] = max(0, min(size - 1, self.journal_cursor[tab] + step))
        self.audio.play("select")

    def journal_forget_key(self):
        """BACKSPACE on KNOWN: ask once, then wipe what the enemy learned."""
        if TABS[self.journal_tab] != "KNOWN":
            return
        if self.journal_forget:
            self.reset_brain()
            self.journal_forget = False
            self.audio.play("hijack")
        else:
            self.journal_forget = True
            self.audio.play("denied")

    def _known(self):
        m = self.player_model
        top = max(m.heat) or 1.0
        weapons = sorted(m.weapons, key=lambda n: -m.weapons[n])[:3]
        return {"heat": [v / top for v in m.heat], "cols": m.cols, "rows": m.rows,
                "dodges": {d: m.dodge_share(d) for d in m.dodges},
                "dodge_count": int(m.dodge_count),
                "weapons": [(n, m.weapon_share(n)) for n in weapons],
                "reaction": m.reaction, "minutes": m.seconds / 60,
                "insights": insights(m)[:4], "forget": self.journal_forget,
                "bosses": sorted(n for n, b in self.bandits.items() if b.best())}

    # --- what the player knows ------------------------------------------------------------
    @property
    def ghost_record_shown(self):
        """After galaxy 1, the title's score board shows a record of all 50 levels by
        your own callsign (the previous scout's)."""
        return 1 in self.save.medals

    @property
    def decoder(self):
        """Every galaxy 1 echo found: the journal can read the hidden layer."""
        return all(e.cache in self.save.caches for e in ECHOES)

    @property
    def decoder2(self):
        """Every galaxy 2 echo found: the second hidden layer."""
        return all(e.cache in self.save.caches for e in ECHOES_2)

    def _echoes(self):
        """The echoes the journal lists: galaxy 1's, and galaxy 2's once it is open."""
        open2 = 1 in self.save.medals or any(e.cache in self.save.caches for e in ECHOES_2)
        return ECHOES + (ECHOES_2 if open2 else ())

    def boss_defeated(self, name):
        if name in self.save.bosses:
            return True
        return any(name in (e.spec.name for w in level.waves for e in w.bosses)
                   and key in self.save.cleared for level, key in zip(LEVELS, LEVEL_KEYS))

    def _boss_files(self):
        files, seen = [], set()
        for level in LEVELS:
            for wave in level.waves:
                for entry in wave.bosses:
                    name = entry.spec.name
                    if name in seen:
                        continue
                    seen.add(name)
                    where = f"G{galaxy_of(level).number} L{level.number}"
                    if self.boss_defeated(name):
                        d = DOSSIER_BY_BOSS.get(name)
                        lines = (d.facts + ("",) + ("VANTA:",) + d.vanta) if d else ()
                        files.append(BossFile(name, where, "defeated",
                                              getattr(entry.boss_class, "EPITHET", ""),
                                              lines, d.note if d else "", entry))
                    else:
                        files.append(BossFile("?" * len(name), where, "unknown",
                                              lines=("DEFEAT IT TO OPEN ITS FILE.",),
                                              entry=entry))
        medals = self.save.medals
        for herald in HERALDS:
            if herald.name == "VANTA":
                opened = [text for cond, text in VANTA_FILE if self._story_flag(cond)]
                shown = "VANTA" if opened else redact("VANTA", 0)
                files.append(BossFile(shown, f"GALAXY {herald.galaxy}", "vanta",
                                      herald.title if opened else "",
                                      tuple(opened) or ("NO FILE. NOT YET.",)))
                continue
            known = herald.galaxy - 1 in medals
            files.append(BossFile(herald.name if known else redact(herald.name),
                                  f"GALAXY {herald.galaxy}", "herald",
                                  herald.title if known else redact(herald.title, 0),
                                  herald.lines if known else ("A HERALD OF VANTA.",)
                                  if medals else ("???",)))
        return files

    def _story_flag(self, cond):
        return {"medal1": 1 in self.save.medals, "decoder": self.decoder,
                "medal2": 2 in self.save.medals, "decoder2": self.decoder2,
                "never": False}[cond]

    def _journal_log(self):
        """Every radio line of the levels reached, then the intercepted transmissions."""
        out = []
        decoded = {1: self.decoder, 2: self.decoder2}
        if self.decoder:
            out.append(("decoded", f"FIRST LETTERS: {DECODED}", False))
        if self.decoder2:
            out.append(("decoded", f"GALAXY 2 FIRST LETTERS: {DECODED_2}", False))
        reached = max(self.save.unlocked, self.start_level + 1)
        for level in LEVELS[:reached]:
            out.append(("head", f"{level_title(level)}  {level.name}", False))
            lit = decoded.get(galaxy_of(level).number, False)
            for i, entry in enumerate(level.radio):
                out.append(self._log_line(entry, i == 0 and lit))
            for wave in level.waves:
                for entry in wave.radio:
                    out.append(self._log_line(entry, False))
        for beat in self.save.story:
            out.append(("head", "INTERCEPTED TRANSMISSION", False))
            for line in map(as_line, TRANSMISSIONS.get(beat, ())):
                out.append(("speaker", f"{line.speaker}: {line.text}", False))
        return out

    @staticmethod
    def _log_line(entry, highlight):
        line = as_line(entry)
        if line.speaker == VEGA:
            return ("line", line.text, highlight)
        return ("speaker", f"{line.speaker}: {line.text}", False)

    def journal_page(self):
        level = LEVELS[min(len(LEVELS), max(self.save.unlocked, 1)) - 1]
        loadout = self.loadout_for(level)
        tiers = self.inventory.tiers
        gear = tuple((label, sum(self.inventory.owns(i.id) for i in items_of(kind)),
                      len(items_of(kind)))
                     for label, kind in (("SHIPS", SHIP), ("WEAPONS", WEAPON),
                                         ("WINGMEN", WINGMAN), ("SKINS", SKIN)))
        achievements = tuple((a.name, a.text, a.id in self.save.achievements,
                              ITEMS[a.reward].name) for a in ACHIEVEMENTS)
        stats = (("MODEL", loadout.name), ("HULL", str(loadout.max_hp)),
                 ("GUN", str(round(loadout.gun_damage, 1))),
                 ("LASER", f"{int(loadout.laser_dps)} DPS"),
                 ("SPEED", str(int(loadout.max_speed))),
                 ("CREDITS", str(self.save.coins)))
        return JournalPage(
            self.journal_tab, self.journal_cursor[TABS[self.journal_tab]], CALLSIGN,
            self.hull.name, self.paint_for(level.loadout), stats,
            round(power_ratio(tiers) * 100), {t.id: tiers.get(t.id, 0) for t in TRACKS}, gear,
            achievements, tuple(self.save.medals), tuple(self.save.shards),
            tuple(self._boss_files()),
            tuple((e, e.cache in self.save.caches) for e in self._echoes()), self.decoder,
            tuple(self._journal_log()), self._known(), self.decoder2)

