# Dodging Asteroid

A small 2D arcade game built with [Pygame](https://www.pygame.org/) for the "Objektorientierte Skriptsprachen" course (ESA3). Steer a rocket, dodge falling asteroids, and try to survive.

## How to play

- **Arrow keys** — move the rocket
- **R** — restart after game over / win
- **Esc** — quit
- Survive and reach a score of **10** to win. Getting hit by an asteroid ends the game.

## Setup

Requires Python 3.9–3.13 (pygame does not yet ship prebuilt wheels for 3.14).

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 ESA3.py
```

Run the command from the project root so the relative `images/`, `astroids/`, and `sounds/` asset paths resolve correctly.

## Project structure

```
ESA3.py        # game logic
images/        # player sprite and background
astroids/      # asteroid sprites (randomly chosen per enemy)
sounds/        # background music and collision sound
```
