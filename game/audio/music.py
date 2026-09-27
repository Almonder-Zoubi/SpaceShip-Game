"""The soundtrack, composed as data: chord progressions + melodies for the synth's sequencer.

Every song is a function returning a synth.Song; SONGS maps track names to them.
Melodies are written in 8th notes (8 tokens per bar), arpeggios and drums in 16ths.
To hear a change: python3 tools/build_audio.py <track>, then play the WAV in sounds/music/.
"""
from .synth import Instrument, Part, Song, chord, mix, noise, tone

# --- instruments -------------------------------------------------------------------------------
LEAD = Instrument("square", duty=0.25, volume=0.30, decay=0.12, sustain=0.55, release=0.08,
                  vibrato=0.15, vibrato_rate=6)
LEAD_SOFT = Instrument("square", duty=0.5, volume=0.22, attack=0.02, decay=0.2, sustain=0.6,
                       release=0.15, vibrato=0.2, vibrato_rate=5)
ARP = Instrument("square", duty=0.125, volume=0.13, decay=0.05, sustain=0.35, release=0.02)
BASS = Instrument("triangle", volume=0.6, decay=0.08, sustain=0.85, release=0.02)
BASS_LONG = Instrument("triangle", volume=0.55, attack=0.02, decay=0.3, sustain=0.7, release=0.2)

KIT = {
    "k": mix(tone("sine", 160, 45, 0.18, 0.9, power=1.0), noise(0.012, 6000, None, 0.3)),
    "s": mix(noise(0.15, 9000, 4000, 0.4), tone("triangle", 230, 140, 0.08, 0.35)),
    "h": noise(0.03, 15000, None, 0.14, power=2.0),
    "o": noise(0.14, 13000, None, 0.11, power=1.2),
    "c": noise(1.0, 12000, 6000, 0.25, power=1.2),
}


# --- pattern helpers ----------------------------------------------------------------------------
def arp(chords, octave=4, pattern=(0, 1, 2, 1)):
    """16th-note arpeggio, one bar per chord."""
    tokens = []
    for symbol in chords:
        notes = chord(symbol, octave)
        tokens += [notes[pattern[i % len(pattern)] % len(notes)] for i in range(16)]
    return tokens


def bass(chords, octave=2, rhythm="R R O R R R O R"):
    """8th-note bass line, one bar per chord. R = root, O = root an octave up, F = fifth,
    '.' = hold, '-' = rest."""
    tokens = []
    for symbol in chords:
        notes = chord(symbol, octave)
        root, fifth = notes[0], notes[2] if len(notes) > 2 else notes[-1]
        up = chord(symbol, octave + 1)[0]
        for r in rhythm.split():
            tokens.append({"R": root, "O": up, "F": fifth}.get(r, r))
    return tokens


def drums(bar, bars, fill=None, crash=True):
    """Repeat a 16-step drum bar; optional fill as the last bar and a crash on the downbeat."""
    tokens = (bar.split() * bars)
    if fill:
        tokens[-16:] = fill.split()
    if crash:
        tokens[0] = "c"
    return tokens


def song(bpm, chords, melody, lead=LEAD, arp_pattern=(0, 1, 2, 1), arp_octave=4,
         bass_rhythm="R R O R R R O R", beat=None, fill=None, lead_echo=None, arp_echo=None,
         bass_instrument=BASS):
    """The usual four channels: lead melody, arpeggio, triangle bass, drums."""
    parts = [Part(lead, melody, step=2, echo=lead_echo),
             Part(ARP, arp(chords, arp_octave, arp_pattern), echo=arp_echo),
             Part(bass_instrument, bass(chords, rhythm=bass_rhythm), step=2)]
    if beat:
        parts.append(Part(None, drums(beat, len(chords), fill), kit=KIT))
    return Song(bpm, parts)


# --- songs ----------------------------------------------------------------------------------------
def title():
    """Dreamy and calm: major sevenths, soft echoing lead, no drums."""
    chords = ["Cmaj7", "Am7", "Fmaj7", "G", "Cmaj7", "Am7", "Fmaj7", "Gsus"]
    melody = """E5 . . . G5 . B5 . | A5 . . . . . G5 . | F5 . . . A5 . C6 . | B5 . . . . . - -
                E5 . G5 . C6 . B5 . | A5 . . . E5 . . . | F5 . E5 . D5 . C5 . | D5 . . . . . - -"""
    return song(112, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 3, 2, 1),
                bass_rhythm="R . . . . . F .", bass_instrument=BASS_LONG,
                lead_echo=(0.4, 0.35), arp_echo=(0.27, 0.3))


