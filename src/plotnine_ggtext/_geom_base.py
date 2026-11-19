from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from plotnine._utils import order_as_data_mapping
from plotnine.exceptions import PlotnineError
from plotnine.geoms.geom import geom
from plotnine.positions import position_nudge

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes
    from matplotlib.offsetbox import DrawingArea

    from plotnine import aes
    from plotnine.iapi import panel_view
    from plotnine.layer import layer
    from plotnine.typing import DataLike

_JUST = {
    "left": 0.0,
    "center": 0.5,
    "centre": 0.5,
    "right": 1.0,
    "bottom": 0.0,
    "middle": 0.5,
    "top": 1.0,
}


def _just_dir(x: np.ndarray, tol: float = 0.001) -> np.ndarray:
    out = np.full(len(x), 1)
    out[x < 0.5 - tol] = 0
    out[x > 0.5 + tol] = 2
    return out


def compute_just(just: Any, x_npc: np.ndarray) -> np.ndarray:
    """
    Resolve justification values, including "inward" and "outward"

    Port of ggplot2's `compute_just()`.
    """
    just = np.asarray(just, dtype=object)
    if just.ndim == 0:
        just = np.repeat(just, len(x_npc))
    out = np.empty(len(just), dtype=float)
    d = _just_dir(np.asarray(x_npc, dtype=float))
    for i, j in enumerate(just):
        if isinstance(j, str):
            if j == "inward":
                j = ("left", "middle", "right")[d[i]]
            elif j == "outward":
                j = ("right", "middle", "left")[d[i]]
            try:
                out[i] = _JUST[j]
            except KeyError as e:
                raise PlotnineError(f"Unknown justification {j!r}") from e
        else:
            out[i] = float(j)
    return out


def to_npc(values: np.ndarray, rng: tuple[float, float]) -> np.ndarray:
    lo, hi = rng
    if hi == lo:
        return np.full(len(values), 0.5)
    return (np.asarray(values, dtype=float) - lo) / (hi - lo)


class geom_rich_base(geom):
    """Shared behaviour of the rich text geoms"""

    def __init__(
        self,
        mapping: aes | None = None,
        data: DataLike | None = None,
        **kwargs: Any,
    ):
        data, mapping = order_as_data_mapping(data, mapping)
        nudge = {}
        if "nudge_x" in kwargs:
            nudge["x"] = kwargs["nudge_x"]
        if "nudge_y" in kwargs:
            nudge["y"] = kwargs["nudge_y"]
        if nudge:
            if "position" in kwargs:
                raise PlotnineError(
                    "You must specify either `position` or "
                    "`nudge_x`/`nudge_y` but not both."
                )
            kwargs["position"] = position_nudge(**nudge)
        super().__init__(mapping, data, **kwargs)

    def draw_panel(
        self,
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: Any,
        ax: Axes,
    ):
        from ._artist import RichTextCollection

        data = coord.transform(data, panel_params)
        params = self.params
        data = data.reset_index(drop=True)
        x_npc = to_npc(data["x"], panel_params.x.range)
        y_npc = to_npc(data["y"], panel_params.y.range)
        data["hjust"] = compute_just(data["hjust"], x_npc)
        data["vjust"] = compute_just(data["vjust"], y_npc)
        specs = [self.make_spec(row, params) for _, row in data.iterrows()]
        artist = RichTextCollection(specs, zorder=params["zorder"])
        if params.get("raster"):
            artist.set_rasterized(True)
        ax.add_artist(artist)

    def make_spec(self, row: pd.Series, params: dict[str, Any]):
        raise NotImplementedError

    @staticmethod
    def draw_legend(
        data: pd.Series[Any], da: DrawingArea, lyr: layer
    ) -> DrawingArea:
        """
        Draw letter 'a' in the box (ggplot2's `draw_key_text`)
        """
        from matplotlib.text import Text

        from ._artist import rgba

        color = data.get("text_color")
        if color is None or (isinstance(color, float) and np.isnan(color)):
            color = data["color"]
        key = Text(
            x=0.5 * da.width,
            y=0.5 * da.height,
            text="a",
            size=data["size"],
            family=data.get("family"),
            color=rgba(color, data["alpha"]),
            rotation=data.get("angle", 0),
            horizontalalignment="center",
            verticalalignment="center",
        )
        da.add_artist(key)
        return da

    @staticmethod
    def legend_key_size(
        data: pd.Series[Any], min_size: tuple[int, int], lyr: layer
    ) -> tuple[int, int]:
        w, h = min_size
        s = data["size"]
        return max(w, s), max(h, s)
