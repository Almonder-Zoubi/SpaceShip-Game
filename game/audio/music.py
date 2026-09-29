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


def level5():
    """SOLAR FORGE: pounding G minor with an anvil-like snare, hammering bass."""
    chords = ["Gm", "Gm", "Eb", "F", "Gm", "Gm", "Eb", "D",
              "Cm", "Cm", "Gm", "Gm", "Eb", "F", "D", "D"]
    melody = """G4 . Bb4 . D5 . G5 . | F5 . D5 . Bb4 . . . | Eb5 . G5 . Bb5 . G5 . | A5 . F5 . C5 . . .
                G5 . . . D5 . G5 . | Bb5 . A5 . G5 . D5 . | Eb5 . . . G5 . Bb5 . | A5 . . . F#5 . D5 .
                C5 . Eb5 . G5 . C6 . | Bb5 . G5 . Eb5 . . . | D5 . . . G5 . Bb5 . | A5 . G5 . D5 . . .
                Eb5 . F5 . G5 . Bb5 . | C6 . . . A5 . F5 . | F#5 . . . A5 . D6 . | C6 . A5 . F#5 . D5 ."""
    beat = "k . h k s . h . k k h . s . h s"
    fill = "k . h k s . h . s s k s s k s s"
    return song(146, chords, melody, arp_pattern=(0, 2, 1, 2), bass_rhythm="R R R O R R R O",
                beat=beat, fill=fill)


def helios():
    """HELIOS: blazing E minor boss theme, a rising three-note hook, driving eighths."""
    chords = ["Em", "C", "D", "B", "Em", "C", "Am", "B",
              "C", "D", "Em", "Em", "C", "D", "B7", "B7"]
    melody = """E5 . G5 . B5 . E6 . | E6 . D6 . C6 . G5 . | F#5 . A5 . D6 . F#6 . | D#6 . . . B5 . F#5 .
                E5 . G5 . B5 . E6 . | G6 . F#6 . E6 . C6 . | A5 . C6 . E6 . A6 . | F#6 . . . D#6 . B5 .
                C6 . E6 . G6 . . . | D6 . F#6 . A6 . . . | B6 . . . G6 . E6 . | B5 . E6 . G6 . B6 .
                C7 . B6 . G6 . E6 . | D7 . C7 . A6 . F#6 . | D#6 . F#6 . A6 . B6 . | D#7 . . . B6 . F#6 ."""
    beat = "k k h k s . h k k . h k s . s h"
    fill = "k k h k s . h k s s s s s s s s"
    return song(170, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R O R O R O R O",
                beat=beat, fill=fill)


def level6():
    """GHOST NEBULA: slow, haunted D minor, a wandering lead full of echoes."""
    chords = ["Dm", "Dm", "Bb", "A", "Dm", "Dm", "Gm", "A",
              "Bb", "Bb", "F", "C", "Gm", "Gm", "A", "A"]
    melody = """D5 . . . F5 . . . | A5 . . . G#5 . A5 . | Bb5 . . . A5 . F5 . | E5 . . . C#5 . . .
                D5 . . . A5 . . . | D6 . . . C6 . A5 . | G5 . . . Bb5 . D6 . | C#6 . . . A5 . . .
                Bb5 . . . D6 . . . | F6 . . . E6 . D6 . | C6 . . . A5 . F5 . | G5 . . . E5 . C5 .
                D5 . F5 . G5 . Bb5 . | A5 . . . G5 . F5 . | E5 . . . C#5 . E5 . | A4 . . . - - - -"""
    beat = "k . . . . . h . s . . . . . h ."
    return song(118, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 2, 0, 1),
                bass_rhythm="R . . . R . F .", beat=beat, lead_echo=(0.45, 0.45),
                arp_echo=(0.4, 0.4), bass_instrument=BASS_LONG)


def wraith():
    """WRAITH: nervous chromatic A minor, stabbing arpeggios and a skittering beat."""
    chords = ["Am", "Am", "G#dim", "Am", "F", "E", "Am", "E",
              "Dm", "Dm", "Am", "Am", "F", "E7", "Am", "E7"]
    melody = """A5 . C6 . B5 . A5 . | E6 . . . D#6 . E6 . | D6 . B5 . G#5 . F5 . | E5 . . . A5 . C6 .
                F6 . E6 . D6 . C6 . | B5 . G#5 . E5 . B5 . | C6 . A5 . E5 . A5 . | G#5 . . . B5 . E6 .
                F6 . . . D6 . A5 . | F5 . A5 . D6 . F6 . | E6 . C6 . A5 . E6 . | D#6 . E6 . C6 . A5 .
                F5 . A5 . C6 . F6 . | E6 . D6 . B5 . G#5 . | A5 . C6 . E6 . A6 . | G#6 . . . - - - -"""
    beat = "k . h h s . h k . k h h s . h h"
    fill = "k . h h s . h k s s s . s s s s"
    return song(158, chords, melody, arp_pattern=(0, 1, 2, 1, 0, 2), bass_rhythm="R R O R R O R R",
                beat=beat, fill=fill, arp_echo=(0.2, 0.3))


