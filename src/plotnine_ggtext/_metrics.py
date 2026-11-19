"""
Device-independent text metrics, in points

gridtext measures text with grid, which reports (per font):

- ascent: a *font-level* value (the same for every string),
- descent: the descent of the string ``"gjpqyQ"``,
- width: the advance width of the string.

Vertical metrics use matplotlib's unhinted outline metrics
([](`~matplotlib.textpath.TextToPath`)). At draw time, horizontal advances
are measured with the active renderer, so word spacing matches what the
backend draws (Agg hints glyphs); outside a draw, outline metrics are used.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath

if TYPE_CHECKING:
    from ._markup import Style

_t2p = TextToPath()

# When set, horizontal advances are measured with this renderer so that the
# layout matches what the backend actually draws (e.g. hinted glyphs in Agg).
_renderer: ContextVar[Any] = ContextVar("_renderer", default=None)
_renderer_cache: dict[tuple, float] = {}


@contextmanager
def measure_with(renderer):
    """Measure text widths with `renderer` inside this context"""
    token = _renderer.set(renderer)
    try:
        yield
    finally:
        _renderer.reset(token)
        _renderer_cache.clear()


def _renderer_width(renderer, text: str, style: Style) -> float:
    key = (id(renderer), text, _key(style))
    w = _renderer_cache.get(key)
    if w is None:
        w_px, _, _ = renderer.get_text_width_height_descent(
            text, font_properties(style), ismath=False
        )
        w = w_px * 72 / renderer.points_to_pixels(72)
        _renderer_cache[key] = w
    return w


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
    renderer = _renderer.get()
    if renderer is not None:
        return _renderer_width(renderer, text, style)
    return _width(text, _key(style))


def font_ascent(style: Style) -> float:
    return _font_info(_key(style))[0]


def font_descent(style: Style) -> float:
    return _font_info(_key(style))[1]


def space_width(style: Style) -> float:
    renderer = _renderer.get()
    if renderer is not None:
        # Agg reports zero width for a lone space; measure it in context
        a = _renderer_width(renderer, "M M", style)
        b = _renderer_width(renderer, "MM", style)
        return a - b
    return _font_info(_key(style))[2]
