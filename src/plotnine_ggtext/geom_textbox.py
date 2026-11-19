from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ggir import as_margin_pt, as_pt_scalar, layout_rect_box, markup_to_boxes, unit
from plotnine.exceptions import PlotnineError

from ._artist import BoxSpec
from ._geom_base import geom_rich_base
from .geom_richtext import PT, _missing, base_style

if TYPE_CHECKING:
    import pandas as pd

# orientation -> (angle, flip)
ORIENTATIONS = {
    "upright": (0.0, False),
    "left-rotated": (90.0, True),
    "right-rotated": (-90.0, True),
    "inverted": (180.0, False),
}


class geom_textbox(geom_rich_base):
    """
    Draw boxes containing word-wrapped rich text

    Port of `ggtext::geom_textbox()`. Text is formatted with basic
    markdown/html (see [](`~plotnine_ggtext.geom_richtext`)) and wrapped to
    the box width.

    Parameters
    ----------
    mapping, data, stat, position, na_rm, inherit_aes, show_legend :
        As for any plotnine geom.
    nudge_x, nudge_y :
        Shift the boxes horizontally / vertically. Cannot be combined
        with `position`.
    width, height :
        Size of the box, *including margins*. A [](`~plotnine_ggtext.unit`)
        (``"npc"`` is relative to the panel) or a number in points.
        Default width is ``unit(2, "in")``. If `height` is `None`
        (the default), the height fits the text. If `width` is `None`,
        no word wrapping takes place.
    minwidth, maxwidth, minheight, maxheight :
        Limits for `width` and `height`. `None` means not enforced.
    box_padding :
        Padding inside the box, (top, right, bottom, left).
        Default ``unit(5.5, "pt")``.
    box_margin :
        Margin outside the box. Default ``0``.
    box_r :
        Corner radius of the box. Default ``unit(5.5, "pt")``.
    use_markdown :
        If `False`, the label is interpreted as HTML only.

    Aesthetics
    ----------
    **x**, **y**, **label**, alpha, box_color (outline colour, overrides
    `color`; use ``"none"`` for no outline), box_size (outline width, mm), color (default colour of text
    and outline), family, fontweight, fontstyle, fill (background), group,
    halign (alignment of text inside the box), hjust (alignment of the box),
    lineheight, orientation (``"upright"``, ``"left-rotated"``,
    ``"right-rotated"``, ``"inverted"``), size (font size, pt), text_color
    (text colour, overrides `color`), valign (vertical alignment of the
    text inside the box), vjust (vertical alignment of the box).
    """

    DEFAULT_AES = {
        "color": "black",
        "fill": "white",
        "size": 11,
        "hjust": 0.5,
        "vjust": 0.5,
        "halign": 0,
        "valign": 1,
        "alpha": 1,
        "family": None,
        "fontweight": "normal",
        "fontstyle": "normal",
        "lineheight": 1.2,
        "text_color": None,
        "box_color": None,
        "box_size": 0.25,
        "orientation": "upright",
    }
    REQUIRED_AES = {"x", "y", "label"}
    DEFAULT_PARAMS = {
        "stat": "identity",
        "position": "identity",
        "na_rm": False,
        "nudge_x": 0,
        "nudge_y": 0,
        "box_padding": unit(5.5, "pt"),
        "box_margin": unit(0, "pt"),
        "box_r": unit(5.5, "pt"),
        "width": unit(2, "in"),
        "minwidth": None,
        "maxwidth": None,
        "height": None,
        "minheight": None,
        "maxheight": None,
        "use_markdown": True,
    }

    def make_spec(self, row: pd.Series, params: dict[str, Any]) -> BoxSpec:
        style = base_style(row)
        orientation = row["orientation"]
        if orientation not in ORIENTATIONS:
            raise PlotnineError(
                f"Unknown orientation {orientation!r}, must be one of "
                f"{list(ORIENTATIONS)}"
            )
        angle, flip = ORIENTATIONS[orientation]
        halign, valign = float(row["halign"]), float(row["valign"])
        pars = markup_to_boxes(row["label"], style, halign=halign, use_markdown=params["use_markdown"])
        margin = as_margin_pt(params["box_margin"])
        padding = as_margin_pt(params["box_padding"])
        r = as_pt_scalar(params["box_r"]) or 0.0

        def layout(npc_w: float, npc_h: float):
            # with a rotated box, the width runs along the panel's y axis
            ref_w, ref_h = (npc_h, npc_w) if flip else (npc_w, npc_h)
            width = as_pt_scalar(params["width"], ref_w)
            if width is not None:
                lo = as_pt_scalar(params["minwidth"], ref_w)
                hi = as_pt_scalar(params["maxwidth"], ref_w)
                if lo is not None and width < lo:
                    width = lo
                if hi is not None and width > hi:
                    width = hi
            height = as_pt_scalar(params["height"], ref_h)

            def _do(h):
                return layout_rect_box(
                    pars, margin, padding,
                    width=width, height=h, wrap=width is not None,
                    content_hjust=halign, content_vjust=valign, r=r,
                )  # fmt: skip

            L = _do(height)
            lo = as_pt_scalar(params["minheight"], ref_h)
            hi = as_pt_scalar(params["maxheight"], ref_h)
            h = L.height
            if lo is not None and h < lo:
                h = lo
            if hi is not None and h > hi:
                h = hi
            if h != L.height:
                L = _do(h)
            return L

        # None inherits `color`; "none"/NaN (R's NA) means no outline
        edge = row.get("box_color")
        if edge is None:
            edge = row["color"]
        return BoxSpec(
            x=float(row["x"]),
            y=float(row["y"]),
            hjust=float(row["hjust"]),
            vjust=float(row["vjust"]),
            angle=angle,
            layout=layout,
            text_color=style.color,
            alpha=row["alpha"],
            fill=row["fill"],
            edgecolor=edge,
            linewidth=float(row["box_size"]) * PT,
        )