def level7():
    """CRYSTAL VEIL: bright, glassy E major with sparkling 16th arpeggios up high."""
    chords = ["E", "C#m", "A", "B", "E", "C#m", "F#m", "B",
              "A", "B", "G#m", "C#m", "A", "B", "E", "E"]
    melody = """B4 . E5 . G#5 . B5 . | C#6 . B5 . G#5 . E5 . | A5 . . . C#6 . E6 . | D#6 . . . B5 . F#5 .
                G#5 . B5 . E6 . G#6 . | F#6 . E6 . C#6 . G#5 . | A5 . F#5 . C#6 . A5 . | B5 . . . D#6 . F#6 .
                E6 . . . C#6 . A5 . | F#6 . . . D#6 . B5 . | G#6 . . . E6 . B5 . | C#6 . E6 . G#6 . C#7 .
                A6 . G#6 . F#6 . E6 . | D#6 . F#6 . B6 . A6 . | G#6 . . . E6 . B5 . | E6 . . . - - - -"""
    beat = "k . h h s . h . k h h . s . h h"
    fill = "k . h h s . h . s . s s s s s s"
    return song(144, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 3, 2, 1, 0, 2),
                arp_octave=5, bass_rhythm="R . O . R R O .", beat=beat, fill=fill,
                arp_echo=(0.18, 0.35), lead_echo=(0.3, 0.3))


def kaleidos():
    """KALEIDOS: whirling F# minor, spiralling arpeggios and a four-on-the-floor pulse."""
    chords = ["F#m", "D", "E", "C#", "F#m", "D", "Bm", "C#",
              "D", "E", "F#m", "F#m", "Bm", "C#", "D", "C#7"]
    melody = """F#5 . A5 . C#6 . F#6 . | F#6 . E6 . D6 . A5 . | G#5 . B5 . E6 . G#6 . | F6 . . . C#6 . G#5 .
                A5 . C#6 . F#6 . A6 . | F#6 . D6 . A5 . F#5 . | D6 . F#6 . B6 . D7 . | C#7 . . . G#6 . F6 .
                F#6 . D6 . A5 . D6 . | G#6 . E6 . B5 . E6 . | A6 . . . F#6 . C#6 . | F#6 . A6 . C#7 . F#7 .
                D7 . B6 . F#6 . D6 . | C#7 . G#6 . F6 . C#6 . | D6 . F#6 . A6 . D7 . | C#7 . . . - - - -"""
    beat = "k . h . k . h . k . h . k . h h"
    fill = "k . h . k . h . s s s s s s s s"
    return song(164, chords, melody, arp_pattern=(0, 1, 2, 3, 3, 2, 1, 0), arp_octave=5,
                bass_rhythm="R O R O R O R O", beat=beat, fill=fill)


def level8():
    """IRON GRAVEYARD: heavy, grinding C minor, slow and relentless."""
    chords = ["Cm", "Cm", "Ab", "G", "Cm", "Cm", "Fm", "G",
              "Ab", "Ab", "Eb", "Bb", "Fm", "Fm", "G", "G"]
    melody = """C5 . . . Eb5 . G5 . | F5 . Eb5 . D5 . . . | C5 . Eb5 . Ab5 . G5 . | G5 . . . D5 . B4 .
                C5 . . . G5 . C6 . | Bb5 . Ab5 . G5 . Eb5 . | F5 . . . Ab5 . C6 . | B5 . . . G5 . D5 .
                Eb5 . . . Ab5 . C6 . | Bb5 . Ab5 . G5 . Eb5 . | G5 . . . Bb5 . Eb6 . | D6 . . . Bb5 . F5 .
                Ab5 . G5 . F5 . C5 . | Eb5 . F5 . Ab5 . C6 . | B5 . . . D6 . G6 . | F6 . D6 . B5 . G5 ."""
    beat = "k . . k s . . . k . k . s . . h"
    fill = "k . . k s . . . s . s s s s s s"
    return song(124, chords, melody, arp_pattern=(0, 1, 0, 2), arp_octave=3,
                bass_rhythm="R . R R . R O .", beat=beat, fill=fill)


