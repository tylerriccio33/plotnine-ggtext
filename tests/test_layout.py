import numpy as np
import pytest
from plotnine.exceptions import PlotnineError

from plotnine_ggtext._geom_base import compute_just
from plotnine_ggtext._layout import (
    INF,
    break_lines,
    layout_paragraph,
    layout_rect_box,
    layout_vbox,
)
from plotnine_ggtext._markup import Break, Glue, Paragraph, Style, TextBox, parse
from plotnine_ggtext._metrics import font_ascent, font_descent, space_width, text_width

S = Style(fontsize=12, family="DejaVu Sans")


def T(s):
    return TextBox(s, S)


def G():
    return Glue(S)


def w(s):
    return text_width(s, S)


def par(md, halign=0.0):
    return parse(md, S, halign=halign)[0]


# --- break_lines -------------------------------------------------------------


def test_no_wrap_single_line():
    nodes = [T("aa"), G(), T("bb")]
    lines = break_lines(nodes, INF, True)
    assert len(lines) == 1
    assert lines[0][:2] == (0, 3)
    assert lines[0][2] == pytest.approx(w("aa") + space_width(S) + w("bb"))


def test_forced_break():
    nodes = [T("aa"), T(""), Break(), T("bb")]
    lines = break_lines(nodes, INF, True)
    assert [(a, b) for a, b, _ in lines] == [(0, 2), (3, 4)]
    assert lines[0][2] == pytest.approx(w("aa"))


def test_consecutive_forced_breaks_give_empty_line():
    nodes = [T("a"), Break(), Break(), T("b")]
    lines = break_lines(nodes, INF, True)
    assert len(lines) == 3
    assert lines[1][2] == 0


def test_wraps_at_glue():
    nodes = [T("aaaa"), G(), T("bbbb"), G(), T("cccc")]
    two = w("aaaa") + space_width(S) + w("bbbb")
    lines = break_lines(nodes, two + 1, True)
    assert [(a, b) for a, b, _ in lines] == [(0, 3), (4, 5)]
    assert lines[0][2] == pytest.approx(two)


def test_narrow_width_one_word_per_line():
    nodes = [T("aaaa"), G(), T("bbbb"), G(), T("cccc")]
    lines = break_lines(nodes, 1, True)
    assert [(a, b) for a, b, _ in lines] == [(0, 1), (2, 3), (4, 5)]


def test_no_wrap_when_word_wrap_false():
    nodes = [T("aaaa"), G(), T("bbbb"), G(), T("cccc")]
    lines = break_lines(nodes, 1, False)
    assert len(lines) == 1
    assert lines[0][:2] == (0, 5)


def test_no_wrap_still_honours_forced_breaks():
    nodes = [T("a"), G(), T("b"), Break(), T("c")]
    lines = break_lines(nodes, 1, False)
    assert [(a, b) for a, b, _ in lines] == [(0, 3), (4, 5)]


def test_leading_glue_skipped():
    nodes = [G(), G(), T("aa")]
    lines = break_lines(nodes, INF, True)
    assert [(a, b) for a, b, _ in lines] == [(2, 3)]
    assert lines[0][2] == pytest.approx(w("aa"))


def test_glue_after_wrap_skipped():
    nodes = [T("aaaa"), G(), T("bbbb")]
    lines = break_lines(nodes, 1, True)
    assert lines[1][0] == 2


def test_empty_nodes():
    assert break_lines([], INF, True) == []


def test_no_glue_between_tags_is_not_breakable():
    nodes = [T("5"), T("x"), G(), T("y")]
    lines = break_lines(nodes, 1, True)
    assert [(a, b) for a, b, _ in lines] == [(0, 2), (3, 4)]


# --- layout_paragraph --------------------------------------------------------


def _xs(pl):
    return {n.text: x for x, _, n in pl.placed}


def _ys(pl):
    return {n.text: y for _, y, n in pl.placed}


def test_native_paragraph_width_is_longest_line():
    p = par("aaaa bbbb<br>cc")
    pl = layout_paragraph(p, None)
    assert pl.width == pytest.approx(w("aaaa") + space_width(S) + w("bbbb"))