def level1():
    """ASTEROID FIELD: upbeat and heroic, A minor."""
    chords = ["Am", "F", "C", "G", "Am", "F", "C", "G",
              "F", "G", "Em", "Am", "F", "G", "E", "E"]
    melody = """A4 . C5 . E5 . D5 C5 | C5 . . . A4 . . . | G4 . C5 . E5 . G5 . | F5 . E5 . D5 . . .
                A4 . C5 . E5 . A5 . | G5 . F5 . E5 . C5 . | D5 . E5 . G5 . E5 . | D5 . . . B4 . . .
                A5 . . . G5 F5 E5 . | D5 . . . B4 . G4 . | E5 . G5 . B5 . A5 G5 | A5 . . . E5 . . .
                F5 . E5 . D5 . C5 . | D5 . E5 . F5 . G5 . | G#5 . . . B5 . . . | E5 . G#4 . B4 . D5 ."""
    beat = "k . h . s . h . k . k h s . h ."
    fill = "k . h . s . h . k . s s s s s s"
    return song(140, chords, melody, beat=beat, fill=fill)


def level2():
    """CRIMSON BELT: tense galloping D minor."""
    chords = ["Dm", "Dm", "Bb", "C", "Dm", "Dm", "Bb", "A",
              "Gm", "Gm", "Dm", "Dm", "Bb", "C", "A", "A"]
    melody = """D5 . F5 . A5 . . G5 | F5 . E5 . D5 . . . | D5 . F5 . Bb5 . A5 . | G5 . . . E5 . C5 .
                D5 . F5 . A5 . D6 . | C6 . A5 . F5 . . . | G5 . F5 . D5 . F5 . | E5 . . . C#5 . . .
                D5 . . . Bb4 . D5 . | G5 . . . F5 . D5 . | F5 . E5 . D5 . A4 . | D5 . . . . . - -
                F5 . G5 . A5 . Bb5 . | G5 . A5 . C6 . . . | A5 . . . G5 . E5 . | C#5 . E5 . A5 . . ."""
    beat = "k . h k s . h . k . h k s . h h"
    fill = "k . h k s . h . s s s s s s s s"
    return song(152, chords, melody, arp_pattern=(0, 2, 1, 2), bass_rhythm="R R O R R R O R",
                beat=beat, fill=fill)


def level3():
    """DARK NEBULA: slow, spacey E minor with long echoing notes."""
    chords = ["Em", "Em", "C", "D", "Em", "Em", "C", "B",
              "Am", "Am", "Em", "Em", "C", "D", "B", "B"]
    melody = """E5 . . . . . G5 . | F#5 . . . E5 . . . | G5 . . . A5 . B5 . | A5 . . . F#5 . . .
                B5 . . . . . A5 . | G5 . F#5 . E5 . . . | C6 . . . B5 . G5 . | F#5 . . . D#5 . . .
                E5 . . . A5 . . . | C6 . . . B5 . A5 . | G5 . . . F#5 . E5 . | B4 . . . . . - -
                E5 . G5 . C6 . . . | D6 . . . A5 . F#5 . | D#6 . . . B5 . F#5 . | D#5 . F#5 . B5 . . ."""
    beat = "k . . . h . . . s . . . h . k ."
    return song(128, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 1, 2, 0),
                bass_rhythm="R . . R . . O .", beat=beat, lead_echo=(0.35, 0.4),
                arp_echo=(0.35, 0.35))


def level4():
    """FROZEN RIFT: glassy B minor, high echoing arpeggios over a steady pulse."""
    chords = ["Bm", "Bm", "G", "A", "Bm", "Bm", "G", "F#",
              "Em", "Em", "Bm", "Bm", "G", "A", "F#", "F#"]
    melody = """B4 . D5 . F#5 . B5 . | A5 . F#5 . D5 . . . | G5 . . . B5 . D6 . | C#6 . . . A5 . E5 .
                F#5 . B5 . D6 . F#6 . | E6 . D6 . C#6 . B5 . | D6 . . . B5 . G5 . | A#5 . . . F#5 . C#5 .
                E5 . G5 . B5 . E6 . | D6 . B5 . G5 . . . | F#5 . . . D5 . B4 . | D5 . F#5 . B5 . . .
                B5 . D6 . G6 . . . | E6 . C#6 . A5 . E6 . | F#6 . . . C#6 . A#5 . | C#6 . A#5 . F#5 . - -"""
    beat = "k . h . s . h h k . h . s . h ."
    fill = "k . h . s . h h s . s . s s s s"
    return song(136, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 3, 2, 1), arp_octave=5,
                bass_rhythm="R . R . O . R .", beat=beat, fill=fill, lead_echo=(0.3, 0.35),
                arp_echo=(0.22, 0.35))


def boss():
    """Boss fight: fast, aggressive C minor."""
    chords = ["Cm", "Cm", "Ab", "Bb", "Cm", "Cm", "Ab", "G",
              "Fm", "Fm", "Cm", "Cm", "Ab", "Bb", "G", "G"]
    melody = """C5 . C5 . Eb5 . G5 . | Bb5 . G5 . Eb5 . F5 . | Eb5 . C5 . Ab4 . C5 . | D5 . F5 . Bb5 . . .
                C6 . Bb5 . G5 . Eb5 . | F5 . G5 . Eb5 . C5 . | Eb5 . F5 . Ab5 . C6 . | B5 . . . G5 . D5 .
                F5 . . . Ab5 . C6 . | Bb5 . Ab5 . G5 . F5 . | G5 . . . Eb5 . C5 . | D5 . Eb5 . F5 . G5 .
                Ab5 . . . C6 . Eb6 . | D6 . . . Bb5 . F5 . | G5 . B5 . D6 . F6 . | D6 . B5 . G5 . D5 ."""
    beat = "k . h k s . h k k . h k s . s h"
    fill = "k . h k s . h k s s s s s s s s"
    return song(160, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R O R O R O R O",
                beat=beat, fill=fill)


