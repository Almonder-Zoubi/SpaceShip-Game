"""Main loop and state machine."""
import math
import os
import random
from enum import Enum, auto

import pygame

from .audio import Audio
from .background import Background
from .boss import Gunship
from .entities import Asteroid
from .hud import Hud
from .particles import ParticleSystem, ScreenShake, Shockwave
from .pixelart import opaque_surface
from .pixelfont import PixelFont
from .settings import (ACCENT, BOSS_CONTACT_DAMAGE, BULLET_KNOCKBACK, DANGER, DEATH_DELAY,
                       DEFAULT_DIFFICULTY, FLAME, FPS, GOOD, LEVEL_LENGTH, LOW_H, LOW_W, MAX_DT,
                       POINTS_BOSS, POINTS_DODGE, POINTS_PER_RADIUS, ROCK_DAMAGE_BASE,
                       ROCK_DAMAGE_PER_RADIUS, ROCK_SPLIT_RADIUS, SCALE, SHIP_COLORS,
                       SHIP_MAX_HP, SMOKE, SPACE, SPARK, TEXT, TEXT_DIM, TEXT_SHADOW,
                       THROTTLE_BOOST, THROTTLE_IDLE, THROTTLE_RETRO, TITLE, WARNING_TIME, WIN_H,
                       WIN_W, WORLD_SPEED_FAST, WORLD_SPEED_SLOW)
from .ship import Ship
from .spawner import AsteroidSpawner
from .sprites import AsteroidLibrary, ship_icon
from .weapons import Laser, MachineGun


