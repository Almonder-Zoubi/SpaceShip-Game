"""Tiny chiptune synthesizer in pure Python: oscillators, envelopes, a step sequencer, WAV output.

Sounds are lists of floats in -1..1 at RATE samples per second. Nothing here touches pygame,
so it also runs in tools/build_audio.py.
"""
import array
import math
import random
import sys
import wave
from dataclasses import dataclass

RATE = 22050

_NOTE_INDEX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_CHORDS = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10),
           "maj7": (0, 4, 7, 11), "dim": (0, 3, 6), "sus": (0, 5, 7), "5": (0, 7)}


# --- pitch -------------------------------------------------------------------------------
def semitone(note):
    """'A4' -> 57 (semitones above C0); accidentals '#' and 'b' ('C#5', 'Bb3')."""
    name, octave = note[:-1], int(note[-1])
    return octave * 12 + _NOTE_INDEX[name[0]] + name[1:].count("#") - name[1:].count("b")


def freq(note):
    """Frequency in Hz of a note name ('A4' = 440)."""
    return 440.0 * 2 ** ((semitone(note) - 57) / 12)


def note_name(semis):
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[semis % 12]}{semis // 12}"


def chord(symbol, octave=4):
    """'Am' -> ['A4', 'C5', 'E5']; 'F#m7', 'Bb', 'Gsus' ... (root in the given octave)."""
    root = symbol[0] + ("#" if symbol[1:2] == "#" else "b" if symbol[1:2] == "b" else "")
    base = semitone(f"{root}{octave}")
    return [note_name(base + i) for i in _CHORDS[symbol[len(root):]]]


# --- oscillators ---------------------------------------------------------------------------
def _wave_value(kind, phase, duty):
    if kind == "square":
        return 1.0 if phase < duty else -1.0
    if kind == "triangle":                       # 4-bit stepped, like the NES triangle
        v = 4 * abs(phase - 0.5) - 1
        return round((v + 1) * 7.5) / 7.5 - 1
    if kind == "saw":
        return 2 * phase - 1
    return math.sin(math.tau * phase)            # sine


def oscillate(kind, f0, f1, n, duty=0.5, vibrato=0.0, vibrato_rate=5.5):
    """n samples of a wave whose frequency slides exponentially from f0 to f1.
    kind: square, triangle, saw, sine or noise (f = how often the noise value changes)."""
    out = [0.0] * n
    ratio = (f1 / f0) if f1 else 1.0
    phase = 0.0
    if kind == "noise":
        value, hold = 1.0, 0.0
        rnd = random.random
        for i in range(n):
            f = f0 * ratio ** (i / n)
            hold += f / RATE
            if hold >= 1.0:
                hold -= int(hold)
                value = 1.0 if rnd() < 0.5 else -1.0
            out[i] = value
        return out
    for i in range(n):
        f = f0 * ratio ** (i / n) if ratio != 1.0 else f0
        if vibrato:
            f *= 2 ** (vibrato * math.sin(math.tau * vibrato_rate * i / RATE) / 12)
        phase = (phase + f / RATE) % 1.0
        out[i] = _wave_value(kind, phase, duty)
    return out


# --- one-shot sound building blocks ----------------------------------------------------------
def tone(kind, f0, f1=None, dur=0.1, volume=1.0, duty=0.5, attack=0.003, power=1.5,
         vibrato=0.0, vibrato_rate=5.5):
    """A sweep from f0 to f1 Hz with a quick attack and a decay to silence over dur seconds."""
    n = max(1, int(dur * RATE))
    wave_ = oscillate(kind, f0, f1, n, duty, vibrato, vibrato_rate)
    a = max(1, int(attack * RATE))
    for i in range(n):
        env = min(1.0, i / a) * (1 - i / n) ** power
        wave_[i] *= env * volume
    return wave_


def noise(dur, rate0=9000, rate1=None, volume=1.0, attack=0.002, power=1.5):
    """Noise burst; a falling rate (rate1 < rate0) sounds like a deepening rumble."""
    return tone("noise", rate0, rate1, dur, volume, attack=attack, power=power)


def silence(dur):
    return [0.0] * int(dur * RATE)


def mix(*parts):
    """Sum sounds sample by sample (the result is as long as the longest)."""
    out = [0.0] * max(len(p) for p in parts)
    for p in parts:
        for i, v in enumerate(p):
            out[i] += v
    return out


def seq(*parts):
    """Play sounds one after another."""
    out = []
    for p in parts:
        out.extend(p)
    return out


def at(offset, part):
    """Delay a sound by offset seconds (for use with mix)."""
    return silence(offset) + part


def lowpass(samples, k):
    """One-pole low-pass filter, k in 0..1 (smaller = darker)."""
    out, y = [0.0] * len(samples), 0.0
    for i, v in enumerate(samples):
        y += (v - y) * k
        out[i] = y
    return out


def echo(samples, delay, gain, tail=0.0):
    """Feedback delay: every repeat is `gain` times quieter. Adds `tail` seconds at the end."""
    out = list(samples) + [0.0] * int(tail * RATE)
    d = max(1, int(delay * RATE))
    for i in range(d, len(out)):
        out[i] += out[i - d] * gain
    return out


def dc_block(samples, r=0.995):
    """Remove the DC offset narrow pulse waves add (it wastes headroom and thumps)."""
    out, prev_x, prev_y = [0.0] * len(samples), 0.0, 0.0
    for i, x in enumerate(samples):
        prev_y = x - prev_x + r * prev_y
        prev_x = x
        out[i] = prev_y
    return out


def limit(samples, peak=0.9):
    """Scale down only if the sound would go above peak (layers can add up past 1.0)."""
    top = max((abs(v) for v in samples), default=0.0)
    return [v * peak / top for v in samples] if top > peak else samples


def normalise(samples, peak=0.9):
    top = max((abs(v) for v in samples), default=0.0)
    return [v * peak / top for v in samples] if top else samples


def make_loop(samples, fade):
    """Crossfade the end into the start so the sound loops without a click."""
    n = int(fade * RATE)
    body, tail = samples[:-n], samples[-n:]
    for i in range(n):
        k = i / n
        body[i] = body[i] * k + tail[i] * (1 - k)
    return body


# --- sequencer -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Instrument:
    """How a note sounds: waveform, volume envelope (ADSR, seconds), vibrato, pitch slide."""
    wave: str = "square"
    duty: float = 0.5
    volume: float = 0.5
    attack: float = 0.004
    decay: float = 0.1
    sustain: float = 0.6
    release: float = 0.06
    vibrato: float = 0.0         # depth in semitones (starts after the attack)
    vibrato_rate: float = 5.5
    slide: float = 0.0           # semitones the pitch falls over slide_time (drums, plucks)
    slide_time: float = 0.08

    def render(self, f, gate):
        """One note: held for `gate` seconds, then released."""
        n_gate, n_rel = int(gate * RATE), int(self.release * RATE)
        n = n_gate + n_rel
        f1 = f * 2 ** (-self.slide / 12) if self.slide else None
        if f1:                                   # slide happens in slide_time, then holds
            n_slide = min(n, max(1, int(self.slide_time * RATE)))
            samples = (oscillate(self.wave, f, f1, n_slide, self.duty)
                       + oscillate(self.wave, f1, None, n - n_slide, self.duty))
        else:
            samples = oscillate(self.wave, f, None, n, self.duty, self.vibrato, self.vibrato_rate)
        a, d = max(1, int(self.attack * RATE)), max(1, int(self.decay * RATE))
        s, vol = self.sustain, self.volume
        level = held = 0.0
        for i in range(n):
            if i < n_gate:
                if i < a:
                    level = i / a
                elif i < a + d:
                    level = 1 - (1 - s) * (i - a) / d
                else:
                    level = s
                held = level
            else:
                level = held * (1 - (i - n_gate) / max(1, n_rel))
            samples[i] *= level * vol
        return samples


class Part:
    """One channel of a song. tokens: one per step, separated by spaces ('|' is ignored).

    note name ('A4') = new note, '.' = hold the previous note, '-' = silence.
    For drum parts the tokens are drum names from `kit` instead of note names.
    step = how many sequencer steps one token lasts (1 = 16th note, 2 = 8th ...).
    """

    def __init__(self, instrument, tokens, step=1, kit=None, echo=None):
        if isinstance(tokens, str):
            tokens = tokens.split()
        self.tokens = [t for t in tokens if t != "|"]
        self.instrument, self.step, self.kit, self.echo = instrument, step, kit, echo


class Song:
    """A tempo plus parts. loop=True wraps note tails round to the start (seamless loop)."""

    def __init__(self, bpm, parts, steps_per_beat=4, loop=True):
        self.bpm, self.parts, self.steps_per_beat, self.loop = bpm, parts, steps_per_beat, loop
        steps = [len(p.tokens) * p.step for p in parts]
        assert len(set(steps)) == 1, f"parts differ in length (in 16th steps): {steps}"

    @property
    def step_time(self):
        return 60 / self.bpm / self.steps_per_beat

    @property
    def length(self):
        """Seconds until the song repeats (the longest part)."""
        return max(len(p.tokens) * p.step for p in self.parts) * self.step_time

    def render(self):
        n = int(self.length * RATE)
        tail = int(2.5 * RATE)
        out = [0.0] * (n + tail)
        for part in self.parts:
            buf = self._render_part(part, n + tail)
            if part.echo:
                buf = echo(buf, *part.echo)[:n + tail]
            for i, v in enumerate(buf):
                out[i] += v
        out = dc_block(out)
        if self.loop:                           # note tails and echoes wrap to the start
            for i in range(tail):
                out[i] += out[n + i]
            out = out[:n]
        else:
            while len(out) > n and abs(out[-1]) < 1e-4:
                out.pop()
        return normalise(out)

    def _render_part(self, part, total):
        buf = [0.0] * total
        step = self.step_time * part.step
        tokens = part.tokens
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            held = 1
            while i + held < len(tokens) and tokens[i + held] == ".":
                held += 1
            if tok not in (".", "-"):
                if part.kit:
                    samples = part.kit[tok]
                else:
                    samples = part.instrument.render(freq(tok), held * step)
                start = int(i * step * RATE)
                for j, v in enumerate(samples[:total - start]):
                    buf[start + j] += v
            i += held
        return buf


# --- output ----------------------------------------------------------------------------------
def write_wav(path, samples):
    """16-bit mono WAV."""
    data = array.array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in samples))
    if sys.byteorder == "big":                  # WAV is little-endian
        data.byteswap()
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data.tobytes())
