# CLAUDE.md

Guidance for Claude (and humans) working on this repo.

## What this is

**Dodging Asteroid** — a retro (Atari / NES-style) pixel-art arcade game in Python + pygame,
built for the THB course "Objektorientierte Skriptsprachen" (ESA3). Keep the code object-oriented
and readable: it is graded coursework as well as a game.

- Developer guide (assets, randomness, workflow, recipes for new levels / bosses / modes):
  [docs/GUIDE.md](docs/GUIDE.md) — keep it in sync when adding a new kind of thing.
- Design bible (galaxies, levels 5–10, bosses, weapons, gifts, coins, wingmen, inventory,
  skins, colour/juice rules): [docs/DESIGN.md](docs/DESIGN.md) — new content follows its pillars.
- Plan and phases: [ROADMAP.md](ROADMAP.md)
- What's done / what's next: [PROGRESS.md](PROGRESS.md) — **read it first, update it last** in every session.
  Its "Snapshot" section describes the current game in one screen; the "Decisions" section is binding.

## Working with the user

- The user playtests on macOS and reports how it *feels*. Ask before adding control complexity.
- Show visual changes: `--smoke-test --shots DIR` saves screenshots of every state (headless), but
  also capture a **real window** frame (see "Verify in a real window" below) — some bugs only show there.
- Commit only when asked. Work happens on feature branches (e.g. `levels`), `main` is stable.

## Run

```bash
source .venv/bin/activate        # Python 3.9–3.13, pygame >= 2.5
python3 ESA3.py
python3 ESA3.py --boss           # skip the asteroid field, straight to the level boss
python3 ESA3.py --level 2        # start at level 2 (with --boss: straight to the Carrier)
python3 ESA3.py --level 3 --boss # Mothership
python3 ESA3.py --level 4 --boss # final boss (Leviathan)
python3 ESA3.py --dev            # dev menu: any level / wave / boss / ship, god mode, hotkeys
python3 tools/build_audio.py     # re-render sounds + music after changing game/audio/ recipes
python3 tools/build_audio.py boss gun    # ...or only some of them
```

Headless smoke test (no window, no audio device) — run after every change. It drives every state
and mechanic in named sections (title, controls, mouse, weapons, damage, balance, pickups,
campaign, level4, save, economy, inventory, upgrades, feel, menus, hulls, dev, retry, audio, busy); each section starts from its own state:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test [--shots DIR]
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 ESA3.py --smoke-test --only hulls,audio
python3 -m pyflakes ESA3.py game/ tests/ tools/     # lint (pyflakes is installed in .venv only)
```

### Verify in a real window

The dummy video driver has a different surface format than macOS, so render checks need a real
window. Script pattern (run with `PYTHONPATH=.`, saves what the window shows):

```python
import sys, pygame
from game.flow.game import Game
from game.core.input import Keys
g = Game(dev=True); g.start(); g.ship.hp = 10**9  # dev=True: never writes save.json
for i in range(180):
    g.handle_events(); dt = g.clock.tick(60) / 1000
    g.update(dt, Keys(pygame.K_SPACE, pygame.K_UP)); g.draw(); g._present()
