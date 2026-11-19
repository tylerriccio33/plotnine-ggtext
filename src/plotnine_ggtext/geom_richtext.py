from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._artist import BoxSpec
from ._geom_base import geom_rich_base
from ._layout import layout_rect_box
from ._markup import Style, parse
from ._units import as_margin_pt, as_pt_scalar, unit

if TYPE_CHECKING:
    import pandas as pd

# ggplot2's .pt: converts mm (line widths) to points
PT = 72.27 / 25.4


def _missing(v: Any) -> bool:
    return v is None or (isinstance(v, float) and v != v)


def base_style(row: pd.Series) -> Style:
    color = row.get("text_color")
    if _missing(color):
        color = row["color"]
    return Style(
        fontsize=float(row["size"]),
        family=None if _missing(row.get("family")) else row["family"],
        weight=row.get("fontweight", "normal") or "normal",
        style=row.get("fontstyle", "normal") or "normal",
        color=color,
        lineheight=float(row["lineheight"]),
    )


class geom_richtext(geom_rich_base):
    """
    Richtext labels

    Draws text labels similar to [](`~plotnine.geom_label`), but formatted
    using basic markdown/html. Port of `ggtext::geom_richtext()`.

    Supported markup: `**bold**`, `*italic*`, `<b>`, `<strong>`, `<i>`,
    `<em>`, `<br>`, `<sup>`, `<sub>` and
    `<span style="color:...; font-size:...; font-family:...">`.

    Parameters
    ----------
    mapping, data, stat, position, na_rm, inherit_aes, show_legend :
        As for any plotnine geom.
    nudge_x, nudge_y :
        Shift the labels horizontally / vertically. Cannot be combined
        with `position`.
    label_padding :
        Padding inside the label frame, (top, right, bottom, left).
        A [](`~plotnine_ggtext.unit`) or number(s) in points.
        Default ``unit(0.25, "lines")``.
    label_margin :
        Margin outside the label frame. Default ``0``.
    label_r :
        Corner radius of the frame. Default ``unit(0.15, "lines")``.
    use_markdown :
        If `False`, the label is interpreted as HTML only.

    Aesthetics
    ----------
    **x**, **y**, **label**, alpha, angle, color (default colour of text and
    frame), family, fontweight, fontstyle, fill (background), group,
    hjust, vjust (numbers or "left", "center", "right", "bottom",
    "middle", "top", "inward", "outward"), label_color (frame colour,
    overrides `color`), label_size (frame line width, mm), lineheight,
    size (font size, pt), text_color (text colour, overrides `color`).
    """

    DEFAULT_AES = {
        "color": "black",
        "fill": "white",
        "size": 11,
        "angle": 0,
        "hjust": 0.5,
        "vjust": 0.5,
        "alpha": 1,
        "family": None,
        "fontweight": "normal",
        "fontstyle": "normal",
        "lineheight": 1.2,
        "text_color": None,
        "label_color": None,
        "label_size": 0.25,
    }
    REQUIRED_AES = {"x", "y", "label"}
    DEFAULT_PARAMS = {
        "stat": "identity",
        "position": "identity",
        "na_rm": False,
        "label_padding": unit(0.25, "lines"),
        "label_margin": unit(0, "lines"),
        "label_r": unit(0.15, "lines"),
        "use_markdown": True,
    }

    def make_spec(self, row: pd.Series, params: dict[str, Any]) -> BoxSpec:
        style = base_style(row)
        hjust, vjust = float(row["hjust"]), float(row["vjust"])
        # gridtext: halign = hjust, valign = vjust
        pars = parse(row["label"], style, halign=hjust, use_markdown=params["use_markdown"])
        margin = as_margin_pt(params["label_margin"])
        padding = as_margin_pt(params["label_padding"])
        r = as_pt_scalar(params["label_r"]) or 0.0

        def layout(npc_w: float, npc_h: float):
            return layout_rect_box(
                pars, margin, padding,
                content_hjust=hjust, content_vjust=vjust, r=r,
            )  # fmt: skip

        edge = row.get("label_color")
        if _missing(edge):
            edge = row["color"]
        return BoxSpec(
            x=float(row["x"]),
            y=float(row["y"]),
            hjust=hjust,
            vjust=vjust,
            angle=float(row["angle"]),
            layout=layout,
            text_color=style.color,
            alpha=row["alpha"],
            fill=row["fill"],
            edgecolor=edge,
            linewidth=float(row["label_size"]) * PT,
        )
