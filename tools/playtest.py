"""Headless bot playtest: a simple autopilot flies levels and reports how it went.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/playtest.py [levels] [--maxed]
        levels   e.g. 1-4 or 2,3 or 10 (default 1-4)
        --maxed  every item, maxed upgrades, a level 5 wingman (otherwise a new player)
        --tank   refill the hull at half (every level completes; damage = difficulty)
        --seed N reproducible run

The bot is no substitute for a human (it dodges badly and never uses the mouse), but it
plays every system for real: fields, minions, bosses, boosts, combo, wingmen, gifts, coins.
It prints per level: result, attempts, time, damage taken, rank, coins banked, combo, and
the slowest frame. Uses a temporary save file (never the player's).
"""
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from game.config.display import LOW_W  # noqa: E402
from game.config.tuning import UPGRADE_TIERS, WINGMAN_XP  # noqa: E402
from game.core.input import Keys  # noqa: E402
from game.flow.game import Game  # noqa: E402
from game.flow.states import State  # noqa: E402
from game.levels.data import LEVELS  # noqa: E402
from game.progression.upgrades import TRACK_IDS  # noqa: E402

DT = 1 / 60
MAX_ATTEMPTS = 4


def _threats(game):
    """Things that will cross the ship's row soon: (seconds until then, x there, size)."""
    ship = game.ship
    out = []
    for obj, size in ([(b, 3) for b in game.enemy_bullets] + [(r, r.radius) for r in game.asteroids]
                      + [(e, 7) for e in game.enemies]):
        vy = getattr(obj, "vy", 60) or 1e-3
        dy = ship.y - obj.y
        if dy < -10 or vy <= 0:
            continue
        t = dy / vy
        if t > 0.9:
            continue
        x = obj.x + getattr(obj, "vx", 0) * t
        out.append((t, x, size))
    return out


def bot_keys(game):
    """Fire all the time, sidestep what will cross the ship's row soon, otherwise line up
    under the nearest target; press T when the ULTIMATE is ready."""
    ship = game.ship
    keys = [pygame.K_SPACE]
    half = ship.w / 2 + 3
    blocked = [(t, x, size) for t, x, size in _threats(game) if abs(x - ship.x) < size + half]
    if blocked:
        t, x, size = min(blocked)
        free_left = ship.x - (x - size - half)
        free_right = (x + size + half) - ship.x
        go_left = free_left < free_right if 30 < ship.x < 290 else ship.x > 160
        keys.append(pygame.K_LEFT if go_left else pygame.K_RIGHT)
    else:
        targets = [t for t in game.weapon_targets() if t.y < ship.y - 20]
        if targets:
            goal = min(targets, key=lambda t: abs(t.x - ship.x) + (ship.y - t.y) * 0.3)
            if goal.x < ship.x - 4:
                keys.append(pygame.K_LEFT)
            elif goal.x > ship.x + 4:
                keys.append(pygame.K_RIGHT)
    width = getattr(game.hazard, "width", None)            # the hive walls (level 10)
    if width:
        left, right = width(-1, ship.y) + ship.w, LOW_W - width(1, ship.y) - ship.w
        if ship.x < left + 6 or ship.x > right - 6:
            keys = [k for k in keys if k not in (pygame.K_LEFT, pygame.K_RIGHT)]
            keys.append(pygame.K_RIGHT if ship.x < left + 6 else pygame.K_LEFT)
    if ship.y < 190:
        keys.append(pygame.K_DOWN)
    if game.ship.loadout.ultimate and game.ultimate.ready:
        game.fire_ultimate()
    return Keys(*keys)


def play_level(game, index, report, tank=False):
    """Attempts until cleared (or MAX_ATTEMPTS). Returns True if cleared.
    tank: the hull is refilled whenever it drops below half (counted as refills)."""
    score = game.score if game.level_index == index else 0
    for attempt in range(1, MAX_ATTEMPTS + 1):
        game.start(index, score)
        game.radio = None
        worst, frames, t0 = 0.0, 0, time.perf_counter()
        best_combo = refills = 0
        while game.state == State.PLAYING or game.state == State.DYING:
            if tank and game.ship.hp < game.ship.max_hp / 2 and game.ship.alive:
                game.ship.hp = game.ship.max_hp
                refills += 1
            track = game.audio.track
            start = time.perf_counter()
            game.update(DT, bot_keys(game))
            if frames % 30 == 0:
                game.draw()
            if game.audio.track == track:        # loading music stalls the dummy driver
                worst = max(worst, time.perf_counter() - start)
            frames += 1
            best_combo = max(best_combo, game.combo)
            if frames > 60 * 60 * 8:
                break
        cleared = game.state in (State.LEVEL_CLEAR, State.WIN, State.WARP)
        level = LEVELS[index]
        report.append({
            "level": level.number, "attempt": attempt, "cleared": cleared,
            "game_s": round(frames * DT), "damage": int(game.stats.damage_taken),
            "rank": game.level_rank or "-", "coins": game.payout.total if game.payout else 0,
            "pending": game.pending_coins, "combo": best_combo, "refills": refills,
            "boss": f"{int(game.stats.boss_time)}/{int(game.stats.boss_par)}",
            "hp": game.ship.max_hp,
            "worst_ms": round(worst * 1000, 1), "wall_s": round(time.perf_counter() - t0, 1),
        })
        if cleared:
            return True
    return False


def main():
    args = sys.argv[1:]
    seed = None
    if "--seed" in args:
        seed = int(args[args.index("--seed") + 1])
        random.seed(seed)
    maxed = "--maxed" in args
    plain = [a for i, a in enumerate(args)
             if not a.startswith("--") and (i == 0 or args[i - 1] != "--seed")]
    spec = plain[0] if plain else "1-4"
    if "-" in spec:
        lo, hi = map(int, spec.split("-"))
        numbers = range(lo, hi + 1)
    else:
        numbers = [int(n) for n in spec.split(",")]
    save = os.path.join(tempfile.mkdtemp(), "save.json")
    game = Game(save_path=save)
    game.library.finish()                    # rocks the menus would build in the background
    if maxed:
        game.inventory.grant_all()
        game.save.upgrades = {t: UPGRADE_TIERS for t in TRACK_IDS}
        game.save.choose_wingman("PIP")
        game.save.wingmen_xp["PIP"] = WINGMAN_XP[-1]
        game.save.secondary = "ROCKET POD"
    report = []
    for number in numbers:
        index = number - 1
        if not play_level(game, index, report, tank="--tank" in args):
            break
        if game.state == State.LEVEL_CLEAR:              # take the first gift, like a player
            options = game.inventory.gift_options(game.level_key)
            if options:
                game.inventory.claim(game.level_key, options[0])
    print(f"playtest {'maxed' if maxed else 'new player'} (seed {seed})")
    print(" lvl try  ok   time  dmg/hp refill rank coins pend combo worst_ms wall_s  boss/par s")
    for r in report:
        print(f" {r['level']:>3} {r['attempt']:>3} {'Y' if r['cleared'] else 'N':>3} "
              f"{r['game_s']:>5}s {r['damage']:>4}/{r['hp']:<4} {r['refills']:>3} "
              f"{r['rank']:>4} {r['coins']:>5} {r['pending']:>4} {r['combo']:>5} "
              f"{r['worst_ms']:>8} {r['wall_s']:>6}  {r['boss']:>8}")
    print(f"bank {game.save.coins} CR, owned {len(game.save.owned)} items, "
          f"achievements {game.save.achievements}")
    pygame.quit()


if __name__ == "__main__":
    main()