@pytest.mark.parametrize("halign", [0.0, 0.5, 1.0])
def test_halign_offsets(halign):
    p = par("aaaa bbbb<br>cc", halign=halign)
    W = 300
    pl = layout_paragraph(p, W)
    xs = _xs(pl)
    assert xs["aaaa"] == pytest.approx(
        halign * (W - (w("aaaa") + space_width(S) + w("bbbb")))
    )
    assert xs["cc"] == pytest.approx(halign * (W - w("cc")))


def test_wrapped_paragraph_width_is_hint():
    pl = layout_paragraph(par("aaaa bbbb"), 500)
    assert pl.width == 500


def test_linespacing_between_lines():
    p = par("aaa<br>bbb")
    pl = layout_paragraph(p, None)
    ys = _ys(pl)
    assert ys["aaa"] - ys["bbb"] == pytest.approx(12 * 1.2)
    assert ys["bbb"] == pytest.approx(0)  # relative to last baseline


def test_linespacing_with_wrapping():
    p = par("aaaa bbbb cccc")
    pl = layout_paragraph(p, w("aaaa") + 1)
    ys = sorted(_ys(pl).values(), reverse=True)
    assert len(ys) == 3
    assert ys[0] - ys[1] == pytest.approx(12 * 1.2)
    assert ys[1] - ys[2] == pytest.approx(12 * 1.2)


def test_big_font_line_exceeds_linespacing():
    p = par('a<br><span style="font-size:40pt">B</span>')
    pl = layout_paragraph(p, None)
    ys = _ys(pl)
    big = Style(fontsize=40, family="DejaVu Sans")
    expected = font_ascent(big) + font_descent(S)
    assert expected > 12 * 1.2
    assert ys["a"] - ys["B"] == pytest.approx(expected)


def test_paragraph_ascent_descent():
    pl = layout_paragraph(par("aaa"), None)
    assert pl.ascent == pytest.approx(font_ascent(S))
    assert pl.descent == pytest.approx(font_descent(S))


def test_empty_paragraph():
    pl = layout_paragraph(Paragraph(), None)
    assert pl.placed == [] and pl.ascent == 0 and pl.descent == 0


def test_sup_raises_ascent():
    plain = layout_paragraph(par("x"), None)
    sup = layout_paragraph(par("x<sup>2</sup>"), None)
    assert sup.ascent > plain.ascent


# --- layout_vbox -------------------------------------------------------------


def test_vbox_height_single_line():
    v = layout_vbox([par("aaa")], None)
    assert v.height == pytest.approx(font_ascent(S) + font_descent(S))
    assert v.width == pytest.approx(w("aaa"))
    (x, y, n), = v.placed
    assert y == pytest.approx(font_descent(S))


def test_vbox_stacks_paragraphs():
    pars = parse("aaa\n\nbbb", S)
    v = layout_vbox(pars, None)
    ys = {n.text: y for _, y, n in v.placed}
    assert ys["aaa"] > ys["bbb"]
    one = font_ascent(S) + font_descent(S)
    assert v.height > one


# --- layout_rect_box ---------------------------------------------------------

M = (1.0, 2.0, 3.0, 4.0)
P = (5.0, 6.0, 7.0, 8.0)
Z = (0.0, 0.0, 0.0, 0.0)


def test_native_size_is_content_padding_margin():
    pars = [par("hello world")]
    content = layout_vbox(pars, None)
    lay = layout_rect_box(pars, M, P)
    assert lay.width == pytest.approx(content.width + 4 + 2 + 8 + 6)
    assert lay.height == pytest.approx(content.height + 1 + 3 + 5 + 7)


def test_rect_excludes_margins():
    lay = layout_rect_box([par("hello")], M, P)
    x, y, rw, rh = lay.rect
    assert x == M[3] and y == M[2]
    assert rw == pytest.approx(lay.width - M[1] - M[3])
    assert rh == pytest.approx(lay.height - M[0] - M[2])


def test_text_position_default_top_left():
    pars = [par("hello")]
    content = layout_vbox(pars, None)
    lay = layout_rect_box(pars, M, P)
    (t,) = lay.texts
    assert t.x == pytest.approx(M[3] + P[3])
    assert t.y == pytest.approx(M[2] + P[2] + content.placed[0][1])


def test_r_passed_through():
    assert layout_rect_box([par("a")], Z, Z, r=7.5).r == 7.5
    assert layout_rect_box([par("a")], Z, Z).r == 0.0