def final_boss():
    """Final boss: frantic F# minor with a galloping bass and double kicks."""
    chords = ["F#m", "F#m", "D", "E", "F#m", "F#m", "D", "C#7",
              "Bm", "Bm", "F#m", "F#m", "D", "E", "C#7", "C#7"]
    melody = """F#5 . A5 . C#6 . F#5 . | E6 . C#6 . A5 . C#6 . | D6 . A5 . F#5 . A5 . | B5 . G#5 . E5 . G#5 .
                F#5 . G#5 . A5 . B5 . | C#6 . . . A5 . F#5 . | F#6 . E6 . D6 . A5 . | E#5 . G#5 . B5 . C#6 .
                D6 . . . B5 . F#5 . | D5 . F#5 . B5 . D6 . | C#6 . . . A5 . F#5 . | C#5 . F#5 . A5 . C#6 .
                D6 . E6 . F#6 . A6 . | G#6 . F#6 . E6 . B5 . | E#6 . . . C#6 . G#5 . | B5 . G#5 . E#5 . C#5 ."""
    beat = "k k h k s . h k k k h k s . s s"
    fill = "k k h k s . h k s s s s s s s s"
    return song(172, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R R O R R O R R",
                beat=beat, fill=fill)


def leviathan():
    """Leviathan: heavy E phrygian riffing (the F against E), relentless double kicks."""
    chords = ["Em", "Em", "F", "F", "Em", "Em", "D", "B",
              "Am", "Am", "F", "F", "Em", "D", "B", "B"]
    melody = """E5 . E5 . G5 . B5 . | C6 . B5 . G5 . E5 . | F5 . A5 . C6 . F6 . | E6 . C6 . A5 . F5 .
                E5 . G5 . B5 . E6 . | D6 . B5 . G5 . B5 . | A5 . F#5 . D5 . F#5 . | D#5 . F#5 . B5 . D#6 .
                A5 . . . C6 . E6 . | D6 . C6 . B5 . A5 . | C6 . . . A5 . F5 . | A5 . C6 . F6 . E6 .
                E6 . B5 . G5 . E5 . | F#5 . A5 . D6 . F#6 . | D#6 . . . B5 . F#5 . | D#5 . F#5 . A5 . B5 ."""
    beat = "k k h k s . h k k . k k s . s h"
    fill = "k k h k s . h k s s s s s s s s"
    return song(168, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R R O R R O R O",
                beat=beat, fill=fill)


# --- jingles (play once) ----------------------------------------------------------------------------
def level_clear():
    lead = "C5 E5 G5 C6 . . G5 C6 . . . . . . . . - - - -"
    harmony = "E4 G4 C5 E5 . . E5 G5 . . . . . . . . - - - -"
    low = "C3 . . . . . . . C3 . . . . . . . - - - -"
    return Song(150, [Part(LEAD, lead), Part(ARP, harmony), Part(BASS, low)], loop=False)


def game_over():
    lead = "E5 . D5 . C5 . B4 . A4 . . . . . . . - - - -"
    low = "A2 . . . . . . . F2 . . . E2 . . . - - - -"
    return Song(96, [Part(LEAD_SOFT, lead, step=2), Part(BASS_LONG, low, step=2)], loop=False)


def win():
    lead = """G4 . C5 . E5 . G5 . . . E5 . G5 . . . | C6 . . . . . . . B5 . . . A5 . . .
              G5 . F5 . E5 . D5 . C5 . D5 . E5 . G5 . | C6 . . . . . . . . . . . . . . . - - - -"""
    return Song(140, [Part(LEAD, lead),
                      Part(ARP, arp(["C", "F", "G", "C"], 4, (0, 1, 2, 1)) + ["-"] * 4),
                      Part(BASS, bass(["C", "F", "G", "C"], rhythm="R . O . R . O .") + ["-"] * 2,
                           step=2),
                      Part(None, drums("k . h . s . h . k . h . s . h .", 3,
                                       crash=False) + "c . . . . . . . . . . . . . . . - - - -".split(),
                           kit=KIT)],
                loop=False)


SONGS = {"title": title, "level1": level1, "level2": level2, "level3": level3,
         "level4": level4, "boss": boss, "final_boss": final_boss, "leviathan": leviathan,
         "level_clear": level_clear, "game_over": game_over, "win": win}
JINGLES = ("level_clear", "game_over", "win")      # play once instead of looping
