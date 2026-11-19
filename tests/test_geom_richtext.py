"""
Tests for geom_richtext

`test_rotated_labels_w_colors` is a one-to-one port of ggtext's
tests/testthat/test-geom-richtext.R ("Rotated labels w/ colors").
The R rendering lives in tests/reference_r/ for side-by-side comparison.
"""

import pandas as pd
import pytest
from plotnine import (
    aes,
    facet_wrap,
    geom_point,
    ggplot,
    position_nudge,
    scale_color_identity,
    scale_fill_identity,
    xlim,
    ylim,
)
from plotnine.exceptions import PlotnineError

from plotnine_ggtext import geom_richtext, unit


# ggtext: test-geom-richtext.R -------------------------------------------------


def test_rotated_labels_w_colors():
    df = pd.DataFrame(
        {
            "x": 0.5,
            "y": 0.5,
            "label": "The **quick** *brown* fox.",
            "angle": [0, 45, 90, 135],
            "label_colour": ["#858E4E", "#24988F", "#8C82B8", "#B97681"],
            "fill": ["#E6EBD1", "#CDEFE9", "#E8E6FC", "#FEE1E5"],
            "label_size": [0.1, 0.25, 0.5, 1],
        }
    )

    p = (
        ggplot()
        + geom_richtext(
            data=df,
            mapping=aes(
                "x",
                "y",
                label="label",
                label_colour="label_colour",
                fill="fill",
                label_size="label_size",
                angle="angle",
            ),
            label_margin=unit([0.25] * 4, "in"),
            hjust=0,
            vjust=0.5,
        )
        + xlim(0, 1)
        + ylim(0, 1)
        # R: scale_discrete_identity(aesthetics = c("orientation",
        #    "label.colour", "fill")); plotnine passes unscaled aesthetics
        #    (label_colour) through as is.
        + scale_fill_identity()
    )

    assert p == "rotated_labels_w_colors"


# roxygen @examples ------------------------------------------------------------

example_df = pd.DataFrame(
    {
        "label": [
            "Some text **in bold.**",
            "Linebreaks<br>Linebreaks<br>Linebreaks",
            "*x*<sup>2</sup> + 5*x* + *C*<sub>*i*</sub>",
            "Some <span style='color:blue'>blue text **in bold.**</span><br>"
            "And *italics text.*<br>\n"
            "      And some <span style='font-size:18pt; color:black'>"
            "large</span> text.",
        ],
        "x": [0.2, 0.1, 0.5, 0.9],
        "y": [0.8, 0.4, 0.1, 0.5],
        "hjust": [0.5, 0, 0, 1],
        "vjust": [0.5, 1, 0, 0.5],
        "angle": [0, 0, 45, -45],
        "color": ["black", "blue", "black", "red"],
        "fill": ["cornsilk", "white", "lightblue", "white"],
    }
)


def test_example_markup():
    p = (
        ggplot(example_df)
        + aes(
            "x",
            "y",
            label="label",
            angle="angle",
            color="color",
            fill="fill",
            hjust="hjust",
            vjust="vjust",
        )
        + geom_richtext()
        + geom_point(color="black", fill="black", size=2)
        + scale_color_identity()
        + scale_fill_identity()
        + xlim(0, 1)
        + ylim(0, 1)
    )
    assert p == "example_markup"


def test_example_no_frame():
    p = (
        ggplot(example_df)
        + aes(
            "x",
            "y",
            label="label",
            angle="angle",
            color="color",
            hjust="hjust",
            vjust="vjust",
        )
        + geom_richtext(
            fill="none",
            label_color="none",  # R: label.color = NA
            label_padding=unit([0] * 4, "pt"),
        )
        + geom_point(color="black", fill="black", size=2)
        + scale_color_identity()
        + xlim(0, 1)
        + ylim(0, 1)
    )
    assert p == "example_no_frame"


# additional behaviour ---------------------------------------------------------


def test_text_color_alpha_and_named_just():
    df = pd.DataFrame(
        {
            "x": [1, 2, 3],
            "y": [1, 2, 3],
            "label": ["*left* / bottom", "**center**", "right / top"],
            "hjust": ["left", "center", "right"],
            "vjust": ["bottom", "middle", "top"],
        }
    )
    p = (
        ggplot(df, aes("x", "y", label="label", hjust="hjust", vjust="vjust"))
        + geom_richtext(
            color="darkblue", text_color="firebrick", alpha=0.6, size=14
        )
        + geom_point()
    )
    assert p == "text_color_alpha_and_named_just"


def test_inward_outward_and_nudge():
    df = pd.DataFrame(
        {
            "x": [0, 0.5, 1, 0, 0.5, 1],
            "y": [1, 1, 1, 0, 0, 0],
            "label": ["in<sub>0</sub>", "in", "in<sup>1</sup>", "out", "out", "out"],
            "just": ["inward"] * 3 + ["outward"] * 3,
        }
    )
    p = (
        ggplot(df, aes("x", "y", label="label", hjust="just", vjust="just"))
        + geom_point()
        + geom_richtext(nudge_y=0.05)
        + xlim(-0.25, 1.25)
        + ylim(-0.25, 1.25)
    )
    assert p == "inward_outward_and_nudge"


def test_facets_and_legend():
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 1, 2, 3],
            "y": [1, 2, 1, 2, 1, 2],
            "g": ["a", "a", "a", "b", "b", "b"],
            "label": [f"**{i}**<sup>{i}</sup>" for i in range(6)],
        }
    )
    p = (
        ggplot(df, aes("x", "y", label="label", color="g"))
        + geom_richtext()
        + facet_wrap("g")
    )
    assert p == "facets_and_legend"


def test_nudge_and_position_conflict():
    with pytest.raises(PlotnineError):
        geom_richtext(nudge_x=1, position=position_nudge(1))


def test_unsupported_tag_raises():
    df = pd.DataFrame({"x": [1], "y": [1], "label": ["<table></table>"]})
    p = ggplot(df, aes("x", "y", label="label")) + geom_richtext()
    with pytest.raises(ValueError, match="isn't supported"):
        p.draw_test()  # pyright: ignore
