"""
Matplotlib artist that draws the rich text boxes of a geom layer

Layout is done at draw time, because some sizes (e.g. a textbox width
in npc units) depend on the size of the axes. The layout and drawing
primitives come from ggir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from ggir import box_artists, box_extent, box_transform, measure_with
from matplotlib.artist import Artist, allow_rasterization
from matplotlib.transforms import Bbox

if TYPE_CHECKING:
    from ggir import Layout
    from matplotlib.backend_bases import RendererBase


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

    def _boxes(self):
        """Yield (spec, layout, transform) for each box, in display coords"""
        ax = self.axes
        assert ax is not None
        npc_w, npc_h = self._panel_size_pt()
        dpi = self.figure.dpi  # pyright: ignore
        for s in self.specs:
            if not (np.isfinite(s.x) and np.isfinite(s.y)):
                continue
            L = s.layout(npc_w, npc_h)
            anchor = ax.transData.transform((s.x, s.y))
            trans = box_transform(
                L, anchor, hjust=s.hjust, vjust=s.vjust, angle=s.angle, dpi=dpi
            )
            yield s, L, trans

    @allow_rasterization
    def draw(self, renderer: RendererBase):
        if not self.get_visible():
            return
        ax = self.axes
        renderer.open_group("richtext", gid=self.get_gid())
        with measure_with(renderer):
            boxes = list(self._boxes())
        for s, L, trans in boxes:
            artists = box_artists(
                L,
                trans,
                angle=s.angle,
                text_color=s.text_color,
                alpha=s.alpha,
                fill=s.fill,
                edgecolor=s.edgecolor,
                linewidth=s.linewidth,
            )
            for a in artists:
                a.set_figure(self.figure)  # pyright: ignore
                if self._clip_on and ax is not None:
                    a.set_clip_box(ax.bbox)
                a.draw(renderer)
        renderer.close_group("richtext")
        self.stale = False

    def get_window_extent(self, renderer=None):
        if renderer is None:
            renderer = self.figure._get_renderer()  # pyright: ignore
        with measure_with(renderer):
            bboxes = [box_extent(L, t, margins=False) for _, L, t in self._boxes()]
        if not bboxes:
            return Bbox.null()
        return Bbox.union(bboxes)
