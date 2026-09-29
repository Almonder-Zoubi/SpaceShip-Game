"""PlayerModel: what the enemy has seen of the player, updated every frame in flight."""
from ..config.tuning import (BRAIN_DODGE_SPEED, BRAIN_FORGET, BRAIN_GRID, BRAIN_REACTIONS)

DIRECTIONS = ("L", "R", "U", "D")


class PlayerModel:
    """Counts, nothing else. Screen positions are in canvas px (w x h); the heatmap cells
    hold seconds spent there."""

    def __init__(self, w=320, h=240):
        self.w, self.h = w, h
        cols, rows = BRAIN_GRID
        self.cols, self.rows = cols, rows
        self.heat = [0.0] * (cols * rows)
        self.dodges = {d: 0.0 for d in DIRECTIONS}
        self.weapons = {}                 # weapon name -> seconds fired
        self.reactions = []               # seconds from a telegraph to the first move
        self._dodging = False
        self._telegraph = None            # seconds since a telegraph (None = not waiting)

    # --- watching -------------------------------------------------------------------------
    def observe(self, dt, x, y, vx, vy, threatened, weapon=None):
        """One frame of flight. threatened: a bullet or body is about to reach the rocket."""
        col = min(self.cols - 1, max(0, int(x / self.w * self.cols)))
        row = min(self.rows - 1, max(0, int(y / self.h * self.rows)))
        self.heat[row * self.cols + col] += dt
        if weapon:
            self.weapons[weapon] = self.weapons.get(weapon, 0.0) + dt
        moving = abs(vx) > BRAIN_DODGE_SPEED or abs(vy) > BRAIN_DODGE_SPEED
        if threatened and moving and not self._dodging:
            if abs(vx) >= abs(vy):
                self.dodges["L" if vx < 0 else "R"] += 1
            else:
                self.dodges["U" if vy < 0 else "D"] += 1
        self._dodging = threatened and moving
        if self._telegraph is not None:
            self._telegraph += dt
            if moving:
                self.reactions = (self.reactions + [self._telegraph])[-BRAIN_REACTIONS:]
                self._telegraph = None
            elif self._telegraph > 3.0:            # never reacted: stop waiting
                self._telegraph = None

    def telegraph(self):
        """A boss just showed an attack coming (a lock-on, a warning line)."""
        self._telegraph = 0.0

    def forget(self, keep=BRAIN_FORGET):
        """At every level start old habits weigh a little less (recent play counts more)."""
        self.heat = [v * keep for v in self.heat]
        self.dodges = {d: v * keep for d, v in self.dodges.items()}
        self.weapons = {k: v * keep for k, v in self.weapons.items()}

    # --- what it knows --------------------------------------------------------------------
    @property
    def seconds(self):
        return sum(self.heat)

    @property
    def dodge_count(self):
        return sum(self.dodges.values())

    def dodge_share(self, direction):
        total = self.dodge_count
        return self.dodges[direction] / total if total else 0.0

    def weapon_share(self, name):
        total = sum(self.weapons.values())
        return self.weapons.get(name, 0.0) / total if total else 0.0

    def zone_share(self, cols=None, rows=None):
        """Share of time spent in these columns / rows (ranges; None = all)."""
        total = self.seconds
        if not total:
            return 0.0
        cols = cols or range(self.cols)
        rows = rows or range(self.rows)
        return sum(self.heat[r * self.cols + c] for r in rows for c in cols) / total

    def hot_spot(self):
        """Centre (px) of the cell the rocket spends most time in."""
        i = max(range(len(self.heat)), key=self.heat.__getitem__)
        col, row = i % self.cols, i // self.cols
        return (col + 0.5) * self.w / self.cols, (row + 0.5) * self.h / self.rows

    @property
    def reaction(self):
        return sum(self.reactions) / len(self.reactions) if self.reactions else None

    # --- saving ---------------------------------------------------------------------------
    def to_dict(self):
        return {"heat": [round(v, 2) for v in self.heat],
                "dodges": {d: round(v, 2) for d, v in self.dodges.items()},
                "weapons": {k: round(v, 2) for k, v in self.weapons.items()},
                "reactions": [round(v, 3) for v in self.reactions]}

    @classmethod
    def from_dict(cls, data, w=320, h=240):
        model = cls(w, h)
        heat = [float(v) for v in data.get("heat", [])]
        if len(heat) == len(model.heat):
            model.heat = heat
        for d in DIRECTIONS:
            model.dodges[d] = float(data.get("dodges", {}).get(d, 0.0))
        model.weapons = {str(k): float(v) for k, v in data.get("weapons", {}).items()}
        model.reactions = [float(v) for v in data.get("reactions", [])][-BRAIN_REACTIONS:]
        return model
