"""
Minimal grid-style units.

ggtext takes padding, margins, radii and box sizes as `grid::unit()`
values. This module provides a small equivalent so the same values can be
expressed in Python, e.g. ``unit(0.25, "in")`` or ``unit([5, 5, 5, 5], "pt")``.

Bare numbers are interpreted as points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

# Conversion factors to points (1/72 inch, the matplotlib point)
_TO_PT = {
    "pt": 1.0,
    "points": 1.0,
    "in": 72.0,
    "inch": 72.0,
    "inches": 72.0,
    "cm": 72.0 / 2.54,
    "mm": 72.0 / 25.4,
    "px": 72.0 / 96.0,
}

# A grid "line" is fontsize * lineheight of the enclosing graphical context.
# ggplot2 draws panels with the grid defaults (fontsize=12, lineheight=1.2).
LINE_PT = 12 * 1.2


@dataclass(frozen=True)
class unit:
    """
    A length (or a vector of lengths) with units

    Parameters
    ----------
    value :
        A number or a sequence of numbers.
    units :
        One of ``"pt"``, ``"in"``, ``"cm"``, ``"mm"``, ``"px"``,
        ``"lines"`` or ``"npc"``. ``"npc"`` is relative to the size of the
        panel (only meaningful for the box `width`/`height` of
        [](`~plotnine_ggtext.geom_textbox`)).
    """

    value: float | Sequence[float]
    units: str = "pt"

    def __post_init__(self):
        if self.units not in _TO_PT and self.units not in ("lines", "npc"):
            raise ValueError(f"Unknown unit {self.units!r}")

    @property
    def values(self) -> list[float]:
        v = self.value
        if isinstance(v, (int, float)):
            return [float(v)]
        return [float(x) for x in v]

    def to_pt(self, npc_pt: float | None = None) -> list[float]:
        """
        Convert to points

        Parameters
        ----------
        npc_pt :
            Size, in points, that corresponds to 1 npc.
        """
        if self.units == "lines":
            f = LINE_PT
        elif self.units == "npc":
            if npc_pt is None:
                raise ValueError("npc units need a reference size")
            f = npc_pt
        else:
            f = _TO_PT[self.units]
        return [x * f for x in self.values]


UnitLike = Union[unit, float, int, Sequence[float]]


def as_pt(x: UnitLike | None, npc_pt: float | None = None) -> list[float] | None:
    """Convert unit-like input to a list of point values"""
    if x is None:
        return None
    if isinstance(x, unit):
        return x.to_pt(npc_pt)
    if isinstance(x, (int, float)):
        return [float(x)]
    return [float(v) for v in x]


def as_pt_scalar(x: UnitLike | None, npc_pt: float | None = None) -> float | None:
    v = as_pt(x, npc_pt)
    if v is None:
        return None
    return v[0]


def as_margin_pt(x: UnitLike) -> tuple[float, float, float, float]:
    """
    Convert to a (top, right, bottom, left) margin in points

    Values are recycled to length 4, as `rep(x, length.out = 4)` in R.
    """
    v = as_pt(x)
    assert v is not None
    v = (v * 4)[:4]
    return (v[0], v[1], v[2], v[3])