def scrapjaw():
    """SCRAPJAW: stomping G minor metal riff, hammering bass, crashing snares."""
    chords = ["Gm", "Gm", "F", "Eb", "Gm", "Gm", "Cm", "D",
              "Eb", "F", "Gm", "Gm", "Cm", "D", "Eb", "D7"]
    melody = """G4 . G4 . Bb4 . C5 . | D5 . . . C5 . Bb4 . | A4 . C5 . F5 . A5 . | G5 . Eb5 . Bb4 . . .
                G5 . D5 . Bb4 . G4 . | Bb4 . D5 . G5 . Bb5 . | C6 . G5 . Eb5 . C5 . | D5 . F#5 . A5 . D6 .
                Eb6 . . . Bb5 . G5 . | F5 . A5 . C6 . F6 . | D6 . Bb5 . G5 . D5 . | G5 . Bb5 . D6 . G6 .
                Eb6 . C6 . G5 . Eb5 . | F#5 . A5 . D6 . F#6 . | G6 . Eb6 . Bb5 . G5 . | F#5 . . . - - - -"""
    beat = "k k . k s . k . k k . k s . s s"
    fill = "k k . k s . k . s s s s s s s s"
    return song(160, chords, melody, arp_pattern=(0, 0, 2, 1), arp_octave=3,
                bass_rhythm="R R R R O O R R", beat=beat, fill=fill)


def level9():
    """EVENT HORIZON: vast B phrygian drift, echoing lead, a pulse that feels like gravity."""
    chords = ["Bm", "C", "Bm", "A", "Bm", "C", "G", "F#",
              "Em", "C", "Bm", "Bm", "G", "C", "F#", "F#"]
    melody = """B4 . . . D5 . F#5 . | E5 . . . C5 . G4 . | F#4 . B4 . D5 . F#5 . | E5 . . . C#5 . A4 .
                B4 . D5 . F#5 . B5 . | C6 . . . G5 . E5 . | D5 . . . G5 . B5 . | A#5 . . . F#5 . C#5 .
                E5 . . . G5 . B5 . | C6 . . . E6 . G6 . | F#6 . . . D6 . B5 . | F#5 . B5 . D6 . F#6 .
                G6 . . . D6 . B5 . | C6 . . . G5 . E5 . | F#5 . . . A#5 . C#6 . | F#6 . . . - - - -"""
    beat = "k . . . h . . . k . . . s . . h"
    return song(132, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 1, 2, 3), arp_octave=5,
                bass_rhythm="R . . R . . R .", beat=beat, lead_echo=(0.45, 0.4),
                arp_echo=(0.3, 0.45), bass_instrument=BASS_LONG)


def twins():
    """THE TWINS: two voices chasing each other in C# minor, a fast call and answer."""
    chords = ["C#m", "C#m", "A", "B", "C#m", "C#m", "F#m", "G#",
              "A", "B", "C#m", "C#m", "F#m", "G#", "A", "G#7"]
    melody = """C#5 . E5 . G#5 . C#6 . | G#5 . C#6 . E6 . G#6 . | A5 . C#6 . E6 . A6 . | F#6 . D#6 . B5 . F#5 .
                C#6 . G#5 . E5 . C#5 . | E5 . G#5 . C#6 . E6 . | F#6 . C#6 . A5 . F#5 . | G#5 . C6 . D#6 . G#6 .
                A6 . E6 . C#6 . A5 . | B5 . D#6 . F#6 . B6 . | G#6 . E6 . C#6 . G#5 . | C#6 . E6 . G#6 . C#7 .
                A6 . F#6 . C#6 . A5 . | G#5 . C6 . D#6 . G#6 . | E6 . C#6 . A5 . E5 . | G#5 . . . - - - -"""
    beat = "k k h k s . h k k . h k s k s h"
    fill = "k k h k s . h k s s s s s s s s"
    return song(176, chords, melody, arp_pattern=(0, 2, 1, 2), bass_rhythm="R O R O R O R O",
                beat=beat, fill=fill, lead_echo=(0.17, 0.4))


