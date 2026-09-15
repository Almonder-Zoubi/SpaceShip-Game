#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25
@author: Almonder Zoubi
"""
# Import & Initialization
import pygame
import random
from pygame.locals import *
import os
import sys
pygame.init()

# Display Configuration
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Dodging Asteroid")
icon = pygame.image.load('images/rocket.png')
pygame.display.set_icon(icon)
bg = pygame.image.load('images/space_img.png')
bg = pygame.transform.scale(bg, (800, 600))
# Colors
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)

# Fonts
font = pygame.font.Font(None, 36)
# Entities
class Player:
    def __init__(self, x, y, width, height, speed):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.image = pygame.transform.scale(
            pygame.image.load('images/rocket.png'), (self.width, self.height)
        )
        self.sound = pygame.mixer.Sound('sounds/crash.wav')

    def draw(self):
        # Draw the player's ship
        screen.blit(self.image, (self.x, self.y))
        # pygame.draw.rect(screen, white, [self.x, self.y, self.width, self.height])

    def hit_sound(self):
        self.sound.play()

    def move_left(self):
        if self.x > 0:
            self.x -= self.speed

    def move_right(self):
        if self.x < screen_width - self.width:
            self.x += self.speed

    def move_up(self):
        if self.y > 0:
            self.y -= self.speed

    def move_down(self):
        if self.y < screen_height - self.height:
            self.y += self.speed

class Enemy:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.image_path = os.path.join("astroids", random.choice(os.listdir("astroids")))
        self.image = pygame.image.load(self.image_path)
        self.image = pygame.transform.scale(self.image, (self.size, self.size))

    def draw(self):
        # Draw the enemy
        screen.blit(self.image, (self.x, self.y))
        # pygame.draw.rect(screen, red, [self.x, self.y, self.size, self.size])

    def move(self):
        self.y += self.speed

# Action -- ALTER
# Assignment
player = Player(screen_width // 2 - 45, screen_height - 150, 90, 120, 6)
enemies = []
enemy_spawn_delay = 60
enemy_spawn_counter = 0
score = 0
game_over_flag = False
win_flag = False
game_running = True
clock = pygame.time.Clock()

def move_enemies():
    '''
    Move the atroids down the screen
    and check for collision with player. If there is a collision, end game.
    it is not included within the Enemy class because it primarily handles the 
    movement logic for all enemies in the game, not just a single enemy instance
    '''
    
    global score, game_over_flag, win_flag, game_running
    for enemy in enemies:
        enemy.move()
        if enemy.y > screen_height:
            enemies.remove(enemy)
            score += 1

        # Check collision with player
        if (
            player.x < enemy.x + enemy.size
            and player.x + player.width > enemy.x
            and player.y < enemy.y + enemy.size
            and player.y + player.height > enemy.y
        ):
            player.hit_sound()
            game_over_flag = True
            game_running = False

def display_score(score):
    score_text = font.render(f"Score: {score}", True, white)
    screen.blit(score_text, (10, 10))
def game_over():
    game_over_text = font.render(
        "Game Over! Press R to restart.", True, red)
    screen.blit(
        game_over_text,
        (
            screen_width // 2 - game_over_text.get_width() // 2,
            screen_height // 2 - game_over_text.get_height() // 2,
        ),
    )
def game_win():
    win_text = font.render("You Win! Press R to restart.", True, green)
    screen.blit(
        win_text,
        (
            screen_width // 2 - win_text.get_width() // 2,
            screen_height // 2 - win_text.get_height() // 2,
        ),
    )
def restart():
    global score, game_over_flag, win_flag, game_running
    player.x = screen_width // 2 - player.width // 2
    player.y = screen_height - 150
    score = 0
    enemies.clear()
    game_over_flag = False
    win_flag = False
    game_running = True

pygame.mixer.music.load('sounds/nes.mp3')  
pygame.mixer.music.play(-1)  # Play the background music in a loop

# Loop
while True:
    while game_running:
        screen.blit(bg, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move_left()
        if keys[pygame.K_RIGHT]:
            player.move_right()
        if keys[pygame.K_UP]:
            player.move_up()
        if keys[pygame.K_DOWN]:
            player.move_down()
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

        # Enemy spawning
        if enemy_spawn_counter <= 0:
            enemy_x = random.randint(10, screen_width-10)
            enemy_size = random.randint(45,65)
            enemies.append(Enemy(enemy_x, -50, enemy_size, speed=5))
            enemy_spawn_counter = enemy_spawn_delay
        else:
            enemy_spawn_counter -= 1

        move_enemies()

        for enemy in enemies:
            enemy.draw()
        player.draw()

        display_score(score)

        if game_over_flag:
            game_over()
        elif score >= 10:
            win_flag = True
            game_win()
            game_running = False

        pygame.display.update()
        clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart()
    # Redisplay
    pygame.display.flip()
    clock.tick(60)