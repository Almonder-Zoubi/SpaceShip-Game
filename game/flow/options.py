"""Options in the pause menu: volumes, reduce shake, reduce flashes (saved in save.json)."""
from ..config.tuning import REDUCED_SHAKE
from ..core.options import Options


class OptionsMixin:
    """Game mixin: the pause screen lists the options; UP/DOWN pick, LEFT/RIGHT change."""

    def load_options(self):
        self.options = Options(self.save.options)
        self.options_cursor = 0
        self.apply_options()

    def apply_options(self):
        self.shake.scale = 1.0 if self.options["shake"] else REDUCED_SHAKE
        self.audio.set_volume(self.options.sound_volume, self.options.music_volume)

    def options_move(self, step):
        self.options_cursor = (self.options_cursor + step) % len(Options.ROWS)
        self.audio.play("select")

    def options_change(self, step):
        key = Options.ROWS[self.options_cursor][0]
        self.options.change(key, step)
        self.apply_options()
        self.save.options = dict(self.options.values)
        self.save.save()
        self.audio.play("select")
