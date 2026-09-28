"""Sound effect recipes, built from synth parts. SOUNDS maps a name to a function -> samples.

To add a sound: write a function here, add it to SOUNDS, run tools/build_audio.py,
then call game.audio.play("name").
"""
from .synth import (RATE, at, echo, freq, lowpass, make_loop, mix, noise, oscillate, seq, silence,
                    tone)


# --- player weapons ------------------------------------------------------------------------
def gun():
    """Soft, very short blip: it plays 14 times a second."""
    return mix(tone("square", 1400, 520, 0.045, 0.35, duty=0.25),
               noise(0.02, 12000, 6000, 0.12))


def laser_loop():
    """Humming beam, loops while the laser fires."""
    n = int(0.7 * RATE)
    body = oscillate("saw", 220, None, n, vibrato=0.25, vibrato_rate=12)
    shine = oscillate("sine", 1320, None, n)
    buzz = oscillate("square", 110, None, n, duty=0.3)
    hum = [0.35 * a + 0.12 * b + 0.1 * c for a, b, c in zip(lowpass(body, 0.35), shine, buzz)]
    mean = sum(hum) / len(hum)                  # centre it (a loop can't be DC-filtered)
    return make_loop([v - mean for v in hum], 0.15)


def scatter():
    """Shotgun blast: a punchy noise burst with a low thump."""
    return mix(noise(0.14, 6000, 900, 0.55, power=1.2), tone("sine", 160, 60, 0.1, 0.5))


def plasma():
    """Plasma orb: a wobbling, falling 'bwomp'."""
    return mix(tone("saw", 520, 180, 0.16, 0.3, vibrato=0.5, vibrato_rate=30),
               lowpass(noise(0.1, 3000, 800, 0.2), 0.5))