def level10():
    """SWARM HEART: a throbbing D minor, bass like a heartbeat, an alien wailing lead."""
    chords = ["Dm", "Dm", "Bb", "A", "Dm", "Dm", "Gm", "A",
              "Bb", "C", "Dm", "Dm", "Gm", "Bb", "A", "A7"]
    melody = """D5 . . . F5 . E5 . | D5 . A4 . . . - - | Bb4 . D5 . F5 . Bb5 . | A5 . . . C#5 . E5 .
                D5 . F5 . A5 . D6 . | C6 . A5 . F5 . D5 . | G5 . . . Bb5 . D6 . | C#6 . . . A5 . E5 .
                F5 . . . Bb5 . D6 . | E6 . . . C6 . G5 . | A5 . . . F5 . D5 . | A5 . D6 . F6 . A6 .
                G6 . . . D6 . Bb5 . | F6 . . . D6 . Bb5 . | A5 . C#6 . E6 . A6 . | A6 . . . - - - -"""
    beat = "k . . k . . . . s . . . k k . h"
    return song(118, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 2, 3, 2), arp_octave=4,
                bass_rhythm="R R - - R R - -", beat=beat, lead_echo=(0.38, 0.4),
                arp_echo=(0.25, 0.35))


def overmind():
    """THE OVERMIND: the galaxy's last fight. Driving A minor, a heroic hook against a
    pounding pulse; it quotes the first level's melody in the second half."""
    chords = ["Am", "Am", "F", "G", "Am", "Am", "Dm", "E",
              "F", "G", "Am", "Am", "Dm", "E", "F", "E7"]
    melody = """A4 . C5 . E5 . A5 . | G5 . E5 . C5 . E5 . | F5 . A5 . C6 . A5 . | G5 . B5 . D6 . B5 .
                A5 . . . E5 . A5 . | C6 . . . B5 . A5 . | D6 . . . A5 . F5 . | E5 . G#5 . B5 . E6 .
                F6 . . . C6 . A5 . | G5 . B5 . D6 . G6 . | E6 . . . C6 . A5 . | A5 . C6 . E6 . A6 .
                F6 . D6 . A5 . F5 . | E5 . G#5 . B5 . E6 . | F6 . E6 . D6 . C6 . | B5 . G#5 . E5 . - -"""
    beat = "k . h k s . h . k k h . s . h s"
    fill = "k . h k s . h . s s s s s s s s"
    return song(170, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R R O R R O R O",
                beat=beat, fill=fill, lead_echo=(0.18, 0.35))


def escape():
    """ESCAPE: the hive collapses. A frantic E minor, 16th arpeggios, no time to breathe."""
    chords = ["Em", "Em", "C", "D", "Em", "Em", "C", "B"]
    melody = """E5 . G5 . B5 . E6 . | D6 . B5 . G5 . B5 . | C6 . E6 . G6 . E6 . | D6 . F#6 . A6 . F#6 .
                E6 . B5 . G5 . E5 . | G5 . B5 . E6 . G6 . | E6 . C6 . G5 . C6 . | D#6 . F#6 . B6 . - -"""
    beat = "k h s h k h s h k h s h k k s s"
    return song(196, chords, melody, arp_pattern=(0, 1, 2, 3), arp_octave=5,
                bass_rhythm="R O R O R O R O", beat=beat)


def starmap():
    """STAR MAP: wide open and curious, F lydian drifting over a slow pulse (the B natural
    is the sense of wonder)."""
    chords = ["Fmaj7", "G", "Em", "Am", "Fmaj7", "G", "C", "C",
              "Dm", "G", "Em", "Am", "Fmaj7", "G", "Am", "E"]
    melody = """A4 . . . C5 . E5 . | D5 . . . B4 . G4 . | G4 . B4 . E5 . G5 . | E5 . . . C5 . A4 .
                A4 . C5 . F5 . A5 . | B5 . . . G5 . D5 . | E5 . . . G5 . C6 . | C6 . . . - - - -
                D5 . F5 . A5 . D6 . | B5 . . . G5 . D5 . | E5 . G5 . B5 . E6 . | C6 . . . A5 . E5 .
                F5 . A5 . C6 . E6 . | D6 . . . B5 . G5 . | A5 . . . E5 . C5 . | G#5 . . . - - - -"""
    beat = "k . . . h . . . s . . . h . . ."
    return song(96, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 3, 2, 1), arp_octave=5,
                bass_rhythm="R . . . F . . .", beat=beat, lead_echo=(0.5, 0.45),
                arp_echo=(0.33, 0.5), bass_instrument=BASS_LONG)


