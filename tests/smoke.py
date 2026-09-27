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
                                UPGRADE_TIERS, WARNING_TIME, WINGMAN_KO_TIME,
                                WINGMAN_TRAIN_COST, WINGMAN_TRAIN_XP, WINGMAN_XP,
                                WINGMAN_XP_KILL, WINGMAN_XP_OWN)
from game.core.input import Keys
from game.core.storage import SaveData
from game.flow.game import Game
from game.flow.states import Phase, State
from game.levels.data import LEVELS
from game.minions.diver import Diver
from game.minions.drone import drone_formation
from game.bosses.helios import Flare, Helios
from game.bosses.kaleidos import Kaleidos, Shard
from game.bosses.wraith import Wraith
from game.minions.bullets import ColoredBullet
from game.minions.prism import prism_turret
from game.obstacles.asteroid import CrystalRock, WreckChunk
from game.bosses.scrapjaw import JunkShot, Scrapjaw
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

FIRE = Keys(pygame.K_SPACE)
JUICE_PAD = 0.8          # hit-stop + slow-mo after a big event stretch the world's time


class Harness:
    """The game under test plus helpers to drive it frame by frame."""

    def __init__(self, shots_dir):
        self.shots_dir = shots_dir
        self.save_path = os.path.join(tempfile.mkdtemp(), "save.json")   # never the player's
        self.game = Game(save_path=self.save_path)
        self.game.inventory.grant_all()     # sections below test levels 1-4 with every item
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
    assert game.state == State.HANGAR, "click = ENTER on the title"
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
    maxed = {t: UPGRADE_TIERS for t in upgrades.TRACK_IDS}
    assert abs(upgrades.power_ratio({}) - 1) < 1e-9
    assert abs(upgrades.power_ratio(maxed) - 1.3225) < 1e-6, upgrades.power_ratio(maxed)
    assert abs(upgrades.power_ratio({"LASER": 5}) - upgrades.power_ratio({"GUNS": 5})) < 1e-9
    assert abs(upgrades.power_ratio({"GUNS": 5, "LASER": 5}) - 1.15) < 1e-9, "weapons don't stack"
    up = upgrades.apply(MK4, maxed)
    assert up.max_hp == round(MK4.max_hp * 1.15) and abs(up.gun_damage - MK4.gun_damage * 1.15) < 1e-9
    assert abs(up.laser_dps - MK4.laser_dps * 1.15) < 1e-9
    assert abs(up.max_speed - MK4.max_speed * 1.2) < 1e-9 and abs(up.charge_rate - 1.5) < 1e-9
    assert upgrades.apply(MK4, {}) == MK4

    # The cap: every boss in a damage race against a maxed build, with every hull.
    for level in LEVELS:
        for spec in (e.spec for wave in level.waves for e in wave.bosses):
            for hull in HULLS:
                ship = upgrades.apply(hull.apply(spec.player), maxed)
                ratio = (spec.hp / ship.gun_dps) / (ship.max_hp / spec.dps)
                assert ratio >= spec.strength / 1.33, (spec.name, hull.name, ratio)
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
        json.dump({"version": 2, "upgrades": {"ARMOR": 9, "GUNS": -2}}, f)
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

    # Balance: maxed upgrades + a level 5 PIP still face a 5x boss as >= 3.5x.
    maxed = {t: UPGRADE_TIERS for t in upgrades.TRACK_IDS}
    for level in LEVELS:
        for spec in (e.spec for wave in level.waves for e in wave.bosses if e.spec.strength >= 5):
            for hull in HULLS:
                ship = upgrades.apply(hull.apply(spec.player), maxed)
                dps = ship.gun_dps * (1 + PIP_SHARE[-1])       # PIP fires a share of it
                ratio = (spec.hp / dps) / (ship.max_hp / spec.dps)
                assert ratio >= 3.5, (spec.name, hull.name, ratio)

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
    """Title: level select with LEFT/RIGHT, scores alternate in; ENTER -> hangar -> launch."""
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
    assert game.state == State.HANGAR and game.hangar_item.id == game.hull.name
    h.post(pygame.K_DOWN)
    h.run(30)
    h.shot("hangar")
    h.post(pygame.K_ESCAPE)
    assert game.state == State.TITLE, "ESC leaves the hangar"
    h.post(pygame.K_UP)                                  # arrows open the hangar too
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


SECTIONS = (
    ("title", test_title), ("controls", test_controls), ("mouse", test_mouse),
    ("weapons", test_weapons),
    ("damage", test_damage), ("balance", test_balance), ("pickups", test_pickups),
    ("campaign", test_campaign), ("level4", test_level4),
    ("level5", test_level5), ("level6", test_level6), ("level7", test_level7),
    ("level8", test_level8), ("save", test_save), ("menus", test_title_menus),
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
