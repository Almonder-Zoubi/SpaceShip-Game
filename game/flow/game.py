"""The Game: setup, main loop and update order. The rest of its behaviour lives in mixins."""
import math
import random

import pygame

from ..audio import bank
from ..audio.player import Audio
from ..background.background import Background
from ..config.display import FPS, LOW_H, LOW_W, MAX_DT, SAVE_FILE, SCALE, TITLE, WIN_H, WIN_W
from ..config.palette import SPACE, TEXT_DIM
from ..config.tuning import (DEATH_DELAY, THROTTLE_BOOST, THROTTLE_IDLE, THROTTLE_RETRO,
                             WORLD_SPEED_FAST, WORLD_SPEED_SLOW)
from ..core.input import Keys, Mouse
from ..core.particles import ParticleSystem, ScreenShake
from ..core.pixelart import opaque_surface, window_icon
from ..core.pixelfont import PixelFont
from ..core.storage import SaveData
from ..levels.data import LEVEL_KEYS, LEVELS
from ..minions.diver import Diver
from ..obstacles.art import AsteroidLibrary
from ..player.hulls import ARROW, hull_named
from ..player.ship import Ship
from ..progression.inventory import Inventory
from ..ui.gifts import GiftScreen
from ..ui.hangar import HangarScreen
from ..ui.item_art import ItemArt
from ..ui.radio import RadioView
from ..ui.hud import Hud
from ..ui.screens import ScreensMixin
from ..weapons.gun import MachineGun
from ..weapons.laser import Laser
from ..weapons.specials import Blast, Ultimate
from .boosts import BoostsMixin
from .combat import CombatMixin
from .dev import DevMixin
from .events import EventsMixin
from .hangar import HangarMixin
from .juice import JuiceMixin
from .level_flow import LevelFlowMixin
from .options import OptionsMixin
from .progression import ProgressionMixin
from .sound import SoundMixin
from .states import MENU_STATES, State
from .wingmen import WingmenMixin
from .world import WorldMixin