def veil():
    """THE VEIL: a strange, wide E phrygian (the F is the unease), a lead that echoes into
    the distance over a pulse that never quite resolves."""
    chords = ["Em", "F", "Em", "Dm", "Em", "F", "Am", "B",
              "C", "F", "Em", "Em", "Am", "F", "B", "B7"]
    melody = """E5 . . . G5 . B5 . | A5 . . . F5 . C5 . | B4 . E5 . G5 . B5 . | A5 . . . F5 . D5 .
                E5 . G5 . B5 . E6 . | F6 . . . C6 . A5 . | A5 . C6 . E6 . A6 . | F#6 . . . D#6 . B5 .
                G5 . . . C6 . E6 . | F6 . . . A5 . F5 . | E5 . G5 . B5 . E6 . | B5 . . . G5 . E5 .
                A5 . C6 . E6 . A6 . | F6 . . . C6 . A5 . | B5 . D#6 . F#6 . B6 . | A6 . . . - - - -"""
    beat = "k . . h . . s . k . h . . . s h"
    return song(124, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 3, 2, 1), arp_octave=5,
                bass_rhythm="R . R . R . O .", beat=beat, lead_echo=(0.36, 0.45),
                arp_echo=(0.24, 0.4), bass_instrument=BASS_LONG)


def warden():
    """THE WARDEN: a machine that waits. D minor with a tritone stab, clockwork 16ths."""
    chords = ["Dm", "Dm", "G#", "A", "Dm", "Dm", "Bb", "A",
              "Gm", "G#", "Dm", "Dm", "Bb", "G#", "A", "A7"]
    melody = """D5 . F5 . A5 . G#5 . | A5 . . . F5 . D5 . | G#5 . C6 . D#6 . C6 . | A5 . C#6 . E6 . A6 .
                D6 . A5 . F5 . D5 . | F5 . A5 . D6 . F6 . | F6 . D6 . Bb5 . F5 . | E5 . A5 . C#6 . E6 .
                G5 . Bb5 . D6 . G6 . | G#6 . . . D#6 . C6 . | A5 . D6 . F6 . A6 . | G#6 . A6 . F6 . D6 .
                F6 . D6 . Bb5 . F5 . | G#5 . C6 . D#6 . G#6 . | A6 . E6 . C#6 . A5 . | A5 . . . - - - -"""
    beat = "k h h k s h k h k h h k s h s s"
    return song(152, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R R O R R O R R",
                beat=beat, lead_echo=(0.2, 0.3))


# --- galaxy 2, levels 2-6 --------------------------------------------------------------------------
def reef():
    """BONE REEF: something is right behind you. C minor at a sprint, the bass never rests."""
    chords = ["Cm", "Cm", "Ab", "Bb", "Cm", "Cm", "Fm", "G"]
    melody = """C5 . Eb5 . G5 . C6 . | Bb5 . G5 . Eb5 . G5 . | Ab5 . . . C6 . Eb6 . | D6 . Bb5 . F5 . D5 .
                C5 . G5 . C6 . Eb6 . | D6 . C6 . G5 . Eb5 . | F5 . Ab5 . C6 . F6 . | G5 . B5 . D6 . - -"""
    beat = "k h s h k k s h k h s h k k s s"
    return song(164, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R O R O R O R O",
                beat=beat)


def maw():
    """LEECH MAW: F minor, low and hungry, a lead that climbs out of the throat."""
    chords = ["Fm", "Fm", "Db", "C", "Fm", "Fm", "Bbm", "C7"]
    melody = """F4 . Ab4 . C5 . F5 . | E5 . F5 . Ab5 . C6 . | Db6 . . . Ab5 . F5 . | E5 . G5 . C6 . E6 .
                F6 . C6 . Ab5 . F5 . | Ab5 . C6 . F6 . Ab6 . | Bb5 . Db6 . F6 . Bb6 . | G6 . E6 . C6 . - -"""
    beat = "k . h k s . h k k . h k s s h s"
    return song(176, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R R O R R R O R",
                beat=beat, lead_echo=(0.17, 0.3))


