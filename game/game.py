"""Main loop and state machine."""
import math
import os
import random
from enum import Enum, auto

import pygame

from .audio import Audio
from .background import Background
from .entities import Asteroid, Ship, world_speed_for
from .hud import Hud
from .particles import ParticleSystem, ScreenShake, Shockwave
from .pixelfont import PixelFont
from .settings import (ACCENT, DANGER, DEATH_DELAY, DEFAULT_DIFFICULTY, FLAME, FPS, GOOD,
                       LOW_H, LOW_W, MAX_DT, SCALE, SHIP_COLORS, SMOKE, SPACE, SPARK, TEXT,
                       TEXT_DIM, TEXT_SHADOW, TITLE, WIN_H, WIN_SCORE, WIN_W,
                       WORLD_SPEED_BOOST, WORLD_SPEED_RETRO)
from .spawner import AsteroidSpawner
from .sprites import AsteroidLibrary, ship_icon


class State(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    DYING = auto()       # explosion plays, then GAME_OVER
    GAME_OVER = auto()
    WIN = auto()


class Keys:
    """Stand-in for pygame.key.get_pressed(): used for the title demo and tests."""

    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


class Game:
    SHIP_START = (LOW_W / 2, LOW_H - 40)

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((LOW_W, LOW_H))
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
        self.background = Background(rng)
        self.ship = Ship(*self.SHIP_START)
        pygame.display.set_icon(ship_icon(self.ship.frames))
        self.audio = Audio()

        self.fire = ParticleSystem(additive=True)
        self.smoke = ParticleSystem()
        self.shockwaves = []
        self.flash = 0.0

        self.best = 0
        self.time = 0.0
        self.new_run()
        self.set_state(State.TITLE)

    # --- setup -------------------------------------------------------------------
    def _loading_screen(self):
        self.canvas.fill(SPACE)
        self.font.draw(self.canvas, "GENERATING ASTEROIDS...", (LOW_W // 2, LOW_H // 2), TEXT_DIM,
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
        self.fire.clear()
        self.smoke.clear()
        self.shockwaves.clear()

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    # --- main loop ---------------------------------------------------------------
    def run(self):
        self.audio.play_music()
        while self.handle_events():
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.update(dt, pygame.key.get_pressed())
            self.draw()
            self._present()
        pygame.quit()

    def handle_events(self):
        """Process the event queue. Returns False when the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            key, s = event.key, self.state
            if key == pygame.K_c:
                self.show_scanlines = not self.show_scanlines
            elif s == State.TITLE:
                if key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start()
                elif key == pygame.K_ESCAPE:
                    return False
            elif s == State.PLAYING:
                if key == pygame.K_p:
                    self.set_state(State.PAUSED)
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s == State.PAUSED:
                if key == pygame.K_p:
                    self.state = State.PLAYING
                elif key == pygame.K_ESCAPE:
                    self.to_title()
            elif s in (State.GAME_OVER, State.WIN):
                if key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    self.start()
                elif key == pygame.K_ESCAPE:
                    self.to_title()
        return True

    def start(self):
        self.new_run()
        self.set_state(State.PLAYING)

    def to_title(self):
        self.new_run()
        self.set_state(State.TITLE)

    # --- update ------------------------------------------------------------------
    def update(self, dt, keys):
        self.time += dt
        self.state_time += dt
        if self.state == State.PAUSED:
            return

        if self.state == State.TITLE:
            self.ship.update(dt, Keys(), self.fire, self.smoke)
            self.ship.y = self.SHIP_START[1] + math.sin(self.time * 2) * 2   # gentle hover
        elif self.state == State.PLAYING:
            self.ship.update(dt, keys, self.fire, self.smoke)
        elif self.state == State.WIN:
            self.ship.update(dt, keys, self.fire, self.smoke, autopilot=True)

        world_speed = world_speed_for(self.ship.throttle, WORLD_SPEED_RETRO, WORLD_SPEED_BOOST) \
            if self.ship.alive else 0.7
        self.background.update(dt, world_speed)
        self._update_asteroids(dt, world_speed)

        self.fire.update(dt)
        self.smoke.update(dt)
        for wave in self.shockwaves:
            wave.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]
        self.shake.update(dt)
        self.flash = max(0.0, self.flash - dt)

        if self.state == State.PLAYING and self.score >= WIN_SCORE:
            self.best = max(self.best, self.score)
            self.set_state(State.WIN)
        elif self.state == State.DYING and self.state_time > DEATH_DELAY:
            self.set_state(State.GAME_OVER)

    def _update_asteroids(self, dt, world_speed):
        # Rocks keep spawning on the title screen as ambience, but never while winning.
        if self.state in (State.TITLE, State.PLAYING):
            self.asteroids += self.spawner.update(dt, world_speed)
        for rock in self.asteroids:
            rock.update(dt, world_speed)
        kept = []
        for rock in self.asteroids:
            if rock.offscreen:
                if self.state == State.PLAYING:
                    self.score += 1
            else:
                kept.append(rock)
        self.asteroids = kept

        if self.state == State.PLAYING:
            for rock in self.asteroids:
                if rock.collides_with(self.ship):
                    self._explode(rock)
                    break

    def _explode(self, rock):
        ship = self.ship
        ship.alive = False
        x, y = ship.x, ship.y
        hull = [SHIP_COLORS[c] for c in "WLRGDr"]
        self.fire.burst(x, y, 90, 150, 0.9, FLAME, size=(1, 3), drag=2.5)
        self.fire.burst(x, y, 30, 230, 0.35, SPARK, size=(1, 1), drag=1.0)
        self.smoke.burst(x, y, 40, 60, 1.4, SMOKE, size=(2, 3), drag=1.8)
        self.smoke.burst(x, y, 30, 120, 1.3, hull, size=(1, 2), drag=0.8)
        rock_colors = rock.art.palette[:0:-1]    # light -> dark, without outline
        self.smoke.burst(rock.x, rock.y, 26, 90, 1.1, rock_colors, size=(1, 2), drag=1.0)
        self.asteroids.remove(rock)
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
        if self.ship.alive:
            self.ship.draw_flames(c)
            self.ship.draw(c)
        self.fire.draw(c)
        for wave in self.shockwaves:
            wave.draw(c)
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
        self.hud.draw(c, self.score, self.best, WIN_SCORE, self.ship.throttle if self.ship.alive else 0)
        if s == State.PAUSED:
            shade = pygame.Surface((LOW_W, LOW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            c.blit(shade, (0, 0))
            self.hud.banner(c, "PAUSED", "P TO RESUME  -  ESC FOR MENU", blink_on=blink)
        elif s == State.GAME_OVER:
            self.hud.banner(c, "GAME OVER", "PRESS R TO RESTART", title_color=DANGER, blink_on=blink)
            self.font.draw(c, f"YOU DODGED {self.score} OF {WIN_SCORE}", (LOW_W // 2, LOW_H // 2 + 40),
                           TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        elif s == State.WIN and self.state_time > 0.8:
            self.hud.banner(c, "YOU WIN!", "PRESS R TO PLAY AGAIN", title_color=GOOD, blink_on=blink)

    def _draw_title(self, c, blink):
        f = self.font
        f.draw(c, "DODGING", (LOW_W // 2, 30), ACCENT, scale=4, shadow=DANGER, center=True)
        f.draw(c, "ASTEROID", (LOW_W // 2, 64), TEXT, scale=4, shadow=TEXT_SHADOW, center=True)
        if blink:
            f.draw(c, "PRESS ENTER", (LOW_W // 2, 108), TEXT, scale=2, shadow=TEXT_SHADOW, center=True)
        lines = ("ARROWS / WASD  MOVE",
                 "UP  BOOST     DOWN  RETRO",
                 "P PAUSE   C SCANLINES   ESC QUIT")
        for i, line in enumerate(lines):
            f.draw(c, line, (LOW_W // 2, 134 + i * 11), TEXT_DIM, shadow=TEXT_SHADOW, center=True)
        if self.best:
            f.draw(c, f"BEST {self.best}", (LOW_W // 2, 10), ACCENT, shadow=TEXT_SHADOW, center=True)

    def _present(self):
        ox, oy = self.shake.offset()
        self.window.fill(SPACE)
        self.window.blit(pygame.transform.scale(self.canvas, (WIN_W, WIN_H)), (ox * SCALE, oy * SCALE))
        if self.show_scanlines:
            self.window.blit(self.scanlines, (0, 0))
        pygame.display.flip()


def run_smoke_test(shots_dir=None):
    """Drive the game headlessly through every state; optionally save screenshots."""
    game = Game()
    dt = 1 / FPS
    script = [  # (frames, state to enter or None, keys)
        (90, None, Keys()),
        (1, State.PLAYING, Keys()),
        (60, None, Keys(pygame.K_UP)),
        (40, None, Keys(pygame.K_UP, pygame.K_LEFT)),
        (60, None, Keys(pygame.K_DOWN, pygame.K_RIGHT)),
        (30, None, Keys()),
    ]
    frame = 0

    def shot(name):
        if shots_dir:
            os.makedirs(shots_dir, exist_ok=True)
            pygame.image.save(pygame.transform.scale(game.canvas, (WIN_W, WIN_H)),
                              os.path.join(shots_dir, f"{name}.png"))

    for frames, state, keys in script:
        if state == State.PLAYING:
            game.start()
        for _ in range(frames):
            game.update(dt, keys)
            game.draw()
            frame += 1
        shot(f"{frame:04d}_{game.state.name.lower()}")
        if game.state != State.PLAYING and state is None and game.state != State.TITLE:
            game.start()   # got hit early; keep exercising gameplay

    # Force a collision to exercise the explosion path.
    game.start()
    art = game.library.variants[-1]
    game.asteroids.append(Asteroid(art, game.ship.x, game.ship.y, 0, 0, 0))
    for i in range(int((DEATH_DELAY + 0.3) * FPS)):
        game.update(dt, Keys())
        game.draw()
        if i == 8:
            shot("explosion")
    assert game.state == State.GAME_OVER, game.state
    shot("game_over")

    # Win path.
    game.start()
    game.score = WIN_SCORE
    for _ in range(90):
        game.update(dt, Keys())
        game.draw()
    assert game.state == State.WIN, game.state
    shot("win")
    pygame.quit()
    print("smoke test OK")
