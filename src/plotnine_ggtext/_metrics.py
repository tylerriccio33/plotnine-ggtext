"""
Device-independent text metrics, in points

gridtext measures text with grid, which reports (per font):

- ascent: a *font-level* value (the same for every string),
- descent: the descent of the string ``"gjpqyQ"``,
- width: the advance width of the string.

We reproduce this with matplotlib's unhinted outline metrics
([](`~matplotlib.textpath.TextToPath`)) so the layout does not depend on
the output DPI or on pixel hinting.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath

if TYPE_CHECKING:
    from ._markup import Style

_t2p = TextToPath()


def font_properties(style: Style) -> FontProperties:
    return FontProperties(
        family=style.family or None,
        size=style.fontsize,
        weight=style.weight,
        style=style.style,
    )


def _key(style: Style):
    # The resolved default family depends on rcParams (plotnine themes set
    # them), so it is part of the cache key.
    import matplotlib as mpl

    family = style.family or tuple(mpl.rcParams["font.family"])
    sans = tuple(mpl.rcParams["font.sans-serif"])
    return (family, sans, style.fontsize, style.weight, style.style)


@lru_cache(maxsize=4096)
def _width(text: str, key) -> float:
    fam, _, size, weight, fstyle = key
    prop = FontProperties(
        family=list(fam) if isinstance(fam, tuple) else fam,
        size=size,
        weight=weight,
        style=fstyle,
    )
    w, _, _ = _t2p.get_text_width_height_descent(text, prop, ismath=False)
    return w


@lru_cache(maxsize=512)
def _font_info(key) -> tuple[float, float, float]:
    fam, _, size, weight, fstyle = key
    prop = FontProperties(
        family=list(fam) if isinstance(fam, tuple) else fam,
        size=size,
        weight=weight,
        style=fstyle,
    )
    # ascent: height of a capital letter, like grid's font-level ascent
    h, d = _t2p.get_text_width_height_descent("M", prop, ismath=False)[1:]
    ascent = h - d
    _, h2, descent = _t2p.get_text_width_height_descent(
        "gjpqyQ", prop, ismath=False
    )
    space = _t2p.get_text_width_height_descent(" ", prop, ismath=False)[0]
    return ascent, descent, space


def text_width(text: str, style: Style) -> float:
    if not text:
        return 0.0
    return _width(text, _key(style))


def font_ascent(style: Style) -> float:
    return _font_info(_key(style))[0]


def font_descent(style: Style) -> float:
    return _font_info(_key(style))[1]


def space_width(style: Style) -> float:
    return _font_info(_key(style))[2]
