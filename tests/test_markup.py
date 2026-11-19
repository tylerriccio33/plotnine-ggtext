import math

import pytest

from plotnine_ggtext._markup import (
    Break,
    Glue,
    Style,
    TextBox,
    convert_css_unit_pt,
    parse,
    parse_css,
)
from plotnine_ggtext._metrics import font_ascent

S = Style(fontsize=12, family="DejaVu Sans")


def texts(par):
    return [n for n in par.nodes if isinstance(n, TextBox)]


def words(par):
    return [n.text for n in texts(par) if n.text]


def kinds(par):
    return [
        "T:" + n.text if isinstance(n, TextBox) else type(n).__name__[0]
        for n in par.nodes
    ]


def test_plain_text_single_paragraph():
    pars = parse("hello world", S)
    assert len(pars) == 1
    assert kinds(pars[0]) == ["T:hello", "G", "T:world", "T:", "B"]
    assert pars[0].linespacing == pytest.approx(12 * 1.2)


def test_paragraph_termination():
    par = parse("hello", S)[0]
    assert isinstance(par.nodes[-1], Break)
    assert isinstance(par.nodes[-2], TextBox) and par.nodes[-2].text == ""


def test_multiple_paragraphs():
    pars = parse("one\n\ntwo", S)
    assert len(pars) == 2
    assert words(pars[0]) == ["one"]
    assert words(pars[1]) == ["two"]


def test_halign_propagates():
    assert parse("x", S, halign=0.5)[0].halign == 0.5


@pytest.mark.parametrize("md", ["**b**", "<b>b</b>", "<strong>b</strong>"])
def test_bold(md):
    t = [n for n in texts(parse(md, S)[0]) if n.text][0]
    assert t.style.weight == "bold"
    assert t.style.style == "normal"


@pytest.mark.parametrize("md", ["*i*", "<i>i</i>", "<em>i</em>"])
def test_italic(md):
    t = [n for n in texts(parse(md, S)[0]) if n.text][0]
    assert t.style.style == "italic"
    assert t.style.weight == "normal"


def test_nested_bold_italic():
    t = [n for n in texts(parse("***x***", S)[0]) if n.text][0]
    assert t.style.weight == "bold" and t.style.style == "italic"
    t = [n for n in texts(parse("<b><i>x</i></b>", S)[0]) if n.text][0]
    assert t.style.weight == "bold" and t.style.style == "italic"


def test_style_restored_after_tag():
    ts = [n for n in texts(parse("a <b>b</b> c", S)[0]) if n.text]
    assert [t.style.weight for t in ts] == ["normal", "bold", "normal"]


def test_br_produces_empty_textbox_and_break():
    par = parse("a<br>b", S)[0]
    assert kinds(par)[:4] == ["T:a", "T:", "B", "T:b"]


def test_br_self_closing():
    par = parse("a<br/>b", S)[0]
    assert any(isinstance(n, Break) for n in par.nodes[:-1])
    assert words(par) == ["a", "b"]


def test_leading_and_trailing_space_glue():
    par = parse("<b>a</b> <i>b</i>", S)[0]
    assert kinds(par)[:3] == ["T:a", "G", "T:b"]


def test_trailing_space_inside_tag_gives_glue():
    par = parse("<b>a </b>b", S)[0]
    assert kinds(par)[:3] == ["T:a", "G", "T:b"]


def test_leading_space_inside_tag_gives_glue():
    par = parse("a<b> b</b>", S)[0]
    assert kinds(par)[:3] == ["T:a", "G", "T:b"]


def test_no_glue_across_tags_without_space():
    par = parse("5<em>x</em>", S)[0]
    assert kinds(par)[:2] == ["T:5", "T:x"]
    assert not any(isinstance(n, Glue) for n in par.nodes)


def test_multiple_spaces_collapse():
    par = parse("a    b", S)[0]
    assert kinds(par)[:3] == ["T:a", "G", "T:b"]


def test_span_color_font_family_size():
    html = '<span style="color:red; font-family: Courier; font-size:20pt">x</span>'
    t = [n for n in texts(parse(html, S)[0]) if n.text][0]
    assert t.style.color == "red"
    assert t.style.family == "Courier"
    assert t.style.fontsize == pytest.approx(20)


def test_span_font_family_quotes_stripped():
    html = "<span style=\"font-family: 'Courier New'\">x</span>"
    t = [n for n in texts(parse(html, S)[0]) if n.text][0]
    assert t.style.family == "Courier New"


@pytest.mark.parametrize(
    "size, expected",
    [
        ("12px", 9.0),
        ("1in", 72.0),
        ("2.54cm", 72.0),
        ("25.4mm", 72.0),
        ("10pt", 10.0),
        ("10", 10.0),
    ],
)
def test_css_unit_conversion(size, expected):
    assert convert_css_unit_pt(size) == pytest.approx(expected)
    html = f'<span style="font-size:{size}">x</span>'
    t = [n for n in texts(parse(html, S)[0]) if n.text][0]
    assert t.style.fontsize == pytest.approx(expected)


def test_css_unit_bad():
    with pytest.raises(ValueError):
        convert_css_unit_pt("3em")
    with pytest.raises(ValueError):
        convert_css_unit_pt("abc")


def test_parse_css():
    assert parse_css("Color: red; font-size : 3pt;") == {
        "color": "red",
        "font-size": "3pt",
    }
    assert parse_css(None) == {}


def test_sup_size_and_offset():
    ts = [n for n in texts(parse("x<sup>2</sup>", S)[0]) if n.text]
    base, sup = ts
    assert sup.style.fontsize == pytest.approx(0.8 * 12)
    assert base.voff == 0
    expected = font_ascent(sup.style) / 2
    assert sup.voff == pytest.approx(expected)
    assert sup.voff > 0


def test_sub_size_and_offset():
    sub = [n for n in texts(parse("x<sub>2</sub>", S)[0]) if n.text][1]
    assert sub.style.fontsize == pytest.approx(0.8 * 12)
    assert sub.voff == pytest.approx(-font_ascent(sub.style) / 2)


def test_style_override_inside_sup():
    html = '<sup style="font-size:20pt">2</sup>'
    sup = [n for n in texts(parse(html, S)[0]) if n.text][0]
    assert sup.style.fontsize == pytest.approx(20)
    assert sup.voff == pytest.approx(font_ascent(sup.style) / 2)


def test_nested_sup_shrinks_and_accumulates():
    ts = [n for n in texts(parse("<sup>a<sup>b</sup></sup>", S)[0]) if n.text]
    assert ts[1].style.fontsize == pytest.approx(0.64 * 12)
    assert ts[1].voff > ts[0].voff > 0


@pytest.mark.parametrize("md", ["<h1>Title</h1>", "# Title", "<div>x</div>"])
def test_unsupported_tag_raises(md):
    with pytest.raises(ValueError, match="isn't supported"):
        parse(md, S)


@pytest.mark.parametrize("label", [None, float("nan"), ""])
def test_missing_label_no_content(label):
    pars = parse(label, S)
    assert all(not words(p) for p in pars)


def test_html_entities():
    par = parse("a &amp; b &lt; c", S)[0]
    assert words(par) == ["a", "&", "b", "<", "c"]


def test_use_markdown_false():
    par = parse("**a**", S, use_markdown=False)[0]
    assert words(par) == ["**a**"]


def test_html_no_markdown_loose_inline():
    pars = parse("a <b>b</b>", S, use_markdown=False)
    assert len(pars) == 1
    assert words(pars[0]) == ["a", "b"]
