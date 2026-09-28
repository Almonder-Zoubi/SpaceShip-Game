"""Headless smoke test: drives the game through every state and mechanic.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test
        [--shots DIR]          save a screenshot of every interesting moment
        [--only hulls,audio]   run only some sections (names in SECTIONS)

Each section is a function that gets the shared Harness and starts from its own state,
so a failing area can be re-run alone while debugging.
"""
import json
import math
import os
import random
import tempfile

import pygame

from game.audio.music import SONGS
from game.audio.sfx import SOUNDS
from game.bosses.carrier import Carrier
from game.bosses.leviathan import Leviathan
from game.bosses.mothership import Mothership
from game.config.display import FPS, SCALE, WIN_H, WIN_W
from game.config.loadouts import MK1, MK2, MK3, MK4
from game.config.tuning import (ARC_JUMPS, PLASMA_PIERCE, COMBO_COIN_CAP, COMBO_MAX, COMBO_STEP, COMBO_WINDOW,
                                DEATH_DELAY, FEVER_AT, MEDIC_DELAY, MEDIC_REVIVE, PIP_SHARE,
                                POWER_MAX, REPAIR_SMALL, SHIELD_HITS, UPGRADE_COSTS,
                                UPGRADE_TIERS, GALAXY1_TIERS, WARNING_TIME, WINGMAN_KO_TIME,
                                WINGMAN_TRAIN_COST, WINGMAN_TRAIN_XP, WINGMAN_XP,
                                WINGMAN_XP_KILL, WINGMAN_XP_OWN)
from game.core.input import Keys
from game.core.storage import SaveData
from game.flow.game import Game
from game.flow.states import Phase, State
from game.levels.data import GALAXIES, LEVELS, galaxy_of
from game.minions.diver import Diver
from game.minions.drone import drone_formation
from game.bosses.helios import Flare, Helios
from game.bosses.kaleidos import Kaleidos, Shard
from game.bosses.wraith import Wraith
from game.minions.bullets import ColoredBullet
from game.minions.prism import prism_turret
from game.obstacles.asteroid import CrystalRock, WreckChunk
from game.bosses.scrapjaw import JunkShot, Scrapjaw
from game.bosses.twins import Twin as TwinShip, Twins
from game.config.tuning import SLINGSHOT_SCORE, WHITE_HOLE_WARN
from game.hazards.blackhole import BlackHole
from game.minions.interceptor import Interceptor, interceptor_pair
from game.obstacles.asteroid import Comet
from game.weapons.gun import Bullet as GunBullet
from game.minions.salvager import Salvager
from game.config.tuning import REFRACT_BEAMS
from game.hazards.fog import FogBanks
from game.minions.bullets import CurvedBullet
from game.minions.phantom import Phantom
from game.config.tuning import PHANTOM_FADE
from game.config.tuning import MINE_ARM
from game.minions.minelayer import Mine, MineLayer
from game.obstacles.asteroid import Asteroid, IceRock, MagmaRock
from game.pickups.boosts import Boost, Overdrive, Shield
from game.pickups.types import BigCoin, Coin, FullRepair, PowerCore, RepairKit
from game.player.hulls import ARROW, HULLS, TITAN, WASP
from game.progression import upgrades
from game.progression.economy import level_payout
from game.progression.inventory import LOCKED, SHOP
from game.progression.items import SKIN, STARTER, UPGRADE, WINGMAN
from game.config.palette import BEAMS, TRACERS, TRAILS
from game.player.art import SHIP_PALETTES
from game.wingmen.types import Guardian, Pip, Twin
from game.minions.bullets import EnemyBullet
from game.progression.results import RANKS, LevelStats, better_rank
from game.ui.popup import DamageNumber
from game.weapons.base import Hit
from game.bosses.overmind import Overmind
from game.config.display import LOW_H, LOW_W
from game.config.tuning import (BOSS_ROAR_TIME, ESCAPE_SPEED, LARVA_TIME, MAP_H, MAP_W,
                                SPORE_RIPEN, SPORE_SHOTS, SPORE_SWELL)
from game.hazards.hive import HiveTunnel
from game.minions.swarm import SporePod, larva_flock
from game.progression.items import PAINT
from game.starmap.model import BLACK_HOLE, CACHES, GATE, MAPS, NODES
from game.bosses.gunship import GUNSHIP_SPEC, Gunship
from game.bosses.learning import Learner
from game.brains.bandit import Bandit
from game.brains.director import Director
from game.brains.insight import insights
from game.brains.model import PlayerModel
from game.bosses.warden import Warden
from game.config.tuning import (BOOMERANG_TIME, BOSS_REPAIR_G2, ELITE_HP, RIFT_OPEN, RIFT_RADIUS,
                                RUNE_SHOTS, RUNE_TIME, SHIFT_BONUS, SHIFT_GLASS, SHIFT_ROCK_SPEED,
                                SPLIT_TIME)
from game.hazards.rifts import RiftPortals
from game.levels.data import level_title
from game.levels.shifts import BY_ID as BY_SHIFT, SHIFTS
from game.minions.bullets import bullet
from game.minions.veil_bullets import (Boomerang, RuneMark, SplitterBullet, TwinBullet,
                                      VeilBullet, twinned)
from game.minions.wisp import Wisp
from game.story.dialog import UNKNOWN, VANTA, VEGA, Line, cards, is_hijack
from game.bosses.eclipse import Eclipse
from game.bosses.leechmaw import LeechMaw
from game.bosses.mimic import Mimic
from game.bosses.reaper import Reaper
from game.bosses.tempo import Tempo
from game.config.tuning import (DECOY_TIME, MARROW_REGROW, PHASE_DASH, PHASE_TIME, POD_SAVED_COINS,
                                REAPER_BREAK, REPAIR_SHARE, REPAIR_TIME, TIME_SLIP_SCALE,
                                TIME_SLIP_TIME)
from game.bosses.grinder import Grinder
from game.bosses.nyx import Nyx, NyxCourt
from game.bosses.spinner import Spinner
from game.config.tuning import EGG_HATCH, FORK_AT, WARP_TIME
from game.hazards.court import CourtOfNyx
from game.hazards.darkness import Darkness
from game.hazards.maze import HollowMaze
from game.hazards.siege import Siege
from game.hazards.throne import HollowThrone
from game.minions.egg import EggCluster
from game.minions.leader import leader_squad
from game.story.dialog import UNMASKED
from game.story.lore import ACROSTIC_2, DECODED_2, ECHOES_2
from game.hazards.escort import BroodEscort
from game.hazards.mirror import MirrorSea
from game.hazards.pulse import PulseField
from game.hazards.pursuit import MawPursuit
from game.minions.latcher import latcher_trio
from game.minions.lurker import lurker_pair
from game.minions.mirror import echo_ghost
from game.minions.stalker import stalker_pair
from game.obstacles.asteroid import MarrowCore, rock_class
from game.story.lore import (ACROSTIC, DECODED, DOSSIER_BY_BOSS, DOSSIERS, ECHOES, HERALDS,
                             TEXT_WIDTH, TRANSMISSIONS, VANTA_FILE)

FIRE = Keys(pygame.K_SPACE)
JUICE_PAD = 0.8          # hit-stop + slow-mo after a big event stretch the world's time


class Harness:
    """The game under test plus helpers to drive it frame by frame."""

    def __init__(self, shots_dir):
        self.shots_dir = shots_dir
        self.save_path = os.path.join(tempfile.mkdtemp(), "save.json")   # never the player's
        self.game = Game(save_path=self.save_path)
        self.game.inventory.grant_all()     # sections below test levels 1-4 with every item
        self.game.library.finish()          # the rocks the menus would build in the background
        self.dt = 1 / FPS
        self.field = LEVELS[0].difficulty

    def shot(self, name):
        if self.shots_dir:
            os.makedirs(self.shots_dir, exist_ok=True)
            pygame.image.save(pygame.transform.scale(self.game.canvas, (WIN_W, WIN_H)),
                              os.path.join(self.shots_dir, f"{name}.png"))

    def run(self, frames, keys=Keys(), clear_rocks=False, mouse=None):
        for _ in range(frames):
            if clear_rocks:
                self.game.asteroids.clear()
            self.game.update(self.dt, keys, mouse)
            self.game.draw()

    def seconds(self, s):
        return int(s / self.dt)

    def post(self, key, kind=pygame.KEYDOWN):
        pygame.event.post(pygame.event.Event(kind, key=key, mod=0, unicode="", scancode=0))
        self.game.handle_events()

    def mouse(self, kind, canvas_pos, rel=(0, 0)):
        """Post a real mouse event at a canvas position (window = canvas x SCALE)."""
        pos = (int(canvas_pos[0] * SCALE), int(canvas_pos[1] * SCALE))
        if kind == pygame.MOUSEMOTION:
            event = pygame.event.Event(kind, pos=pos, rel=rel, buttons=(0, 0, 0))
        else:
            event = pygame.event.Event(kind, pos=pos, button=1)
        pygame.event.post(event)
        self.game.handle_events()

    def rock_ahead(self, radius, dist=50):
        game = self.game
        art = game.library.pick(radius, radius, self.field.palettes)
        fx, fy = game.ship.forward
        return Asteroid(art, game.ship.x + fx * dist, game.ship.y + fy * dist, 0, 0, 0)

    @staticmethod
    def kill(boss):
        """A single hit can't skip a phase: hit through every phase, skipping the roars."""
        while boss.state == "fight":
            boss.roar = 0
            boss.damage(boss.max_hp)

    def saved_records(self):
        """Records in the save file on disk (None if there is no file yet)."""
        if not os.path.exists(self.save_path):
            return None
        with open(self.save_path) as f:
            return json.load(f)["records"]

    def next_level(self):
        """Results screen -> ENTER -> (gift) -> hangar -> SPACE launches the next level."""
        self.post(pygame.K_RETURN)
        if self.game.state == State.REWARD:
            self.game.state_time = 1.0
            self.post(pygame.K_RETURN)
        assert self.game.state == State.HANGAR, self.game.state
        self.post(pygame.K_SPACE)

    def die(self):
        game = self.game
        game.ship.hp = 1
        game.ship.invulnerable_time = 0
        game.hurt_ship(5, 0, 0)
        self.run(self.seconds(DEATH_DELAY + 0.2))


# --- sections ------------------------------------------------------------------------------------
def test_title(h):
    game = h.game
    # Regression: an alpha channel on the canvas turns sprites into black boxes on macOS.
    assert game.canvas.get_masks()[3] == 0, "canvas must not have an alpha channel"
    game.to_title()
    h.run(90)
    h.shot("title")


def test_controls(h):
    """Real input path: key events -> held keys -> ship moves diagonally, never rotates."""
    game = h.game
    game.start()
    pygame.event.clear()
    x0, y0 = game.ship.x, game.ship.y
    h.post(pygame.K_UP)
    h.post(pygame.K_RIGHT)
    h.run(30, game.held, clear_rocks=True)
    assert game.ship.x > x0 + 5 and game.ship.y < y0 - 5, "diagonal movement"
    assert game.ship.throttle > 0.9, "UP boosts the engine"
    assert game.ship.tilt_index == 3 and game.ship.forward[0] > 0.4, "UP+RIGHT leans like '/'"
    h.shot("diagonal")
    h.post(pygame.K_UP, pygame.KEYUP)
    h.post(pygame.K_RIGHT, pygame.KEYUP)
    h.run(40, game.held, clear_rocks=True)
    assert math.hypot(game.ship.vx, game.ship.vy) < 5, "ship stops quickly after release"
    assert game.ship.tilt_index == 0, "straightens after release"
    h.post(pygame.K_DOWN)
    h.run(30, game.held, clear_rocks=True)
    assert game.ship.throttle < 0.2, "DOWN shrinks the flames"
    h.post(pygame.K_DOWN, pygame.KEYUP)
    h.post(pygame.K_r)
    assert game.weapon.name == "LASER", "R switches weapons"


def test_mouse(h):
    """Mouse: the rocket flies to the pointer and eases in, leans on the way, left click
    fires, an arrow key hands control back; a click in a menu is ENTER."""
    game = h.game
    game.to_title()
    pygame.event.clear()
    game.mouse.release()
    h.mouse(pygame.MOUSEMOTION, (100, 100), rel=(2, 1))
    assert not game.mouse.active, "a resting / barely moved pointer doesn't take over"
    h.mouse(pygame.MOUSEBUTTONDOWN, (100, 100))
    h.mouse(pygame.MOUSEBUTTONUP, (100, 100))
    assert game.state == State.STAR_MAP, "click = ENTER on the title"
    h.mouse(pygame.MOUSEBUTTONDOWN, (100, 100))
    h.mouse(pygame.MOUSEBUTTONUP, (100, 100))
    assert game.state == State.HANGAR, "click = land on the planet the rocket is parked at"
    h.mouse(pygame.MOUSEBUTTONDOWN, (100, 100))
    h.mouse(pygame.MOUSEBUTTONUP, (100, 100))
    assert game.state == State.PLAYING and game.mouse.active and not game.mouse.firing
    ship, target = game.ship, (60, 80)
    h.mouse(pygame.MOUSEMOTION, target, rel=(-60, -60))
    h.run(15, game.held, clear_rocks=True, mouse=game.mouse)
    assert ship.tilt_index < 0 and ship.throttle > 0.8, "flying up-left leans '\\' and boosts"
    h.shot("mouse_flight")
    h.run(90, game.held, clear_rocks=True, mouse=game.mouse)
    dist = math.hypot(ship.x - target[0], ship.y - target[1])
    assert dist < 2 and math.hypot(ship.vx, ship.vy) < 5, f"arrives and stops ({dist:.1f} px)"
    assert ship.tilt_index == 0, "straightens once it's there"
    h.mouse(pygame.MOUSEBUTTONDOWN, target)
    assert game.state == State.PLAYING, "a click while playing only fires"
    h.run(10, game.held, clear_rocks=True, mouse=game.mouse)
    gun = game.weapons[0]
    assert gun.bullets, "left button fires"
    h.shot("mouse_fire")
    h.mouse(pygame.MOUSEBUTTONUP, target)
    shots = gun.shots
    h.run(10, game.held, clear_rocks=True, mouse=game.mouse)
    assert gun.shots == shots, "releasing the button stops firing"
    x0 = ship.x
    h.post(pygame.K_RIGHT)
    assert not game.mouse.active, "an arrow key hands control back to the keyboard"
    h.run(20, game.held, clear_rocks=True, mouse=game.mouse)
    assert ship.x > x0 + 10, "the keyboard steers again"
    h.post(pygame.K_RIGHT, pygame.KEYUP)


def test_weapons(h):
    game = h.game
    # Laser: sustained fire destroys a big rock, which splits.
    game.start()
    game.switch_weapon()
    big = h.rock_ahead(12)
    game.asteroids = [big]
    for i in range(240):
        game.update(h.dt, FIRE)
        game.draw()
        if i == 20:
            h.shot("laser")
        if big not in game.asteroids:
            break
    assert big not in game.asteroids, f"laser failed, hp {big.hp:.0f}/{big.max_hp:.0f}"
    assert len(game.asteroids) >= 2, "big rock should split into fragments"
    assert game.score > 0

    # Shots slow a falling rock down (but never stop it).
    game.start()
    slow = h.rock_ahead(12, dist=90)
    slow.vy = 90.0
    game.asteroids = [slow]
    for _ in range(30):
        game.update(h.dt, FIRE)
    assert slow.vy < 85 and slow.vy >= 12, f"push: vy {slow.vy:.1f}"

    # Machine gun kills a small rock (placed on one barrel's line: the wing barrels straddle
    # the nose, so a small rock dead ahead only gets grazed by both streams).
    game.start()
    small = h.rock_ahead(5)
    small.x += game.ship.hull.barrels[0][0]
    game.asteroids = [small]
    for i in range(120):
        game.asteroids = [r for r in game.asteroids if r is small]   # no stray rocks in the way
        game.update(h.dt, FIRE)
        game.draw()
        if i == 10:
            h.shot("gun")
        if small not in game.asteroids:
            break
    assert small not in game.asteroids, "machine gun failed"

    # Laser overheats.
    game.start()
    game.switch_weapon()
    h.run(h.seconds(3), FIRE, clear_rocks=True)
    assert game.weapon.overheated


def test_damage(h):
    game = h.game
    # Asteroid collision costs health, then invulnerability protects.
    game.start()
    game.asteroids = [Asteroid(game.library.pick(10, 10, h.field.palettes),
                               game.ship.x, game.ship.y, 0, 0, 0)]
    h.run(1)
    assert 0 < game.ship.hp < 100 and game.ship.invulnerable
    h.shot("hurt")

    # Losing all health -> explosion -> game over.
    game.ship.invulnerable_time = 0
    game.ship.hp = 1
    game.asteroids = [Asteroid(game.library.variants[-1], game.ship.x, game.ship.y, 0, 0, 0)]
    for i in range(int((DEATH_DELAY + 0.3) * FPS)):
        game.update(h.dt, Keys())
        game.draw()
        if i == 8:
            h.shot("explosion")
    assert game.state == State.GAME_OVER, game.state
    h.shot("game_over")


def test_balance(h):
    """The rocket is strength-times weaker in a damage race — with every hull."""
    for level in LEVELS:
        for entry in (e for wave in level.waves for e in wave.bosses):
            spec = entry.spec
            assert spec.player == level.loadout, f"{spec.name} balanced for the wrong ship"
            for hull in HULLS:
                ship = hull.apply(spec.player)
                ratio = (spec.hp / ship.gun_dps) / (ship.max_hp / spec.dps)
                # max_hp is rounded to whole points, hence the tolerance.
                assert abs(ratio - spec.strength) < 0.01 * spec.strength, (hull.name, ratio)


def test_pickups(h):
    """Repair kits heal (capped at max hp); a full kit restores everything."""
    game = h.game
    game.start()
    game.ship.hp = 40
    game.pickups = [RepairKit(game.ship.x, game.ship.y - 60)]
    h.run(120, clear_rocks=True)
    assert game.ship.hp == 40 + REPAIR_SMALL and not game.pickups, "small kit (magnet + heal)"
    game.pickups = [FullRepair(game.ship.x, game.ship.y)]
    h.run(2, clear_rocks=True)
    assert game.ship.hp == game.ship.max_hp
    game.pickups = [RepairKit(game.ship.x, game.ship.y - 50)]
    h.run(20, clear_rocks=True)
    h.shot("pickup")


