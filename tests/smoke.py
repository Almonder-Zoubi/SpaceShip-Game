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
from game.bosses.mothership import Mothership
from game.config.display import FPS, WIN_H, WIN_W
from game.config.loadouts import MK1, MK2, MK3
from game.config.tuning import DEATH_DELAY, POWER_MAX, REPAIR_SMALL, WARNING_TIME
from game.core.input import Keys
from game.core.storage import SaveData
from game.flow.game import Game
from game.flow.states import Phase, State
from game.levels.data import LEVELS
from game.minions.drone import drone_formation
from game.obstacles.asteroid import Asteroid
from game.pickups.types import FullRepair, PowerCore, RepairKit
from game.player.hulls import ARROW, HULLS, TITAN, WASP
from game.weapons.base import Hit

FIRE = Keys(pygame.K_SPACE)


class Harness:
    """The game under test plus helpers to drive it frame by frame."""

    def __init__(self, shots_dir):
        self.shots_dir = shots_dir
        self.save_path = os.path.join(tempfile.mkdtemp(), "save.json")   # never the player's
        self.game = Game(save_path=self.save_path)
        self.dt = 1 / FPS
        self.field = LEVELS[0].difficulty

    def shot(self, name):
        if self.shots_dir:
            os.makedirs(self.shots_dir, exist_ok=True)
            pygame.image.save(pygame.transform.scale(self.game.canvas, (WIN_W, WIN_H)),
                              os.path.join(self.shots_dir, f"{name}.png"))

    def run(self, frames, keys=Keys(), clear_rocks=False):
        for _ in range(frames):
            if clear_rocks:
                self.game.asteroids.clear()
            self.game.update(self.dt, keys)
            self.game.draw()

    def seconds(self, s):
        return int(s / self.dt)

    def post(self, key, kind=pygame.KEYDOWN):
        pygame.event.post(pygame.event.Event(kind, key=key, mod=0, unicode="", scancode=0))
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
    """All three levels in a row: field -> warning -> bosses -> level clear ... -> WIN."""
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
    for i in range(seconds(game.boss.DEATH_TIME + 0.3)):
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
    h.post(pygame.K_RETURN)
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
    run(seconds(game.boss.DEATH_TIME + 1.7), clear_rocks=True)
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
    run(seconds(carrier.DEATH_TIME + 0.3))
    assert not game.enemies, "drones die with the carrier"
    run(seconds(1.6))
    assert game.state == State.LEVEL_CLEAR, game.state
    run(seconds(1.2))
    h.shot("level2_clear")

    # Level 3: MK III with BLAST and ULTIMATE, three waves.
    h.post(pygame.K_RETURN)
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
    run(seconds(Carrier.DEATH_TIME + 1.7), clear_rocks=True)
    assert game.wave_index == 2 and game.phase == Phase.FIELD, (game.wave_index, game.phase)

    # Wave 3: the final boss.
    game.distance = game.wave.length
    game.ship.hp = 5
    run(seconds(1.0), clear_rocks=True)
    assert game.phase == Phase.WARNING and game.ship.hp == MK3.max_hp
    assert game.is_final_boss() and game._music_track() is None, "silence during the warning"
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
    run(seconds(boss.DEATH_TIME + 1.9))
    assert game.state == State.WIN, game.state
    run(seconds(1.0))
    h.shot("win")
    assert game.record_rank and game.save.unlocked == 3


def test_save(h):
    """Records, unlocks and the ship survive a reload; a corrupt file doesn't crash."""
    game = h.game
    game.save.add_record(4321, 2)
    game.save.unlock(3)
    game.choose_hull(TITAN)
    reloaded = SaveData(h.save_path)
    assert reloaded.records == game.save.records and reloaded.unlocked == 3
    assert reloaded.best == game.save.best > 0 and reloaded.ship == "TITAN"
    with open(h.save_path, "w") as f:
        f.write("{not json")
    fresh = SaveData(h.save_path)
    assert fresh.records == [] and fresh.unlocked == 1 and fresh.ship == "ARROW"
    game.save.save()                                     # restore it for the checks below
    game.choose_hull(ARROW)


def test_title_menus(h):
    """Title: level select with LEFT/RIGHT, scores alternate in; ENTER -> hangar -> launch."""
    game = h.game
    game.save.unlock(3)
    game.save.add_record(1000, 1)
    game.to_title()
    assert game.state == State.TITLE and game.selectable_levels == 3
    h.post(pygame.K_RIGHT)
    h.post(pygame.K_RIGHT)
    assert game.start_level == 2
    game.time = 6.5                                      # attract mode: TOP SCORES panel
    game.draw()
    h.shot("title_records")
    h.post(pygame.K_RETURN)
    assert game.state == State.HANGAR and game.hangar_cursor == HULLS.index(game.hull)
    h.post(pygame.K_RIGHT)
    h.run(30)
    h.shot("hangar")
    h.post(pygame.K_ESCAPE)
    assert game.state == State.TITLE, "ESC leaves the hangar"
    h.post(pygame.K_UP)                                  # arrows open the hangar too
    assert game.state == State.HANGAR
    while HULLS[game.hangar_cursor] is not WASP:
        h.post(pygame.K_RIGHT)
    h.post(pygame.K_RETURN)
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
    game.dev, game.save = True, SaveData(None)
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
    game.dev, game.save = False, SaveData(h.save_path)


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
            ("busy_mothership", 2, True, ARROW)):
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
    ("title", test_title), ("controls", test_controls), ("weapons", test_weapons),
    ("damage", test_damage), ("balance", test_balance), ("pickups", test_pickups),
    ("campaign", test_campaign), ("save", test_save), ("menus", test_title_menus),
    ("hulls", test_hulls), ("dev", test_dev), ("retry", test_retry), ("audio", test_audio),
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
