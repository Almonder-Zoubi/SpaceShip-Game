"""Sound direction: which music plays, engine / laser loops, and sounds for weapon state changes.

One-off sounds for events (explosions, pickups, hits) are played where the event happens;
this mixin handles everything that follows from the game's state each frame.
"""
from .states import MENU_STATES, Phase, State


class SoundMixin:
    """Game mixin: call _update_audio() once per frame."""

    def _music_track(self):
        """The track for the current state (None = silence)."""
        s = self.state
        if s in MENU_STATES:
            return "title"
        if s in (State.STAR_MAP, State.JOURNAL):
            return "starmap"
        if s == State.LEVEL_CLEAR:
            return "level_clear"
        if s in (State.WIN, State.WARP):
            return "win"
        if s == State.GAME_OVER:
            return "game_over"
        if s == State.DYING or self.phase in (Phase.WARNING, Phase.CLEARED):
            return None
        if self.phase == Phase.BOSS:
            return self.boss_entry.music
        return self.wave.music or self.level.music

    def _update_audio(self):
        audio = self.audio
        audio.music(self._music_track())
        flying = self.state == State.PLAYING and self.ship.alive
        audio.loop("engine", 0.25 + 0.75 * self.ship.throttle if flying else 0)
        weapons = {w.name: w for w in self.weapons}
        laser, arc = weapons["LASER"], weapons["ARC"]
        audio.loop("laser", 1.0 if flying and laser.active else 0)
        audio.loop("arc", 1.0 if flying and arc.active else 0)

        # Rising edges of weapon states since the last frame.
        was = self._sound_state
        now = {"overheated": laser.overheated, "blast": self.blast.active}
        shooters = (("GUN", weapons["GUN"], "gun"), ("SCATTER", weapons["SCATTER"], "scatter"),
                    ("PLASMA", weapons["PLASMA"], "plasma"),
                    ("POD", self.secondaries["ROCKET POD"], "rocket"))
        for key, weapon, _ in shooters:
            now[key] = weapon.shots
        if flying:
            for key, weapon, sound in shooters:
                if now[key] > was.get(key, now[key]):
                    audio.play(sound)
            if now["overheated"] and not was.get("overheated"):
                audio.play("overheat")
            if now["blast"] and not was.get("blast"):
                audio.play("blast")
        self._sound_state = now
