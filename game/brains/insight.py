"""What they learned, in words (<= 32 characters a line, most telling first)."""
from ..config.tuning import BRAIN_MIN_DODGES, BRAIN_MIN_SECONDS

NAMES = {"L": "LEFT", "R": "RIGHT", "U": "UP", "D": "DOWN"}


def insights(model):
    if model.seconds < BRAIN_MIN_SECONDS:
        return ["WE ARE STILL WATCHING."]
    out = []
    if model.dodge_count >= BRAIN_MIN_DODGES:
        d = max(NAMES, key=model.dodge_share)
        share = model.dodge_share(d)
        if share >= 0.62:
            out.append((share, f"YOU ALWAYS BREAK {NAMES[d]}."))
        elif share >= 0.5:
            out.append((share, f"UNDER FIRE YOU GO {NAMES[d]}."))
    bottom = model.zone_share(rows=range(model.rows - 2, model.rows))
    if bottom >= 0.55:
        out.append((bottom, "YOU HIDE AT THE BOTTOM."))
    left = model.zone_share(cols=range(0, model.cols // 2))
    if left >= 0.65:
        out.append((left, "YOU KEEP TO THE LEFT."))
    elif left <= 0.35:
        out.append((1 - left, "YOU KEEP TO THE RIGHT."))
    for name in model.weapons:
        share = model.weapon_share(name)
        if share >= 0.6 and sum(model.weapons.values()) > 10:
            out.append((share, f"YOU TRUST THE {name}."))
    if model.reaction is not None and len(model.reactions) >= 3:
        r = model.reaction
        word = "SLOW" if r > 0.45 else "FAST" if r < 0.25 else "STEADY"
        out.append((0.5, f"YOU REACT IN {r:.2f} S. {word}."))
    out.sort(key=lambda item: -item[0])
    return [text for _, text in out] or ["YOU ARE HARD TO READ. FOR NOW."]