pygame.image.save(g.window, sys.argv[1]); pygame.quit()
```

## Architecture

`ESA3.py` is only the entry point. All code lives in the `game/` package, one folder per area.
Every folder's `__init__.py` docstring lists what its modules do.

| Folder | Modules | Responsibility |
|---|---|---|
| `config/` | `display`, `palette`, `tuning`, `loadouts` | Resolution + paths, shared colours, gameplay numbers, ship models `MK1..MK4` (`Loadout`) |
| `core/` | `pixelart`, `pixelfont`, `particles`, `input`, `storage`, `options` | Engine helpers: sprite-from-rows, `CharCanvas`, `mirrored`/`outlined`, RotSprite, dithering, noise, glow; 5x7 font; `ParticleSystem`/`Shockwave`/`ScreenShake`; `Keys` + key groups, `Mouse` (steering target + left-click fire); `SaveData` (`save.json` v2: records, unlocks, ship, coin bank, best rank per level, inventory, upgrade tiers, options); `Options` (volumes, reduce shake / flashes) |
| `background/` | `nebula`, `planet`, `starfield`, `background` | One layer per module; `Background` draws them back to front |
| `player/` | `hulls`, `art`, `ship` | `Hull` shapes (ARROW, WASP, TITAN, LANCE: rows, nozzles, barrels, stat multipliers); MK paint jobs + banked/lean frames; `Ship` (controls, lean, throttle, flames, health) |
| `weapons/` | `base`, `gun`, `laser`, `specials` | `Hit`, `Weapon`, `raycast()`; `MachineGun`; `Laser`; `Charged` → `Blast`, `Ultimate` (+`Missile`) |
| `obstacles/` | `art`, `asteroid`, `spawner` | Procedural `AsteroidArt`/`AsteroidLibrary`; `Asteroid` (hp, push, pixel-exact hits, how it splits) + `IceRock` (brittle, shatters), `rock_class(palette)`; `AsteroidSpawner` (driven by a `Difficulty`) |
| `minions/` | `bullets`, `base`, `drone`, `diver` | `EnemyBullet`, `shoot()`, `bullet()`; `Enemy` base; `Drone` sprite + class + `drone_formation()`; `Diver` (kamikaze: lock on, dive) + `diver_squad()` |
| `bosses/` | `spec`, `base`, `art`, `gunship`, `carrier`, `mothership`, `leviathan` | `BossSpec` balance maths; `Boss` base (phases, roar, drones, `parts()`/`hit_part()` for multi-part bosses, `prebuild()`); shared hull colours; **one file per boss = its sprite, muzzles/vents and class** |
| `pickups/` | `art`, `base`, `types` | Sprites; `Pickup` base; `RepairKit`, `FullRepair`, `PowerCore`, `Coin` / `BigCoin` (spinning) |
| `levels/` | `model`, `data` | `Difficulty`, `Level`, `Wave`, `BossEntry` (incl. music track), `Galaxy`; `GALAXIES` (10 levels each), `LEVELS` (all, play order), `galaxy_of()` |
| `progression/` | `results`, `economy`, `items`, `inventory`, `upgrades` | Pure logic (no pygame): `LevelStats` + rank S/A/B/C; coin drops and the level-clear `Payout`; item catalog + `GIFTS` + prices; `Inventory` (owns / status / claim / buy, upgrade tiers + `buy_upgrade`, migrates old saves); upgrade `TRACKS`, `apply(loadout, tiers)`, `power_ratio()` |
| `audio/` | `synth`, `sfx`, `music`, `bank`, `player` | Pure-Python chiptune synth; SFX recipes (`SOUNDS`); songs as chords + melodies (`SONGS`); WAV cache in `sounds/generated/`; `Audio` (`play`, `loop`, `music`) |
| `ui/` | `hud`, `popup`, `item_art`, `hangar`, `gifts`, `radio`, `screens` | HUD + banners; floating popups + boss `DamageNumber`s; radio cards (COMMANDER VEGA portrait); item pictures (ship previews, weapon + upgrade icons, locked silhouettes); HANGAR 2.0 (`HangarView`: tabs, list, stats, shop, UPGRADES tab, POWER %); gift cards; `ScreensMixin` draws every state (pause = options menu, boss name card on WARNING) |
| `flow/` | `game`, `states`, `events`, `level_flow`, `world`, `combat`, `progression`, `hangar`, `juice`, `options`, `sound`, `dev` | `Game` = setup, main loop, update order. The rest is one **mixin per responsibility**: key handling (one `_keys_<state>` method per state), level/wave/phase flow + hull choice, world update + hazards, player hits, coins + stats + rank + payout, hangar + gifts + shop, juice (tiers, hit-stop, slow-mo, damage numbers, radio), options, music/loops, dev tools |

Other folders: `tests/smoke.py` (headless smoke test, `run_smoke_test(shots, seed, only)`),
`tools/build_audio.py` (renders `game/audio` recipes to WAV).

Where to look when debugging:
- A key does the wrong thing → `flow/events.py`, the `_keys_<state>` handler.
- Something about one boss → its file in `bosses/`. Balance → `bosses/spec.py` + `levels/data.py`.
- Damage / score / charge → `flow/combat.py` (player hits) or `flow/world.py` (hits on the ship).
- Coins, rank, payout → `flow/progression.py` (game side), `progression/` (rules), numbers in `config/tuning.py`.
- Gifts, shop, what a player owns → `progression/items.py` (catalog, prices), `flow/hangar.py` (screens' logic).
- Upgrades → `progression/upgrades.py` (tracks, `apply`, POWER), numbers in `config/tuning.py`; applied in `loadout_for()` after the hull, never to `BossSpec`.
- Tests start with every item owned (`Harness` calls `inventory.grant_all()`) and 0 upgrade tiers; `test_inventory` covers a new player.
- Hit-stop / slow-mo / shake per event → `flow/juice.py` (`juice(tier, x, y)`), tiers in `config/tuning.JUICE`. `update()` gives the world `world_dt(dt)`; popups, shake, radio run on real time.
- Wrong music or a sound missing → `flow/sound.py` (state → track, loops) or the event's own call.

## Conventions

- **Low-res canvas**: all game logic and drawing use `LOW_W x LOW_H` (320x240) pixel coordinates.
  The canvas is scaled x`SCALE` with nearest-neighbour in `Game._present()`. Never draw on the window directly.
- **Frame-rate independent**: every `update(dt)` takes seconds; speeds are px/second.
- **No image files for game art.** Sprites are generated in code, next to the class that uses
  them, so they stay consistent in palette and pixel size. Shared colours come from
  `config/palette.py`; a sprite's own colour key (e.g. a boss hull) lives next to its drawing.
- **No audio files by hand either.** Sounds and music are recipes in `game/audio/` (`sfx.py`,
  `music.py`); `sounds/generated/` is a git-ignored cache that the game renders on first start
  (~9 s) and `tools/build_audio.py` re-renders. Play with `game.audio.play("name")`; unknown
  names raise an `AssertionError`, so typos fail in the smoke test even without a sound device.
  Music follows the state in `flow/sound.py`; a level's / boss's track is data (`Level.music`,
  `BossEntry.music`).
- **Surfaces**: sprites use `pygame.SRCALPHA`; anything opaque (canvas, backgrounds, glow) must use
  `pixelart.opaque_surface()`, never a bare `pygame.Surface()`. On macOS the display format has an
  alpha channel and a bare surface turns sprites into black boxes. The headless dummy driver does
  NOT reproduce this — check visual changes in a real window too.
- Flames/glow use additive blending (`BLEND_ADD`); smoke and debris use normal blending.
- Collision is pixel-perfect via `pygame.mask`.
- Tuning numbers belong in `config/tuning.py` (ship models in `config/loadouts.py`), not in logic code.
- **Controls are deliberately simple**: the rocket moves directly with the arrows (diagonal =
  two arrows) and only *leans* up to 30° on UP+LEFT/RIGHT. Drift/360° rotation was tried and
  rejected as too hard — don't reintroduce it. Use `Ship.to_world(lx, ly)` / `Ship.nose()` to place things relative to the ship.
- **Hulls** (`player/hulls.py`): shape + engine/barrel positions + multipliers on the level's
  `Loadout` (`Hull.apply`). Keep `hp * firepower == 1` so every hull is equally strong in the boss
  damage race (the smoke test checks it); trade speed, size and weapon focus instead. Weapons
  read barrels and the nose from `ship.hull`, never hard-coded offsets.
- **Boss balance**: never hand-pick boss HP or bullet damage. Give a `BossSpec(strength,
  fight_time, player=<Loadout of that level>)`; HP and damage are derived so the boss is `strength`
  times stronger in a damage race. Pickups and POWER levels are the player's edge on top.
- **Levels are data** (`levels/data.py`). A new level = a `Level` entry; a new ship model = a
  `Loadout` in `config/loadouts.py` + a paint job in `player/art.SHIP_PALETTES`; a new hull = a
  `Hull` in `player/hulls.py` added to `HULLS`.
- **Game mixins**: a new area of game behaviour gets its own mixin in `flow/` (added to the
  `Game` bases), not more methods in `flow/game.py`. Mixins share state through `self`; the
  attributes are created in `Game.__init__` / `new_run()`.
- Weapons never apply damage themselves: `update()` returns `Hit`s and `Game` applies them,
  so new target types (enemies, bosses) only need `x`, `y`, `bound`, `contains()` (+ `damage()`).
  A boss made of pieces returns them from `Boss.parts()`; hits on a part go through
  `Boss.hit_part()` (the Leviathan's head takes x1.5).
- Expensive sprites (rotated frames) are built at startup via `Boss.prebuild()` /
  `Diver.prebuild()`, never when the enemy first appears (that would hitch mid-game).
- Input: `Game.held` (a `Keys` set filled from KEYDOWN/KEYUP) — not `pygame.key.get_pressed()`,
  which is unreliable on macOS. Tests pass `Keys(...)` directly to `Game.update()`.
- Mouse: `Game.mouse` (`core.input.Mouse`) is passed as `Game.update(dt, keys, mouse)`. It
  takes over after the pointer really moves (6 px) or a click, and hands back on any arrow key
  or ENTER. `Ship.update(target=...)` turns the pointer into a wanted velocity and the arrows
  that velocity "presses", so flames / bank / lean behave exactly as with the keyboard.
  A left click in a menu = ENTER. The system cursor is hidden while PLAYING (own reticle).
- Big sprites (bosses) are drawn as a left half on a `CharCanvas`, then `mirrored()` + `outlined()`
  (`bosses/art.build_boss_sprite`). Keep muzzle/vent coordinates next to the sprite, in the boss's file.
- Heading/lean: angles in radians clockwise from "nose up"; `Ship.angle`, `forward`, `right`.
- Code comments/docstrings in English; keep them short.
- Never write the player's `save.json` from tests or scripts: pass `save_path=` (temp file) or
  use `dev=True` (memory only). The smoke test already does this.
- Only runtime dependency is `pygame`. Pure Python otherwise (no numpy).

## Legacy assets

`images/` and `astroids/` hold the original clip-art PNGs from the first version, and
`sounds/crash.wav` + `sounds/nes.mp3` the original audio. None of them are loaded any more
(the game's audio is synthesized, see `game/audio/`).
