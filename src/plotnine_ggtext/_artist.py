"""
Matplotlib artist that draws laid-out rich text boxes

Layout is done at draw time, because some sizes (e.g. a textbox width
in npc units) depend on the size of the axes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from matplotlib.artist import Artist, allow_rasterization
from matplotlib.colors import to_rgba
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.text import Text
from matplotlib.transforms import Affine2D, Bbox

from ._metrics import font_properties

if TYPE_CHECKING:
    from matplotlib.backend_bases import RendererBase

    from ._layout import Layout

# Bezier constant for approximating a quarter circle
_KAPPA = 0.5522847498


def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> Path:
    """Rounded rectangle path, like `grid::roundrectGrob()`"""
    r = max(0.0, min(r, w / 2, h / 2))
    if r == 0:
        verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        codes = [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY]
        return Path(verts, codes)

    k = _KAPPA * r
    x0, y0, x1, y1 = x, y, x + w, y + h
    verts = [
        (x0 + r, y0),
        (x1 - r, y0),
        (x1 - r + k, y0), (x1, y0 + r - k), (x1, y0 + r),
        (x1, y1 - r),
        (x1, y1 - r + k), (x1 - r + k, y1), (x1 - r, y1),
        (x0 + r, y1),
        (x0 + r - k, y1), (x0, y1 - r + k), (x0, y1 - r),
        (x0, y0 + r),
        (x0, y0 + r - k), (x0 + r - k, y0), (x0 + r, y0),
        (x0 + r, y0),
    ]  # fmt: skip
    C = Path.CURVE4
    codes = (
        [Path.MOVETO, Path.LINETO]
        + [C] * 3 + [Path.LINETO]
        + [C] * 3 + [Path.LINETO]
        + [C] * 3 + [Path.LINETO]
        + [C] * 3 + [Path.CLOSEPOLY]
    )  # fmt: skip
    return Path(verts, codes)


def _is_missing(c: Any) -> bool:
    if c is None:
        return True
    if isinstance(c, float) and np.isnan(c):
        return True
    if isinstance(c, str) and c.lower() in ("none", "na", ""):
        return True
    return False


def rgba(c: Any, alpha: float | None = None):
    """Colour with alpha, or 'none' for missing colours"""
    if _is_missing(c):
        return "none"
    if alpha is None or (isinstance(alpha, float) and np.isnan(alpha)):
        return to_rgba(c)
    r, g, b, a = to_rgba(c)
    return (r, g, b, a * alpha)


@dataclass
class BoxSpec:
    """Everything needed to draw one rich text box"""

    x: float  # anchor, data coordinates
    y: float
    hjust: float
    vjust: float
    angle: float
    # Called with the npc reference sizes (width_pt, height_pt) of the
    # panel and returns the layout
    layout: Callable[[float, float], Layout]
    text_color: Any
    alpha: float
    fill: Any
    edgecolor: Any
    linewidth: float  # pt


class RichTextCollection(Artist):
    """Draws a set of rich text boxes onto an axes"""

    def __init__(self, specs: list[BoxSpec], zorder: float = 1, clip_on=True):
        super().__init__()
        self.specs = specs
        self.set_zorder(zorder)
        self._clip_on = clip_on

    def _panel_size_pt(self) -> tuple[float, float]:
        ax = self.axes
        assert ax is not None
        dpi = self.figure.dpi  # pyright: ignore
        bb = ax.bbox
        return bb.width * 72 / dpi, bb.height * 72 / dpi

    def _draw_items(self, renderer: RendererBase | None):
        """Generate patches and texts for all boxes, in display coords"""
        ax = self.axes
        assert ax is not None
        npc_w, npc_h = self._panel_size_pt()
        px_per_pt = self.figure.dpi / 72  # pyright: ignore
        items = []
        for s in self.specs:
            if not (np.isfinite(s.x) and np.isfinite(s.y)):
                continue
            L = s.layout(npc_w, npc_h)
            ax_px, ay_px = ax.transData.transform((s.x, s.y))
            trans = (
                Affine2D()
                .translate(-s.hjust * L.width, -s.vjust * L.height)
                .scale(px_per_pt)
                .rotate_deg(s.angle)
                .translate(ax_px, ay_px)
            )

            rx, ry, rw, rh = L.rect
            patch = PathPatch(
                rounded_rect_path(rx, ry, rw, rh, L.r),
                transform=trans,
                facecolor=rgba(s.fill, s.alpha),
                edgecolor=rgba(s.edgecolor, s.alpha),
                linewidth=s.linewidth,
            )
            box_items = [patch]
            for t in L.texts:
                px, py = trans.transform((t.x, t.y))
                color = t.style.color if t.style.color is not None else s.text_color
                txt = Text(
                    px,
                    py,
                    t.text,
                    color=rgba(color, s.alpha),
                    fontproperties=font_properties(t.style),
                    rotation=s.angle,
                    rotation_mode="anchor",
                    horizontalalignment="left",
                    verticalalignment="baseline",
                )
                box_items.append(txt)
            items.append(box_items)
        return items

    @allow_rasterization
    def draw(self, renderer: RendererBase):
        if not self.get_visible():
            return
        ax = self.axes
        renderer.open_group("richtext", gid=self.get_gid())
        for box_items in self._draw_items(renderer):
            for a in box_items:
                a.set_figure(self.figure)  # pyright: ignore
                if self._clip_on and ax is not None:
                    a.set_clip_box(ax.bbox)
                a.draw(renderer)
        renderer.close_group("richtext")
        self.stale = False

    def get_window_extent(self, renderer=None):
        bboxes = []
        for box_items in self._draw_items(renderer):
            patch = box_items[0]
            path = patch.get_path().transformed(patch.get_transform())
            bboxes.append(Bbox.from_extents(*path.vertices.min(0), *path.vertices.max(0)))
        if not bboxes:
            return Bbox.null()
        return Bbox.union(bboxes)