def sanctuary():
    """BROOD SANCTUARY: E minor, soft and watchful - something here is worth protecting."""
    chords = ["Em", "C", "G", "D", "Em", "C", "Am", "B"]
    melody = """E5 . . . G5 . B5 . | C6 . . . G5 . E5 . | D5 . G5 . B5 . D6 . | A5 . . . F#5 . D5 .
                E5 . G5 . B5 . E6 . | E6 . C6 . G5 . E5 . | A5 . C6 . E6 . A6 . | F#6 . . . D#6 . - -"""
    beat = "k . . h s . . h k . k h s . . h"
    return song(112, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 1, 3, 1), arp_octave=5,
                bass_rhythm="R . F . R . O .", beat=beat, lead_echo=(0.4, 0.4),
                arp_echo=(0.27, 0.35), bass_instrument=BASS_LONG)


def reaper():
    """THE HOLLOW REAPER: B minor with a raised leading tone, a scythe of 16th notes."""
    chords = ["Bm", "Bm", "G", "F#", "Bm", "Bm", "Em", "F#7"]
    melody = """B4 . D5 . F#5 . B5 . | A5 . F#5 . D5 . F#5 . | G5 . B5 . D6 . G6 . | F#6 . C#6 . A#5 . F#5 .
                B5 . F#5 . D5 . B4 . | D5 . F#5 . B5 . D6 . | E6 . B5 . G5 . E5 . | F#5 . A#5 . C#6 . - -"""
    beat = "k h h s k h s h k h h s k s s s"
    return song(158, chords, melody, arp_pattern=(0, 2, 1, 2), bass_rhythm="R R O R R O R O",
                beat=beat, lead_echo=(0.19, 0.3))


def dark():
    """THE DARK VEIL: almost nothing. A minor, long notes, rests where you listen for them."""
    chords = ["Am", "Am", "Fmaj7", "E", "Am", "Am", "Dm", "E"]
    melody = """A4 . . . . . C5 . | E5 . . . - - - - | F5 . . . E5 . C5 . | B4 . . . - - - -
                A4 . . . E5 . A5 . | C6 . . . B5 . . . | A5 . . . F5 . D5 . | G#5 . . . - - - -"""
    beat = "k . . . . . . . s . . . . . h ."
    return song(100, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 2), arp_octave=3,
                bass_rhythm="R . . . - . . .", beat=beat, lead_echo=(0.6, 0.5),
                arp_echo=(0.45, 0.5), bass_instrument=BASS_LONG)


def eclipse():
    """ECLIPSE: C# minor, blinding - the lead burns bright over a pounding pulse."""
    chords = ["C#m", "C#m", "A", "B", "C#m", "C#m", "F#m", "G#"]
    melody = """C#5 . E5 . G#5 . C#6 . | B5 . G#5 . E5 . G#5 . | A5 . C#6 . E6 . A6 . | F#6 . D#6 . B5 . F#5 .
                G#5 . C#6 . E6 . G#6 . | F#6 . E6 . C#6 . G#5 . | A5 . C#6 . F#6 . A6 . | G#6 . . . C6 . - -"""
    beat = "k h s h k h s k k h s h k k s s"
    return song(150, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R O R O R R O R",
                beat=beat, lead_echo=(0.2, 0.35))


def mirror():
    """MIRROR SEA: D dorian, glassy and calm on top, every phrase answered by its echo."""
    chords = ["Dm", "G", "Dm", "G", "C", "Am", "Dm", "A"]
    melody = """D5 . F5 . A5 . D6 . | B5 . . . G5 . D5 . | F5 . A5 . D6 . F6 . | E6 . . . B5 . G5 .
                C6 . E6 . G6 . E6 . | C6 . A5 . E5 . A5 . | D6 . A5 . F5 . D5 . | C#5 . E5 . A5 . - -"""
    beat = "k . h . s . h . k . h k s . h ."
    return song(132, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 3, 2, 1), arp_octave=5,
                bass_rhythm="R . R . F . O .", beat=beat, lead_echo=(0.45, 0.55),
                arp_echo=(0.34, 0.45), bass_instrument=BASS_LONG)


def mimic():
    """THE MIMIC: G minor - the melody runs down where yours would run up."""
    chords = ["Gm", "Gm", "Eb", "D", "Gm", "Gm", "Cm", "D7"]
    melody = """G5 . D5 . Bb4 . G4 . | Bb4 . D5 . G5 . Bb5 . | Bb5 . G5 . Eb5 . Bb4 . | A4 . D5 . F#5 . A5 .
                D6 . Bb5 . G5 . D5 . | G5 . Bb5 . D6 . G6 . | Eb6 . C6 . G5 . Eb5 . | F#5 . A5 . D6 . - -"""
    beat = "k h s h k h s h k k s h k h s s"
    return song(160, chords, melody, arp_pattern=(2, 1, 0, 1), bass_rhythm="R R O R R O R R",
                beat=beat, lead_echo=(0.19, 0.4))