class State(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    DYING = auto()       # explosion plays, then GAME_OVER
    GAME_OVER = auto()
    WIN = auto()


class Phase(Enum):
    """Stages of a level while PLAYING."""
    FIELD = auto()       # asteroid field, progress bar fills up
    WARNING = auto()     # hull repaired, "WARNING" banner
    BOSS = auto()        # boss fight
    CLEARED = auto()     # boss destroyed, short pause before WIN


class Keys:
    """Set of held keys, indexable like pygame.key.get_pressed().

    The game fills one from KEYDOWN/KEYUP events instead of polling get_pressed(),
    which can report stale state on macOS depending on how the window got focus.
    """

    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


MOVE_KEYS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
             pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Game:
    SHIP_START = (LOW_W / 2, LOW_H - 40)

    def __init__(self, skip_to_boss=False):
        self.skip_to_boss = skip_to_boss       # testing aid: start every run at the boss
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(TITLE)
        self.canvas = opaque_surface((LOW_W, LOW_H))
        self.clock = pygame.time.Clock()
        self.font = PixelFont()
        self.hud = Hud(self.font)
        self.shake = ScreenShake()
        self.scanlines = self._make_scanlines()
        self.show_scanlines = True
        self._loading_screen()

        rng = random.Random()
        self.library = AsteroidLibrary(rng)
        self.library.prebuild(radii=range(4, 15), palettes=DEFAULT_DIFFICULTY.palettes)
        for palette in DEFAULT_DIFFICULTY.palettes:   # fragments: every small size in every colour
            self.library.prebuild(radii=range(4, 9), palettes=(palette,))
        self.background = Background(rng)
        self.ship = Ship(*self.SHIP_START)
        pygame.display.set_icon(ship_icon(self.ship.frames[0]))
        self.audio = Audio()
        self.weapons = [MachineGun(), Laser()]

        self.fire = ParticleSystem(additive=True)
        self.smoke = ParticleSystem()
        self.shockwaves = []
        self.flash = 0.0
        self.hurt_flash = 0.0

        self.held = Keys()
        self.best = 0
        self.time = 0.0
        self.new_run()
        self.set_state(State.TITLE)

    # --- setup -------------------------------------------------------------------
    def _loading_screen(self):
        self.canvas.fill(SPACE)
        self.font.draw(self.canvas, "BUILDING SPRITES...", (LOW_W // 2, LOW_H // 2), TEXT_DIM,
                       center=True)
        self._present()

    @staticmethod
    def _make_scanlines():
        lines = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        for y in range(0, WIN_H, SCALE):
            lines.fill((0, 0, 0, 38), (0, y + SCALE - 1, WIN_W, 1))
        return lines

    def new_run(self):
        self.ship.reset(*self.SHIP_START)
        self.asteroids = []
        self.spawner = AsteroidSpawner(self.library, DEFAULT_DIFFICULTY)
        self.score = 0
        self.distance = 0.0
        self.phase = Phase.FIELD
        self.phase_time = 0.0
        self.boss = None
        self.enemy_bullets = []
        self.weapon_index = 0
        for weapon in self.weapons:
            weapon.reset()
        self.fire.clear()
        self.smoke.clear()
        self.shockwaves.clear()
        self.hurt_flash = 0.0

    @property
    def weapon(self):
        return self.weapons[self.weapon_index]

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def set_phase(self, phase):
        self.phase = phase
        self.phase_time = 0.0

    # --- main loop ---------------------------------------------------------------
    def run(self):
        self.audio.play_music()
        while self.handle_events():
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.update(dt, self.held)
            self.draw()
            self._present()
        pygame.quit()

    def handle_events(self):
        """Process the event queue. Returns False when the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP:
                self.held.pressed.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.held.pressed.clear()     # avoid keys "stuck" after alt-tab
            if event.type != pygame.KEYDOWN:
                continue
            key, s = event.key, self.state
            self.held.pressed.add(key)
            if key == pygame.K_c:
                self.show_scanlines = not self.show_scanlines
            elif s == State.TITLE:
                if key in START_KEYS or key in MOVE_KEYS:
                    self.start()
                elif key == pygame.K_ESCAPE:
                    return False
            elif s == State.PLAYING:
                if key == pygame.K_p:
                    self.set_state(State.PAUSED)
                elif key == pygame.K_ESCAPE:
                    self.to_title()
                elif key == pygame.K_r:
                    self.switch_weapon()
            elif s == State.PAUSED:
                if key == pygame.K_p:
                    self.state = State.PLAYING
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s in (State.GAME_OVER, State.WIN):
                if key == pygame.K_r or key in START_KEYS:
                    self.start()
                elif key == pygame.K_ESCAPE:
                    self.to_title()
        return True

    def start(self):
        self.new_run()
        if self.skip_to_boss:
            self.distance = LEVEL_LENGTH
        self.set_state(State.PLAYING)

    def to_title(self):
        self.new_run()
        self.set_state(State.TITLE)

    def switch_weapon(self):
        self.weapon_index = (self.weapon_index + 1) % len(self.weapons)

    # --- update ------------------------------------------------------------------
    def update(self, dt, keys):
        self.time += dt
        self.state_time += dt
        if self.state == State.PAUSED:
            return

        firing = False
        if self.state == State.TITLE:
            self.ship.update(dt, Keys(), self.fire, self.smoke)
            self.ship.y = self.SHIP_START[1] + math.sin(self.time * 2) * 2   # gentle hover
        elif self.state == State.PLAYING:
            firing = keys[pygame.K_SPACE]
            self.ship.update(dt, keys, self.fire, self.smoke)
        elif self.state == State.WIN:
            self.ship.update(dt, keys, self.fire, self.smoke, autopilot=True)

        world_speed = self._world_speed()
        self.background.update(dt, world_speed)
        self._update_asteroids(dt, world_speed)
        self._update_boss(dt)
        self._update_weapons(dt, firing)
        self._update_enemy_bullets(dt)
        if self.state == State.PLAYING:
            self._check_ship_collisions()
            self._update_phase(dt, world_speed)

        self.fire.update(dt)
        self.smoke.update(dt)
        for wave in self.shockwaves:
            wave.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]
        self.shake.update(dt)
        self.flash = max(0.0, self.flash - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)

        if self.state == State.DYING and self.state_time > DEATH_DELAY:
            self.set_state(State.GAME_OVER)

    def _update_phase(self, dt, world_speed):
        """Asteroid field -> warning (hull repaired) -> boss -> cleared -> WIN."""
        self.phase_time += dt
        if self.phase == Phase.FIELD:
            self.distance += dt * world_speed
            if self.distance >= LEVEL_LENGTH:
                self.ship.hp = SHIP_MAX_HP          # full health for the boss fight
                self.set_phase(Phase.WARNING)
        elif self.phase == Phase.WARNING and self.phase_time >= WARNING_TIME:
            self.boss = Gunship()
            self.set_phase(Phase.BOSS)
        elif self.phase == Phase.CLEARED and self.phase_time >= 1.5:
            self.best = max(self.best, self.score)
            self.set_state(State.WIN)

    def _update_boss(self, dt):
        if not self.boss:
            return
        if self.boss.update(dt, self) == "defeated":
            self._boss_destroyed()
        if not self.boss.targetable and self.enemy_bullets:
            for b in self.enemy_bullets:          # a dying boss's bullets fizzle out
                self.fire.burst(b.x, b.y, 3, 30, 0.2, SPARK, size=(1, 1))
            self.enemy_bullets.clear()
        if (self.state == State.PLAYING and self.boss.fighting and not self.ship.invulnerable
                and self.boss.collides_with(self.ship)):
            self._hurt_ship(BOSS_CONTACT_DAMAGE, self.boss.x, self.boss.y)

    def _boss_destroyed(self):
        b = self.boss
        self.explosion(b.x, b.y, size=3.0)
        for _ in range(6):
            self.explosion(*b.random_hull_point(), size=1.2)
        self.shockwaves.append(Shockwave(b.x, b.y, max_radius=110, duration=0.8))
        self.flash = 0.15
        self.shake.add(1.0)
        self.audio.play_crash()
        if self.state == State.PLAYING:
            self.score += POINTS_BOSS
            self.set_phase(Phase.CLEARED)

    def explosion(self, x, y, size=1.0):
        """Generic fiery blast (used by the boss death sequence)."""
        self.fire.burst(x, y, int(25 * size), 60 + 50 * size, 0.6, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, int(8 * size), 150, 0.3, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, int(12 * size), 40, 1.0, SMOKE, size=(2, 3), drag=1.8)
        self.shockwaves.append(Shockwave(x, y, max_radius=int(14 * size), duration=0.3))
        self.shake.add(0.12 * size)

    def _update_enemy_bullets(self, dt):
        ship = self.ship
        kept = []
        for b in self.enemy_bullets:
            b.update(dt)
            if b.offscreen:
                continue
            if self.state == State.PLAYING and ship.alive and not ship.invulnerable:
                sx, sy = ship.topleft
                mx, my = int(b.x) - sx, int(b.y) - sy
                w, h = ship.mask.get_size()
                if 0 <= mx < w and 0 <= my < h and ship.mask.get_at((mx, my)):
                    self.fire.burst(b.x, b.y, 8, 60, 0.25, SPARK, size=(1, 1))
                    self._hurt_ship(b.damage, b.x, b.y, knockback=BULLET_KNOCKBACK)
                    continue
            kept.append(b)
        self.enemy_bullets = kept

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

    def _update_asteroids(self, dt, world_speed):
        # Rocks spawn in the asteroid field (and on the title screen as ambience).
        if self.state == State.TITLE or (self.state == State.PLAYING and self.phase == Phase.FIELD):
            self.asteroids += self.spawner.update(dt, world_speed)
        for rock in self.asteroids:
            rock.update(dt, world_speed)
        kept = []
        for rock in self.asteroids:
            if rock.offscreen:
                if self.state == State.PLAYING:
                    self.score += POINTS_DODGE
            else:
                kept.append(rock)
        self.asteroids = kept

    def _update_weapons(self, dt, firing):
        """Every weapon keeps simulating (bullets in flight, laser cooling); only the active one fires."""
        targets = list(self.asteroids)
        if self.boss and self.boss.targetable:
            targets.append(self.boss)
        for weapon in self.weapons:
            active = firing and weapon is self.weapon and self.ship.alive
            for hit in weapon.update(dt, active, self.ship, targets, self.fire):
                if hit.target is self.boss:
                    self._damage_boss(hit)
                else:
                    self._damage_rock(hit)

    def _damage_boss(self, hit):
        self.boss.damage(hit.damage, flash=not hit.continuous)
        if not hit.continuous:
            self.fire.burst(hit.x, hit.y, 3, 50, 0.15, SPARK, size=(1, 1))

    def _damage_rock(self, hit):
        rock = hit.target
        if rock.destroyed or rock not in self.asteroids:
            return
        rock.damage(hit.damage, flash=not hit.continuous)
        rock.push(hit.dx, hit.dy, hit.push)
        chips = 1 if hit.continuous and random.random() < 0.3 else 0 if hit.continuous else 2
        colors = rock.art.palette[:0:-1]
        for _ in range(chips):
            a = random.uniform(0, math.tau)
            self.smoke.emit(hit.x, hit.y, math.cos(a) * 40, math.sin(a) * 40,
                            random.uniform(0.2, 0.5), colors, drag=2)
        if rock.destroyed:
            self._destroy_rock(rock, scored=True)

    def _destroy_rock(self, rock, scored):
        """Explode a rock; big ones break into smaller fragments."""
        r = rock.radius
        colors = rock.art.palette[:0:-1]    # light -> dark, without outline
        self.smoke.burst(rock.x, rock.y, 8 + r * 3, 40 + r * 4, 1.0, colors, size=(1, 2), drag=1.5)
        self.fire.burst(rock.x, rock.y, 4 + r * 2, 50 + r * 5, 0.45, FLAME[:4], size=(1, 2), drag=3)
        self.shockwaves.append(Shockwave(rock.x, rock.y, max_radius=r * 2 + 4, duration=0.3,
                                         color=colors[0]))
        self.shake.add(0.04 + r * 0.012)
        if rock in self.asteroids:
            self.asteroids.remove(rock)
        if scored:
            self.score += r * POINTS_PER_RADIUS
        if r >= ROCK_SPLIT_RADIUS:
            self._split(rock)

    def _split(self, rock):
        r = rock.radius
        count = 2 if r < 12 else 3
        base = random.uniform(0, math.tau)
        for i in range(count):
            art = self.library.pick(max(4, int(r * 0.4)), max(4, int(r * 0.6)),
                                    (rock.art.palette_name,))
            a = base + math.tau * i / count + random.uniform(-0.4, 0.4)
            speed = random.uniform(25, 55)
            dx, dy = math.cos(a), math.sin(a)
            self.asteroids.append(Asteroid(
                art, rock.x + dx * r * 0.5, rock.y + dy * r * 0.5,
                rock.vx + dx * speed, rock.vy * 0.8 + dy * speed,
                spin=random.choice((-1, 1)) * random.uniform(1.5, 3.5)))

    def _check_ship_collisions(self):
        if self.ship.invulnerable:
            return
        for rock in self.asteroids:
            if rock.collides_with(self.ship):
                damage = ROCK_DAMAGE_BASE + ROCK_DAMAGE_PER_RADIUS * rock.radius
                self._destroy_rock(rock, scored=False)
                self._hurt_ship(damage, rock.x, rock.y)
                return

    def _hurt_ship(self, damage, from_x, from_y, **kwargs):
        if self.state != State.PLAYING:
            return
        died = self.ship.take_hit(damage, from_x, from_y, **kwargs)
        self.shake.add(0.45)
        self.hurt_flash = 0.25
        if died:
            self._ship_destroyed()

    def _ship_destroyed(self):
        ship = self.ship
        ship.alive = False
        x, y = ship.x, ship.y
        hull = [SHIP_COLORS[c] for c in "WLRGDr"]
        self.fire.burst(x, y, 90, 150, 0.9, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, 30, 230, 0.35, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, 40, 60, 1.4, SMOKE, size=(2, 3), drag=1.8)
        self.smoke.burst(x, y, 30, 120, 1.3, hull, size=(1, 2), drag=0.8)
        self.shockwaves.append(Shockwave(x, y, max_radius=46))
        self.shockwaves.append(Shockwave(x, y, max_radius=24, duration=0.3, color=(255, 255, 255)))
        self.shake.add(0.9)
        self.flash = 0.12
        self.audio.play_crash()
        self.best = max(self.best, self.score)
        self.set_state(State.DYING)

    # --- draw --------------------------------------------------------------------
    def draw(self):
        c = self.canvas
        c.fill(SPACE)
        self.background.draw(c)
        self.smoke.draw(c)
        for rock in self.asteroids:
            rock.draw(c)
        if self.boss:
            self.boss.draw(c)
        if self.ship.alive:
            self.ship.draw_flames(c)
            self.ship.draw(c)
        for weapon in self.weapons:
            weapon.draw(c)
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
        self.hud.draw(c, self.ship, self.score, max(self.best, self.score),
                      self.distance / LEVEL_LENGTH, self.weapon, self.time, boss=self.boss)
        if s == State.PLAYING and self.phase == Phase.WARNING:
            self._draw_warning(c)
        if s == State.PAUSED:
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            c.blit(shade, (0, 0))
            self.hud.banner(c, "PAUSED", "P TO RESUME  -  ESC FOR MENU", blink_on=blink)
        elif s == State.GAME_OVER:
            self.hud.banner(c, "GAME OVER", "PRESS R TO RESTART", title_color=DANGER, blink_on=blink)
            self.font.draw(c, f"SCORE {self.score}", (LOW_W // 2, LOW_H // 2 + 40),
                           TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        elif s == State.WIN and self.state_time > 0.8:
            self.hud.banner(c, "YOU WIN!", "PRESS R TO PLAY AGAIN", title_color=GOOD, blink_on=blink)

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
        self.font.draw(c, "BOSS APPROACHING: GUNSHIP", (LOW_W // 2, 124), TEXT, shadow=TEXT_SHADOW,
                       center=True)
        if self.phase_time < 2.0:
            self.font.draw(c, "HULL REPAIRED", (LOW_W // 2, 160), GOOD, shadow=TEXT_SHADOW,
                           center=True)

    def _draw_title(self, c, blink):
        f = self.font
        f.draw(c, "DODGING", (LOW_W // 2, 24), ACCENT, scale=4, shadow=DANGER, center=True)
        f.draw(c, "ASTEROID", (LOW_W // 2, 58), TEXT, scale=4, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(c, "PRESS ENTER", (LOW_W // 2, 100), TEXT, scale=2, shadow=TEXT_SHADOW, center=True)
        lines = ("ARROWS / WASD  MOVE",
                 "UP  BOOST     DOWN  RETRO",
                 "SPACE  FIRE    R  GUN / LASER",
                 "P PAUSE   C SCANLINES   ESC QUIT")
        for i, line in enumerate(lines):
            f.draw(c, line, (LOW_W // 2, 128 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if self.best:
            f.draw(c, f"HI {self.best}", (LOW_W // 2, 8), ACCENT, shadow=TEXT_SHADOW, center=True)

    def _present(self):
        ox, oy = self.shake.offset()
        self.window.fill(SPACE)
        self.window.blit(pygame.transform.scale(self.canvas, (WIN_W, WIN_H)), (ox * SCALE, oy * SCALE))
        if self.show_scanlines:
            self.window.blit(self.scanlines, (0, 0))
        pygame.display.flip()


def run_smoke_test(shots_dir=None):
    """Drive the game headlessly through every state and mechanic; optionally save screenshots."""
    game = Game()
    # Regression: an alpha channel on the canvas turns sprites into black boxes on macOS.
    assert game.canvas.get_masks()[3] == 0, "canvas must not have an alpha channel"
    dt = 1 / FPS

    def shot(name):
        if shots_dir:
            os.makedirs(shots_dir, exist_ok=True)
            pygame.image.save(pygame.transform.scale(game.canvas, (WIN_W, WIN_H)),
                              os.path.join(shots_dir, f"{name}.png"))

    def run(frames, keys=Keys(), clear_rocks=False):
        for _ in range(frames):
            if clear_rocks:
                game.asteroids.clear()
            game.update(dt, keys)
            game.draw()

    def post(kind, key):
        pygame.event.post(pygame.event.Event(kind, key=key, mod=0, unicode="", scancode=0))
        game.handle_events()

    run(90)
    shot("title")

    # Real input path: key events -> held keys -> ship moves diagonally, never rotates.
    game.start()
    pygame.event.clear()
    x0, y0 = game.ship.x, game.ship.y
    post(pygame.KEYDOWN, pygame.K_UP)
    post(pygame.KEYDOWN, pygame.K_RIGHT)
    run(30, game.held, clear_rocks=True)
    assert game.ship.x > x0 + 5 and game.ship.y < y0 - 5, "diagonal movement"
    assert game.ship.throttle > 0.9, "UP boosts the engine"
    assert game.ship.tilt_index == 3 and game.ship.forward[0] > 0.4, "UP+RIGHT leans like '/'"
    shot("diagonal")
    post(pygame.KEYUP, pygame.K_UP)
    post(pygame.KEYUP, pygame.K_RIGHT)
    run(40, game.held, clear_rocks=True)
    assert math.hypot(game.ship.vx, game.ship.vy) < 5, "ship stops quickly after release"
    assert game.ship.tilt_index == 0, "straightens after release"
    post(pygame.KEYDOWN, pygame.K_DOWN)
    run(30, game.held, clear_rocks=True)
    assert game.ship.throttle < 0.2, "DOWN shrinks the flames"
    post(pygame.KEYUP, pygame.K_DOWN)

    # Weapon switch.
    post(pygame.KEYDOWN, pygame.K_r)
    assert game.weapon.name == "LASER"

    def rock_ahead(radius):
        art = game.library.pick(radius, radius, DEFAULT_DIFFICULTY.palettes)
        fx, fy = game.ship.forward
        return Asteroid(art, game.ship.x + fx * 50, game.ship.y + fy * 50, 0, 0, 0)

    # Laser: sustained fire destroys a big rock, which splits.
    game.start()
    game.switch_weapon()
    big = rock_ahead(12)
    game.asteroids = [big]
    fire_keys = Keys(pygame.K_SPACE)
    for i in range(240):
        game.update(dt, fire_keys)
        game.draw()
        if i == 20:
            shot("laser")
        if big not in game.asteroids:
            break
    assert big not in game.asteroids, f"laser failed, hp {big.hp:.0f}/{big.max_hp:.0f}"
    assert len(game.asteroids) >= 2, "big rock should split into fragments"
    assert game.score > 0

    # Shots slow a falling rock down (but never stop it).
    game.start()
    game.weapon_index = 0
    slow = rock_ahead(12)
    slow.vy = 90.0
    game.asteroids = [slow]
    for _ in range(30):
        game.update(dt, fire_keys)
    assert slow.vy < 85 and slow.vy >= 12, f"push: vy {slow.vy:.1f}"

    # Machine gun kills a small rock.
    game.start()
    small = rock_ahead(5)
    game.asteroids = [small]
    for i in range(120):
        game.update(dt, fire_keys)
        game.draw()
        if i == 10:
            shot("gun")
        if small not in game.asteroids:
            break
    assert small not in game.asteroids, "machine gun failed"

    # Laser overheats.
    game.start()
    game.switch_weapon()
    run(int(3 / dt), fire_keys, clear_rocks=True)
    assert game.weapon.overheated

    # Asteroid collision costs health, then invulnerability protects.
    game.start()
    game.asteroids = [Asteroid(game.library.pick(10, 10, DEFAULT_DIFFICULTY.palettes),
                               game.ship.x, game.ship.y, 0, 0, 0)]
    run(1)
    assert 0 < game.ship.hp < 100 and game.ship.invulnerable
    shot("hurt")

    # Losing all health -> explosion -> game over.
    game.ship.invulnerable_time = 0
    game.ship.hp = 1
    game.asteroids = [Asteroid(game.library.variants[-1], game.ship.x, game.ship.y, 0, 0, 0)]
    for i in range(int((DEATH_DELAY + 0.3) * FPS)):
        game.update(dt, Keys())
        game.draw()
        if i == 8:
            shot("explosion")
    assert game.state == State.GAME_OVER, game.state
    shot("game_over")

    # Boss balance: the rocket is strength-times weaker in a damage race.
    from .boss import GUNSHIP_SPEC
    from .settings import PLAYER_DPS
    ratio = (GUNSHIP_SPEC.hp / PLAYER_DPS) / (SHIP_MAX_HP / GUNSHIP_SPEC.dps)
    assert abs(ratio - GUNSHIP_SPEC.strength) < 1e-6, ratio

    # Boss flow: end of field -> warning (hull repaired) -> boss fight -> defeated -> WIN.
    game.start()
    game.ship.hp = 30
    game.distance = LEVEL_LENGTH
    run(2)
    assert game.phase == Phase.WARNING and game.ship.hp == SHIP_MAX_HP
    run(int(1.0 / dt))
    shot("warning")
    run(int(WARNING_TIME / dt))
    assert game.phase == Phase.BOSS and game.boss is not None
    run(int(3.0 / dt), clear_rocks=True)
    assert game.boss.fighting
    shot("boss_enter")
    game.ship.hp = 10 ** 9          # watch the boss attack without dying
    run(int(4.0 / dt), clear_rocks=True)
    assert game.ship.hp < 10 ** 9, "boss bullets should hit a rocket that sits still"
    shot("boss_attack")
    hp0 = game.boss.hp
    game.ship.x = game.boss.x
    for _ in range(60):
        game.ship.x = game.boss.x
        game.update(dt, fire_keys)
    assert game.boss.hp < hp0, "player bullets damage the boss"
    game.boss.hp = game.boss.max_hp * 0.4             # enraged phase
    run(int(5.0 / dt), clear_rocks=True)
    shot("boss_enraged")
    game.boss.damage(game.boss.max_hp)
    assert game.boss.state == "dying"
    for i in range(int((game.boss.DEATH_TIME + 0.3) / dt)):
        game.update(dt, Keys())
        game.draw()
        if i == 40:
            shot("boss_dying")
    assert game.phase == Phase.CLEARED
    run(int(1.6 / dt))
    assert game.state == State.WIN, game.state
    shot("win")

    # A busy minute of normal play must not crash.
    game.start()
    game.ship.hp = 10 ** 9
    game.distance = -10 ** 9          # stay in the asteroid field
    pattern = [Keys(pygame.K_UP, pygame.K_SPACE), Keys(pygame.K_LEFT, pygame.K_SPACE),
               Keys(pygame.K_DOWN, pygame.K_RIGHT), Keys(pygame.K_SPACE)]
    for i in range(3600):
        if i % 600 == 0:
            game.switch_weapon()
        game.update(dt, pattern[(i // 90) % len(pattern)])
        game.draw()
        if i == 1800:
            shot("busy")
    assert game.state == State.PLAYING, game.state
    pygame.quit()
    print("smoke test OK")
