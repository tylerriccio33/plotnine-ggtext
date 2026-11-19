"""
Tests for geom_textbox

`test_rotated_boxes_w_colors_and_alignments` is a one-to-one port of
ggtext's tests/testthat/test-geom-textbox.R
("Rotated boxes w/ colors and alignments").
The R rendering lives in tests/reference_r/ for side-by-side comparison.
"""

import pandas as pd
import pytest
from plotnine import (
    aes,
    geom_point,
    ggplot,
    scale_color_identity,
    scale_fill_identity,
    xlim,
    ylim,
)
from plotnine.exceptions import PlotnineError

from plotnine_ggtext import geom_textbox, unit

# ggtext: test-geom-textbox.R --------------------------------------------------


def test_rotated_boxes_w_colors_and_alignments():
    df = pd.DataFrame(
        {
            "x": 0.5,
            "y": 0.5,
            "label": "The quick brown fox **jumps over** the *lazy* dog.",
            "orientation": [
                "upright",
                "left-rotated",
                "inverted",
                "right-rotated",
            ],
            "box_colour": ["#858E4E", "#24988F", "#8C82B8", "#B97681"],
            "fill": ["#E6EBD1", "#CDEFE9", "#E8E6FC", "#FEE1E5"],
            "halign": [0, 0.5, 1, 0.5],
            "valign": [1, 0.5, 0.5, 0],
            "box_size": [0.1, 0.25, 0.5, 1],
        }
    )

    p = (
        ggplot()
        + geom_textbox(
            data=df,
            mapping=aes(
                "x",
                "y",
                label="label",
                box_colour="box_colour",
                fill="fill",
                halign="halign",
                valign="valign",
                box_size="box_size",
                orientation="orientation",
            ),
            width=unit(1.5, "in"),
            height=unit(1.5, "in"),
            box_margin=unit([0.25] * 4, "in"),
            hjust=0,
            vjust=1,
        )
        + xlim(0, 1)
        + ylim(0, 1)
        # R: scale_discrete_identity(aesthetics = c("orientation",
        #    "box.colour", "fill"))
        + scale_fill_identity()
    )

    assert p == "rotated_boxes_w_colors_and_alignments"


# roxygen @examples ------------------------------------------------------------


def test_example_npc_width():
    label = (
        "Lorem ipsum dolor **sit amet,** consectetur adipiscing elit,\n"
        "    sed do *eiusmod tempor incididunt* ut labore et dolore magna\n"
        "    aliqua."
    )
    df = pd.DataFrame(
        {
            "label": [label, label],
            "x": [0, 0.6],
            "y": [1, 0.6],
            "hjust": [0, 0],
            "vjust": [1, 0],
            "orientation": ["upright", "right-rotated"],
            "color": ["black", "blue"],
            "fill": ["cornsilk", "white"],
        }
    )
    p = (
        ggplot(df)
        + aes(
            "x",
            "y",
            label="label",
            color="color",
            fill="fill",
            hjust="hjust",
            vjust="vjust",
            orientation="orientation",
        )
        + geom_textbox(width=unit(0.4, "npc"))
        + geom_point(color="black", fill="black", size=2)
        + scale_color_identity()
        + scale_fill_identity()
        + xlim(0, 1)
        + ylim(0, 1)
    )
    assert p == "example_npc_width"


# additional behaviour ---------------------------------------------------------

lorem = (
    "Lorem ipsum dolor sit amet, *consectetur* adipiscing elit. "
    "<span style='color:#B97681'>Quisque tincidunt</span> eget arcu in "
    "**pulvinar**.<br>Morbi varius leo<sup>2</sup> vel consectetur."
)


def test_size_limits_and_paragraphs():
    df = pd.DataFrame(
        {
            "x": [0, 1, 0, 1],
            "y": [1, 1, 0, 0],
            "label": [lorem, lorem, "short", lorem + "\n\nA second paragraph."],
        }
    )
    p = (
        ggplot(df, aes("x", "y", label="label"))
        + geom_textbox(
            width=unit(0.6, "npc"),
            maxwidth=unit(2.5, "in"),
            minheight=unit(1, "in"),
            maxheight=unit(1.8, "in"),
            fill="#F0F7FF",
            box_color="#748696",
            box_r=unit(3, "pt"),
            valign=0.5,
        )
        + xlim(-0.5, 1.5)
        + ylim(-0.5, 1.5)
    )
    assert p == "size_limits_and_paragraphs"


def test_native_width_no_wrap():
    df = pd.DataFrame(
        {"x": [0.5], "y": [0.5], "label": ["No wrapping<br>with **width=None**"]}
    )
    p = (
        ggplot(df, aes("x", "y", label="label"))
        + geom_textbox(width=None, box_color="none", fill="lightyellow", size=16)
        + xlim(0, 1)
        + ylim(0, 1)
    )
    assert p == "native_width_no_wrap"


def test_bad_orientation():
    df = pd.DataFrame({"x": [1], "y": [1], "label": ["x"]})
    p = ggplot(df, aes("x", "y", label="label")) + geom_textbox(
        orientation="sideways"
    )
    with pytest.raises(PlotnineError, match="orientation"):
        p.draw_test()  # pyright: ignore
