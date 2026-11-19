"""
Box layout, a port of gridtext's C++ layout engine

All lengths are in points. The coordinate system has y pointing up.
The result of a layout is a set of drawing primitives positioned relative
to the lower-left corner of the outer box (margins included); the caller
then places that box relative to the anchor point using `hjust`/`vjust`
and rotates it around the anchor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._markup import Break, Glue, Paragraph, Style, TextBox
from ._metrics import font_ascent, font_descent, space_width, text_width

INF = float("inf")


@dataclass
class PlacedText:
    x: float
    y: float  # baseline
    text: str
    style: Style


@dataclass
class Layout:
    """Result of laying out a rich text box"""

    width: float  # outer width, including margins
    height: float  # outer height, including margins
    # Rectangle drawn for the box (x, y, width, height), margins excluded
    rect: tuple[float, float, float, float]
    texts: list[PlacedText] = field(default_factory=list)


# --- measuring ---------------------------------------------------------------


def _node_width(n) -> float:
    if isinstance(n, TextBox):
        return text_width(n.text, n.style)
    if isinstance(n, Glue):
        return space_width(n.style)
    return 0.0


def _ascent(n) -> float:
    return font_ascent(n.style) if isinstance(n, TextBox) else 0.0


def _descent(n) -> float:
    return font_descent(n.style) if isinstance(n, TextBox) else 0.0


def _voff(n) -> float:
    return n.voff if isinstance(n, TextBox) else 0.0


# --- line breaking -----------------------------------------------------------


def break_lines(
    nodes: list, line_length: float, word_wrap: bool
) -> list[tuple[int, int, float]]:
    """
    Naive (first-fit) line breaking, as gridtext's `LineBreaker`

    Returns
    -------
    :
        List of (start, end, width) with `end` exclusive.
    """
    m = len(nodes)
    widths = [_node_width(n) for n in nodes]
    cum = [0.0] * (m + 1)
    for i in range(m):
        cum[i + 1] = cum[i] + widths[i]

    def measure(a, b):
        return cum[min(b, m)] - cum[min(a, m)]

    def is_forced(i):
        return i >= m or isinstance(nodes[i], Break)

    def is_feasible(i):
        if not word_wrap:
            return is_forced(i)
        if i >= m:
            return True
        n = nodes[i]
        if isinstance(n, Break):
            return True
        return i > 0 and isinstance(n, Glue) and isinstance(nodes[i - 1], TextBox)

    def removable(i):
        return i < m and isinstance(nodes[i], Glue)

    def next_start(i):
        while i < m and removable(i):
            i += 1
        return i

    def next_feasible(i):
        while i < m and not is_feasible(i):
            i += 1
        return i

    lines = []
    a = 0
    while a < m:
        a = next_start(a)
        b = next_feasible(a)
        width = measure(a, b)
        while b < m and not is_forced(b):
            b_new = next_feasible(b + 1)
            delta = measure(b, b_new)
            if width + delta < line_length:
                width += delta
                b = b_new
            else:
                break
        if a < m:
            lines.append((a, b, width))
            if is_forced(b):
                b += 1
            a = b
        else:
            break
    return lines


# --- boxes -------------------------------------------------------------------


@dataclass
class _ParLayout:
    width: float
    ascent: float
    descent: float
    # nodes placed relative to the baseline of the *last* line
    placed: list[tuple[float, float, TextBox]]


def layout_paragraph(par: Paragraph, width_hint: float | None) -> _ParLayout:
    """
    Lay out a paragraph (gridtext `ParBox`)

    Parameters
    ----------
    width_hint :
        Available width. `None` means "native" policy: no word wrapping
        and the width is that of the longest line.
    """
    nodes = par.nodes
    word_wrap = width_hint is not None
    lines = break_lines(nodes, width_hint if word_wrap else INF, word_wrap)

    if not word_wrap:
        width = max((w for _, _, w in lines), default=0.0)
    else:
        width = width_hint  # type: ignore[assignment]

    placed: list[tuple[float, float, TextBox]] = []
    y_off = 0.0
    first_ascent = 0.0
    descent = 0.0
    for k, (a, b, lw) in enumerate(lines):
        x_off = par.halign * (width - lw)
        ascent = max((_ascent(n) + _voff(n) for n in nodes[a:b]), default=0.0)
        if k == 0:
            first_ascent = ascent
        elif ascent + descent > par.linespacing:
            y_off -= ascent + descent
        else:
            y_off -= par.linespacing

        descent = 0.0
        for n in nodes[a:b]:
            if isinstance(n, TextBox) and n.text:
                placed.append((x_off, y_off, n))
            x_off += _node_width(n)
            descent = max(descent, _descent(n) - _voff(n))

    if not lines:
        return _ParLayout(width, 0.0, 0.0, [])

    # shift so that coordinates are relative to the last baseline
    shift = -y_off
    placed = [(x, y + shift, n) for x, y, n in placed]
    return _ParLayout(width, first_ascent - y_off, descent, placed)


@dataclass
class _VBoxLayout:
    width: float
    height: float
    # (x, baseline y) relative to the lower-left corner of the vbox
    placed: list[tuple[float, float, TextBox]]


def layout_vbox(pars: list[Paragraph], width_hint: float | None) -> _VBoxLayout:
    """Stack paragraphs vertically (gridtext `VBox`, hjust = vjust = 0)"""
    laid = [layout_paragraph(p, width_hint) for p in pars]
    y_off = 0.0
    rows = []
    for pl in laid:
        y_off -= pl.ascent
        rows.append((y_off, pl))
        y_off -= pl.descent
    height = -y_off
    if width_hint is None:
        width = max((pl.width for pl in laid), default=0.0)
    else:
        width = width_hint

    placed = []
    for base, pl in rows:
        for x, y, n in pl.placed:
            placed.append((x, height + base + y + n.voff, n))
    return _VBoxLayout(width, height, placed)


def layout_rect_box(
    pars: list[Paragraph],
    margin: tuple[float, float, float, float],
    padding: tuple[float, float, float, float],
    *,
    width: float | None = None,
    height: float | None = None,
    wrap: bool = False,
    content_hjust: float = 0.0,
    content_vjust: float = 1.0,
) -> Layout:
    """
    Lay out content inside a box with padding and margins (gridtext `RectBox`)

    Parameters
    ----------
    margin, padding :
        (top, right, bottom, left) in points
    width, height :
        Outer size including margins. `None` means native (fit content).
    wrap :
        Whether the content is word-wrapped to the available width
        (requires `width`).
    """
    mt, mr, mb, ml = margin
    pt, pr, pb, pl = padding
    hextra = ml + mr + pl + pr
    vextra = mt + mb + pt + pb

    if width is not None and wrap:
        content = layout_vbox(pars, width - hextra)
    else:
        content = layout_vbox(pars, None)

    W = width if width is not None else content.width + hextra
    H = height if height is not None else content.height + vextra

    x_align = content_hjust * (W - hextra - content.width)
    y_align = content_vjust * (H - vextra - content.height)

    rx, ry = ml, mb
    rect = (rx, ry, W - ml - mr, H - mt - mb)
    cx = rx + pl + x_align
    cy = ry + pb + y_align
    texts = [PlacedText(cx + x, cy + y, n.text, n.style) for x, y, n in content.placed]
    return Layout(W, H, rect, texts)