def arc_loop():
    """Crackling lightning, loops while the ARC fires."""
    n = int(0.6 * RATE)
    crackle = noise(0.6, 9000, None, 1.0, attack=0.0, power=0.0)
    buzz = oscillate("square", 90, None, n, duty=0.2)
    zap = [0.45 * a * (1 if (i // 900) % 3 else 0.3) + 0.12 * b
           for i, (a, b) in enumerate(zip(crackle, buzz))]
    mean = sum(zap) / len(zap)
    return make_loop([v - mean for v in zap], 0.1)


def rocket():
    """ROCKET POD launch: a short hiss."""
    return mix(noise(0.2, 3000, 8000, 0.3, attack=0.02), tone("square", 300, 700, 0.1, 0.12))


def overheat():
    return mix(tone("square", 700, 120, 0.35, 0.4, duty=0.5, power=1.0),
               noise(0.35, 3000, 800, 0.25))


def switch():
    return seq(tone("square", 660, None, 0.03, 0.3, duty=0.25),
               tone("square", 990, None, 0.05, 0.3, duty=0.25))


def blast():
    """3 s roaring beam: rumble + rising whine, matching BLAST_TIME."""
    rumble = noise(3.0, 2500, 900, 0.5, attack=0.08, power=0.6)
    whine = tone("saw", 180, 420, 3.0, 0.3, attack=0.1, power=0.8, vibrato=0.4, vibrato_rate=9)
    return mix(lowpass(rumble, 0.5), lowpass(whine, 0.4), tone("sine", 70, 40, 0.6, 0.6))


def blast_ready():
    return seq(tone("square", freq("E6"), None, 0.07, 0.3, duty=0.25),
               tone("square", freq("B6"), None, 0.14, 0.3, duty=0.25))


def ultimate():
    """Missile storm launch: whoosh + rising alarm."""
    whoosh = noise(0.9, 1500, 7000, 0.45, attack=0.05, power=1.2)
    alarm = seq(*(tone("square", freq(n), None, 0.08, 0.22, duty=0.25)
                  for n in ("C5", "G5", "C6", "G6")))
    return mix(whoosh, alarm)


def missile_hit():
    return mix(noise(0.18, 5000, 700, 0.5), tone("sine", 160, 60, 0.12, 0.4))


# --- hits and explosions ---------------------------------------------------------------------
def hit_rock():
    return noise(0.04, 7000, 3000, 0.3)


def hit_metal():
    return mix(tone("square", 1800, 1500, 0.04, 0.18, duty=0.125), noise(0.03, 12000, None, 0.15))


def rock_break():
    return mix(lowpass(noise(0.3, 4000, 600, 0.8), 0.6), tone("sine", 120, 50, 0.15, 0.4))


def rock_break_big():
    return mix(lowpass(noise(0.65, 3000, 300, 0.9, power=1.2), 0.45),
               tone("sine", 90, 35, 0.35, 0.7), at(0.05, noise(0.2, 6000, 2000, 0.3)))


def drone_explode():
    return mix(lowpass(noise(0.4, 5000, 500, 0.8), 0.55), tone("square", 500, 60, 0.25, 0.3))


def ship_hurt():
    return mix(tone("square", 600, 140, 0.22, 0.45, duty=0.5, power=1.0),
               noise(0.18, 6000, 1500, 0.35))


def ship_explode():
    boom = lowpass(noise(1.6, 3500, 150, 1.0, power=1.1), 0.35)
    return echo(mix(boom, tone("sine", 70, 28, 0.9, 0.8), noise(0.25, 9000, 3000, 0.4)),
                0.11, 0.3, tail=0.4)


def boss_explode():
    booms = mix(*(at(t, lowpass(noise(0.9, 3000, 200, 0.7, power=1.2), 0.4))
                  for t in (0.0, 0.25, 0.5, 0.8)))
    return echo(mix(booms, tone("sine", 60, 22, 2.2, 0.9, power=1.0)), 0.13, 0.35, tail=0.6)


# --- enemies ---------------------------------------------------------------------------------
def enemy_shot():
    return tone("square", 900, 380, 0.08, 0.28, duty=0.25)


def lock_on():
    """Diver / Leviathan target lock: two quick high beeps."""
    beep = tone("square", freq("A6"), None, 0.05, 0.22, duty=0.25)
    return seq(beep, silence(0.04), beep)


def dive():
    """Leviathan lunge: a rushing roar that swoops down."""
    rush = lowpass(noise(0.9, 1200, 5000, 0.5, attack=0.08, power=0.9), 0.5)
    growl = tone("saw", 110, 45, 0.9, 0.45, attack=0.05, power=0.8, vibrato=1.0, vibrato_rate=18)
    return mix(rush, lowpass(growl, 0.3))


def ice_break():
    """Ice rock shattering: glassy pings over a bright crunch."""
    pings = mix(tone("sine", 2600, 2450, 0.28, 0.25), at(0.03, tone("sine", 3300, 3150, 0.22, 0.2)),
                at(0.07, tone("triangle", 1950, 1850, 0.3, 0.22)))
    return mix(noise(0.16, 14000, 5000, 0.35), lowpass(noise(0.2, 3000, 800, 0.35), 0.6), pings)


def boss_roar():
    """Phase change: a deep rising growl with a crash."""
    growl = tone("saw", 55, 110, 1.4, 0.6, attack=0.1, power=0.7, vibrato=1.2, vibrato_rate=16)
    return mix(lowpass(growl, 0.25), lowpass(noise(1.4, 1200, 500, 0.5, attack=0.1, power=0.8), 0.4),
               lowpass(noise(0.5, 6000, 1000, 0.5), 0.6))


def beam():
    """Mothership beam: charging zap into a harsh buzz (~2 s)."""
    zap = tone("saw", 200, 1200, 0.25, 0.4, power=0.3)
    buzz = tone("square", 90, 80, 2.0, 0.45, duty=0.4, attack=0.02, power=0.6,
                vibrato=0.5, vibrato_rate=30)
    return seq(zap, lowpass(buzz, 0.5))


def warning():
    """Boss siren: two tones alternating for ~2.8 s."""
    beeps = [tone("square", f, None, 0.35, 0.35, duty=0.5, attack=0.01, power=0.3)
             for _ in range(4) for f in (880, 660)]
    return seq(*beeps)


# --- pickups and UI --------------------------------------------------------------------------
def pickup():
    return seq(*(tone("square", freq(n), None, 0.05, 0.3, duty=0.25)
                 for n in ("C6", "E6", "G6", "C7")))


def power_up():
    arp = seq(*(tone("square", freq(n), None, 0.06, 0.3, duty=0.125)
                for n in ("C5", "G5", "C6", "E6", "G6", "C7")))
    return mix(arp, tone("triangle", 200, 800, 0.36, 0.4, power=0.5))


def coin():
    """Coin pickup: the classic two-note 'ding'."""
    return seq(tone("square", freq("B5"), None, 0.04, 0.28, duty=0.25),
               tone("square", freq("E6"), None, 0.12, 0.28, duty=0.25))


def rank():
    """Results screen: the rank stamp lands — a thump and a bright chord."""
    thump = mix(tone("sine", 110, 45, 0.25, 0.7), lowpass(noise(0.12, 3000, 500, 0.5), 0.5))
    chord = mix(*(tone("square", freq(n), None, 0.35, 0.14, duty=0.25, attack=0.01)
                  for n in ("C5", "E5", "G5", "C6")))
    return mix(thump, at(0.04, chord))


def denied():
    """Menu: can't do that (locked, not enough credits) — a low double buzz."""
    buzz = tone("square", 140, 120, 0.09, 0.3, duty=0.5, power=0.5)
    return seq(buzz, silence(0.03), buzz)


def boost():
    """Boost pickup: bright rising sweep + sparkle."""
    return mix(tone("square", 500, 1600, 0.18, 0.28, duty=0.25),
               at(0.08, seq(*(tone("square", freq(n), None, 0.05, 0.22, duty=0.125)
                              for n in ("E6", "B6", "E7")))))


def shield():
    """The bubble absorbs a hit: glassy ping."""
    return mix(tone("sine", 1900, 1100, 0.22, 0.4), tone("triangle", 950, 700, 0.18, 0.3),
               noise(0.05, 9000, 4000, 0.12))


def combo():
    """Combo multiplier up: a quick two-note blip, higher is better."""
    return seq(tone("square", freq("G5"), None, 0.04, 0.26, duty=0.25),
               tone("square", freq("D6"), None, 0.07, 0.26, duty=0.25))


def fever():
    """FEVER: fast arpeggio sweeping up two octaves."""
    notes = ("C5", "E5", "G5", "C6", "E6", "G6", "C7")
    return mix(seq(*(tone("square", freq(n), None, 0.05, 0.3, duty=0.25) for n in notes)),
               tone("saw", 200, 800, 0.4, 0.15, attack=0.02))


def wingman_down():
    """A wingman is knocked out: falling whine + crackle."""
    return mix(tone("square", 900, 150, 0.35, 0.25, duty=0.25),
               noise(0.3, 5000, 800, 0.25))


def wingman_up():
    """A wingman reboots: three rising beeps."""
    return seq(*(tone("square", freq(n), None, 0.05, 0.22, duty=0.25) for n in ("C6", "E6", "A6")))


def achievement():
    """Achievement unlocked: a bright fanfare."""
    notes = ("G5", "C6", "E6", "G6")
    return mix(seq(*(tone("square", freq(n), None, 0.07, 0.25, duty=0.25) for n in notes)),
               at(0.28, mix(*(tone("triangle", freq(n), None, 0.4, 0.18) for n in ("C6", "E6", "G6")))))


def magma_burst():
    """A magma rock explodes: deep boom + sizzle."""
    return mix(lowpass(noise(0.55, 3500, 300, 0.8, power=1.1), 0.5),
               tone("sine", 110, 40, 0.4, 0.8), at(0.03, noise(0.3, 9000, 5000, 0.2)))


def flare():
    """A solar flare wall launches: rushing roar rising in pitch."""
    return mix(lowpass(noise(1.0, 1200, 5000, 0.6, attack=0.1, power=0.8), 0.4),
               tone("saw", 90, 200, 0.9, 0.2, attack=0.1))


def teleport():
    """The Wraith vanishes: a falling warble into static."""
    return mix(tone("sine", 1400, 200, 0.3, 0.3, vibrato=0.6, vibrato_rate=25),
               at(0.15, noise(0.25, 8000, 2000, 0.2)))


def metal_break():
    """A wreck chunk bursts / armour is shot off: clanging metal crash."""
    return mix(tone("square", 420, 180, 0.25, 0.3, duty=0.3), tone("square", 610, 240, 0.2, 0.2,
                                                                      duty=0.2),
               lowpass(noise(0.4, 5000, 600, 0.6), 0.5))


def white_hole():
    """The black hole flips: a reversed whoosh swelling up into a bright chord."""
    swell = noise(1.0, 400, 9000, 0.5, attack=0.8, power=0.6)
    return mix(swell, at(0.8, mix(*(tone("triangle", freq(n), None, 0.6, 0.15)
                                    for n in ("C6", "E6", "G6", "B6")))))


def spore():
    """A spore pod bursts: a wet pop with a rising squelch."""
    return mix(lowpass(noise(0.25, 2500, 600, 0.6, power=1.3), 0.4),
               tone("sine", 180, 420, 0.18, 0.4, vibrato=0.4, vibrato_rate=20))


def heartbeat():
    """The Overmind's heart: a double thump (lub-dub)."""
    return mix(tone("sine", 70, 38, 0.16, 0.9, power=1.2),
               at(0.2, tone("sine", 60, 34, 0.2, 0.7, power=1.2)))


def warp():
    """Jump to hyperspace: a long rising whine into a bright boom."""
    return mix(tone("saw", 80, 1800, 1.6, 0.25, attack=0.3, power=0.8),
               noise(1.6, 800, 12000, 0.3, attack=1.2, power=0.6),
               at(1.5, mix(tone("sine", 140, 40, 0.8, 0.7), noise(0.8, 6000, 800, 0.4))))


def data_cache():
    """A data cache on the star map: a shimmering three-note chime."""
    return seq(*(tone("triangle", freq(n), None, 0.09, 0.3) for n in ("E6", "B6", "G#6")),
               tone("triangle", freq("E7"), None, 0.3, 0.25))


def hijack():
    """A hostile voice breaks into the radio: bit-crushed static that stutters, a low drone."""
    burst = noise(0.9, 2500, 600, 0.45, attack=0.01, power=0.4)
    crushed = [v if (i // 700) % 3 else 0.0 for i, v in enumerate(burst)]
    return mix(crushed, tone("saw", 55, 48, 0.9, 0.3, attack=0.05, power=0.5),
               at(0.35, tone("square", 1900, 300, 0.12, 0.15, duty=0.1)))


def page():
    """The journal: a page turns (a soft papery swish)."""
    return mix(noise(0.12, 7000, 2500, 0.25, attack=0.03, power=1.0),
               tone("triangle", 660, 880, 0.05, 0.12))


def select():
    return tone("square", 880, None, 0.04, 0.3, duty=0.25)


def confirm():
    return seq(tone("square", freq("C6"), None, 0.05, 0.3, duty=0.25),
               tone("square", freq("G6"), None, 0.12, 0.3, duty=0.25))


def engine_loop():
    """Engine rumble, looped; its volume follows the throttle."""
    rumble = lowpass(noise(1.3, 1800, None, 1.0, attack=0.0, power=0.0), 0.12)
    hum = oscillate("triangle", 55, None, len(rumble))
    return make_loop([0.8 * a + 0.15 * b for a, b in zip(rumble, hum)], 0.3)


SOUNDS = {
    "gun": gun, "laser": laser_loop, "overheat": overheat, "switch": switch,
    "blast": blast, "blast_ready": blast_ready, "ultimate": ultimate, "missile_hit": missile_hit,
    "hit_rock": hit_rock, "hit_metal": hit_metal, "rock_break": rock_break,
    "rock_break_big": rock_break_big, "drone_explode": drone_explode, "ship_hurt": ship_hurt,
    "ship_explode": ship_explode, "boss_explode": boss_explode, "enemy_shot": enemy_shot,
    "boss_roar": boss_roar, "beam": beam, "warning": warning, "pickup": pickup,
    "power_up": power_up, "select": select, "confirm": confirm, "engine": engine_loop,
    "lock_on": lock_on, "dive": dive, "ice_break": ice_break, "coin": coin, "rank": rank,
    "denied": denied, "boost": boost, "shield": shield, "combo": combo, "fever": fever,
    "wingman_down": wingman_down, "wingman_up": wingman_up, "scatter": scatter,
    "plasma": plasma, "arc": arc_loop, "rocket": rocket,
    "achievement": achievement, "magma_burst": magma_burst, "flare": flare,
    "teleport": teleport, "metal_break": metal_break,
    "white_hole": white_hole, "spore": spore, "heartbeat": heartbeat, "warp": warp,
    "data_cache": data_cache, "hijack": hijack, "page": page,
}
LOOPS = ("laser", "engine", "arc")         # played on their own channel, looping