def test_campaign(h):
    """Levels 1-3 in a row: field -> warning -> bosses -> level clear ... -> on to level 4."""
    game = h.game
    run, seconds = h.run, h.seconds
    game.choose_hull(ARROW)
    game.start()
    game.ship.hp = 30
    game.distance = game.wave.length
    run(2)
    assert game.phase == Phase.WARNING and game.ship.hp == game.ship.max_hp
    run(seconds(1.0))
    h.shot("warning")
    run(seconds(WARNING_TIME))
    assert game.phase == Phase.BOSS and game.boss is not None
    run(seconds(3.0), clear_rocks=True)
    assert game.boss.fighting
    h.shot("boss_enter")
    game.ship.hp = 10 ** 9          # watch the boss attack without dying
    run(seconds(4.0), clear_rocks=True)
    assert game.ship.hp < 10 ** 9, "boss bullets should hit a rocket that sits still"
    h.shot("boss_attack")
    hp0 = game.boss.hp
    for _ in range(60):
        game.ship.x = game.boss.x
        game.update(h.dt, FIRE)
    assert game.boss.hp < hp0, "player bullets damage the boss"
    game.boss.hp = game.boss.max_hp * 0.4             # enraged phase
    run(seconds(5.0), clear_rocks=True)
    h.shot("boss_enraged")
    game.boss.damage(game.boss.max_hp)
    assert game.boss.state == "dying"
    for i in range(seconds(game.boss.DEATH_TIME + JUICE_PAD + 0.3)):
        game.update(h.dt, Keys())
        game.draw()
        if i == 40:
            h.shot("boss_dying")
    assert game.phase == Phase.CLEARED
    run(seconds(1.6))
    assert game.state == State.LEVEL_CLEAR, game.state
    run(seconds(1.2))
    h.shot("level_clear")

    # Level 2: upgraded ship, crimson field with drone formations.
    h.next_level()
    assert game.state == State.PLAYING and game.level.number == 2
    assert game.score > 0, "score carries over"
    assert game.ship.loadout == MK2 and game.ship.hp == MK2.max_hp == game.ship.max_hp
    assert game.weapons[0].loadout == MK2 and game.weapons[1].power == 0
    run(seconds(1.0), clear_rocks=True)
    h.shot("level2_intro")
    game.formation_timer = 0
    run(2, clear_rocks=True)
    assert len(game.enemies) == 5, "level 2 spawns drone formations"
    game.enemies = drone_formation("line")      # one drone flies straight down the middle
    game.formation_timer = 99
    game.ship.hp = 10 ** 9
    run(seconds(2.5), FIRE, clear_rocks=True)
    h.shot("level2_drones")
    assert game.score > game.level_start_score, "drones get shot down"
    drone = drone_formation("v")[0]
    drone.x, drone.y = game.ship.x, game.ship.y
    game.enemies = [drone]
    game.ship.hp, game.ship.invulnerable_time = 100, 0
    run(1)
    assert game.ship.hp < 100 and drone not in game.enemies, "ramming a drone hurts"

    # Level 2 boss rush: weakened Gunship first, then the Carrier.
    game.distance = game.wave.length
    run(seconds(WARNING_TIME + 0.2), clear_rocks=True)
    assert game.boss.spec.name == "GUNSHIP" and game.boss.spec.strength == 1.5
    run(seconds(3.0), clear_rocks=True)
    game.boss.damage(game.boss.max_hp)
    game.ship.hp = 10
    run(seconds(game.boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.phase == Phase.WARNING and game.boss_index == 1
    run(seconds(WARNING_TIME + 3.0), clear_rocks=True)
    carrier = game.boss
    assert isinstance(carrier, Carrier) and carrier.fighting, (carrier, carrier.state)
    assert game.ship.hp > 10 and game.ship.max_hp == MK2.max_hp, "hull repaired before the carrier"
    game.ship.hp = 10 ** 9
    run(seconds(1.2), clear_rocks=True)
    assert game.enemies, "carrier launches drones"
    run(seconds(2.8), clear_rocks=True)
    h.shot("carrier_phase1")

    # Phase change at 2/3 hp: clamped, roars (invulnerable), clears bullets, drops rewards.
    carrier.hp = carrier.max_hp * 0.7
    for _ in range(3):
        game._damage_boss(Hit(carrier, carrier.max_hp * 0.2, carrier.x, carrier.y, 0, -1, 0))
    assert carrier.phase == 1 and abs(carrier.hp - carrier.max_hp * 2 / 3) < 1e-6, carrier.hp
    assert carrier.roar > 0 and not game.enemy_bullets
    assert any(isinstance(p, PowerCore) for p in game.pickups)
    assert any(isinstance(p, RepairKit) for p in game.pickups)
    run(seconds(0.5), clear_rocks=True)
    h.shot("carrier_roar")
    run(seconds(4.0), clear_rocks=True)
    assert all(w.power == 1 for w in game.weapons), "POWER core homes in and powers both weapons"
    h.shot("carrier_phase2")
    game._damage_boss(Hit(carrier, carrier.max_hp * 0.34, carrier.x, carrier.y, 0, -1, 0))
    assert carrier.phase == 2 and any(isinstance(p, FullRepair) for p in game.pickups)
    run(seconds(6.0), clear_rocks=True)
    assert all(w.power == POWER_MAX for w in game.weapons)
    h.shot("carrier_phase3")
    hp0 = carrier.hp
    for _ in range(90):
        game.ship.x = carrier.x
        game.update(h.dt, FIRE)
    assert carrier.hp < hp0, "powered gun damages the carrier"
    h.shot("carrier_powered_gun")
    carrier.damage(carrier.max_hp)
    run(seconds(carrier.DEATH_TIME + JUICE_PAD + 0.3))
    assert not game.enemies, "drones die with the carrier"
    run(seconds(1.6))
    assert game.state == State.LEVEL_CLEAR, game.state
    run(seconds(1.2))
    h.shot("level2_clear")

    # Level 3: MK III with BLAST and ULTIMATE, three waves.
    h.next_level()
    assert game.level.number == 3 and game.ship.loadout == MK3 and game.wave_index == 0
    assert game.blast.charge == 0 and game.ultimate.charge == 0
    game.ship.hp = 10 ** 9
    run(seconds(1.0), clear_rocks=True)
    h.shot("level3_intro")

    # Damaging rocks charges both meters; hits from the specials themselves don't.
    rock = h.rock_ahead(12)
    game.asteroids = [rock]
    game._damage_rock(Hit(rock, 700, rock.x, rock.y, 0, -1, 0))
    assert game.blast.charge > 0.5 and 0 < game.ultimate.charge < 0.5, (game.blast.charge,
                                                                         game.ultimate.charge)
    before = game.blast.charge, game.ultimate.charge
    rock = h.rock_ahead(12)
    game.asteroids = [rock]
    game._damage_rock(Hit(rock, 50, rock.x, rock.y, 0, -1, 0, charges=False))
    assert (game.blast.charge, game.ultimate.charge) == before

    # BLAST: charged + fire = huge beam that destroys everything in front, then recharges.
    game.blast.charge = 1.0
    front = [h.rock_ahead(14, dist=70), h.rock_ahead(11, dist=130)]
    game.asteroids = list(front)
    game.enemies = []
    for i in range(seconds(0.8)):
        game.update(h.dt, FIRE)
        game.draw()
        if i == 20:
            h.shot("blast")
    assert game.blast.active and not any(r in game.asteroids for r in front), "blast destroys"
    assert not game.weapons[0].bullets, "the normal gun pauses while the blast fires"
    run(seconds(2.5), FIRE, clear_rocks=True)
    assert not game.blast.active and game.blast.charge < 0.05, game.blast.charge

    # ULTIMATE: T launches homing missiles at every target on screen.
    h.post(pygame.K_t)
    assert not game.ultimate.active, "not charged yet"
    game.ultimate.charge = 1.0
    art = game.library.pick(6, 6, h.field.palettes)
    spread = [Asteroid(art, x, 70, 0, 0, 0) for x in (40, 120, 200, 280)]
    game.asteroids = list(spread)
    game.enemies = drone_formation("line")
    for e in game.enemies:
        e.y = 40
    h.post(pygame.K_t)
    assert game.ultimate.active
    for i in range(seconds(3.0)):
        game.update(h.dt, Keys())
        game.draw()
        if i == 40:
            h.shot("ultimate")
    left = [r for r in spread if r in game.asteroids]
    assert len(left) <= 1, f"missiles missed {len(left)} rocks"
    run(seconds(3.0), clear_rocks=True)                 # stragglers fly off or hit
    assert not game.ultimate.active and not game.ultimate.missiles

    # Wave 1 has no boss: straight on to wave 2.
    game.distance = game.wave.length
    run(2, clear_rocks=True)
    assert game.wave_index == 1 and game.phase == Phase.FIELD and game.alert[0] == "WAVE 2"
    h.shot("wave2")
    # Wave 2 ends with the Carrier (weakened); each third of its health charges the ULTIMATE.
    game.distance = game.wave.length
    run(seconds(WARNING_TIME + 3.0), clear_rocks=True)
    assert isinstance(game.boss, Carrier) and game.boss.spec.strength == 1.5
    game.ultimate.reset()
    game._damage_boss(Hit(game.boss, game.boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert abs(game.ultimate.charge - 0.25) < 1e-6, game.ultimate.charge
    h.kill(game.boss)
    run(seconds(Carrier.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.wave_index == 2 and game.phase == Phase.FIELD, (game.wave_index, game.phase)

    # Wave 3: the final boss.
    game.distance = game.wave.length
    game.ship.hp = 5
    run(seconds(1.0), clear_rocks=True)
    assert game.phase == Phase.WARNING and game.ship.hp == MK3.max_hp
    assert not game.is_final_boss(), "the Leviathan (level 4) is the final boss now"
    assert game._music_track() is None, "silence during the warning"
    h.shot("final_warning")
    run(seconds(WARNING_TIME + 2.0), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Mothership) and boss.fighting
    assert game._music_track() == "final_boss"
    game.ship.hp = 10 ** 9
    run(seconds(4.5), clear_rocks=True)
    assert game.enemies, "mothership launches drones"
    h.shot("mothership_phase1")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 1 and any(isinstance(p, PowerCore) for p in game.pickups)
    fired = False
    game.ship.hp = 1000
    for i in range(seconds(4.0)):                 # phase 2 opens with the sweeping beam
        game.ship.x = boss.x
        game.update(h.dt, Keys())
        game.draw()
        if boss.beam == 2 and not fired:
            fired = True
            run(10, clear_rocks=True)
            h.shot("mothership_beam")
    assert fired and game.ship.hp < 1000, "the beam hurts a rocket under it"
    assert game.state == State.PLAYING, "invulnerability after a hit stops the beam shredding"
    game.ship.hp = 10 ** 9
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 2
    run(seconds(6.0), clear_rocks=True)
    h.shot("mothership_phase3")
    h.kill(boss)
    run(seconds(boss.DEATH_TIME + JUICE_PAD + 1.9))
    assert game.state == State.LEVEL_CLEAR and game.save.unlocked == 4, game.state
    run(seconds(1.2))
    h.shot("level3_clear")
    score = game.score
    h.next_level()
    assert game.level.number == 4 and game.ship.loadout == MK4 and game.score == score


def test_level4(h):
    """Level 4: MK IV; ice rocks shatter into shards; divers lock on and dive; the Mothership
    again; then the Leviathan: every plate is a target, the head a weak spot, it lunges
    through the locked spot, blows apart plate by plate -> WIN."""
    game = h.game
    run, seconds = h.run, h.seconds
    game.choose_hull(ARROW)
    game.start(3, 5000)
    assert game.ship.loadout == MK4 and game.ship.max_hp == MK4.max_hp
    game.ship.hp = 10 ** 9
    spawned = [r for _ in range(200) for r in game.spawner.update(0.1, 1.0)]
    assert any(isinstance(r, IceRock) for r in spawned), "the field spawns ice rocks"
    ice = IceRock(game.library.pick(10, 10, ("ice",)), 160, 80, 0, 0, 0)
    rock = Asteroid(game.library.pick(10, 10, ("slate",)), 160, 80, 0, 0, 0)
    assert ice.max_hp < rock.max_hp and ice.splits, "ice is brittle"
    game.asteroids = [ice]
    game._damage_rock(Hit(ice, 10 ** 6, ice.x, ice.y, 0, -1, 0))
    assert len(game.asteroids) >= 3 and all(isinstance(r, IceRock) for r in game.asteroids)
    run(8)
    h.shot("level4_ice_shatter")

    # Divers: drop in, lock on (aim follows the rocket), then dive through that spot.
    game.asteroids.clear()
    game.diver_timer = 0
    run(2, clear_rocks=True)
    assert any(isinstance(e, Diver) for e in game.enemies), "diver squads in the field"
    game.diver_timer = game.formation_timer = 99
    diver = Diver(game.ship.x + 40, hover_y=60)
    game.enemies = [diver]
    run(seconds(1.2), clear_rocks=True)
    assert diver.state == "lock" and diver.aim == (game.ship.x, game.ship.y)
    h.shot("level4_diver_lock")
    game.ship.hp, game.ship.invulnerable_time = 1000, 0
    run(seconds(2.0), clear_rocks=True)
    assert diver not in game.enemies and game.ship.hp < 1000, "a rocket that sits still gets hit"

    # Wave 2: the Mothership, weakened; wave 3: the Leviathan.
    game.ship.hp = 10 ** 9
    game.distance = game.wave.length
    run(2, clear_rocks=True)
    game.distance = game.wave.length
    run(seconds(WARNING_TIME + 3.0), clear_rocks=True)
    assert isinstance(game.boss, Mothership) and game.boss.spec.strength == 1.5
    h.kill(game.boss)
    run(seconds(Mothership.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.wave_index == 2
    game.distance = game.wave.length
    run(seconds(WARNING_TIME + Leviathan.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Leviathan) and boss.fighting
    assert game.is_final_boss() == (len(LEVELS) == 4)
    assert game._music_track() == "leviathan"
    assert len(boss.parts()) == 12 and all(0 < p.x < 320 for p in boss.parts()[:4])
    h.shot("leviathan")
    hp0 = boss.hp
    game._damage_boss(Hit(boss.head, 100, 0, 0, 0, -1, 0))
    game._damage_boss(Hit(boss.plates[3], 100, 0, 0, 0, -1, 0))
    assert abs(hp0 - boss.hp - 100 * (1 + boss.HEAD_WEAK)) < 1e-6, "the head takes extra damage"
    hp0 = boss.hp
    for _ in range(90):
        game.ship.x = boss.head.x
        game.update(h.dt, FIRE)
        game.draw()
    assert boss.hp < hp0, "the gun hits the serpent"
    # The dive: lock on, then lunge through the locked spot, hurting more than a ram.
    closest, locked = 10 ** 9, None
    for i in range(seconds(12)):
        game.update(h.dt, Keys())
        game.draw()
        if boss.dive == 1 and locked is None and boss.attack_time > 0.5:
            h.shot("leviathan_lock")
            locked = True
        if boss.dive == 2:
            assert boss.contact_damage > 20
            tx, ty = boss.dive_target
            closest = min(closest, math.hypot(boss.x - tx, boss.y - ty))
        if locked and boss.dive == 3:
            break
    assert locked and closest < 8, f"the lunge goes through the locked spot ({closest:.0f} px)"
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 2
    run(seconds(6.0), clear_rocks=True)
    h.shot("leviathan_phase3")
    h.kill(boss)
    run(seconds(1.2))
    h.shot("leviathan_dying")
    run(seconds(boss.DEATH_TIME + JUICE_PAD))
    assert boss.popped == len(boss.plates), "every plate blows off"
    run(seconds(1.9))
    if len(LEVELS) > 4:                                 # levels 5+ exist: on to level 5
        assert game.state == State.LEVEL_CLEAR, game.state
        return
    assert game.state == State.WIN, game.state
    run(seconds(1.0))
    h.shot("win")
    assert game.record_rank


def test_level5(h):
    """Level 5 SOLAR FORGE: magma rocks chain-explode, mine layers drop mines that arm and
    blow up rocks when shot (never the ship), HELIOS: pods on the ring pass damage to the
    core, detach in phase 2 with their own armour, flares hit outside the gaps only,
    phase 3 opens the core and rains magma."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(4)
    game.radio = None
    game.ship.hp = 10 ** 6
    assert game.level.name == "SOLAR FORGE" and game.ship.loadout.name == "MK V"
    assert game._music_track() == "level5" and game.background.event
    h.run(h.seconds(1.5))
    h.shot("level5")

    # Magma chain: a blast destroys the rock next to it.
    lib, hp = game.library, game.level.difficulty.rock_hp
    a = MagmaRock(lib.pick(6, 6, ("magma",)), 100, 80, 0, 0, 0, hp_scale=hp)
    b = MagmaRock(lib.pick(6, 6, ("magma",)), 120, 80, 0, 0, 0, hp_scale=hp)
    c = Asteroid(lib.pick(5, 5, ("brown",)), 138, 84, 0, 0, 0)
    game.asteroids = [a, b, c]
    game._damage_rock(Hit(a, a.max_hp, a.x, a.y, 0, -1, 0))
    assert not game.asteroids, "the blast chained through the row"

    # Mine layer -> a mine; armed after a second; shot: it clears rocks, the ship is safe.
    layer = MineLayer(-1)
    layer.x, layer.drop_timer = 100, 0
    game.enemies = [layer]
    game.asteroids.clear()
    h.run(3)
    mines = [e for e in game.enemies if isinstance(e, Mine)]
    assert mines and not mines[0].armed
    h.run(h.seconds(MINE_ARM + 0.1))
    assert mines[0].armed and mines[0].contact_damage > 0
    mine = mines[0]
    rock = Asteroid(lib.pick(5, 5, ("brown",)), mine.x + 12, mine.y, 0, 0, 0)
    game.asteroids = [rock]
    game.ship.x, game.ship.y = mine.x, mine.y + 20
    hp_ship = game.ship.hp
    game._damage_enemy(Hit(mine, 5, mine.x, mine.y, 0, -1, 0))
    assert rock not in game.asteroids and game.ship.hp == hp_ship, "mine blast"
    game.enemies.clear()
    game.ship.x, game.ship.y = game.SHIP_START

    # HELIOS.
    game.start(4, 0, 2, 0)
    game.radio = None
    game.ship.hp = 10 ** 6
    h.run(h.seconds(WARNING_TIME + Helios.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Helios) and boss.fighting and game._music_track() == "helios"
    assert len(boss.parts()) == 5
    hp0 = boss.hp
    game._damage_boss(Hit(boss.pods[0], 50, 0, 0, 0, -1, 0))
    assert abs(hp0 - boss.hp - 50) < 1e-6, "an attached pod passes the hit to the core"
    h.run(h.seconds(4.0), FIRE, clear_rocks=True)
    h.shot("helios")
    # A flare: outside the gap it hurts, inside it doesn't.
    ship = game.ship
    flare = Flare("h", ship.y, 0, [(ship.x - 20, ship.x + 20)])
    assert not flare.touches(ship)
    flare.gaps = [(0, 10)]
    assert flare.touches(ship)
    boss.pattern_index, boss.attack_time = 1, 0.0          # the flare pattern
    h.run(h.seconds(1.3), clear_rocks=True)
    assert boss.flares, "a flare launched after the warning"
    h.shot("helios_flare")
    # Phase 2: pods detach and have their own armour.
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    assert boss.phase == 1 and all(p.detached for p in boss.pods)
    boss.roar = 0
    hp0, pod = boss.hp, boss.pods[1]
    game._damage_boss(Hit(pod, pod.hp + 1, 0, 0, 0, -1, 0))
    assert boss.hp == hp0, "a detached pod's damage doesn't hurt the core"
    h.run(3, clear_rocks=True)
    assert pod.dead and pod not in boss.parts()
    h.run(h.seconds(3.0), clear_rocks=True)
    h.shot("helios_pods")
    # Phase 3: the core takes more; magma rain.
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    assert boss.phase == 2
    hp0 = boss.hp
    game._damage_boss(Hit(boss, 100, 0, 0, 0, -1, 0))
    assert abs(hp0 - boss.hp - 100 * boss.CORE_OPEN) < 1e-6
    boss.pattern_index = 1                                 # rain
    boss.attack_time = 0.0
    h.run(h.seconds(1.5))
    assert any(isinstance(r, MagmaRock) for r in game.asteroids), "magma rain"
    h.shot("helios_phase3")
    h.kill(boss)
    h.run(h.seconds(boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state in (State.LEVEL_CLEAR, State.WIN)
    game.to_title()


def test_level6(h):
    """Level 6 GHOST NEBULA: fog banks drift down and cover rocks; phantoms fade in before
    they fire; WRAITH teleports (untargetable in between), phase 2 decoys pop in one hit
    without hurting it, phase 3 fogs the screen and fires curving shots after a tell."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(5)
    game.radio = None
    game.ship.hp = 10 ** 6
    assert isinstance(game.hazard, FogBanks) and game.ship.loadout.name == "MK VI"
    game.hazard.timer = 0
    h.run(h.seconds(3.0))
    bank = game.hazard.banks[0]
    image, bx, by = bank
    px, py = next((x, y) for y in range(image.get_height()) for x in range(image.get_width())
                  if image.get_at((x, y)).a)
    assert game.hazard.covers(bx + px, by + py)
    h.shot("level6_fog")

    # Phantom: hidden, fades in, fires a burst, cloaks again.
    game.hazard.banks.clear()
    phantom = Phantom(160)
    phantom.y, phantom.cloak = 60, 0.0
    game.enemies = [phantom]
    game.enemy_bullets.clear()
    h.run(h.seconds(PHANTOM_FADE * 0.5), clear_rocks=True)
    assert 0 < phantom.visible < 1 and not game.enemy_bullets
    h.run(h.seconds(PHANTOM_FADE * 0.5 + 0.6), clear_rocks=True)
    assert game.enemy_bullets, "it fired after fading in"
    h.shot("phantom")
    game.enemies.clear()

    # WRAITH.
    game.start(5, 0, 2, 0)
    game.radio = None
    game.ship.hp = 10 ** 6
    h.run(h.seconds(WARNING_TIME + Wraith.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Wraith) and boss.fighting and game._music_track() == "wraith"
    boss.pattern_index, boss.attack_time = 0, 0.0          # teleport
    h.run(3, clear_rocks=True)
    assert boss.hidden and boss.parts() == [], "untargetable while it jumps"
    h.run(h.seconds(1.0), clear_rocks=True)
    assert not boss.hidden and boss.spot == (boss.x, boss.y) or not boss.hidden
    h.run(h.seconds(2.0), FIRE, clear_rocks=True)
    h.shot("wraith")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    assert boss.phase == 1
    boss.pattern_index, boss.attack_time = 0, 0.0
    for weapon in game.weapons:                        # no stray shots to pop the decoys
        weapon.reset()
    h.run(h.seconds(1.0), clear_rocks=True)
    assert len(boss.decoys) == 2
    hp0, decoy = boss.hp, boss.decoys[0]
    game._damage_boss(Hit(decoy, 500, 0, 0, 0, -1, 0))
    h.run(1, clear_rocks=True)
    assert boss.hp == hp0 and decoy not in boss.decoys, "a decoy pops, the boss is fine"
    h.shot("wraith_decoys")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    assert boss.phase == 2
    boss.pattern_index, boss.attack_time = 1, 0.0          # curves
    game.enemy_bullets.clear()
    h.run(h.seconds(1.2), clear_rocks=True)
    assert any(isinstance(b, CurvedBullet) for b in game.enemy_bullets), "curving shots"
    h.shot("wraith_phase3")
    h.kill(boss)
    h.run(h.seconds(boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state in (State.LEVEL_CLEAR, State.WIN)
    game.to_title()


def test_level7(h):
    """Level 7 CRYSTAL VEIL: a lasered crystal splits the beam onto nearby rocks; a prism
    turret falls with its crystal; KALEIDOS mirrors the laser back in phase 1 (the gun
    breaks shards, they regrow), burns a blinking lattice in phase 2, prism spirals in 3."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(6)
    game.radio = None
    game.ship.hp = 10 ** 6
    assert game.ship.loadout.name == "MK VII" and game._music_track() == "level7"
    lib, hp = game.library, game.level.difficulty.rock_hp
    crystal = CrystalRock(lib.pick(8, 8, ("crystal",)), game.ship.x, 90, 0, 0, 0, hp_scale=hp)
    others = [Asteroid(lib.pick(5, 5, ("slate",)), game.ship.x + dx, 70, 0, 0, 0,
                       hp_scale=hp) for dx in (-40, 40, 0)]
    game.asteroids = [crystal] + others
    laser = game.weapons[1]
    game._damage_rock(Hit(crystal, 5, crystal.x, crystal.y, 0, -1, 0, continuous=True,
                          source=laser))
    assert len(game.refractions) == REFRACT_BEAMS
    assert all(r.hp < r.max_hp for r in others), "the split beams hit"
    game.weapon_index = 1
    for _ in range(20):
        crystal.vx = crystal.vy = 0
        game.update(h.dt, FIRE)
        game.draw()
    h.shot("level7_refract")

    # Prism turret: falls when its crystal breaks.
    game.asteroids.clear()
    game.enemies = prism_turret(game)
    turret = game.enemies[0]
    host = turret.host
    h.run(2)
    game._damage_rock(Hit(host, host.max_hp + 1, host.x, host.y, 0, -1, 0))
    h.run(2)
    assert turret not in game.enemies, "the turret fell with its crystal"
    game.weapon_index = 0

    # KALEIDOS.
    game.start(6, 0, 2, 0)
    game.radio = None
    game.ship.hp = 10 ** 6
    h.run(h.seconds(WARNING_TIME + Kaleidos.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Kaleidos) and boss.fighting and game._music_track() == "kaleidos"
    shard = boss.shards[2]
    hp0, ship_hp = boss.hp, game.ship.hp
    game.ship.invulnerable_time = 0
    game._damage_boss(Hit(shard, 20, 0, 0, 0, -1, 0, continuous=True, source=laser))
    h.run(1, clear_rocks=True)
    assert boss.hp == hp0 and game.ship.hp < ship_hp, "the mirror bounced the laser back"
    game._damage_boss(Hit(shard, shard.max_hp + 1, 0, 0, 0, -1, 0))
    assert not shard.whole and shard not in boss.parts()
    h.run(h.seconds(Shard.REGROW + 1.0), clear_rocks=True)         # (+ hit-stops)
    assert shard.whole, "shards regrow"
    h.run(h.seconds(2.0), FIRE, clear_rocks=True)
    h.shot("kaleidos")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    boss.pattern_index, boss.attack_time = 1, 0.0            # lattice
    h.run(3, clear_rocks=True)
    assert boss.lattice == 1 and boss.beams()
    h.shot("kaleidos_lattice_warn")
    h.run(h.seconds(Kaleidos.LATTICE_WARN + JUICE_PAD), clear_rocks=True)   # (+ slow-mo)
    assert boss.lattice == 2
    ax, ay, bx, by = boss.beams()[0]
    game.ship.x, game.ship.y = (ax + bx) / 2, (ay + by) / 2
    game.ship.invulnerable_time, ship_hp = 0, game.ship.hp
    h.run(1, clear_rocks=True)
    assert game.ship.hp < ship_hp, "the burning lattice hurts"
    h.shot("kaleidos_lattice")
    game.ship.x, game.ship.y = game.SHIP_START
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    boss.pattern_index, boss.attack_time = 0, 0.0            # spiral7
    game.enemy_bullets.clear()
    h.run(h.seconds(1.0), clear_rocks=True)
    assert any(isinstance(b, ColoredBullet) for b in game.enemy_bullets)
    h.shot("kaleidos_phase3")
    h.kill(boss)
    h.run(h.seconds(boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state in (State.LEVEL_CLEAR, State.WIN)

    # The level 7 gift offers a skin (SOLAR paint): the card draws, taking it wears it.
    game.save.gifts = [k for k in game.save.gifts if k != "1-7"]
    game.save.owned.remove("SOLAR")
    game.offer_gift("1-7", ("hangar", 7 if len(LEVELS) > 7 else 6, 0))
    game.gift_cursor = 1
    h.run(3)
    h.shot("gift_skin")
    game.state_time = 1.0
    h.post(pygame.K_RETURN)
    assert game.skin("PAINT").id == "SOLAR" and game.ship.colors == SHIP_PALETTES["solar"]
    game.save.skins = {}
    game.choose_hull(ARROW)
    game.to_title()


def test_level8(h):
    """Level 8 IRON GRAVEYARD: wreck chunks are tough and drop coins; a salvager steals a
    coin and drops it twice when shot; SCRAPJAW assembles itself, plates shot off count for
    the boss and get thrown back, the magnet claw crushes rocks into ammunition, the armour
    falls off in phase 3."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(7)
    game.radio = None
    game.ship.hp = 10 ** 6
    assert game.ship.loadout.name == "MK VIII" and game._music_track() == "level8"
    lib, hp = game.library, game.level.difficulty.rock_hp
    wreck = WreckChunk(lib.pick(8, 8, ("wreck",)), 160, 80, 0, 0, 0, hp_scale=hp)
    rock = Asteroid(lib.pick(8, 8, ("wreck",)), 160, 80, 0, 0, 0, hp_scale=hp)
    assert wreck.max_hp > rock.max_hp * 2
    game.asteroids = [wreck]
    game.pickups.clear()
    game._damage_rock(Hit(wreck, wreck.max_hp + 1, wreck.x, wreck.y, 0, -1, 0))
    assert sum(isinstance(p, Coin) for p in game.pickups) >= 1, "wrecks drop coins"
    h.run(h.seconds(1.0))
    h.shot("level8")

    # Salvager: steals a coin, drops it twice when shot down.
    game.pickups = [Coin(200, 100, 0, 0)]
    thief = Salvager(200)
    thief.y = 60
    game.enemies = [thief]
    for _ in range(h.seconds(2.0)):
        game.update(h.dt, Keys())
        if thief.loot:
            break
    assert thief.loot and not game.pickups, "it grabbed the coin"
    game._damage_enemy(Hit(thief, thief.hp + 1, thief.x, thief.y, 0, -1, 0))
    assert sum(isinstance(p, Coin) for p in game.pickups) >= 2, "stolen coin drops twice"
    game.pickups.clear()
    game.enemies.clear()

    # SCRAPJAW.
    game.start(7, 0, 2, 0)
    game.radio = None
    game.ship.hp = 10 ** 6
    h.run(h.seconds(WARNING_TIME + Scrapjaw.ENTER_TIME * 0.5), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Scrapjaw) and boss.state == "enter"
    h.shot("scrapjaw_assembles")
    h.run(h.seconds(Scrapjaw.ENTER_TIME * 0.5 + 0.3), clear_rocks=True)
    assert boss.fighting and game._music_track() == "scrapjaw"
    plate = boss.plates[0]
    hp0 = boss.hp
    game._damage_boss(Hit(plate, plate.hp + 1, 0, 0, 0, -1, 0))
    assert not plate.attached and boss.stock == 1 and boss.hp < hp0, "shot off, it still hurt"
    boss.pattern_index, boss.attack_time, boss.fire_timer = 1, 0.0, 0.0     # throw
    h.run(3, clear_rocks=True)
    assert any(isinstance(e, JunkShot) for e in game.enemies), "armour thrown back"
    h.run(h.seconds(1.0), FIRE, clear_rocks=True)
    h.shot("scrapjaw")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    assert boss.phase == 1
    boss.pattern_index, boss.attack_time = 0, 0.0           # magnet
    cx, cy = boss._claw()
    pulled = Asteroid(lib.pick(5, 5, ("wreck",)), cx + 30, cy + 20, 0, 0, 0)
    game.asteroids = [pulled]
    stock = boss.stock
    for _ in range(h.seconds(2.5)):
        game.update(h.dt, Keys())
        if pulled not in game.asteroids:
            break
    game.draw()
    assert pulled not in game.asteroids and boss.stock > stock, "crushed into ammunition"
    h.shot("scrapjaw_magnet")
    game._damage_boss(Hit(boss, boss.max_hp * 0.34, 0, 0, 0, -1, 0))
    boss.roar = 0
    assert boss.phase == 2 and not any(p.attached for p in boss.plates)
    h.run(h.seconds(2.0), clear_rocks=True)
    h.shot("scrapjaw_phase3")
    h.kill(boss)
    h.run(h.seconds(boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state in (State.LEVEL_CLEAR, State.WIN)
    game.to_title()


def test_level9(h):
    """Level 9 EVENT HORIZON: the black hole pulls rocks and the ship (full thrust escapes),
    the event horizon hurts, the SLINGSHOT ring triples score and powers shots, the WHITE
    HOLE pushes everything out and spits swallowed bullets back; comets; interceptors block
    head-on shots; THE TWINS: the tether hurts, a twin revives unless both go down; the
    level's gift (ARC or SPECTER) leads on to level 10."""
    game = h.game
    for level in LEVELS:                              # every radio line fits on its card
        for line in list(level.radio) + [x for wave in level.waves for x in wave.radio]:
            assert len(line) <= 43, line
    game.choose_hull(ARROW)
    game.start(8)
    game.radio = None
    game.ship.hp = 10 ** 6
    hole = game.hazard
    assert isinstance(hole, BlackHole) and game.ship.loadout.name == "MK IX"
    assert game._music_track() == "level9"
    h.run(h.seconds(2.0))
    h.shot("level9")

    # The pull: a rock falls towards it; the ship drifts in, but full thrust escapes.
    lib = game.library
    rock = Asteroid(lib.pick(5, 5, ("slate",)), hole.x + 60, hole.y, 0, 0, 0)
    game.asteroids = [rock]
    h.run(20)
    assert rock.vx < 0 or rock not in game.asteroids, "pulled towards the hole"
    game.asteroids.clear()
    ship = game.ship
    ship.x, ship.y = hole.x + 45, hole.y + 50
    d0 = math.hypot(ship.x - hole.x, ship.y - hole.y)
    h.run(30, clear_rocks=True)
    assert math.hypot(ship.x - hole.x, ship.y - hole.y) < d0, "the ship is pulled in"
    ship.x, ship.y = hole.x + 45, hole.y + 50
    h.run(40, Keys(pygame.K_DOWN, pygame.K_RIGHT), clear_rocks=True)
    assert math.hypot(ship.x - hole.x, ship.y - hole.y) > d0, "thrust escapes"
    # The event horizon hurts; the ring triples score.
    hp0 = ship.hp
    ship.invulnerable_time = 0
    ship.x, ship.y = hole.x, hole.y
    h.run(1, clear_rocks=True)
    assert ship.hp < hp0
    lo, hi = hole.ring
    ship.x, ship.y = hole.x + (lo + hi) / 2, hole.y
    ship.invulnerable_time = 5
    h.run(1, clear_rocks=True)
    assert game.slingshot
    game.break_combo()
    assert game.add_kill(100, 0, 0) == 100 * SLINGSHOT_SCORE
    h.shot("slingshot")
    ship.x, ship.y = game.SHIP_START
    h.run(2, clear_rocks=True)
    # A gun shot through the ring is boosted.
    gun = game.weapons[0]
    b = GunBullet(hole.x + (lo + hi) / 2, hole.y + 5, 0, -300)
    gun.bullets = [b]
    hole._pull_shots(h.dt, game)
    assert b.boost
    # WHITE HOLE: warning, then it pushes out and spits swallowed bullets back.
    hole.stored = 6
    hole.flip_timer = WHITE_HOLE_WARN - 0.1
    h.run(3, clear_rocks=True)
    assert hole.warning
    h.shot("white_hole_warning")
    hole.flip_timer = 0.01
    game.enemy_bullets.clear()
    h.run(2, clear_rocks=True)
    assert hole.white > 0 and len(game.enemy_bullets) >= 6 and hole.stored == 0
    assert hole.pull_at(hole.x + 50, hole.y)[0] > 0, "a white hole pushes away"
    h.run(h.seconds(0.5), clear_rocks=True)
    h.shot("white_hole")
    hole.white = 0

    # Comets fall fast; interceptors block head-on shots, not while cooling down.
    comet = Comet(lib.pick(6, 6, ("comet",)), 100, 0, 5, 60, 0)
    assert comet.vy > 60
    inter = Interceptor(160)
    inter.y, inter.facing = 60, math.pi / 2
    inter.mode = "aim"
    assert inter.armour(Hit(inter, 5, 0, 0, 0, -1, 0)) == 0.0
    assert inter.armour(Hit(inter, 5, 0, 0, 1, 0, 0)) == 1.0, "from the side it's open"
    inter.mode = "cool"
    assert inter.armour(Hit(inter, 5, 0, 0, 0, -1, 0)) == 1.0
    game.enemies = interceptor_pair(game)
    game.asteroids = [comet]
    h.run(h.seconds(2.5))
    h.shot("interceptors")
    game.enemies.clear()

    # THE TWINS (level 9's boss).
    game.start(8, 0, 2, 0)
    game.radio = None
    game.ship.hp = 10 ** 6
    h.run(h.seconds(WARNING_TIME + Twins.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    game.ship.hp = 10 ** 6                            # (the WARNING refilled the hull)
    assert isinstance(boss, Twins) and boss.fighting and not game.is_final_boss()
    assert game._music_track() == "twins" and len(boss.parts()) == 2
    h.run(h.seconds(2.0), FIRE, clear_rocks=True)
    h.shot("twins")
    ax, ay, bx, by = boss.tether()
    game.ship.x, game.ship.y = ax * 0.8 + bx * 0.2, ay * 0.8 + by * 0.2   # off the core
    game.ship.invulnerable_time, hp0 = 0, game.ship.hp
    game.shield = 0                                   # (a SHIELD boost may have dropped)
    h.run(1, clear_rocks=True)
    assert game.ship.hp < hp0, "the tether hurts"
    game.ship.x, game.ship.y = game.SHIP_START
    game.god = True                                   # (repair kits clamp the test hull)
    ora, zen = boss.twins
    while ora.alive:                                  # (phase thresholds stop each burst)
        boss.roar = 0
        game._damage_boss(Hit(ora, ora.hp + 1, 0, 0, 0, -1, 0))
    boss.roar = 0
    h.run(2, clear_rocks=True)
    assert not ora.alive and boss.tether() is None and boss.revive_text
    h.shot("twins_revive")
    h.run(h.seconds(TwinShip.REVIVE + JUICE_PAD + 0.5), clear_rocks=True)
    assert ora.alive and ora.hp > 0, "ZEN revived ORA"
    boss.roar = 0
    h.kill(boss)
    assert boss.state == "dying", "both went down together"
    for _ in range(h.seconds(10)):
        h.run(1, clear_rocks=True)
        if game.state == State.LEVEL_CLEAR:
            break
    game.god = False
    assert game.state == State.LEVEL_CLEAR, (game.state, game.phase, boss.state)
    h.run(h.seconds(1.2))
    game.save.gifts = [k for k in game.save.gifts if k != "1-9"]
    game.save.owned.remove("SPECTER")
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["ARC", "SPECTER"]
    game.gift_cursor = 1
    h.run(h.seconds(0.6))
    h.shot("gift_specter")
    h.post(pygame.K_RETURN)
    assert game.inventory.owns("SPECTER") and game.hull.name == "SPECTER"
    assert game.state == State.HANGAR and game.next_launch[0] == 9, "on to level 10"
    game.choose_hull(ARROW)
    game.to_title()


def test_level10(h):
    """Level 10 SWARM HEART: hive walls hurt and push back, spore pods burst into a ring
    (unless shot first), larvae flock onto the rocket and leave; the boss rush; THE OVERMIND:
    glands take the hits while the wall stands (the heart can't be hit), the wall tears, the
    lash locks on, the bio-beam burns; the ESCAPE run; the WARP finale with the galaxy medal,
    CHAMPION, the SWARMBANE gift and the star map with its gate open."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(9)
    game.radio = None
    game.ship.hp = 10 ** 6
    tunnel = game.hazard
    assert isinstance(tunnel, HiveTunnel) and game.ship.loadout.name == "MK X"
    assert game._music_track() == "level10" and game.level.finale
    h.run(h.seconds(2.0))
    h.shot("level10")
    # The walls hurt and push the rocket back into the tunnel; the middle is safe.
    ship = game.ship
    ship.invulnerable_time, hp0 = 0, ship.hp
    game.shield = 0
    h.run(h.seconds(0.5), clear_rocks=True)
    game.enemy_bullets.clear()
    game.enemies.clear()
    game.extra_timers = [99.0] * len(game.extra_timers)   # (no spores / larvae just now)
    ship.x, ship.y = game.SHIP_START
    ship.invulnerable_time, hp0 = 0, ship.hp
    h.run(h.seconds(1.0), clear_rocks=True)
    assert ship.hp == hp0, "the middle of the tunnel is safe"
    edge = tunnel.width(-1, ship.y)
    ship.x = edge - 2
    game.shield = 0
    h.run(1, clear_rocks=True)
    assert ship.hp < hp0 and ship.x > edge, "the wall hurts and pushes back"
    ship.x, ship.y = game.SHIP_START
    # Spore pods: swell, then a ring of bullets; shot early, they just pop.
    game.enemies.clear()
    game.enemy_bullets.clear()
    pod = SporePod(160)
    pod.y = SPORE_RIPEN - 2
    game.spawn_enemies([pod])
    h.run(h.seconds(0.3), clear_rocks=True)
    assert pod.swell >= 0
    h.shot("spore_swell")
    h.run(h.seconds(SPORE_SWELL + 0.3), clear_rocks=True)
    assert pod not in game.enemies and len(game.enemy_bullets) >= SPORE_SHOTS, "the pod bursts"
    game.enemy_bullets.clear()
    early = SporePod(100)
    early.y = 40
    game.enemies = [early]
    early.damage(early.hp + 1)
    h.run(2, clear_rocks=True)
    assert early not in game.enemies and not game.enemy_bullets, "shot early: no ring"
    # Larvae flock onto the rocket, then swarm off.
    game.enemies.clear()
    flock = larva_flock(game, 10)
    game.spawn_enemies(flock)
    d0 = sum(math.hypot(l.x - ship.x, l.y - ship.y) for l in flock) / len(flock)
    h.run(h.seconds(1.2), clear_rocks=True)
    alive = [l for l in flock if l in game.enemies]
    d1 = sum(math.hypot(l.x - ship.x, l.y - ship.y) for l in alive) / max(1, len(alive))
    assert d1 < d0, "the flock hunts the rocket"
    h.shot("larvae")
    game.god = True
    h.run(h.seconds(LARVA_TIME + 3), clear_rocks=True)
    assert not any(l in game.enemies for l in flock), "the flock leaves after a while"
    game.enemy_bullets.clear()

    # The boss rush: three old enemies, one after the other.
    rush = game.level.waves[1].bosses
    assert [e.boss_class for e in rush] == [Mothership, Leviathan, Helios]
    game.start(9, 0, 1, 0)
    game.radio = None
    h.run(h.seconds(WARNING_TIME + 0.5), clear_rocks=True)
    assert isinstance(game.boss, Mothership)
    while not game.boss.fighting:
        h.run(10, clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + 1.5 + JUICE_PAD + 0.5), clear_rocks=True)
    assert game.boss_index == 1 and game.phase in (Phase.WARNING, Phase.BOSS), "next in line"

    # THE OVERMIND.
    game.start(9, 0, 2, 0)
    game.radio = None
    h.run(h.seconds(WARNING_TIME + Overmind.ENTER_TIME + 0.3), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, Overmind) and boss.fighting and game.is_final_boss()
    assert game._music_track() == "overmind" and boss.hive and len(boss.parts()) == 4
    assert not boss.contains(boss.x, boss.y), "the heart hides behind the wall"
    boss.hit_part(boss, boss.max_hp, source=None)
    assert boss.hp == boss.max_hp
    h.run(h.seconds(2.0), FIRE, clear_rocks=True)
    h.shot("overmind_hive")
    for gland in boss.glands[:3]:
        boss.roar = 0
        game._damage_boss(Hit(gland, gland.hp + 50, gland.x, gland.y, 0, -1, 0))
    assert boss.phase == 0 and len(boss.parts()) == 1, "3 glands down, the wall holds"
    boss.roar = 0
    last = boss.glands[3]
    game._damage_boss(Hit(last, last.hp + 50, last.x, last.y, 0, -1, 0))
    assert boss.phase == 1 and boss.parts() == [boss], "the last gland tears the wall"
    h.run(h.seconds(BOSS_ROAR_TIME + 0.4), clear_rocks=True)
    h.shot("overmind_tear")
    h.run(h.seconds(1.5), clear_rocks=True)
    assert boss.tear >= 1 and abs(boss.y - boss.home_y) < 8, "the heart descends"
    h.shot("overmind_heart")
    boss.roar = 0
    game._damage_boss(Hit(boss, boss.max_hp, 0, 0, 0, -1, 0))
    assert boss.phase == 2
    boss.roar = 0
    locked = lashed = False
    for _ in range(h.seconds(8)):
        h.run(1, clear_rocks=True)
        if boss.lock_target and not locked and boss.attack_time > 0.5:
            h.shot("overmind_lock")
            locked = True
        if boss.tentacle.state >= 2:
            lashed = True
            assert boss.contact_damage > boss.bullet_damage
        if locked and lashed and boss.tentacle.state >= 3:
            break
    assert locked and lashed, "the tentacle locks on and lashes"
    h.shot("overmind_lash")
    game._damage_boss(Hit(boss, boss.max_hp, 0, 0, 0, -1, 0))
    assert boss.phase == 3
    boss.roar = 0
    game.god = False
    game.ship.hp = 10 ** 6
    hurt = False
    for _ in range(h.seconds(8)):
        if boss.beam == 2:
            game.ship.x, game.ship.y = boss._mouth()[0], LOW_H - 40
            game.ship.invulnerable_time, hp0 = 0, game.ship.hp
            game.shield = 0
            h.run(1, clear_rocks=True)
            hurt = game.ship.hp < hp0
            break
        h.run(1, clear_rocks=True)
    assert hurt, "the bio-beam burns"
    h.shot("overmind_beam")
    game.god = True
    h.kill(boss)
    for _ in range(h.seconds(8)):
        h.run(1, clear_rocks=True)
        if game.wave.escape:
            break
    assert game.wave.escape and game.phase == Phase.FIELD, "then: ESCAPE!"
    assert game._music_track() == "escape"
    h.run(h.seconds(4.0), Keys(pygame.K_UP), clear_rocks=True)
    assert game.hazard.collapse > 0 and game.hazard.world_speed == ESCAPE_SPEED
    h.shot("escape")
    for _ in range(h.seconds(25)):
        h.run(1, Keys(pygame.K_UP))
        if game.state == State.WARP:
            break
    assert game.state == State.WARP, (game.state, game.phase)
    assert game.medal_new and 1 in game.save.medals and "CHAMPION" in game.save.achievements
    assert game.record_rank and not game.enemies and game.boss is None
    h.run(h.seconds(3.0))
    h.shot("warp")
    h.run(h.seconds(3.0))
    h.shot("warp_jump")
    assert 1 in game.save.shards and "G1_WARP" in game.save.story, "shard 1 + the transmission"
    for _ in range(8):                                   # ENTER skips the radio cards first
        h.post(pygame.K_RETURN)
        if game.state == State.WIN:
            break
    assert game.state == State.WIN, "ENTER skips the rest"
    game.god = False
    h.run(h.seconds(1.2))
    h.shot("win")
    game.save.gifts = [k for k in game.save.gifts if k != "1-10"]
    game.save.owned.remove("SWARMBANE")
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["SWARMBANE"]
    h.run(h.seconds(0.6))
    h.shot("gift_swarmbane")
    h.post(pygame.K_RETURN)
    assert game.inventory.owns("SWARMBANE") and game.skin(PAINT).id == "SWARMBANE"
    assert game.state == State.STAR_MAP and game.star_map.gmap.galaxy == 2, "on to the Veil"
    assert game.star_map.near_gate() and game.star_map.gate_open, "arrived through the gate"
    h.run(10)
    h.shot("starmap_veil_arrival")
    game.open_star_map(9)                                # back home: the gate stands open
    assert game.star_map.medal and game.star_map.gate_open
    h.run(10)
    h.shot("starmap_medal")
    game.save.skins = {}
    game.choose_hull(ARROW)
    game.to_title()


def test_starmap(h):
    """STAR MAP: fly the rocket between planets (cards), locked planets refuse a landing,
    the black hole planet pulls, hidden data caches beep on the scanner, show up close,
    pay once and tell a story; finding all six earns EXPLORER (STARDUST trail); saved."""
    game = h.game
    for cache in CACHES:                                 # every story line fits on its card
        assert len(cache.title) <= 40 and all(len(line) <= 40 for line in cache.lines), cache.id
        assert 0 <= cache.x <= MAP_W and 0 <= cache.y <= MAP_H
    for galaxy in GALAXIES:                              # a planet for every level
        assert len(MAPS[galaxy.number].nodes) >= len(galaxy.levels)
    game.save.caches = []
    game.save.achievements = [a for a in game.save.achievements if a != "EXPLORER"]
    game.save.unlock(10)
    game.to_title()
    game.start_level = 0
    h.post(pygame.K_RETURN)
    m = game.star_map
    assert game.state == State.STAR_MAP and m.near_node() == 0
    assert game._music_track() == "starmap"
    h.run(10)
    h.shot("starmap")
    # Fly to planet 2.
    reached = False
    for _ in range(h.seconds(4)):
        tx, ty = NODES[1]
        keys = []
        if abs(tx - m.ship.x) > 3:
            keys.append(pygame.K_RIGHT if tx > m.ship.x else pygame.K_LEFT)
        if abs(ty - m.ship.y) > 3:
            keys.append(pygame.K_DOWN if ty > m.ship.y else pygame.K_UP)
        h.run(1, Keys(*keys))
        if m.near_node() == 1:
            reached = True
            break
    assert reached and m.ship.angle != 0, "flew to planet 2, nose first"
    h.run(5)
    h.shot("starmap_card")
    # A locked planet refuses a landing.
    m.unlocked = 2
    m.place_at(5)
    h.post(pygame.K_RETURN)
    assert game.state == State.STAR_MAP
    m.unlocked = game.selectable_levels
    # The rocket stays on the map.
    m.ship.x, m.ship.y = 5, 5
    h.run(20, Keys(pygame.K_LEFT, pygame.K_UP))
    assert m.ship.x >= 8 and m.ship.y >= 8
    # The black hole planet pulls the rocket in (it can fly away).
    bx, by = NODES[BLACK_HOLE]
    m.ship.x, m.ship.y, m.ship.vx, m.ship.vy = bx + 50, by, 0, 0
    h.run(30)
    assert m.ship.x < bx + 45, "pulled in"
    h.run(60, Keys(pygame.K_RIGHT))
    assert m.ship.x > bx + 50, "full thrust escapes"
    # A hidden cache: the scanner beeps near it, it shows up close, it pays once.
    cache = CACHES[0]
    m.ship.x, m.ship.y, m.ship.vx, m.ship.vy = cache.x + 100, cache.y, 0, 0
    assert m.signal() > 0 and not m.visible(cache)
    m.ship.x = cache.x + 30
    assert m.visible(cache)
    coins = game.save.coins
    h.run(5)
    h.shot("starmap_cache_near")
    for _ in range(h.seconds(2)):
        h.run(1, Keys(pygame.K_LEFT))
        if m.card:
            break
    assert m.card is cache and game.save.coins == coins + cache.coins
    assert game.save.caches == [cache.id]
    h.shot("starmap_cache")
    h.post(pygame.K_RETURN)
    assert m.card is None and game.state == State.STAR_MAP
    game.open_star_map(0)
    assert cache.id in game.star_map.found and game.star_map.hidden_caches()[0] is not cache
    m = game.star_map
    game._open_cache(cache)                              # (a second visit pays nothing)
    assert game.save.coins == coins + cache.coins
    for other in CACHES[1:]:
        m.card = None
        m.ship.x, m.ship.y, m.ship.vx, m.ship.vy = other.x, other.y, 0, 0
        h.run(1)
    assert set(game.save.caches) == {c.id for c in CACHES} and m.signal() == 0
    assert "EXPLORER" in game.save.achievements and game.inventory.owns("STARDUST")
    # The warp gate: sealed without the medal.
    m.card = None
    m.medal = False
    m.ship.x, m.ship.y = GATE
    h.run(5)
    assert m.near_gate()
    h.shot("starmap_gate")
    saved = SaveData(h.save_path)
    assert set(saved.caches) == {c.id for c in CACHES}
    h.post(pygame.K_ESCAPE)
    assert game.state == State.TITLE


def test_journal(h):
    """JOURNAL + story: Vega's first radio words spell the hidden message, every lore line
    fits, the journal opens from the title (J) and the map, boss files open when a boss is
    beaten (margin note), heralds stay black until their galaxy is near, VANTA's file grows,
    ECHOES fill the mosaic and switch on the decoder, dialogs switch speakers (a hijacked
    card), the ghost record appears after galaxy 1."""
    game = h.game
    assert "".join(level.radio[0][0] for level in LEVELS[:10]) == ACROSTIC
    assert DECODED.replace(" ", "") == ACROSTIC
    for d in DOSSIERS:
        for line in d.facts + d.vanta + (d.note,):
            assert len(line) <= TEXT_WIDTH, line
    for herald in HERALDS:
        assert all(len(line) <= TEXT_WIDTH for line in herald.lines)
    assert all(len(text) <= TEXT_WIDTH for _, text in VANTA_FILE)
    assert all(len(e.text) <= TEXT_WIDTH for e in ECHOES)
    for line in TRANSMISSIONS["G1_WARP"]:
        assert len(line.text) <= 43
    names = {e.spec.name for level in LEVELS for w in level.waves for e in w.bosses}
    assert names <= set(DOSSIER_BY_BOSS), names - set(DOSSIER_BY_BOSS)
    assert {e.cache for e in ECHOES} <= {c.id for c in CACHES}
    assert sorted(e.tile for e in ECHOES) == list(range(6))
    # Dialog cards: a new card per speaker, 3 lines at most.
    split = cards(["A", "B", Line(VANTA, "C"), Line(VANTA, "D"), "E", "F", "G", "H"])
    assert [(s_, len(t)) for s_, t in split] == [(VEGA, 2), (VANTA, 2), (VEGA, 3), (VEGA, 1)]
    assert is_hijack(VANTA) and not is_hijack(VEGA)

    # A fresh logbook: nothing known yet.
    save = game.save
    save.bosses, save.cleared, save.medals, save.shards = [], {}, [], []
    save.caches, save.story = [], []
    game.to_title()
    h.post(pygame.K_j)
    assert game.state == State.JOURNAL and game._music_track() == "starmap"
    h.run(5)
    h.shot("journal_pilot")
    h.post(pygame.K_RIGHT)
    page = game.journal_page()
    files = {f.where + f.status: f for f in page.bosses}
    gunship = page.bosses[0]
    assert gunship.status == "unknown" and gunship.name.startswith("?")
    nyx = next(f for f in page.bosses if f.where == "GALAXY 2")
    assert nyx.name == "N##", "a herald stays black"
    vanta = page.bosses[-1]
    assert vanta.status == "vanta" and vanta.name == "#####"
    h.shot("journal_bosses_blank")
    # Beating a boss opens its file (with a margin note in red).
    game.start(0, 0, 0, 0)
    game.radio = None
    game.god = True
    h.run(h.seconds(WARNING_TIME + 0.5), clear_rocks=True)
    while not game.boss.fighting:
        h.run(10, clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD + 0.5), clear_rocks=True)
    game.god = False
    assert "GUNSHIP" in save.bosses
    game.to_title()
    game.open_journal()
    game.journal_switch(1)
    page = game.journal_page()
    assert page.bosses[0].status == "defeated" and page.bosses[0].note
    assert files                                          # (built without errors before)
    h.run(5)
    h.shot("journal_gunship")
    # Galaxy 1 beaten: the next herald gets a name, VANTA a file, the ghost record shows.
    save.medals, save.shards = [1], [1]
    page = game.journal_page()
    nyx = next(f for f in page.bosses if f.where == "GALAXY 2")
    assert nyx.name == "NYX" and game.ghost_record_shown
    vanta = page.bosses[-1]
    assert vanta.name == "VANTA" and len(vanta.lines) == 4
    game.journal_cursor["BOSSES"] = len(page.bosses) - 1
    h.run(5)
    h.shot("journal_vanta")
    # Echoes fill the mosaic; all six switch on the decoder, which lights the hidden letters.
    save.caches = [e.cache for e in ECHOES[:3]]
    game.journal_switch(1)
    assert not game.decoder and sum(got for _, got in game.journal_page().echoes) == 3
    h.run(5)
    h.shot("journal_echoes")
    save.caches = [e.cache for e in ECHOES]
    page = game.journal_page()
    assert game.decoder and len(page.bosses[-1].lines) == 6
    game.journal_switch(1)
    page = game.journal_page()
    assert page.log[0][0] == "decoded" and DECODED in page.log[0][1]
    assert sum(1 for kind, _, hl in page.log if hl) == min(save.unlocked, 10)   # galaxy 1 only
    for _ in range(30):
        h.post(pygame.K_DOWN)
    assert game.journal_cursor["LOG"] > 0
    h.run(5)
    h.shot("journal_log")
    h.post(pygame.K_ESCAPE)
    assert game.state == State.TITLE
    game.time = 6.5
    save.add_record(500, 1)
    game.draw()
    h.shot("title_ghost_record")
    # From the star map, J opens it and ESC comes back to the map.
    game.open_star_map(0)
    h.post(pygame.K_j)
    assert game.state == State.JOURNAL
    h.post(pygame.K_ESCAPE)
    assert game.state == State.STAR_MAP
    # A hijacked conversation in flight: VANTA first, then Vega.
    game.start(0)
    game.radio_say(TRANSMISSIONS["G1_WARP"], delay=0)
    assert game.radio.speaker == UNKNOWN
    h.run(10)
    h.shot("radio_hijack")
    game.skip_radio()
    game.skip_radio()
    assert game.radio.speaker == VANTA and len(game.radio_queue) == 1
    game.skip_radio()
    game.skip_radio()
    assert game.radio.speaker == VEGA
    game.to_title()


def test_brains(h):
    """The enemy's brains: the player model counts where you fly, how you dodge and react;
    the bandit learns which attack hurts you and re-learns when you adapt; the DIRECTOR
    builds, peaks and gives breathers, never below the base; a learning boss aims ahead and
    counters habits; it all survives a restart; a death in a thinking level says what it
    learned; the journal's KNOWN page shows it and can make them forget."""
    game = h.game
    rng = random.Random(4)
    m = PlayerModel()
    m.observe(1.0, 20, 230, 0, 0, False, "LASER")
    assert m.zone_share(rows=range(4, 6)) == 1.0 and m.weapon_share("LASER") == 1.0
    m.observe(0.1, 100, 200, -120, 0, True)
    m.observe(0.1, 90, 200, -120, 0, True)            # the same dodge: counted once
    m.observe(0.1, 80, 200, 0, 0, False)
    m.observe(0.1, 80, 200, 0, -150, True)
    assert m.dodges["L"] == 1 and m.dodges["U"] == 1
    m.telegraph()
    m.observe(0.2, 80, 200, 0, 0, False)
    m.observe(0.2, 80, 200, 90, 0, False)
    assert abs(m.reaction - 0.4) < 1e-6
    copy = PlayerModel.from_dict(m.to_dict())
    assert copy.heat == [round(v, 2) for v in m.heat] and copy.reactions == m.reactions
    before = m.seconds
    m.forget()
    assert abs(m.seconds - before * 0.9) < 1e-6
    assert insights(PlayerModel()) == ["WE ARE STILL WATCHING."]
    low = PlayerModel()
    low.observe(60, 160, 230, 0, 0, False)
    assert "YOU HIDE AT THE BOTTOM." in insights(low)
    assert all(len(line) <= TEXT_WIDTH for line in insights(m) + insights(low))

    # The bandit: FANS hurt this player, RINGS don't -> it picks FANS; then the player
    # learns to dodge fans and it switches.
    bandit = Bandit()
    picks = []
    for _ in range(80):
        arm = bandit.choose(("FANS", "RINGS"), rng)
        bandit.reward(arm, 10.0 if arm == "FANS" else 2.0)
        picks.append(arm)
    assert picks[-40:].count("FANS") >= 28 and "RINGS" in picks[-40:], "exploits, explores"
    for _ in range(80):
        arm = bandit.choose(("FANS", "RINGS"), rng)
        bandit.reward(arm, 1.0 if arm == "FANS" else 6.0)
        picks.append(arm)
    assert picks[-30:].count("RINGS") >= 20 and bandit.best() == "RINGS", "it re-learns"

    # The DIRECTOR: a player doing well gets peaks, then breathers; never below 1.
    d = Director()
    states, lowest = set(), 9.0
    for _ in range(60 * 60):
        p = d.update(1 / 60, 1.0, 0.0, 2.0)
        states.add(d.state)
        lowest = min(lowest, p)
    assert states == {Director.BUILD, Director.PEAK, Director.BREATHER} and lowest >= 1.0
    struggling = Director()
    top = max(struggling.update(1 / 60, 0.2, 0.05, 0.0) for _ in range(60 * 30))
    assert top < 1.4, "a struggling player gets less pressure"

    # In game: the DIRECTOR speeds the field up.
    game.force_director = True
    game.start(0)
    game.radio = None
    game.god = True
    pressures = []
    for _ in range(h.seconds(25)):
        h.run(1, FIRE)
        pressures.append(game.pressure)
    assert max(pressures) > 1.2 and min(pressures) >= 1.0
    assert game.player_model.seconds > 20 and game.player_model.weapon_share("GUN") > 0.5
    # A death in a thinking level: "IT LEARNED: ..."
    game.god = False
    h.die()
    h.run(h.seconds(1.0))
    assert game.state == State.GAME_OVER and game.death_insight
    h.shot("it_learned")
    game.force_director = False
    saved = SaveData(h.save_path)
    assert saved.brain["model"]["heat"], "it remembers across sessions"
    assert PlayerModel.from_dict(saved.brain["model"]).seconds > 20

    # A learning boss: picks with the saved bandit, is credited for damage, aims ahead.
    class Student(Learner, Gunship):
        pass
    game.start(0, 0, 0, 0)
    game.radio = None
    boss = Student(GUNSHIP_SPEC)
    first = boss.begin_attack(game, ("FAN", "RING"))
    boss.learn_tick(1.0)
    game.boss = boss
    boss.state = "fight"
    game.ship.invulnerable_time = 0
    game.shield = 0
    game.hurt_ship(12, game.ship.x, game.ship.y)
    assert boss._dealt == 12
    boss.begin_attack(game, ("FAN", "RING"))
    assert game.bandit_for("GUNSHIP").arms[first][1] == 12
    ship = game.ship
    ship.x, ship.y, ship.vx, ship.vy = 160, 200, 100, 0
    straight = math.atan2(200 - 50, 160 - 160)
    assert boss.lead_aim(game, 160, 50, 120) < straight, "it aims ahead of a moving rocket"
    game.player_model = low
    assert "floor" in boss.counters(game)
    game.load_brain()

    # The journal's KNOWN page, and FORGET.
    game.to_title()
    game.open_journal()
    game.journal_tab = 4
    h.run(3)
    h.shot("journal_known")
    h.post(pygame.K_BACKSPACE)
    assert game.player_model.seconds > 0 and game.journal_forget
    h.post(pygame.K_BACKSPACE)
    assert game.player_model.seconds == 0 and not game.bandits
    assert SaveData(h.save_path).brain["model"]["heat"] == [0.0] * 48
    h.post(pygame.K_ESCAPE)
    game.god = False


def test_veil(h):
    """Galaxy 2 THE VEIL, level 1 VEIL GATE: galaxy plumbing (labels, 50% boss repair, map
    per galaxy + warp gates), VEIL SHIFTS (each effect), ELITES (x3, guard), WISPS dodge
    lined-up shots, the new bullet types, RIFT portals carry rocks / bullets / your shots,
    the AMBUSH flow, THE WARDEN (rings block, the gap turns away from your side, inner ring,
    the saw), level end -> VEIL gift -> the Veil's map."""
    game = h.game
    g2 = GALAXIES[1]
    index = LEVELS.index(g2.levels[0])
    assert g2.boss_repair == BOSS_REPAIR_G2 and level_title(g2.levels[0]) == "G2 LEVEL 1"
    game.save.unlock(index + 1)
    game.choose_hull(ARROW)
    game.start(index)
    game.radio = None
    assert game.ship.loadout.name == "MK XI" and isinstance(game.hazard, RiftPortals)
    assert game.director_active and game.shift in SHIFTS and game._music_track() == "veil"
    h.run(h.seconds(3.5))
    h.shot("veil_shift_card")

    # VEIL SHIFTS: every effect.
    effects = {}
    for shift in SHIFTS:
        game.roll_shift(shift)
        effects[shift.id] = (game.spawner.speed_scale, game.minion_rate, game.kits_allowed,
                             game.shift_coins, game.elite_chance(), game.glass,
                             game.overlay is not None)
    base = game.level.difficulty.elite_chance
    assert effects["ROCKS FAST"][0] == SHIFT_ROCK_SPEED and effects["DOUBLE MINIONS"][1] == 2
    assert effects["NO KITS"][2] is False and effects["NO KITS"][3] == 2
    assert effects["ELITE SQUAD"][4] == base * 3 and effects["GLASS CANNON"][5] == SHIFT_GLASS
    assert effects["BLIND SPOTS"][6] and game.shift_payout(100) == round(100 * SHIFT_BONUS)
    game.roll_shift(BY_SHIFT["GLASS CANNON"])
    ship = game.ship
    ship.invulnerable_time, game.shield, hp0 = 0, 0, ship.hp
    game.hurt_ship(10, ship.x, ship.y)
    assert abs((hp0 - ship.hp) - 10 * SHIFT_GLASS) < 1e-6
    game.roll_shift(BY_SHIFT["BLIND SPOTS"])
    h.run(5)
    h.shot("blind_spots")
    game.roll_shift(BY_SHIFT["ROCKS FAST"])
    # 50% repair before a galaxy 2 boss (galaxy 1: full).
    ship.hp = ship.max_hp * 0.1
    game._begin_warning()
    assert abs(ship.hp - ship.max_hp * 0.6) < 1
    game.set_phase(Phase.FIELD)

    # ELITES: x3 hull, the golden shell shrugs off one hit, faster.
    wisp = Wisp(160, 60)
    hp = wisp.hp
    wisp.make_elite()
    assert wisp.elite and wisp.hp == hp * ELITE_HP
    wisp.damage(5)
    assert wisp.hp == hp * ELITE_HP, "the first hit bounces"
    wisp.damage(5)
    assert wisp.hp == hp * ELITE_HP - 5
    # WISP: steps out of a shot lined up on it.
    game.enemies = [wisp]
    game.enemy_bullets.clear()
    ship.x, ship.y = 160, 200
    h.run(12, clear_rocks=True)
    assert abs(wisp.x - 160) > 8, "the wisp dodged"
    h.shot("elite_wisp")
    game.enemies.clear()

    # The Veil's bullets (no minions around to add their own).
    game.extra_timers = [99.0] * len(game.extra_timers)
    game.enemies.clear()
    game.enemy_bullets = [SplitterBullet(100, 40, 0, 30, 5)]
    ship.x, ship.y = 300, 220
    h.run(h.seconds(SPLIT_TIME + 0.1), clear_rocks=True)
    assert sum(type(b) is VeilBullet for b in game.enemy_bullets) == 3, "burst into three"
    game.hazard.rifts.clear()                            # (a rift would carry it off)
    game.hazard.timer = 99.0
    boom = Boomerang(160, 40, 0, 120, 5)
    game.enemy_bullets = [boom]
    h.run(h.seconds(BOOMERANG_TIME * 0.5), clear_rocks=True)
    far = boom.y
    h.run(h.seconds(BOOMERANG_TIME * 0.5), clear_rocks=True)
    assert far > 80 and abs(boom.y - 40) < 12, "it comes back"
    rune = RuneMark(ship.x, ship.y, 50)
    game.enemy_bullets = [rune]
    ship.invulnerable_time, hp0 = 0, ship.hp
    h.run(h.seconds(RUNE_TIME * 0.5), clear_rocks=True)
    assert ship.hp == hp0, "a rune mark can't hurt"
    h.shot("rune")
    ship.x = 40
    h.run(h.seconds(RUNE_TIME * 0.6), clear_rocks=True)
    assert sum(type(b) is VeilBullet for b in game.enemy_bullets) == RUNE_SHOTS
    pair = twinned(160, 60, math.pi / 2, 40, 5)
    for _ in range(10):
        for b in pair:
            b.update(0.05)
    assert abs(math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y) - 2 * TwinBullet.RADIUS) < 1
    game.enemy_bullets.clear()

    # RIFTS carry rocks, enemy bullets and your shots through.
    rifts = game.hazard
    rifts.rifts.clear()
    rifts.jumps = 0
    rifts.recent.clear()
    a, b = rifts.open_pair()
    for r in (a, b):
        r.age = RIFT_OPEN + 0.1
    rifts.timer = 99
    rock = h.rock_ahead(5)
    rock.x, rock.y, rock.vx, rock.vy = a.x, a.y, 0, 0
    game.asteroids = [rock]
    shot = GunBullet(a.x + 2, a.y, 0, 0)
    game.weapons[0].bullets = [shot]
    game.enemy_bullets = [bullet(a.x - 2, a.y, 0, 0, 0)]
    rifts.update(1 / 60, game)
    assert math.hypot(rock.x - b.x, rock.y - b.y) < RIFT_RADIUS + 2
    assert math.hypot(shot.x - b.x, shot.y - b.y) < RIFT_RADIUS + 2 and rifts.jumps == 3, (
        rifts.jumps, shot.x, shot.y, b.x, b.y, a.x, a.y)
    h.run(2)
    h.shot("rifts")
    game.enemy_bullets.clear()
    game.asteroids.clear()

    # AMBUSH: the Warden arrives mid-field without WARNING or repair; the rocks keep falling.
    game.start(index, 0, 1)
    game.radio = None
    game.god = True
    ship = game.ship
    phases = set()
    for _ in range(h.seconds(40)):
        h.run(1)
        phases.add(game.phase)
        if game.phase == Phase.BOSS:
            break
    assert Phase.WARNING not in phases and game.phase == Phase.BOSS
    assert game.distance < game.wave.length and game.radio.speaker == UNKNOWN
    boss = game.boss
    assert isinstance(boss, Warden) and game._music_track() == "warden"
    h.run(h.seconds(Warden.ENTER_TIME + 0.2))
    assert boss.fighting and game.asteroids, "the field goes on"
    h.shot("warden_ambush")
    # Rings block; only the core takes damage.
    outer = boss.outer
    assert outer in boss.parts() and boss.inner not in boss.parts()
    hp = boss.hp
    boss.hit_part(outer, 100)
    assert abs((hp - boss.hp) - 100 * Warden.RING_PASS) < 1e-6, "the ring takes most of it"
    hp = boss.hp
    boss.hit_part(boss, 100)
    assert abs((hp - boss.hp) - 100) < 1e-6, "through the gap: full damage"
    # It read you: you keep to the left, so the gap turns to the right side.
    game.player_model = PlayerModel()
    game.player_model.observe(60, 30, 200, 0, 0, False)
    for _ in range(h.seconds(3)):
        h.run(1, clear_rocks=True)
    off = (outer.angle - (math.pi / 2 - 0.8) + math.pi) % math.tau - math.pi
    assert abs(off) < 0.5, f"gap turned away from your side ({outer.angle:.2f})"
    game.load_brain()
    boss.roar = 0
    game._damage_boss(Hit(boss, boss.max_hp * 0.26, 0, 0, 0, -1, 0))
    assert boss.phase == 1 and boss.inner in boss.parts()
    h.run(h.seconds(BOSS_ROAR_TIME + 2), clear_rocks=True)
    h.shot("warden_two_rings")
    for _ in range(2):
        boss.roar = 0
        game._damage_boss(Hit(boss, boss.max_hp * 0.26, 0, 0, 0, -1, 0))
    assert boss.phase == 3 and boss.saw
    h.run(h.seconds(BOSS_ROAR_TIME + 2), clear_rocks=True)
    assert math.hypot(outer.x - boss.x, outer.y - boss.y) > 10, "the ring saws loose"
    assert boss.contact_damage > boss.bullet_damage
    h.shot("warden_saw")
    # The learning: its bandit gets rewarded by the damage it deals.
    game.god = False
    game.ship.hp = 10 ** 6
    game.ship.invulnerable_time, game.shield = 0, 0
    before = boss.attack if boss.attack != "rest" else None
    boss.begin_attack(game, boss.OPTIONS[boss.phase])       # (start a slot of our own)
    slot = boss._attack
    boss.learn_tick(1.0)
    game.hurt_ship(30, game.ship.x, game.ship.y)             # it hit you during that slot
    boss.begin_attack(game, boss.OPTIONS[boss.phase])
    assert game.bandit_for("THE WARDEN").arms[slot][1] > 0, (before, slot)
    game.god = True
    boss.roar = 0
    h.kill(boss)
    for _ in range(h.seconds(10)):
        h.run(1, clear_rocks=True)
        if game.state == State.LEVEL_CLEAR:
            break
    game.god = False
    assert game.state == State.LEVEL_CLEAR and "THE WARDEN" in game.save.bosses
    h.run(h.seconds(1.2))
    h.shot("veil_clear")
    game.save.gifts = [k for k in game.save.gifts if k != "2-1"]
    if "VEIL" in game.save.owned:
        game.save.owned.remove("VEIL")
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["VEIL"]
    h.run(h.seconds(0.6))
    h.post(pygame.K_RETURN)
    assert game.state == State.HANGAR and game.next_launch[0] == 11, game.state
    h.post(pygame.K_ESCAPE)                              # the hangar backs out to the Veil's map
    assert game.state == State.STAR_MAP and game.star_map.gmap.galaxy == 2, (
        game.state, getattr(game, "star_map", None) and game.star_map.gmap.galaxy)
    game.save.skins = {}
    game.choose_hull(ARROW)
    # Warp gates between the maps.
    game.star_map.place_at_gate()
    h.post(pygame.K_RETURN)
    assert game.state == State.STAR_MAP and game.star_map.gmap.galaxy == 1
    h.run(5)
    game.save.medals = [1]
    game.open_star_map(0)
    game.star_map.place_at_gate()
    h.post(pygame.K_RETURN)
    assert game.star_map.gmap.galaxy == 2 and game.star_map.near_node() is None
    game.star_map.place_at(0)
    h.run(5)
    h.shot("veil_map")
    h.post(pygame.K_RETURN)
    assert game.state in (State.HANGAR, State.REWARD) and game.start_level == index
    game.start_level = 0
    game.to_title()


def test_save(h):
    """Records, unlocks and the ship survive a reload; a corrupt file doesn't crash."""
    game = h.game
    game.save.add_record(4321, 2)
    game.save.unlock(3)
    game.choose_hull(TITAN)
    reloaded = SaveData(h.save_path)
    assert reloaded.records == game.save.records and reloaded.unlocked == game.save.unlocked >= 3
    assert reloaded.best == game.save.best > 0 and reloaded.ship == "TITAN"
    with open(h.save_path, "w") as f:
        f.write("{not json")
    fresh = SaveData(h.save_path)
    assert fresh.records == [] and fresh.unlocked == 1 and fresh.ship == "ARROW"
    game.save.save()                                     # restore it for the checks below
    game.choose_hull(ARROW)


def test_economy(h):
    """Coins are pending until a level is won; rank and payout; save file v2 + migration."""
    game = h.game
    # Rank: a clean fast run is S, a battered slow one C; the better rank is kept.
    stats = LevelStats(max_hp=100)
    stats.destroyed, stats.escaped, stats.boss_time, stats.boss_par = 60, 40, 30, 40
    assert stats.rank() == "S", stats.ratings()
    stats.damage_taken, stats.boss_time, stats.destroyed = 160, 120, 10
    assert stats.rank() == "C", stats.ratings()
    assert better_rank("B", "A") == "A" and better_rank(None, "C") == "C"
    # Payout: first clear gets the bonus, a replay pays half.
    first = level_payout(40, 2, "A", first_clear=True)
    replay = level_payout(40, 2, "A", first_clear=False)
    assert first.clear_bonus == 150 and first.total == 40 + 150 + 100
    assert replay.replay and replay.total == round((40 + 150) * 0.5)

    # A version 1 save file loads with an empty bank and keeps records / unlocks / ship.
    with open(h.save_path, "w") as f:
        json.dump({"records": [{"score": 900, "level": 2, "date": "2026-01-01"}],
                   "unlocked": 3, "ship": "WASP"}, f)
    old = SaveData(h.save_path)
    assert old.unlocked == 3 and old.ship == "WASP" and old.best == 900
    assert old.coins == 0 and old.cleared == {}
    with open(h.save_path, "w") as f:
        json.dump({"version": 2, "coins": "lots", "cleared": {"1-1": "A"}}, f)
    assert SaveData(h.save_path).coins == 0, "a broken value falls back to a fresh save"
    fresh = SaveData(h.save_path)
    fresh._reset()
    fresh.save()
    game.load_profile(SaveData(h.save_path))

    # Coins picked up in a level are pending; death loses them, the bank stays.
    game.choose_hull(ARROW)
    game.start(0)
    assert game.pending_coins == 0 and game.save.coins == 0
    game.pickups = [Coin(game.ship.x, game.ship.y), BigCoin(game.ship.x, game.ship.y)]
    h.run(2, clear_rocks=True)
    assert game.pending_coins == 6 and game.save.coins == 0, game.pending_coins
    rock = h.rock_ahead(12)
    game.asteroids = [rock]
    game._damage_rock(Hit(rock, 10 ** 6, rock.x, rock.y, 0, -1, 0))
    assert game.stats.destroyed == 1
    game.ship.hp, game.ship.invulnerable_time = 100, 0
    game.hurt_ship(30, 0, 0)
    assert game.stats.damage_taken == 30
    h.run(20, clear_rocks=True)
    h.shot("coins_hud")
    h.die()
    assert game.state == State.GAME_OVER and game.save.coins == 0
    h.shot("coins_lost")
    h.post(pygame.K_r)
    assert game.pending_coins == 0, "a retry starts without the lost coins"

    # Winning the level banks pending coins + boss coins (collected even if still flying)
    # + clear bonus, keeps the rank, and shows the results screen.
    game.start(0, 0, 0, 0)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    assert game.boss and game.boss.fighting
    game.collect_coins(10)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state == State.LEVEL_CLEAR, game.state
    payout = game.payout
    assert payout.pending >= 10 + 30 // 2 and not payout.replay and payout.first_clear
    assert game.level_rank in RANKS and game.save.cleared == {"1-1": game.level_rank}
    assert game.save.coins == payout.total and SaveData(h.save_path).coins == payout.total
    assert game.stats.boss_par == game.boss.spec.fight_time and game.stats.boss_time > 0
    h.run(h.seconds(1.3))
    h.shot("results_rank")
    h.run(h.seconds(3.0))
    assert game.tally() == payout.total
    h.shot("results")
    bank = game.save.coins
    game.start(0, 0, 0, 0)                               # a replay pays half
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD + 1.7), clear_rocks=True)
    assert game.state == State.LEVEL_CLEAR and game.payout.replay
    assert game.save.coins == bank + game.payout.total
    game.save._reset()
    game.save.save()
    game.load_profile(SaveData(h.save_path))
    game.inventory.grant_all()
    game.to_title()


def test_inventory(h):
    """A new player owns ARROW + gun; gifts (1 of 2, the other goes to the shop); the hangar
    equips, buys and launches; old saves get the gifts of the levels they cleared."""
    game = h.game
    fresh = SaveData(h.save_path)
    fresh._reset()
    fresh.save()
    game.load_profile(SaveData(h.save_path))
    inv = game.inventory
    assert game.save.owned == list(STARTER) and inv.status("LASER") == "LOCKED"
    game.choose_hull(ARROW)
    game.start(2)                                        # no BLAST / ULT / laser yet
    assert not game.ship.loadout.blast and not game.ship.loadout.ultimate
    game.switch_weapon()
    assert game.weapon.name == "GUN", "R does nothing with only the gun"

    # Level 1 won -> gift: choose WASP, LASER goes to the shop -> hangar on the WASP.
    game.start(0, 0, 0, 0)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD + 1.7 + 1.2), clear_rocks=True)
    assert game.state == State.LEVEL_CLEAR
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["LASER", "WASP"]
    h.run(h.seconds(0.6))
    h.post(pygame.K_RIGHT)
    h.run(10)
    h.shot("gift")
    h.post(pygame.K_RETURN)
    assert game.state == State.HANGAR and inv.owns("WASP") and game.hull is WASP
    assert inv.status("LASER") == "SHOP" and game.save.gifts == ["1-1"]
    assert game.hangar_item.id == "WASP" and game.next_launch[0] == 1
    h.run(10)
    h.shot("hangar_new_ship")
    assert not inv.gift_options("1-1"), "a gift is given once"

    # Shop: ENTER asks, ENTER buys; not enough credits is refused; locked says how to unlock.
    h.post(pygame.K_RIGHT)                               # WEAPONS tab
    while game.hangar_item.id != "LASER":
        h.post(pygame.K_DOWN)
    coins = game.save.coins
    game.save.coins = 10
    h.post(pygame.K_RETURN)
    h.post(pygame.K_RETURN)
    assert not inv.owns("LASER") and game.hangar_message[0] == "NOT ENOUGH CREDITS"
    game.save.coins = coins
    assert coins >= 200, coins
    h.post(pygame.K_RETURN)
    assert game.hangar_confirm == "LASER" and not inv.owns("LASER")
    h.run(10)
    h.shot("hangar_buy")
    h.post(pygame.K_RETURN)
    assert inv.owns("LASER") and game.save.coins == coins - 200
    assert SaveData(h.save_path).owned == game.save.owned, "purchases are saved"
    h.post(pygame.K_LEFT)
    while game.hangar_item.id != "TITAN":
        h.post(pygame.K_DOWN)
    h.post(pygame.K_RETURN)
    assert game.hull is WASP and "LEVEL 3" in game.hangar_message[0]
    h.run(10)
    h.shot("hangar_locked")

    # SPACE launches level 2 with the WASP; the laser switches in now.
    score = game.score
    h.post(pygame.K_SPACE)
    assert game.state == State.PLAYING and game.level.number == 2 and game.score == score
    assert game.ship.hull is WASP
    game.switch_weapon()
    assert game.weapon.name == "LASER"

    # Level 2 won -> the fixed gift BLAST + ULTIMATE.
    game.start(1, 0, 0, 1)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD + 1.7 + 1.2), clear_rocks=True)
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and len(game.gift_options) == 1
    h.run(h.seconds(0.6))
    h.post(pygame.K_RETURN)
    assert inv.owns("SPECIALS") and game.loadout_for(LEVELS[2]).blast

    # An older save (no inventory) that reached level 3 gets the gifts of levels 1 and 2.
    with open(h.save_path, "w") as f:
        json.dump({"version": 2, "unlocked": 3, "ship": "WASP", "coins": 70}, f)
    game.load_profile(SaveData(h.save_path))
    inv = game.inventory
    assert all(inv.owns(i) for i in ("ARROW", "GUN", "LASER", "WASP", "SPECIALS"))
    assert inv.status("TITAN") == "LOCKED" and game.save.gifts == ["1-1", "1-2"]
    assert SaveData(h.save_path).owned is not None, "the rebuilt inventory is saved"
    game.save._reset()
    game.save.save()
    game.load_profile(SaveData(h.save_path))
    game.inventory.grant_all()
    game.choose_hull(ARROW)
    game.to_title()


def test_upgrades(h):
    """5 tracks x 5 tiers: prices, what each tier adds, the hangar's UPGRADES tab (ask, buy,
    refused, maxed), saved tiers, bosses still balanced on par, and the cap: a maxed build
    still faces a 5x boss as >= 3.5x."""
    assert [upgrades.cost(t) for t in range(UPGRADE_TIERS + 1)] == [*UPGRADE_COSTS, None]
    maxed = {t: GALAXY1_TIERS for t in upgrades.TRACK_IDS}          # galaxy 1 caps at tier 5
    full = {t: UPGRADE_TIERS for t in upgrades.TRACK_IDS}
    assert abs(upgrades.power_ratio({}) - 1) < 1e-9
    assert abs(upgrades.power_ratio(maxed) - 1.3225) < 1e-6, upgrades.power_ratio(maxed)
    assert abs(upgrades.power_ratio(full) - 1.69) < 1e-6, upgrades.power_ratio(full)
    assert abs(upgrades.power_ratio({"LASER": 5}) - upgrades.power_ratio({"GUNS": 5})) < 1e-9
    assert abs(upgrades.power_ratio({"GUNS": 5, "LASER": 5}) - 1.15) < 1e-9, "weapons don't stack"
    up = upgrades.apply(MK4, maxed)
    assert up.max_hp == round(MK4.max_hp * 1.15) and abs(up.gun_damage - MK4.gun_damage * 1.15) < 1e-9
    assert abs(up.laser_dps - MK4.laser_dps * 1.15) < 1e-9
    assert abs(up.max_speed - MK4.max_speed * 1.2) < 1e-9 and abs(up.charge_rate - 1.5) < 1e-9
    assert upgrades.apply(MK4, {}) == MK4

    # The cap: every boss in a damage race against a maxed build, with every hull
    # (galaxy 1 counts 5 tiers; galaxy 2 all 10, and its bosses are built stronger).
    for level in LEVELS:
        g1 = galaxy_of(level).number == 1
        tiers, edge = (maxed, 1.33) if g1 else (full, 1.7)
        for spec in (e.spec for wave in level.waves for e in wave.bosses):
            for hull in HULLS:
                ship = upgrades.apply(hull.apply(spec.player), tiers)
                ratio = (spec.hp / ship.gun_dps) / (ship.max_hp / spec.dps)
                assert ratio >= spec.strength / edge, (spec.name, hull.name, ratio)
                if spec.strength >= 5:
                    assert ratio >= 3.5, (spec.name, hull.name, ratio)

    # Hangar: a new player (0 tiers) with 300 CR.
    game = h.game
    game.save.upgrades = {}
    game.save.coins = 300
    game.choose_hull(ARROW)
    game.open_hangar(2)
    h.post(pygame.K_LEFT)                                # SHIPS wraps round to SKINS ...
    h.post(pygame.K_LEFT)                                # ... then UPGRADES
    assert game.hangar_tab == UPGRADE and game.hangar_track.id == "ARMOR"
    assert game.hangar_view().power == 1.0
    h.post(pygame.K_RETURN)
    assert game.hangar_confirm == "ARMOR" and game.inventory.tier("ARMOR") == 0
    assert "100 CR" in game.hangar_message[0]
    h.run(10)
    h.shot("hangar_upgrades")
    h.post(pygame.K_RETURN)
    assert game.inventory.tier("ARMOR") == 1 and game.save.coins == 200
    assert SaveData(h.save_path).upgrades == {"ARMOR": 1}, "tiers are saved"
    h.post(pygame.K_RETURN)
    h.post(pygame.K_RETURN)                              # tier 2 = 200 CR: exactly enough
    assert game.inventory.tier("ARMOR") == 2 and game.save.coins == 0
    h.post(pygame.K_RETURN)
    h.post(pygame.K_RETURN)
    assert game.inventory.tier("ARMOR") == 2 and game.hangar_message[0] == "NOT ENOUGH CREDITS"
    h.post(pygame.K_DOWN)
    assert game.hangar_track.id == "GUNS" and game.hangar_confirm is None
    game.save.upgrades["CHARGE"] = UPGRADE_TIERS
    for _ in range(3):
        h.post(pygame.K_DOWN)
    h.post(pygame.K_RETURN)
    assert "MAXED" in game.hangar_message[0] and game.inventory.tier("CHARGE") == UPGRADE_TIERS
    h.run(10)
    h.shot("hangar_upgrades_maxed")
    assert abs(game.hangar_view().power - 1.06) < 1e-9
    for tab_steps in range(3):                           # every tab still draws
        h.post(pygame.K_RIGHT)
        h.run(2)

    # In the level: the ship flies the upgraded model, the boss keeps its par balance.
    h.post(pygame.K_SPACE)
    assert game.state == State.PLAYING and game.level.number == 3
    assert game.ship.max_hp == round(MK3.max_hp * 1.06), game.ship.max_hp
    assert game.ship.loadout.charge_rate == 1.5
    game.start(2, 0, 2, 0)
    h.run(h.seconds(WARNING_TIME + 0.2), clear_rocks=True)
    assert game.boss.max_hp == LEVELS[2].waves[2].bosses[0].spec.hp, "bosses use par, not upgrades"
    game.blast.charge = game.ultimate.charge = 0.0
    game._charge(700, killed=False)                      # 0.5 blast at x1, x1.5 with CHARGE 5
    assert abs(game.blast.charge - 0.75) < 1e-9, game.blast.charge

    # Old saves without upgrades load with 0 tiers; broken tiers are clamped.
    with open(h.save_path, "w") as f:
        json.dump({"version": 2, "unlocked": 2, "coins": 5}, f)
    assert SaveData(h.save_path).upgrades == {}
    with open(h.save_path, "w") as f:
        json.dump({"version": 2, "upgrades": {"ARMOR": 19, "GUNS": -2}}, f)
    assert SaveData(h.save_path).upgrades == {"ARMOR": UPGRADE_TIERS, "GUNS": 0}
    game.save._reset()
    game.save.save()
    game.load_profile(SaveData(h.save_path))
    game.inventory.grant_all()
    game.choose_hull(ARROW)
    game.to_title()


def test_feel(h):
    """G4 game feel: hit-stop freezes the world, slow-mo after large events, boss damage
    numbers, radio cards (ENTER skips), boss name cards, options in the pause menu."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(0)
    assert game.radio and game.radio.lines == LEVELS[0].radio, "level 1 opens with a radio card"
    h.run(h.seconds(3.5))
    h.shot("radio")
    h.post(pygame.K_RETURN)
    assert game.radio and game.radio.typed >= game.radio.chars, "ENTER finishes the typing"
    h.post(pygame.K_RETURN)
    assert game.radio is None, "ENTER again closes the card"

    # Juice: a medium event freezes the world for a moment, a large one slows it down.
    game.juice("medium", game.ship.x, game.ship.y)
    assert game.hitstop > 0 and game.world_dt(h.dt) == 0.0
    game.hitstop = 0.0
    game.juice("large", game.ship.x, game.ship.y)
    game.hitstop = 0.0
    assert 0 < game.world_dt(h.dt) < h.dt, "slow-mo after a large event"
    game.slowmo = 0.0

    # Boss: WARNING shows the name card, hits pop damage numbers.
    game.start(0, 0, 0, 0)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(1.0), clear_rocks=True)
    h.shot("name_card")
    h.run(h.seconds(WARNING_TIME + 2.0), clear_rocks=True)
    assert game.boss.fighting
    game.popups.clear()
    for _ in range(40):
        game.ship.x = game.boss.x
        game.update(h.dt, FIRE)
    assert any(isinstance(p, DamageNumber) for p in game.popups), "boss hits show numbers"
    h.shot("damage_numbers")

    # Options: P pauses; DOWN picks SOUND, LEFT lowers it (saved); shake can be reduced.
    h.post(pygame.K_p)
    assert game.state == State.PAUSED
    h.post(pygame.K_DOWN)
    sound = game.options["sound"]
    h.post(pygame.K_LEFT)
    assert game.options["sound"] == sound - 1 and game.audio.sound_volume == (sound - 1) / 10
    assert SaveData(h.save_path).options["sound"] == sound - 1, "options are saved"
    h.post(pygame.K_DOWN)
    h.post(pygame.K_RIGHT)
    assert game.options["shake"] == 0 and game.shake.scale < 1
    h.run(2)
    h.shot("pause_options")
    h.post(pygame.K_DOWN)
    h.post(pygame.K_RIGHT)
    assert game.options["flashes"] == 0
    game.flash = 0.0
    game.screen_flash(0.1)
    assert game.flash < 0.1, "reduced flashes"
    for key in ("shake", "flashes"):                    # back to full for the other sections
        game.options.change(key, 1)
    game.options.change("sound", 1)
    game.apply_options()
    h.post(pygame.K_p)
    assert game.state == State.PLAYING
    game.to_title()


def test_boosts(h):
    """G5: boost pickups (OVERDRIVE, SHIELD, MAGNET, SLOW-MO), drops, and the combo / FEVER."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(0)
    game.radio = None
    game.ship.hp = 10 ** 6

    # OVERDRIVE: the gun fires twice as often.
    def shots(frames):
        gun = game.weapons[0]
        before = gun.shots
        h.run(frames, FIRE, clear_rocks=True)
        return gun.shots - before
    normal = shots(60)
    game.pickups.append(Overdrive(game.ship.x, game.ship.y))
    h.run(2, clear_rocks=True)
    assert game.boost_left("OVERDRIVE") > 0 and game.ship.overdrive
    boosted = shots(60)
    assert boosted >= normal * 1.5, (normal, boosted)      # cooldowns are whole frames
    h.shot("overdrive")
    game.boosts.clear()

    # SHIELD: absorbs 3 hits, the 4th hurts.
    game.pickups.append(Shield(game.ship.x, game.ship.y))
    h.run(2, clear_rocks=True)
    assert game.shield == SHIELD_HITS
    h.shot("shield")
    hp = game.ship.hp
    for _ in range(SHIELD_HITS):
        game.ship.invulnerable_time = 0
        game.hurt_ship(20, game.ship.x, game.ship.y - 10)
    assert game.ship.hp == hp and game.shield == 0, "the bubble took every hit"
    game.ship.invulnerable_time = 0
    game.hurt_ship(20, game.ship.x, game.ship.y - 10)
    assert game.ship.hp == hp - 20

    # MAGNET: a coin at the far side of the screen flies in.
    game.ship.invulnerable_time = 0
    coin = Coin(10, 30, 0, 0)
    game.pickups.append(coin)
    game.start_boost("MAGNET")
    h.run(h.seconds(3.0), clear_rocks=True)
    assert coin.collected or coin not in game.pickups, "magnet pulled the coin in"
    game.boosts.clear()

    # SLOW-MO: rocks fall at half speed, the ship doesn't slow down.
    rock = h.rock_ahead(8, dist=120)
    rock.vx, rock.vy = 0, 60
    game.asteroids = [rock]
    y0 = rock.y
    h.run(30)
    normal = rock.y - y0
    game.start_boost("SLOW-MO")
    y0 = rock.y
    h.run(30)
    assert abs((rock.y - y0) - normal / 2) < normal * 0.15, (normal, rock.y - y0)
    game.boosts.clear()
    game.asteroids.clear()

    # Drops: the field drops boosts; a new player doesn't get OVERDRIVE before owning it.
    game.boost_timer = 0.0
    h.run(2, clear_rocks=True)
    assert any(isinstance(p, Boost) for p in game.pickups), "a boost dropped"
    game.inventory.save.owned.remove("OVERDRIVE")
    assert "OVERDRIVE" not in game.boost_pool()
    game.inventory.save.owned.append("OVERDRIVE")

    # Combo: kills in quick succession multiply the score; a hit ends the combo.
    game.pickups.clear()
    game.break_combo()
    score = game.score
    for _ in range(COMBO_STEP):
        game.add_kill(100, 100, 100)
    assert game.combo_mult == 2
    assert game.add_kill(100, 100, 100) == 200, "x2 after COMBO_STEP kills"
    game.ship.invulnerable_time = 0
    game.hurt_ship(1, game.ship.x, game.ship.y - 10)
    assert game.combo == 0 and game.combo_mult == 1
    for i in range(FEVER_AT):
        game.add_kill(10, 100, 100)
    assert game.fever > 0 and game.overdrive, "FEVER at combo 25"
    assert game.combo_mult == COMBO_MAX and game.coin_mult == COMBO_COIN_CAP
    h.run(10, clear_rocks=True)
    h.shot("fever")
    h.run(h.seconds(COMBO_WINDOW + 0.1), clear_rocks=True)
    assert game.combo == 0, "the combo runs out"
    assert game.score >= score
    game.to_title()


def test_wingmen(h):
    """G6: wingmen fly beside the ship, act by type, get knocked out (never destroyed), earn
    XP; hangar WINGMEN tab (equip, train), the level 4 gift, MAGPIE in the shop, balance."""
    game = h.game
    game.save.wingmen_xp = {}
    game.save.coins = 1000
    game.choose_hull(ARROW)
    game.open_hangar(0)
    h.post(pygame.K_RIGHT)
    h.post(pygame.K_RIGHT)                               # SHIPS -> WEAPONS -> WINGMEN
    assert game.hangar_tab == WINGMAN and game.hangar_item.id == "PIP"
    h.post(pygame.K_RETURN)
    assert game.save.wingman == "PIP"
    h.run(5)
    h.shot("hangar_wingmen")
    h.post(pygame.K_RETURN)                              # equipped: ENTER offers TRAIN
    assert game.hangar_confirm == "PIP"
    h.post(pygame.K_RETURN)
    assert game.wingman_xp("PIP") == WINGMAN_TRAIN_XP and game.save.coins == 1000 - WINGMAN_TRAIN_COST
    assert game.wingman_level("PIP") == 2

    # PIP flies beside the ship and fires with it; its kills give extra XP.
    h.post(pygame.K_SPACE)
    game.radio = None
    game.ship.hp = 10 ** 6
    pip = game.wingman
    assert isinstance(pip, Pip) and pip.level == 2
    h.run(20, clear_rocks=True)
    assert abs(pip.x - (game.ship.x - game.ship.w / 2 - 9)) < 3, "flies on the left"
    rock = h.rock_ahead(8, dist=60)
    rock.x = pip.x
    rock.art = game.library.pick(8, 8, h.field.palettes)
    game.asteroids = [rock]
    hp = rock.hp
    for _ in range(60):
        rock.vy = rock.vx = 0
        game.update(h.dt, FIRE)
    assert rock.hp < hp, "PIP's bolts hit the rock beside the ship"
    h.shot("wingman_pip")
    xp = game.wingman_xp_gain
    game.wingman_kill()
    game.wingman_kill(source=pip)
    assert game.wingman_xp_gain == xp + 2 * WINGMAN_XP_KILL + WINGMAN_XP_OWN

    # Knocked out by a bullet, reboots later; never removed.
    game.asteroids.clear()
    game.enemy_bullets.append(EnemyBullet(pip.x, pip.y, 0, 0, 5))
    h.run(1)
    assert not pip.flying and pip in game.wingmen
    h.run(h.seconds(WINGMAN_KO_TIME + 0.2), clear_rocks=True)
    assert pip.flying, "rebooted"

    # XP is banked when the level ends (here: game over).
    gain = game.wingman_xp_gain
    xp_before = game.wingman_xp("PIP")
    h.die()
    assert game.wingman_xp("PIP") == xp_before + gain

    # GUARDIAN: blocks a bullet, then needs to recharge; level 5 reflects it.
    game.save.choose_wingman("GUARDIAN")
    game.save.wingmen_xp["GUARDIAN"] = WINGMAN_XP[-1]
    game.start(0)
    game.ship.hp = 10 ** 6
    guard = game.wingman
    assert isinstance(guard, Guardian) and guard.level == 5
    h.run(10, clear_rocks=True)
    game.enemy_bullets.append(EnemyBullet(guard.x, guard.y, 0, 0, 5))
    h.run(1, clear_rocks=True)
    assert not game.enemy_bullets and not guard.ready and guard.bolts.shots, "blocked + reflected"
    h.shot("wingman_guardian")

    # MEDIC: repairs after 3 s without damage; level 5 revives once.
    game.save.choose_wingman("MEDIC")
    game.save.wingmen_xp["MEDIC"] = WINGMAN_XP[-1]
    game.start(0)
    medic = game.wingman
    game.ship.hp = 50
    game.last_hurt = game.time
    h.run(h.seconds(MEDIC_DELAY + 1.0), clear_rocks=True)
    assert game.ship.hp > 50, "repaired"
    game.ship.hp = 1
    game.ship.invulnerable_time = 0
    game.hurt_ship(50, game.ship.x, game.ship.y - 10)
    assert game.ship.alive and game.state == State.PLAYING and medic.revived
    assert game.ship.hp == int(game.ship.max_hp * MEDIC_REVIVE)

    # HUNTER: rockets at a drone.
    game.save.choose_wingman("HUNTER")
    game.start(1)
    game.ship.hp = 10 ** 6
    game.radio = None
    hunter = game.wingman
    game.enemies = drone_formation()[:1]
    game.enemies[0].x, game.enemies[0].y = game.ship.x, 60
    hunter.timer = 0
    h.run(3, clear_rocks=True)
    assert hunter.swarm.rockets, "rockets launched at the drone"

    # MAGPIE: pickups fly in from further away; sold in the shop after level 4.
    game.save.choose_wingman("MAGPIE")
    game.start(0)
    assert game.wingman.radius >= 60
    h.run(3, clear_rocks=True)
    coin = Coin(game.ship.x + 50, game.ship.y, 0, 0)
    game.pickups = [coin]
    h.run(h.seconds(1.5), clear_rocks=True)
    assert coin not in game.pickups

    # TWIN boost: a copy of the ship on the other side for a while.
    game.start_boost("TWIN")
    assert any(isinstance(w, Twin) for w in game.wingmen)
    h.run(10, FIRE, clear_rocks=True)
    h.shot("wingman_twin")
    game.boosts["TWIN"] = 0.01
    h.run(2, clear_rocks=True)
    assert not any(isinstance(w, Twin) for w in game.wingmen)

    # Balance: maxed upgrades + a level 5 PIP still face a 5x boss as >= 3.5x (galaxy 1,
    # 5 tiers) and a galaxy 2 boss as >= 3.2x (all 10 tiers).
    for level in LEVELS:
        g1 = galaxy_of(level).number == 1
        maxed = {t: GALAXY1_TIERS if g1 else UPGRADE_TIERS for t in upgrades.TRACK_IDS}
        for spec in (e.spec for wave in level.waves for e in wave.bosses if e.spec.strength >= 5):
            for hull in HULLS:
                ship = upgrades.apply(hull.apply(spec.player), maxed)
                dps = ship.gun_dps * (1 + PIP_SHARE[-1])       # PIP fires a share of it
                ratio = (spec.hp / dps) / (ship.max_hp / spec.dps)
                assert ratio >= (3.5 if g1 else 3.2), (spec.name, hull.name, ratio)

    # The level 4 gift (PIP or GUARDIAN) after the win; MAGPIE in the shop; a cleared level
    # whose gift is missing (a save from before the update) gets it when the hangar opens.
    game.save.gifts = [k for k in game.save.gifts if k != "1-4"]
    game.save.owned = [i for i in game.save.owned if i not in ("PIP", "GUARDIAN", "MAGPIE")]
    game.save.wingman = None
    game.save.cleared.pop("1-4", None)
    assert game.inventory.status("MAGPIE") == LOCKED
    game.start(3, 0, 2, 0)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 0.5), clear_rocks=True)
    while not game.boss.fighting:                        # the Leviathan's entry is long
        h.run(10, clear_rocks=True)
    h.kill(game.boss)
    done = (State.WIN, State.LEVEL_CLEAR)
    for _ in range(h.seconds(10)):                    # the serpent dies plate by plate
        h.run(1, clear_rocks=True)
        if game.state in done:
            break
    assert game.state in done, game.state
    h.run(h.seconds(1.2))
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["PIP", "GUARDIAN"]
    h.run(h.seconds(0.6))
    h.shot("gift_wingman")
    h.post(pygame.K_RETURN)
    assert game.inventory.owns("PIP") and game.save.wingman == "PIP"
    assert game.state in (State.TITLE, State.DEV_MENU, State.HANGAR)
    assert game.inventory.status("GUARDIAN") == SHOP and game.inventory.status("MAGPIE") == SHOP
    game.save.gifts.remove("1-4")
    game.save.owned.remove("PIP")
    game.open_hangar(0)
    assert game.state == State.REWARD and game.gift_key == "1-4", "missing gift offered"
    game.state_time = 1.0
    h.post(pygame.K_RETURN)
    assert game.state == State.HANGAR
    game.inventory.grant_all()
    game.save.wingman = None
    game.save.wingmen_xp = {}
    game.to_title()


class Dummy:
    """A big round practice target for DPS measurements."""

    def __init__(self, x, y, radius=18):
        self.x, self.y, self.radius, self.bound = x, y, radius, radius

    def contains(self, px, py):
        return (px - self.x) ** 2 + (py - self.y) ** 2 < self.radius ** 2


def test_arsenal(h):
    """G7: SCATTER / PLASMA / ARC do about the gun's DPS (so BossSpec holds), plasma pierces
    but a boss stops it, the arc chains but never along a boss; secondaries fire on their own
    at rocks + minions and never hurt a boss; the hangar fills 2 primary slots + 1 secondary."""
    game = h.game
    game.choose_hull(ARROW)
    game.start(3)
    game.radio = None
    ship, fire = game.ship, game.fire
    weapons = {w.name: w for w in game.weapons}

    def dps(weapon, seconds=2.0):
        weapon.reset()
        dummy = Dummy(ship.x, ship.y - 50)
        total = 0.0
        for _ in range(h.seconds(seconds)):
            total += sum(hit.damage for hit in weapon.update(h.dt, True, ship, [dummy], fire))
        weapon.reset()
        return total / seconds
    gun = dps(weapons["GUN"])
    for name in ("SCATTER", "PLASMA", "ARC"):
        ratio = dps(weapons[name]) / gun
        assert 0.6 < ratio < 1.35, (name, ratio)

    # PLASMA pierces 3 rocks in a row; ARC jumps along a line of rocks.
    def rocks_ahead(n, gap):
        return [Dummy(ship.x, ship.y - 40 - i * gap, 5) for i in range(n)]
    plasma = weapons["PLASMA"]
    row = rocks_ahead(4, 22)
    hit = set()
    for _ in range(h.seconds(1.2)):
        hit |= {id(x.target) for x in plasma.update(h.dt, _ == 0, ship, row, fire)}
    assert len(hit) == PLASMA_PIERCE, len(hit)
    plasma.reset()
    arc = weapons["ARC"]
    row = rocks_ahead(5, 30)
    hits = arc.update(h.dt, True, ship, row, fire)
    assert len(hits) == 1 + ARC_JUMPS and hits[1].damage < hits[0].damage
    arc.reset()

    # Against the Leviathan's body: one orb = one hit, the arc doesn't chain along plates.
    game.start(3, 0, 2, 0)
    game.ship.hp = 10 ** 9
    h.run(h.seconds(WARNING_TIME + 0.5), clear_rocks=True)
    while not game.boss.fighting:
        h.run(10, clear_rocks=True)
    parts = game.boss.parts()
    hits = arc.update(h.dt, True, game.ship, parts, fire)
    assert len({id(x.target) for x in hits}) <= 1
    arc.reset()

    # Secondaries: fire by themselves at rocks, never hurt a boss.
    game.save.secondary = "ROCKET POD"
    game.enemy_bullets.clear()
    pod = game.secondary
    assert pod is game.secondaries["ROCKET POD"]
    hp = game.boss.hp
    pod.timer = 0
    h.run(h.seconds(1.0), clear_rocks=True)
    assert game.boss.hp == hp, "rockets never target the boss"
    game.start(0)
    game.radio = None
    game.ship.hp = 10 ** 6
    rock = h.rock_ahead(10, dist=80)
    rock.vx = rock.vy = 0
    game.asteroids = [rock]
    rock_hp = rock.hp
    pod.timer = 0
    for _ in range(h.seconds(2.0)):
        rock.vx = rock.vy = 0
        game.update(h.dt, Keys())
    assert pod.shots and (rock.hp < rock_hp or rock not in game.asteroids), "rockets hit"
    game.draw()
    h.shot("rocket_pod")
    game.save.secondary = "SIDE CANNONS"
    cannons = game.secondary
    game.enemies = drone_formation()[:1]
    drone = game.enemies[0]
    for _ in range(h.seconds(0.5)):
        drone.x, drone.y = game.ship.x + 60, game.ship.y
        drone.vx = drone.vy = 0
        game.update(h.dt, Keys())
    assert cannons.shots, "side cannons fire at a drone beside the ship"
    game.draw()
    h.shot("side_cannons")
    game.save.secondary = None

    # Hangar: SCATTER into slot 2, R switches GUN <-> SCATTER; secondary on / off.
    game.save.primaries = None
    game.open_hangar(0)
    h.post(pygame.K_RIGHT)                               # WEAPONS
    while game.hangar_item.id != "SCATTER":
        h.post(pygame.K_DOWN)
    h.run(3)
    h.shot("hangar_weapons_scroll")
    h.post(pygame.K_RETURN)
    assert game.primaries == ["GUN", "SCATTER"], game.primaries
    assert SaveData(h.save_path).primaries == ["GUN", "SCATTER"]
    while game.hangar_item.id != "SIDE CANNONS":
        h.post(pygame.K_DOWN)
    h.post(pygame.K_RETURN)
    assert game.save.secondary == "SIDE CANNONS"
    h.post(pygame.K_RETURN)
    assert game.save.secondary is None
    h.post(pygame.K_SPACE)
    assert game.weapon.name == "GUN"
    game.switch_weapon()
    assert game.weapon.name == "SCATTER"
    h.run(30, FIRE, clear_rocks=True)
    h.shot("scatter")
    game.save.primaries = ["PLASMA", "ARC"]
    game.start(0)
    game.radio = None
    assert game.weapon.name == "PLASMA"
    h.run(30, FIRE, clear_rocks=True)
    h.shot("plasma")
    game.switch_weapon()
    game.asteroids = [h.rock_ahead(10, dist=60)]
    h.run(20, FIRE)
    h.shot("arc")
    game.save.primaries = None
    game.to_title()


def test_skins(h):
    """G8: skins (paint, trail, tracers, beam, death style) are bought / earned / worn and
    change only looks; achievements unlock their skins once."""
    game = h.game
    inv = game.inventory
    game.save.achievements = []
    game.save.skins = {}
    for item_id in ("RETRO", "GOLD TRIM", "RAINBOW", "HEARTS", "NEON", "TOXIC", "SUPERNOVA"):
        game.save.owned.remove(item_id)
    game.save.cleared["1-1"] = "B"
    assert inv.status("RETRO") == SHOP and inv.status("GOLD TRIM") == LOCKED
    assert "NO-HIT" in inv.unlock_hint("GOLD TRIM")

    # Hangar SKINS tab: buy RETRO paint and wear it; the ship is repainted, stats unchanged.
    game.choose_hull(ARROW)
    game.save.coins = 1000
    game.open_hangar(0)
    h.post(pygame.K_LEFT)                                # wraps round to SKINS
    assert game.hangar_tab == SKIN
    h.run(3)
    h.shot("hangar_skins")
    while game.hangar_item.id != "RETRO":
        h.post(pygame.K_DOWN)
    h.post(pygame.K_RETURN)
    h.post(pygame.K_RETURN)
    assert inv.owns("RETRO") and game.skin("PAINT").id == "RETRO"
    before = game.loadout_for(LEVELS[0])
    assert before.colors == "retro" and game.ship.colors == SHIP_PALETTES["retro"]
    h.run(3)
    h.shot("hangar_retro")
    for item_id in ("PLASMA BLUE", "CYAN TRACERS", "EMERALD BEAM", "PIXEL SHATTER"):
        game.wear(item_id)
    h.post(pygame.K_SPACE)
    game.radio = None
    weapons = {w.name: w for w in game.weapons}
    assert game.ship.trail == TRAILS["PLASMA BLUE"] and weapons["GUN"].colors == TRACERS["CYAN"]
    assert weapons["LASER"].colors == BEAMS["EMERALD"]
    assert game.ship.max_hp == MK1.max_hp, "skins never change stats"
    h.run(30, Keys(pygame.K_SPACE, pygame.K_UP), clear_rocks=True)
    h.shot("skins_in_flight")
    particles = len(game.smoke.particles)
    h.die()
    assert len(game.smoke.particles) > particles, "pixel shatter"

    # Achievements: a boss beaten without a hit -> GOLD TRIM; FEVER -> RAINBOW; a whole
    # field without firing -> HEARTS; once only.
    game.start(0, 0, 0, 0)
    game.ship.hp = 10 ** 9
    game.god = True
    h.run(h.seconds(WARNING_TIME + 3.0), clear_rocks=True)
    h.kill(game.boss)
    h.run(h.seconds(game.boss.DEATH_TIME + JUICE_PAD), clear_rocks=True)
    game.god = False
    assert "NO_HIT" in game.save.achievements and inv.owns("GOLD TRIM")
    game.start(0)
    for _ in range(FEVER_AT):
        game.add_kill(1, 100, 100)
    assert inv.owns("RAINBOW")
    game.start(0)
    game.distance = game.wave.length - 0.01
    h.run(2, clear_rocks=True)
    assert inv.owns("HEARTS"), "PACIFIST"
    count = len(game.save.achievements)
    game.achieve("FEVER")
    assert len(game.save.achievements) == count, "earned once"
    assert set(SaveData(h.save_path).achievements) == set(game.save.achievements)

    # Supernova death.
    game.inventory.unlock("SUPERNOVA")
    game.wear("SUPERNOVA")
    game.start(0)
    h.die()
    h.shot("supernova")
    game.save.skins = {}
    game.inventory.grant_all()
    game.choose_hull(ARROW)
    game.to_title()


def test_title_menus(h):
    """Title: level select with LEFT/RIGHT, scores alternate in; ENTER -> star map (parked
    at the selected level) -> ENTER lands -> hangar -> launch; ESC goes back step by step."""
    game = h.game
    game.save.unlock(3)
    game.save.add_record(1000, 1)
    game.to_title()
    assert game.state == State.TITLE and game.selectable_levels == game.save.unlocked >= 3
    h.post(pygame.K_RIGHT)
    h.post(pygame.K_RIGHT)
    assert game.start_level == 2
    game.time = 6.5                                      # attract mode: TOP SCORES panel
    game.draw()
    h.shot("title_records")
    h.post(pygame.K_RETURN)
    assert game.state == State.STAR_MAP and game.star_map.near_node() == 2, "parked at 3"
    h.post(pygame.K_RETURN)                              # land: the hangar of that level
    assert game.state == State.HANGAR and game.hangar_item.id == game.hull.name
    h.post(pygame.K_DOWN)
    h.run(30)
    h.shot("hangar")
    h.post(pygame.K_ESCAPE)
    assert game.state == State.STAR_MAP, "ESC leaves the hangar for the map"
    h.post(pygame.K_ESCAPE)
    assert game.state == State.TITLE, "ESC leaves the map"
    h.post(pygame.K_UP)                                  # arrows open the map too
    assert game.state == State.STAR_MAP
    h.post(pygame.K_RETURN)
    assert game.state == State.HANGAR
    while game.hangar_item.id != "WASP":
        h.post(pygame.K_DOWN)
    h.post(pygame.K_RETURN)                              # ENTER equips ...
    assert game.state == State.HANGAR and game.hull is WASP
    h.post(pygame.K_RETURN)                              # ... and ENTER again launches
    assert game.state == State.PLAYING and game.level.number == 3 and game.score == 0
    assert game.hull is WASP and game.ship.hull is WASP and game.save.ship == "WASP"
    assert game.ship.max_hp == round(MK3.max_hp * WASP.hp)
    game.choose_hull(ARROW)
    game.start_level = 0


def test_hulls(h):
    """Every hull flies, shoots from its own barrels, leans and fights a boss."""
    game = h.game
    sizes = set()
    for hull in HULLS:
        game.choose_hull(hull)
        game.start(2)                                    # MK III: all weapons
        ship = game.ship
        assert ship.frames[0].get_size() == hull.size and ship.hull is hull
        assert ship.loadout == hull.apply(MK3) and ship.max_hp == round(MK3.max_hp * hull.hp)
        assert game.weapons[0].loadout == ship.loadout, "weapons use the hull's stats"
        sizes.add(hull.size)
        w, hgt = hull.size
        for bx, by in hull.barrels + ((0, hull.nose_y + 0.5),):
            assert abs(bx) <= w / 2 and abs(by) <= hgt / 2, f"{hull.name} barrel off the sprite"
        for off in hull.nozzles:
            assert abs(off) <= w / 2, f"{hull.name} nozzle off the sprite"
        h.run(20, Keys(pygame.K_UP, pygame.K_LEFT, pygame.K_SPACE), clear_rocks=True)
        assert ship.tilt_index == -3 and game.weapons[0].bullets, f"{hull.name} lean + gun"
        h.shot(f"hull_{hull.name.lower()}")
        # A short boss fight with this hull: must not crash, the gun must hit.
        game.wave_index = len(game.level.waves) - 1
        game.distance = game.wave.length
        game.boss_index = len(game.wave.bosses) - 1
        ship.hp = ship.max_hp = 10 ** 9
        h.run(h.seconds(WARNING_TIME + 3.0), clear_rocks=True)
        hp0 = game.boss.hp
        for _ in range(60):
            ship.x = game.boss.x
            game.update(h.dt, FIRE)
            game.draw()
        assert game.boss.hp < hp0, f"{hull.name} gun hits the boss"
    assert len(sizes) == len(HULLS), "every hull has its own dimensions"
    game.choose_hull(ARROW)


def test_dev(h):
    """Dev mode: a menu of every start point, ship choice, god mode, hotkeys, nothing saved."""
    game = h.game
    records_before = h.saved_records()
    game.dev = True
    game.load_profile(SaveData(None))
    game.to_title()
    assert game.state == State.DEV_MENU
    items = game.dev_items()
    assert len(items) == sum(len(lv.waves) + sum(len(w.bosses) for w in lv.waves) for lv in LEVELS)
    h.post(pygame.K_RIGHT)
    assert game.hull is HULLS[1], "LEFT/RIGHT picks the ship in the dev menu"
    h.run(2)
    h.shot("dev_menu")
    h.post(pygame.K_LEFT)
    target = next(i for i, it in enumerate(items) if "MOTHERSHIP" in it[0])
    for _ in range(target):
        h.post(pygame.K_DOWN)
    h.post(pygame.K_g)
    assert game.god
    h.post(pygame.K_RETURN)
    assert game.state == State.PLAYING and game.level.number == 3 and game.wave_index == 2
    h.run(2)
    assert game.phase == Phase.WARNING
    h.post(pygame.K_n)                                   # skip the warning
    h.run(2)
    assert isinstance(game.boss, Mothership)
    h.post(pygame.K_n)                                   # skip the entry
    h.run(2)
    assert game.boss.fighting
    game.hurt_ship(50, 0, 0)
    assert game.ship.hp == MK3.max_hp, "god mode"
    h.post(pygame.K_n)                                   # next phase, with its rewards
    assert game.boss.phase == 1 and any(isinstance(p, PowerCore) for p in game.pickups)
    h.post(pygame.K_1)
    h.post(pygame.K_2)
    assert game.blast.charge == 1 and game.weapons[0].power >= 1
    h.run(h.seconds(0.5))
    h.shot("dev_play")
    for _ in range(2):
        h.run(h.seconds(1.7))                            # wait out the roar
        h.post(pygame.K_n)
    assert game.boss.state == "dying", game.boss.state
    h.post(pygame.K_ESCAPE)
    assert game.state == State.DEV_MENU
    game.god = False
    game.start(1, 0, 0, None)
    game.score = 500
    h.die()
    assert game.state == State.GAME_OVER and game.save.records != [] and game.save.path is None
    assert h.saved_records() == records_before, "dev runs don't touch the file"
    game.dev = False
    game.load_profile(SaveData(h.save_path))


def test_retry(h):
    """Game over in level 2 retries level 2 with the score it started with."""
    game = h.game
    game.start(1, 1234)
    h.die()
    h.post(pygame.K_r)
    assert game.level.number == 2 and game.score == 1234 and game.ship.loadout == MK2
    game.start(0)
    assert game.ship.loadout == MK1 and game.ship.max_hp == MK1.max_hp


def test_audio(h):
    """Every sound and track the game asks for exists, and the synth renders."""
    game = h.game
    for state in State:                                  # music for every state and phase
        for phase in Phase:
            game.state, game.phase = state, phase
            if phase == Phase.BOSS:
                game.wave_index, game.boss_index = 0, 0
            track = game._music_track()
            assert track is None or track in SONGS, (state, phase, track)
    for level in LEVELS:
        assert level.music in SONGS
        for entry in (e for wave in level.waves for e in wave.bosses):
            assert entry.music in SONGS
    game.to_title()
    for name in SOUNDS:
        game.audio.play(name)                            # asserts the name is known
    samples = SONGS["level_clear"]().render()
    assert samples and max(abs(v) for v in samples) <= 1.0
    try:
        game.audio.play("no_such_sound")
    except AssertionError:
        pass
    else:
        raise AssertionError("unknown sound names must fail loudly")


def test_busy(h):
    """A busy minute of normal play must not crash: every field, the Carrier and the
    Mothership, with BLAST and ULTIMATE going off in level 3."""
    game = h.game
    pattern = [Keys(pygame.K_UP, pygame.K_SPACE), Keys(pygame.K_LEFT, pygame.K_SPACE),
               Keys(pygame.K_DOWN, pygame.K_RIGHT), Keys(pygame.K_SPACE)]
    for name, level_index, boss_fight, hull in (
            ("busy", 0, False, ARROW), ("busy_level2", 1, False, WASP),
            ("busy_carrier", 1, True, TITAN), ("busy_level3", 2, False, HULLS[3]),
            ("busy_mothership", 2, True, ARROW), ("busy_level4", 3, False, WASP),
            ("busy_leviathan", 3, True, HULLS[3])):
        game.choose_hull(hull)
        game.start(level_index)
        game.ship.hp = game.ship.max_hp = 10 ** 9
        if boss_fight:
            game.wave_index = len(game.level.waves) - 1
            game.distance = game.wave.length
            game.boss_index = len(game.wave.bosses) - 1
        else:
            game.distance = -10 ** 9          # stay in the asteroid field
        for i in range(3600):
            if i % 600 == 0:
                game.switch_weapon()
            if i % 700 == 350 and game.ship.loadout.ultimate:
                game.blast.charge = game.ultimate.charge = 1.0
                game.fire_ultimate()
            if game.boss and game.boss.fighting:
                if i % 900 == 0 and game.boss.phase < game.boss.PHASES - 1:
                    game._damage_boss(Hit(game.boss, game.boss.max_hp * 0.3, 0, 0, 0, -1, 0))
                game.boss.hp = max(game.boss.hp, game.boss.max_hp * 0.2)    # keep it fighting
            game.update(h.dt, pattern[(i // 90) % len(pattern)])
            game.draw()
            if i == 1800:
                h.shot(name)
        assert game.state == State.PLAYING, game.state
    game.choose_hull(ARROW)


def _boss_rounds(h, boss, shots=None):
    """Every phase, every attack of a learning boss: force each option for one slot."""
    game = h.game
    for phase in range(boss.PHASES):
        while boss.phase < phase:
            boss.roar = 0
            game._damage_boss(Hit(boss, boss.max_hp * 0.2, 0, 0, 0, -1, 0))
        boss.roar = 0
        for option in boss.OPTIONS[phase]:
            boss.attack, boss.attack_time = option, 0.0
            if hasattr(boss, "fire_timer"):
                boss.fire_timer = 0.0
            h.run(h.seconds(min(boss.SLOT, 3.0)), FIRE, clear_rocks=True)
            game.ship.hp = game.ship.max_hp
        if shots:
            h.shot(f"{shots}_phase{phase + 1}")


def _veil_level(h, number, hazard, music, boss_cls, shot):
    """Start galaxy 2 level `number`, fly its field a while, then jump to its boss."""
    game = h.game
    level = GALAXIES[1].levels[number - 1]
    index = LEVELS.index(level)
    game.save.unlock(index + 1)
    game.start(index)
    game.radio = None
    assert isinstance(game.hazard, hazard) and game._music_track() == music, game._music_track()
    assert game.ship.loadout.name == f"MK {['XII', 'XIII', 'XIV', 'XV', 'XVI'][number - 2]}"
    game.god = True
    h.run(h.seconds(6), FIRE)
    h.shot(f"{shot}_field")
    return level, index


def _veil_boss(h, index, boss_cls, shot):
    game = h.game
    level = LEVELS[index]
    game.start(index, 0, len(level.waves) - 1, 0)
    game.radio = None
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    boss = game.boss
    assert isinstance(boss, boss_cls) and boss.fighting, (boss, game.phase)
    assert boss.spec.name in DOSSIER_BY_BOSS
    _boss_rounds(h, boss, shot)
    return boss


def _win_level(h, boss):
    game = h.game
    boss.roar = 0
    h.kill(boss)
    for _ in range(h.seconds(10)):
        h.run(1, clear_rocks=True)
        if game.state in (State.LEVEL_CLEAR, State.WIN):      # WIN: the last level so far
            break
    assert game.state in (State.LEVEL_CLEAR, State.WIN) and boss.spec.name in game.save.bosses, (
        game.state, game.phase, boss.state, game.save.bosses)


def test_abilities(h):
    """G19: abilities on SHIFT / right click (PHASE dash + i-frames, FLARE, TIME SLIP slows
    the enemy side, REPAIR DRONE heals, DECOY takes the aim), cooldowns, the WING BAY's second
    wingman, upgrade tiers 6-10 (locked until galaxy 1 is beaten, capped in galaxy 1)."""
    game = h.game
    game.choose_hull(ARROW)
    index = LEVELS.index(GALAXIES[1].levels[0])
    game.save.unlock(index + 1)
    game.save.ability = "PHASE"
    game.start(index)
    game.radio = None
    game.god = True                                      # only the abilities change the hull
    ship = game.ship
    assert game.ability == "PHASE" and game.ability_ready
    ship.x, ship.y, ship.vx, ship.vy = 160, 200, 0, 0
    h.post(pygame.K_LSHIFT)
    assert ship.y < 200 - PHASE_DASH + 2 and ship.invulnerable_time >= PHASE_TIME
    assert not game.ability_ready and not game.use_ability(), "on cooldown"
    h.run(h.seconds(0.2))
    h.shot("ability_phase")
    game.ability_cooldown = 0
    # Right click works too.
    game.save.ability = "TIME SLIP"
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10), button=3))
    game.handle_events()
    assert game.time_slip > 0 and abs(game.enemy_dt(1.0) - TIME_SLIP_SCALE) < 1e-9
    h.run(h.seconds(TIME_SLIP_TIME + 0.1))
    assert game.enemy_dt(1.0) == 1.0
    game.ability_cooldown = 0
    game.save.ability = "REPAIR DRONE"
    ship.hp = ship.max_hp * 0.5
    assert game.use_ability()
    h.run(h.seconds(REPAIR_TIME + 0.2), clear_rocks=True)
    assert ship.hp >= ship.max_hp * (0.5 + REPAIR_SHARE) - 2, ship.hp / ship.max_hp
    game.ability_cooldown = 0
    game.save.ability = "DECOY"
    assert game.use_ability() and game.aim_target() is game.decoy
    ship.x = 60
    h.run(h.seconds(0.3), clear_rocks=True)
    h.shot("ability_decoy")
    assert game.aim_target() is not ship
    h.run(h.seconds(DECOY_TIME), clear_rocks=True)
    assert game.aim_target() is ship
    game.ability_cooldown = 0
    game.save.ability = "FLARE"
    assert game.use_ability() and game.flare > 0
    game.save.ability = "NOT AN ABILITY"
    assert game.ability is None and not game.use_ability()
    game.save.ability = None

    # WING BAY: a second wingman flies on the other side.
    game.save.wingman, game.save.wingman2 = None, None
    game.choose_wingman("PIP")
    game.choose_wingman("GUARDIAN")
    assert game.save.wingman == "GUARDIAN" and game.save.wingman2 == "PIP"
    game.start(index)
    assert len(game.wingmen) == 2 and {w.side for w in game.wingmen} == {-1, 1}
    h.run(h.seconds(1), FIRE)
    h.shot("wing_bay")
    game.save.owned.remove("WING BAY")
    game.start(index)
    assert len(game.wingmen) == 1
    game.save.owned.append("WING BAY")
    game.save.wingman = game.save.wingman2 = None

    # Tiers 6-10: galaxy 1 counts at most 5; galaxy 2 all of them.
    game.save.upgrades = {"ARMOR": UPGRADE_TIERS}
    g1 = game.loadout_for(LEVELS[3])
    g2 = game.loadout_for(GALAXIES[1].levels[0])
    hull = game.hull.apply(LEVELS[3].loadout)
    assert g1.max_hp == round(hull.max_hp * upgrades.track_named("ARMOR").multiplier(GALAXY1_TIERS))
    hull2 = game.hull.apply(GALAXIES[1].levels[0].loadout)
    assert g2.max_hp == round(hull2.max_hp * upgrades.track_named("ARMOR").multiplier(UPGRADE_TIERS))
    game.save.upgrades = {"ARMOR": GALAXY1_TIERS}
    game.save.coins = 10 ** 5
    medals = list(game.save.medals)
    game.save.medals = []
    armor = upgrades.track_named("ARMOR")
    game.hangar_confirm = None
    game._hangar_upgrade(armor)
    game._hangar_upgrade(armor)
    assert game.inventory.tier("ARMOR") == GALAXY1_TIERS and "GALAXY 1" in game.hangar_message[0]
    game.save.medals = [1]
    game._hangar_upgrade(armor)
    game._hangar_upgrade(armor)
    assert game.inventory.tier("ARMOR") == GALAXY1_TIERS + 1, game.hangar_message
    game.save.medals = medals
    game.save.upgrades = {}
    game.god = False
    game.to_title()


def test_veil_levels(h):
    """Galaxy 2 levels 2-6: BONE REEF (the maw's pursuit, marrow regrowth, LEECH MAW), BROOD
    SANCTUARY (the pod, its riders, THE HOLLOW REAPER's harvest), THE DARK VEIL (darkness,
    ECLIPSE), MIRROR SEA (reflection, the ship's history, THE MIMIC), PULSE NEBULA (the beat,
    TEMPO) - every boss attack in every phase, and each level won."""
    game = h.game
    game.choose_hull(ARROW)

    # BONE REEF: the jaws rise while you idle and fall back when you boost.
    level, index = _veil_level(h, 2, MawPursuit, "reef", LeechMaw, "reef")
    maw = game.hazard
    assert game.wave.pursuit and maw.active and game._world_speed() > 1.0
    game.god = False
    ship = game.ship
    ship.hp = 10 ** 6
    ship.invulnerable_time, game.shield = 0, 0
    maw.bite_y = ship.y + ship.h / 2 + 30
    ship.y = LOW_H - 20
    h.run(h.seconds(1.5), clear_rocks=True)
    assert maw.bites >= 1, "idle at the bottom: it bites"
    high = maw.bite_y
    h.run(h.seconds(1.5), Keys(pygame.K_UP), clear_rocks=True)
    assert maw.bite_y > high, "boosting pulls away"
    h.shot("reef_jaws")
    game.god = True
    # A big bone rock leaves a marrow core that grows back into a rock.
    art = game.library.pick(12, 14, ("reef",))
    rock = rock_class("reef")(art, 160, 80, 0, 0, 0)
    game.asteroids = [rock]
    game._destroy_rock(rock, scored=True)
    cores = [r for r in game.asteroids if isinstance(r, MarrowCore)]
    assert len(cores) == 1 and cores[0].transform() is None
    cores[0].grow = MARROW_REGROW
    assert type(cores[0].transform()).__name__ == "BoneRock"
    game.spawn_enemies(stalker_pair(game))
    h.run(h.seconds(2), FIRE)
    boss = _veil_boss(h, index, LeechMaw, "leechmaw")
    assert not game.hazard.active, "the pursuit ends at the boss"
    _win_level(h, boss)

    # BROOD SANCTUARY: stray shots hurt the pod, its riders zap minions, the pod pays you.
    level, index = _veil_level(h, 3, BroodEscort, "sanctuary", Reaper, "sanctuary")
    pod = game.hazard.pod
    game.extra_timers = [99.0] * len(game.extra_timers)
    game.enemies.clear()
    game.enemy_bullets = []
    hp = pod.hp
    game.enemy_bullets.append(EnemyBullet(pod.x, pod.y, 0, 0, 40))
    h.run(2, clear_rocks=True)
    assert pod.hp == hp - 20, "a stray bullet hits the pod for half"
    latchers = latcher_trio(game)
    game.spawn_enemies(latchers)
    for e in latchers:
        e.x, e.y = pod.x + 10, pod.y - 20
    hps = [e.hp for e in latchers]
    game.hazard.ally_timer = 0
    h.run(2, clear_rocks=True)
    assert any(e.hp < h0 or e not in game.enemies for e, h0 in zip(latchers, hps)), "zapped"
    boss = _veil_boss(h, index, Reaper, "reaper")
    pod = game.hazard.pod
    pod.hp = pod.max_hp
    boss.attack, boss.attack_time, boss.fire_timer = "harvest", 0.0, 0.0
    boss.harvesting, boss.broken, boss.stagger = True, 0.0, 0.0
    hp = pod.hp
    h.run(h.seconds(2.0), clear_rocks=True)
    assert boss.harvesting and pod.hp < hp, "the harvest drains the pod"
    game._damage_boss(Hit(boss.scythe, boss.max_hp * REAPER_BREAK * 1.2, boss.scythe.x,
                          boss.scythe.y, 0, -1, 0))
    assert not boss.harvesting and boss.harvests_broken == 1, "hit the scythe to break it"
    pod.hp = pod.max_hp
    coins = game.pending_coins
    game.save.story = [s for s in game.save.story if s != "BROOD_SAVED"]
    _win_level(h, boss)
    assert "BROOD_SAVED" in game.save.story and game.payout.total > 0
    assert game.pending_coins >= coins + POD_SAVED_COINS or game.payout.total >= POD_SAVED_COINS

    # THE DARK VEIL: darkness over the field; FLARE lifts it.
    level, index = _veil_level(h, 4, Darkness, "dark", Eclipse, "dark")
    game.spawn_enemies(lurker_pair(game))
    h.run(h.seconds(2), FIRE)
    h.shot("dark_lurkers")
    game.save.ability = "FLARE"
    game.ability_cooldown = 0
    assert game.use_ability()
    h.run(h.seconds(0.5), FIRE)
    h.shot("dark_flare")
    game.save.ability = None
    boss = _veil_boss(h, index, Eclipse, "eclipse")
    _win_level(h, boss)

    # MIRROR SEA: the reflection forms and mirrors you; the ship's path is remembered.
    level, index = _veil_level(h, 5, MirrorSea, "mirror", Mimic, "mirror")
    sea = game.hazard
    if sea.reflection is None:                           # shot down: it re-forms
        sea.back = 0.0
        h.run(2)
    reflection = sea.reflection
    assert reflection in game.enemies
    game.ship.x = 100
    h.run(h.seconds(1.5), clear_rocks=True)
    assert abs(reflection.x - (LOW_W - game.ship.x)) < 20, "it mirrors you"
    h.shot("mirror_reflection")
    reflection.damage(10 ** 6)
    reflection.damage(10 ** 6)                           # (an elite's shell takes the first)
    h.run(2, clear_rocks=True)
    assert sea.reflection is None and sea.back > 0, "broken, it comes back later"
    assert game.ship_at(1) is not None
    game.spawn_enemies(echo_ghost(game))
    h.run(h.seconds(2), FIRE)
    boss = _veil_boss(h, index, Mimic, "mimic")
    for name in ("LASER", "SCATTER", "PLASMA", "ARC", "GUN"):     # it copies each weapon
        boss.attack, boss.attack_time, boss.fire_timer, boss.copying = "copy", 0.0, 0.0, name
        h.run(h.seconds(1.6), clear_rocks=True)
        game.ship.hp = game.ship.max_hp
    _win_level(h, boss)

    # PULSE NEBULA: the enemy side lunges on the beat and drifts between beats.
    level, index = _veil_level(h, 6, PulseField, "pulse", Tempo, "pulse")
    scales = []
    for _ in range(h.seconds(0.5)):
        h.run(1, clear_rocks=True)
        scales.append(game.enemy_dt(1.0))
    assert min(scales) < 0.4 and max(scales) > 2.0, (min(scales), max(scales))
    boss = _veil_boss(h, index, Tempo, "tempo")
    _win_level(h, boss)
    game.god = False
    game.to_title()


def test_veil_finale(h):
    """Galaxy 2 levels 7-10: HOLLOW MAZE (void holes eat bullets, eggs hatch, the fork's gates
    pick GRINDER or SPINNER), LAST LIGHT (the flagship takes hits and shoots back, a leader's
    death breaks its squad, the flagship's bonus, losing it loses the level), THE COURT OF NYX
    (chained rocks, a new rule per arena, NYX retreats), THE HOLLOW THRONE (the rush, NYX's
    five phases: dark, the void closes, VANTA speaks; escape, warp, shard 2, medal 2, the NYX
    paint) and the galaxy 2 story (LOOKBEHIND, caches, mosaic 2, decoder 2, VANTA's face)."""
    game = h.game
    game.choose_hull(ARROW)
    g2 = GALAXIES[1]

    # HOLLOW MAZE ------------------------------------------------------------------------
    level = g2.levels[6]
    index = LEVELS.index(level)
    game.save.unlock(index + 1)
    game.start(index)
    game.radio = None
    game.god = True
    maze = game.hazard
    assert isinstance(maze, HollowMaze) and game.ship.loadout.name == "MK XVII"
    hole = maze.holes[0]
    hole.y, hole.x = 120, 160
    game.enemy_bullets = [EnemyBullet(160, 120, 0, 0, 10), EnemyBullet(20, 230, 0, 0, 10)]
    h.run(1)
    assert len(game.enemy_bullets) <= 1 and maze.erased >= 1, "the void hole ate it"
    eggs = [EggCluster(250, 60)]
    game.spawn_enemies(eggs)
    h.run(h.seconds(EGG_HATCH + 0.2), clear_rocks=True)
    assert eggs[0].hatched and any(type(e).__name__ == "Larva" for e in game.enemies)
    game.enemies.clear()
    game.distance = game.wave.length * FORK_AT
    h.run(h.seconds(2.5), clear_rocks=True)
    assert maze.gates_y is not None and maze.route is None
    h.shot("maze_fork")
    game.ship.x, game.ship.y = 240, maze.gates_y
    h.run(2, clear_rocks=True)
    assert maze.route == 1, "the BLUE gate"
    game.distance = game.wave.length
    h.run(2, clear_rocks=True)
    assert game.wave.route and game.wave_index == 1
    game.distance = game.wave.length                     # (skip the road's field)
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    assert isinstance(game.boss, Spinner), game.boss
    _boss_rounds(h, game.boss, "spinner")
    _win_level(h, game.boss)
    game.start(index, 0, 1, 0)                            # no gate taken: route 0 = GRINDER
    game.radio = None
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    assert isinstance(game.boss, Grinder)
    boss = game.boss
    boss.attack, boss.attack_time, boss.ram, boss.ram_y = "ram", 0.0, 1, 180
    h.run(h.seconds(1.2), clear_rocks=True)
    assert boss.ram == 2 and boss.contact_damage > boss.bullet_damage, "it rams"
    h.shot("grinder_ram")
    h.run(h.seconds(2.5), clear_rocks=True)
    _boss_rounds(h, boss, "grinder")
    _win_level(h, boss)

    # LAST LIGHT -------------------------------------------------------------------------
    index = LEVELS.index(g2.levels[7])
    game.start(index)
    game.radio = None
    siege = game.hazard
    flag = siege.flagship
    assert isinstance(siege, Siege) and not any(w.bosses for w in game.level.waves)
    game.extra_timers = [99.0] * len(game.extra_timers)
    game.enemies.clear()
    hp = flag.hp
    game.enemy_bullets = [EnemyBullet(flag.x, flag.top + 4, 0, 0, 50)]
    h.run(1, clear_rocks=True)
    assert flag.hp == hp - 30, "a stray shot hits the flagship"
    squad = leader_squad(game)
    game.spawn_enemies(squad)
    for e in squad:
        e.y = 80 + e.y
    h.run(h.seconds(1.0), clear_rocks=True)
    h.shot("siege_squad")
    leader = squad[0]
    game._damage_enemy(Hit(leader, 10 ** 6, leader.x, leader.y, 0, -1, 0))
    game._damage_enemy(Hit(leader, 10 ** 6, leader.x, leader.y, 0, -1, 0))
    assert leader not in game.enemies and leader.squad.orphaned
    target = squad[1]
    target.hp = target.max_hp = 10 ** 5
    siege.gun_timer = 0
    h.run(2, clear_rocks=True)
    assert target.hp < 10 ** 5 or siege.tracers, "the flagship's guns fire"
    game.enemies.clear()
    game.wave_index = len(game.level.waves) - 1
    game.distance = game.wave.length
    game.save.story = [b for b in game.save.story if b != "FLAGSHIP_HELD"]
    h.run(h.seconds(1), clear_rocks=True)
    assert game.state == State.LEVEL_CLEAR and "FLAGSHIP_HELD" in game.save.story
    game.start(index)                                    # lose the flagship: lose the level
    game.radio = None
    game.god = False
    game.ship.hp = 10 ** 6
    game.hazard.flagship.hp = 1
    game.hazard.flagship.hurt(5)
    for _ in range(h.seconds(2.5)):
        h.run(1, clear_rocks=True)
    assert game.state in (State.DYING, State.GAME_OVER), game.state
    game.god = True

    # THE COURT OF NYX -------------------------------------------------------------------
    index = LEVELS.index(g2.levels[8])
    game.start(index)
    game.radio = None
    game.god = True
    court = game.hazard
    assert isinstance(court, CourtOfNyx)
    court._spawn(game)
    chain = court.chains[-1]
    chain.cy = 120
    h.run(2)
    (ax, ay), (bx, by) = chain.ends()
    assert abs(chain.a.x - ax) < 1 and abs(chain.b.y - by) < 1, "the rocks ride the chain"
    game.god = False
    ship = game.ship
    ship.hp, ship.invulnerable_time, game.shield = 10 ** 6, 0, 0
    ship.x, ship.y = chain.cx, chain.cy
    hp = ship.hp
    h.run(1)
    assert ship.hp < hp, "the tether hurts"
    game.god = True
    h.shot("court_chain")
    game._destroy_rock(chain.a, scored=True)
    h.run(1)
    assert chain not in court.chains and chain.b.vy > 0, "the other rock flies free"
    game.distance = game.wave.length
    h.run(2, clear_rocks=True)
    assert game.wave_index == 1 and game.shift is not None, "a new arena, a new rule"
    game.distance = game.wave.length                     # (skip ARENA II's field)
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    nyx = game.boss
    assert isinstance(nyx, NyxCourt) and nyx.fighting
    h.run(h.seconds(1), clear_rocks=True)
    assert nyx.greeted
    while nyx.state == "fight":
        nyx.roar = 0
        game._damage_boss(Hit(nyx, nyx.max_hp * 0.1, 0, 0, 0, -1, 0))
    assert nyx.state == "leaving" and nyx.hp > 0
    for _ in range(h.seconds(6)):                        # (phase slow-mo stretches it)
        h.run(1, clear_rocks=True)
        if game.phase == Phase.CLEARED:
            break
    assert game.phase == Phase.CLEARED and "NYX" not in game.save.bosses, (
        "it only retreated", game.phase, nyx.state, game.save.bosses)
    h.shot("court_retreat")

    # THE HOLLOW THRONE ------------------------------------------------------------------
    index = LEVELS.index(g2.levels[9])
    game.save.unlock(index + 1)
    game.start(index, 0, 0, 1)                           # the rush's ECLIPSE: the dark
    game.radio = None
    throne = game.hazard
    assert isinstance(throne, HollowThrone)
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    assert isinstance(game.boss, Eclipse) and throne.dark_on
    h.shot("throne_eclipse")
    game.start(index, 0, 1, 0)
    game.radio = None
    throne = game.hazard                                 # (start() builds a new one)
    h.run(h.seconds(WARNING_TIME + 3.5), clear_rocks=True)
    nyx = game.boss
    assert isinstance(nyx, Nyx) and not isinstance(nyx, NyxCourt) and game.is_final_boss()
    _boss_rounds(h, nyx, "nyx")
    assert nyx.phase == 4 and throne.close > 0.3, ("the void closed in", nyx.phase, throne.close, nyx.state)
    assert 4 in nyx.said
    nyx.said.discard(4)                                  # (say phase 5's words once more)
    nyx._pending_taunt = 4
    nyx._taunt(game)
    speakers = [c.speaker for c in [game.radio] + game.radio_queue if c]
    assert VANTA in speakers, ("VANTA speaks through it", speakers)
    game.save.medals = [m for m in game.save.medals if m != 2]
    game.save.shards = [s for s in game.save.shards if s != 2]
    game.save.story = [b for b in game.save.story if b != "G2_WARP"]
    nyx.roar = 0
    h.kill(nyx)
    for _ in range(h.seconds(8)):
        h.run(1, clear_rocks=True)
        if game.wave.escape:
            break
    assert game.wave.escape and "NYX" in game.save.bosses
    h.run(h.seconds(3), clear_rocks=True)
    assert throne.world_speed > 1 and throne.close > 0.3
    h.shot("throne_escape")
    game.distance = game.wave.length
    h.run(2, clear_rocks=True)
    assert game.state == State.WARP and 2 in game.save.medals and 2 in game.save.shards
    assert "G2_WARP" in game.save.story
    h.run(h.seconds(WARP_TIME + 0.5))
    assert game.state == State.WIN
    game.save.gifts = [k for k in game.save.gifts if k != "2-10"]
    if "NYX" in game.save.owned:
        game.save.owned.remove("NYX")
    h.run(h.seconds(1.2))
    h.post(pygame.K_RETURN)
    assert game.state == State.REWARD and [i.id for i in game.gift_options] == ["NYX"]
    h.run(h.seconds(0.6))
    h.post(pygame.K_RETURN)
    assert game.state == State.STAR_MAP and game.star_map.gmap.galaxy == 2
    game.save.skins = {}
    game.choose_hull(ARROW)

    # The galaxy 2 story -----------------------------------------------------------------
    assert "".join(lv.radio[0][0] for lv in g2.levels) == ACROSTIC_2
    assert {e.cache for e in ECHOES_2} == {c.id for c in MAPS[2].caches}
    assert sorted(e.tile for e in ECHOES_2) == list(range(6))
    assert all(len(line) <= 43 for line in (ln.text for ln in TRANSMISSIONS["G2_WARP"]))
    assert any(ln.speaker == UNMASKED for ln in TRANSMISSIONS["G2_WARP"])
    caches = list(game.save.caches)
    game.save.caches = caches + [e.cache for e in ECHOES_2]
    assert game.decoder2
    log = [text for kind, text, _ in game._journal_log() if kind == "decoded"]
    assert any(DECODED_2 in text for text in log)
    files = {f.name: f for f in game._boss_files()}
    assert any("REEF READS" in line for line in files["VANTA"].lines)
    game.open_journal()
    game.journal_tab = 2
    game.journal_cursor["ECHOES"] = len(ECHOES) + 2      # a galaxy 2 echo: mosaic 2
    h.run(3)
    h.shot("journal_mosaic2")
    game.close_journal()
    game.save.caches = caches
    game.god = False
    game.to_title()


SECTIONS = (
    ("title", test_title), ("controls", test_controls), ("mouse", test_mouse),
    ("weapons", test_weapons),
    ("damage", test_damage), ("balance", test_balance), ("pickups", test_pickups),
    ("campaign", test_campaign), ("level4", test_level4),
    ("level5", test_level5), ("level6", test_level6), ("level7", test_level7),
    ("level8", test_level8), ("level9", test_level9), ("level10", test_level10),
    ("starmap", test_starmap), ("journal", test_journal),
    ("brains", test_brains), ("veil", test_veil), ("abilities", test_abilities),
    ("veil2", test_veil_levels), ("veil3", test_veil_finale), ("save", test_save), ("menus", test_title_menus),
    ("economy", test_economy), ("inventory", test_inventory),
    ("upgrades", test_upgrades), ("feel", test_feel),
    ("boosts", test_boosts), ("wingmen", test_wingmen),
    ("arsenal", test_arsenal), ("skins", test_skins), ("hulls", test_hulls), ("dev", test_dev), ("retry", test_retry), ("audio", test_audio),
    ("busy", test_busy),
)


def run_smoke_test(shots_dir=None, seed=None, only=None):
    """Run every section (or only the named ones); optionally save screenshots."""
    if seed is not None:
        random.seed(seed)
    names = [name for name, _ in SECTIONS]
    unknown = set(only or ()) - set(names)
    assert not unknown, f"unknown sections {sorted(unknown)}; choose from {names}"
    h = Harness(shots_dir)
    for name, section in SECTIONS:
        if only and name not in only:
            continue
        section(h)
        print(f"  ok  {name}")
    pygame.quit()
    print("smoke test OK")