def test_fixed_width_wraps():
    pars = [par("aaaa bbbb cccc dddd")]
    native = layout_rect_box(pars, Z, Z)
    lay = layout_rect_box(pars, Z, Z, width=w("aaaa") + 5, wrap=True)
    assert lay.width == pytest.approx(w("aaaa") + 5)
    assert len(set(round(t.y, 6) for t in lay.texts)) == 4
    assert lay.height > native.height
    assert len(set(round(t.y, 6) for t in native.texts)) == 1


def test_fixed_width_wrap_accounts_for_padding_and_margin():
    pars = [par("aaaa bbbb")]
    both = w("aaaa") + space_width(S) + w("bbbb")
    # exactly enough content room -> still wraps (strict <), more room -> not
    pad = (0, 10, 0, 10)
    roomy = layout_rect_box(pars, Z, pad, width=both + 20 + 5, wrap=True)
    tight = layout_rect_box(pars, Z, pad, width=w("aaaa") + 20 + 1, wrap=True)
    assert len({round(t.y, 6) for t in roomy.texts}) == 1
    assert len({round(t.y, 6) for t in tight.texts}) == 2


def test_fixed_width_without_wrap_keeps_single_line():
    lay = layout_rect_box([par("aaaa bbbb")], Z, Z, width=5, wrap=False)
    assert lay.width == 5
    assert len({round(t.y, 6) for t in lay.texts}) == 1


def test_fixed_height_vjust_placement():
    pars = [par("hello")]
    native = layout_rect_box(pars, Z, Z)
    H = native.height + 50
    ys = {}
    for vj in (0.0, 0.5, 1.0):
        lay = layout_rect_box(pars, Z, Z, height=H, content_vjust=vj)
        assert lay.height == H
        ys[vj] = lay.texts[0].y
    base = native.texts[0].y
    assert ys[0.0] == pytest.approx(base)
    assert ys[0.5] == pytest.approx(base + 25)
    assert ys[1.0] == pytest.approx(base + 50)


def test_fixed_height_vjust_with_padding():
    pars = [par("hello")]
    native = layout_rect_box(pars, M, P)
    lay = layout_rect_box(pars, M, P, height=native.height + 20, content_vjust=1.0)
    assert lay.texts[0].y == pytest.approx(native.texts[0].y + 20)
    lay = layout_rect_box(pars, M, P, height=native.height + 20, content_vjust=0.0)
    assert lay.texts[0].y == pytest.approx(native.texts[0].y)


def test_content_hjust_placement():
    pars = [par("hello")]
    native = layout_rect_box(pars, Z, Z)
    lay = layout_rect_box(pars, Z, Z, width=native.width + 40, content_hjust=0.5)
    assert lay.texts[0].x == pytest.approx(native.texts[0].x + 20)


def test_multiple_lines_in_box_spacing():
    lay = layout_rect_box([par("a<br>b")], Z, Z)
    ya = [t for t in lay.texts if t.text == "a"][0].y
    yb = [t for t in lay.texts if t.text == "b"][0].y
    assert ya - yb == pytest.approx(14.4)


def test_empty_content_box():
    lay = layout_rect_box(parse(None, S), M, P)
    assert lay.texts == []
    assert lay.width == pytest.approx(sum(M[1::2]) + sum(P[1::2]))


# --- compute_just ------------------------------------------------------------


def test_compute_just_numbers():
    out = compute_just(0.3, np.array([0.1, 0.9]))
    assert out == pytest.approx([0.3, 0.3])
    out = compute_just([0.0, 1.0], np.array([0.5, 0.5]))
    assert out == pytest.approx([0.0, 1.0])


@pytest.mark.parametrize(
    "name, val",
    [("left", 0), ("center", 0.5), ("centre", 0.5), ("right", 1),
     ("bottom", 0), ("middle", 0.5), ("top", 1)],
)
def test_compute_just_named(name, val):
    assert compute_just(name, np.array([0.2]))[0] == val


def test_compute_just_inward():
    out = compute_just("inward", np.array([0.1, 0.5, 0.9]))
    assert out == pytest.approx([0, 0.5, 1])


def test_compute_just_outward():
    out = compute_just("outward", np.array([0.1, 0.5, 0.9]))
    assert out == pytest.approx([1, 0.5, 0])


def test_compute_just_inward_tolerance():
    out = compute_just("inward", np.array([0.5004]))
    assert out[0] == 0.5


def test_compute_just_unknown_raises():
    with pytest.raises(PlotnineError):
        compute_just("sideways", np.array([0.5]))