def pulse():
    """PULSE NEBULA: exactly 120 bpm, four on the floor - the enemy moves on this kick."""
    chords = ["Em", "Em", "C", "D", "Em", "Em", "Am", "B"]
    melody = """E5 . E5 . G5 . E5 . | B5 . . . A5 . G5 . | E5 . E5 . G5 . C6 . | B5 . A5 . F#5 . D5 .
                E5 . E5 . G5 . B5 . | E6 . . . D6 . B5 . | C6 . A5 . E5 . A5 . | B5 . D#6 . F#6 . - -"""
    beat = "k . h . k . h . k . h . k . h ."
    return song(120, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R . O . R . O .",
                beat=beat)


def tempo():
    """TEMPO: 120 bpm clockwork in A minor; the snare lands where the pendulum turns."""
    chords = ["Am", "Am", "F", "G", "Am", "Am", "Dm", "E7"]
    melody = """A5 . E5 . A5 . E5 . | C6 . B5 . A5 . E5 . | F5 . C6 . F5 . C6 . | G5 . D6 . B5 . G5 .
                A5 . C6 . E6 . A6 . | G6 . E6 . C6 . A5 . | D6 . F6 . A6 . F6 . | E6 . G#5 . B5 . - -"""
    beat = "k h s h k h s h k h s h k h s h"
    return song(120, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R O R O R O R O",
                beat=beat)


# --- galaxy 2, levels 7-10 ---------------------------------------------------------------------
def maze():
    """HOLLOW MAZE: B locrian-ish unease, turns that go nowhere - a lead that keeps doubling back."""
    chords = ["Bm", "C", "Bm", "Am", "Bm", "C", "G", "F#"]
    melody = """B4 . D5 . F#5 . . . | E5 . C5 . G4 . . . | B4 . D5 . F#5 . B5 . | A5 . E5 . C5 . A4 .
                B4 . F#5 . B5 . D6 . | C6 . G5 . E5 . C5 . | B5 . G5 . D5 . B4 . | A#4 . C#5 . F#5 . - -"""
    beat = "k . . h s . . h k . k . s . h h"
    return song(128, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 2), arp_octave=4,
                bass_rhythm="R . R O R . F .", beat=beat, lead_echo=(0.35, 0.4),
                arp_echo=(0.23, 0.35))


def grinder():
    """GRINDER: E minor power chords at full throttle, a grinding low lead."""
    chords = ["Em", "Em", "C", "D", "Em", "Em", "A", "B"]
    melody = """E4 . E4 . G4 . E4 . | B4 . A4 . G4 . E4 . | C5 . E5 . G5 . E5 . | D5 . F#5 . A5 . F#5 .
                E5 . B4 . G4 . E4 . | G4 . B4 . E5 . G5 . | A5 . E5 . C#5 . A4 . | B4 . D#5 . F#5 . - -"""
    beat = "k k s h k k s h k k s h k s s s"
    return song(172, chords, melody, arp_pattern=(0, 1, 0, 2), arp_octave=3,
                bass_rhythm="R R R O R R R O", beat=beat)


def spinner():
    """SPINNER: a whirling 16th arpeggio in G minor that never stops turning."""
    chords = ["Gm", "Eb", "Bb", "F", "Gm", "Eb", "Cm", "D"]
    melody = """G5 . . . D5 . Bb4 . | G5 . . . Eb5 . Bb4 . | F5 . D5 . Bb4 . D5 . | F5 . A5 . C6 . A5 .
                G5 . Bb5 . D6 . G6 . | G6 . Eb6 . Bb5 . G5 . | C6 . Eb6 . G6 . Eb6 . | D6 . F#5 . A5 . - -"""
    beat = "k h h s h h k h k h h s h s h h"
    return song(156, chords, melody, arp_pattern=(0, 1, 2, 3, 2, 1, 0, 2), arp_octave=5,
                bass_rhythm="R O R O R O R O", beat=beat, lead_echo=(0.19, 0.3))


def siege():
    """LAST LIGHT: a heroic D major march for a hopeless stand, snare rolls under it."""
    chords = ["D", "D", "Bm", "G", "D", "A", "G", "A"]
    melody = """D5 . . . F#5 . A5 . | D6 . . . C#6 . A5 . | B5 . . . F#5 . D5 . | G5 . B5 . D6 . B5 .
                A5 . F#5 . D5 . F#5 . | A5 . C#6 . E6 . A6 . | G6 . D6 . B5 . G5 . | A5 . . . C#6 . E6 ."""
    beat = "k . s s k . s . k . s s k s s s"
    return song(138, chords, melody, arp_pattern=(0, 1, 2, 1), bass_rhythm="R . R . O . R .",
                beat=beat, lead_echo=(0.22, 0.3))


