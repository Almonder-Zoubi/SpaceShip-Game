"""Dialog lines with speakers, grouped into radio cards (pure logic, no pygame)."""
from dataclasses import dataclass

VEGA = "COMMANDER VEGA"
VANTA = "VANTA"
UNKNOWN = "???"
HIJACKERS = (VANTA, UNKNOWN)      # these break into Vega's channel (the card glitches)
CARD_LINES = 3                    # lines per radio card


@dataclass(frozen=True)
class Line:
    """One line of dialog by a speaker. A plain string in level data means VEGA speaks."""
    speaker: str
    text: str


def as_line(entry):
    return entry if isinstance(entry, Line) else Line(VEGA, entry)


def cards(entries):
    """[(speaker, (line, ...)), ...]: consecutive lines of one speaker share a card
    (at most CARD_LINES per card)."""
    out = []
    for line in map(as_line, entries):
        if out and out[-1][0] == line.speaker and len(out[-1][1]) < CARD_LINES:
            out[-1] = (line.speaker, out[-1][1] + (line.text,))
        else:
            out.append((line.speaker, (line.text,)))
    return out


def is_hijack(speaker):
    return speaker in HIJACKERS