class Game(EventsMixin, LevelFlowMixin, WorldMixin, CombatMixin, ProgressionMixin, HangarMixin,
           JuiceMixin, BoostsMixin, WingmenMixin, OptionsMixin, SoundMixin, DevMixin,
           ScreensMixin):
    """Owns the window, the world objects and the state machine.

    Mixins (one file each in flow/ and ui/) add: key handling, level flow, world update,
    combat, progression (coins, rank, payout), hangar + gifts, game feel (juice, damage
    numbers, radio), boosts + combo, wingmen, options, sound, dev tools and drawing. They all work on the attributes
    created here.
    """

    SHIP_START = (LOW_W / 2, LOW_H - 40)

    def __init__(self, skip_to_boss=False, start_level=1, dev=False, save_path=SAVE_FILE):
        self.skip_to_boss = skip_to_boss       # testing aid: start every run at the level boss
        self.start_level = start_level - 1     # index into LEVELS (title level select)
        self.dev = dev                         # dev menu + hotkeys; never writes the save file
        self.load_profile(SaveData(None if dev else save_path))
        self.god = False                       # dev: the rocket takes no damage
        self.dev_cursor = 0
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(TITLE)
        self.canvas = opaque_surface((LOW_W, LOW_H))
        self.clock = pygame.time.Clock()
        self.font = PixelFont()
        self.hud = Hud(self.font)
        art = ItemArt()
        self.hangar_screen = HangarScreen(self.font, art)
        self.gift_screen = GiftScreen(self.font, art)
        self.shake = ScreenShake()
        self.scanlines = self._make_scanlines()
        self.show_scanlines = True
        self._loading_screen()

        rng = random.Random()
        self.library = AsteroidLibrary(rng)
        palettes = tuple(dict.fromkeys(p for lv in LEVELS for p in lv.difficulty.palettes))
        self.library.prebuild(radii=range(4, 15), palettes=palettes)
        for palette in palettes:                  # fragments: every small size in every colour
            self.library.prebuild(radii=range(4, 9), palettes=(palette,))
        self.background = Background(rng)
        for level in LEVELS:                      # build every nebula and boss now, not mid-game
            self.background.set_nebula(level.nebula)
            for wave in level.waves:
                for entry in wave.bosses:
                    entry.boss_class.prebuild()
        Diver.prebuild()
        self.ship = Ship(*self.SHIP_START)
        self.audio = Audio()
        if bank.missing():
            self._loading_screen("BUILDING SOUNDS (FIRST START ONLY)...")
        self.audio.load()
        self.load_options()
        self.radio_view = RadioView(self.font)
        self._sound_state = {}                    # weapon states last frame (see SoundMixin)
        self.level_index = self.start_level
        ship = self.save.ship if self.inventory.owns(self.save.ship) else ARROW.name
        self.choose_hull(hull_named(ship))           # builds that hull's sprites
        pygame.display.set_icon(window_icon(self.ship.frames[0]))
        self.weapons = [MachineGun(), Laser()]
        self.blast = Blast()                      # MK III specials, charged by hitting things
        self.ultimate = Ultimate()

        self.fire = ParticleSystem(additive=True)
        self.smoke = ParticleSystem()
        self.shockwaves = []
        self.flash = 0.0
        self.hurt_flash = 0.0

        self.held = Keys()
        self.mouse = Mouse()                   # mouse steering + left-click fire
        self._cursor_shown = True
        self.best = self.save.best
        self.record_rank = None                # rank of the last finished run in the records
        self.time = 0.0
        self.retry_point = (0, 0, 0, None)
        self.to_title()

    def load_profile(self, save):
        """Use this save file: bank, ranks and the inventory (dev mode owns everything)."""
        self.save = save
        self.inventory = Inventory(save, LEVEL_KEYS, everything=self.dev)
        if hasattr(self, "audio"):                # not during __init__ (no audio yet)
            self.load_options()

    def _loading_screen(self, text="BUILDING SPRITES..."):
        self.canvas.fill(SPACE)
        self.font.draw(self.canvas, text, (LOW_W // 2, LOW_H // 2), TEXT_DIM, center=True)
        self._present()

    @staticmethod
    def _make_scanlines():
        lines = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        for y in range(0, WIN_H, SCALE):
            lines.fill((0, 0, 0, 38), (0, y + SCALE - 1, WIN_W, 1))
        return lines

    @property
    def weapon(self):
        return self.weapons[self.weapon_index]

    @property
    def level(self):
        return LEVELS[self.level_index]

    @property
    def wave(self):
        return self.level.waves[self.wave_index]

    @property
    def boss_entry(self):
        """The BossEntry being fought (or announced) in the current wave."""
        return self.wave.bosses[self.boss_index]

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def set_phase(self, phase):
        self.phase = phase
        self.phase_time = 0.0

    def run(self):
        while self.handle_events():
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.update(dt, self.held, self.mouse)
            self.draw()
            self._present()
        pygame.quit()

    def update(self, dt, keys, mouse=None):
        """Advance one frame. keys: held keys; mouse: a Mouse (None = keyboard only)."""
        self.time += dt
        self.state_time += dt
        self._update_audio()                      # music + loops follow last frame's state
        if self.state == State.PAUSED:
            return

        real_dt, dt = dt, self.world_dt(dt)       # hit-stop / slow-mo slow the world down
        firing = False
        if self.state in MENU_STATES:
            self.ship.update(dt, Keys(), self.fire, self.smoke)
            self.ship.y = self.SHIP_START[1] + math.sin(self.time * 2) * 2   # gentle hover
        elif self.state == State.PLAYING:
            firing = keys[pygame.K_SPACE] or bool(mouse and mouse.firing)
            self.ship.update(dt, keys, self.fire, self.smoke, target=mouse and mouse.aim)
        elif self.state in (State.WIN, State.LEVEL_CLEAR):
            self.ship.update(dt, keys, self.fire, self.smoke, autopilot=True)

        world_speed = self._world_speed()
        edt = self.enemy_dt(dt)                   # SLOW-MO boost: the enemy side at half speed
        self.background.update(dt, world_speed)
        self._update_asteroids(edt, world_speed)
        self._update_boss(edt)
        self._update_enemies(edt)
        self._update_weapons(dt, firing)
        self._update_enemy_bullets(edt)
        self._update_pickups(dt)
        self._update_boosts(dt)
        if self.state == State.PLAYING:
            self._check_ship_collisions()
            self._update_phase(dt, world_speed)
        for popup in self.popups:
            popup.update(real_dt)
        self.popups = [p for p in self.popups if not p.done]
        self._update_damage_numbers(real_dt)
        self._update_radio(real_dt)
        if self.alert:
            self.alert[3] -= real_dt
            if self.alert[3] <= 0:
                self.alert = None

        self.fire.update(dt)
        self.smoke.update(dt)
        for wave in self.shockwaves:
            wave.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]
        self.shake.update(real_dt)
        self.flash = max(0.0, self.flash - real_dt)
        self._update_progress(real_dt)
        self.hurt_flash = max(0.0, self.hurt_flash - real_dt)

        if self.state == State.DYING and self.state_time > DEATH_DELAY:
            self.set_state(State.GAME_OVER)

    def _world_speed(self):
        """Boosting (UP) speeds the world up, retro (DOWN) slows it."""
        if not self.ship.alive:
            return 0.7
        t = self.ship.throttle
        if t < THROTTLE_IDLE:
            k = (t - THROTTLE_RETRO) / (THROTTLE_IDLE - THROTTLE_RETRO)
            return WORLD_SPEED_SLOW + (1 - WORLD_SPEED_SLOW) * k
        k = (t - THROTTLE_IDLE) / (THROTTLE_BOOST - THROTTLE_IDLE)
        return 1 + (WORLD_SPEED_FAST - 1) * k

    def _present(self):
        ox, oy = self.shake.offset()
        self.window.fill(SPACE)
        self.window.blit(pygame.transform.scale(self.canvas, (WIN_W, WIN_H)), (ox * SCALE, oy * SCALE))
        if self.show_scanlines:
            self.window.blit(self.scanlines, (0, 0))
        pygame.display.flip()