def court():
    """THE COURT OF NYX: a courtly waltz gone wrong - 3/4 feel in F minor, too slow, too sure."""
    chords = ["Fm", "C7", "Fm", "Db", "Bbm", "Fm", "C", "C7"]
    melody = """F5 . . . . . C5 . | E5 . . . G5 . . . | F5 . Ab5 . C6 . . . | Db6 . . . Ab5 . F5 .
                Bb5 . . . Db6 . F6 . | C6 . . . Ab5 . F5 . | E5 . G5 . C6 . E6 . | G6 . . . - - - -"""
    beat = "k . . . h . h . k . . . h . h ."
    return song(108, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 1, 2, 1, 2, 1), arp_octave=4,
                bass_rhythm="R . . . F . F .", beat=beat, lead_echo=(0.42, 0.45),
                arp_echo=(0.28, 0.4), bass_instrument=BASS_LONG)


def nyx():
    """NYX, THE FIRST HERALD: the court waltz sped into a duel - F minor, relentless."""
    chords = ["Fm", "Fm", "Db", "C", "Fm", "Fm", "Bbm", "C7",
              "Db", "Eb", "Fm", "Fm", "Bbm", "Db", "C", "C7"]
    melody = """F5 . C5 . Ab5 . F5 . | C6 . Ab5 . F5 . C5 . | Db6 . Ab5 . F5 . Db5 . | E5 . G5 . C6 . E6 .
                F6 . C6 . Ab5 . F5 . | Ab5 . C6 . F6 . Ab6 . | Bb5 . Db6 . F6 . Bb6 . | G6 . E6 . C6 . G5 .
                Ab5 . F5 . Db5 . F5 . | G5 . Eb5 . Bb4 . Eb5 . | F5 . Ab5 . C6 . F6 . | E6 . F6 . Ab6 . F6 .
                Db6 . Bb5 . F5 . Bb5 . | Ab5 . F5 . Db5 . Ab5 . | G5 . C6 . E6 . G6 . | C6 . . . - - - -"""
    beat = "k h s h k k s h k h s h k k s s"
    fill = "k h s h k k s h s s s s s s s s"
    return song(176, chords, melody, arp_pattern=(0, 1, 2, 3), bass_rhythm="R R O R R O R O",
                beat=beat, fill=fill, lead_echo=(0.17, 0.35))


def throne():
    """THE HOLLOW THRONE: the Veil's theme (E phrygian) at its darkest and slowest."""
    chords = ["Em", "F", "Em", "Dm", "Em", "F", "C", "B"]
    melody = """E5 . . . . . G5 . | F5 . . . . . C5 . | B4 . . . E5 . G5 . | F5 . . . D5 . . .
                E5 . G5 . B5 . . . | C6 . . . A5 . F5 . | E5 . . . G5 . C6 . | B5 . . . D#6 . - -"""
    beat = "k . . . s . . . k . . h s . . ."
    return song(96, chords, melody, lead=LEAD_SOFT, arp_pattern=(0, 2, 1, 2), arp_octave=4,
                bass_rhythm="R . . . R . O .", beat=beat, lead_echo=(0.55, 0.5),
                arp_echo=(0.4, 0.45), bass_instrument=BASS_LONG)


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
         "level5": level5, "helios": helios, "level6": level6,
         "wraith": wraith, "level7": level7, "kaleidos": kaleidos,
         "level8": level8, "scrapjaw": scrapjaw,
         "level9": level9, "twins": twins,
         "level10": level10, "overmind": overmind, "escape": escape, "starmap": starmap,
         "veil": veil, "warden": warden,
         "reef": reef, "maw": maw, "sanctuary": sanctuary, "reaper": reaper, "dark": dark,
         "eclipse": eclipse, "mirror": mirror, "mimic": mimic, "pulse": pulse, "tempo": tempo,
         "maze": maze, "grinder": grinder, "spinner": spinner, "siege": siege, "court": court,
         "nyx": nyx, "throne": throne,
         "level_clear": level_clear, "game_over": game_over, "win": win}
JINGLES = ("level_clear", "game_over", "win")      # play once instead of looping
