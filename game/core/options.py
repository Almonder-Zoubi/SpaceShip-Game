"""Player options (pause menu): music / sound volume, reduce shake, reduce flashes.

Stored as a small dict in the save file; this class only knows the rows and their values.
"""

VOLUME_STEPS = 10
DEFAULTS = {"music": 7, "sound": 8, "shake": 1, "flashes": 1}   # shake / flashes: 1 = full


class Options:
    """UP/DOWN pick a row, LEFT/RIGHT change it. Rows: (key, label)."""

    ROWS = (("music", "MUSIC"), ("sound", "SOUND"), ("shake", "SCREEN SHAKE"),
            ("flashes", "FLASHES"))

    def __init__(self, values=None):
        self.values = dict(DEFAULTS)
        for key, value in (values or {}).items():
            if key in DEFAULTS:
                top = VOLUME_STEPS if key in ("music", "sound") else 1
                self.values[key] = min(top, max(0, int(value)))

    def __getitem__(self, key):
        return self.values[key]

    def change(self, key, step):
        """Volumes go 0..10; the on/off rows toggle."""
        if key in ("music", "sound"):
            self.values[key] = min(VOLUME_STEPS, max(0, self.values[key] + step))
        else:
            self.values[key] = 1 - self.values[key]

    def text(self, key):
        """How a row's value reads, e.g. '7' or 'FULL' / 'REDUCED'."""
        if key in ("music", "sound"):
            return str(self.values[key])
        return "FULL" if self.values[key] else "REDUCED"

    @property
    def music_volume(self):
        return self.values["music"] / VOLUME_STEPS

    @property
    def sound_volume(self):
        return self.values["sound"] / VOLUME_STEPS
