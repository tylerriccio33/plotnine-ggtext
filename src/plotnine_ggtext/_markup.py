"""
Markdown / HTML parsing into a box list

This mirrors gridtext's `process_tags()`: text is first converted from
markdown to HTML, then the (very small) supported subset of HTML is walked
to produce a list of paragraphs. Each paragraph is a flat list of
text boxes, glue (inter-word spaces) and forced line breaks.

Supported tags (same as gridtext): ``<p>``, ``<b>``/``<strong>``,
``<i>``/``<em>``, ``<br>``, ``<span style="...">``, ``<sup>``, ``<sub>``.
Supported CSS properties: ``color``, ``font-size``, ``font-family``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from html.parser import HTMLParser

import markdown as _markdown

from ._metrics import font_ascent

__all__ = ("Style", "TextBox", "Glue", "Break", "Paragraph", "parse")


@dataclass(frozen=True)
class Style:
    """Font and colour state (the `gp` of a gridtext drawing context)"""

    fontsize: float = 11.0
    family: str | None = None
    weight: str = "normal"
    style: str = "normal"
    color: object = "black"
    lineheight: float = 1.2


@dataclass
class TextBox:
    text: str
    style: Style
    voff: float = 0.0  # vertical offset from baseline, pt


@dataclass
class Glue:
    style: Style


@dataclass
class Break:
    pass


Node = TextBox | Glue | Break


@dataclass
class Paragraph:
    nodes: list[Node] = field(default_factory=list)
    linespacing: float = 0.0  # pt
    halign: float = 0.0


@dataclass(frozen=True)
class _Context:
    style: Style
    yoff: float = 0.0
    halign: float = 0.0


_UNSUPPORTED_MSG = (
    "plotnine-ggtext has encountered a tag that isn't supported yet: <{}>\n"
    "Only a very limited number of tags are currently supported."
)

_INLINE_TAGS = {"b", "strong", "i", "em", "span", "sup", "sub"}
_SUPPORTED_TAGS = _INLINE_TAGS | {"p", "br"}


def parse_css(style: str | None) -> dict[str, str]:
    """Parse an inline CSS declaration list into a dict"""
    out: dict[str, str] = {}
    if not style:
        return out
    for decl in style.split(";"):
        if ":" not in decl:
            continue
        k, v = decl.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


_CSS_UNIT_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([a-z%]*)\s*$")
_CSS_TO_PT = {
    "pt": 1.0,
    "px": 72 / 96,
    "in": 72.0,
    "cm": 72 / 2.54,
    "mm": 72 / 25.4,
}


def convert_css_unit_pt(x: str) -> float:
    m = _CSS_UNIT_RE.match(x)
    if not m:
        raise ValueError(f"Cannot parse CSS length {x!r}")
    value, u = float(m.group(1)), m.group(2) or "pt"
    if u not in _CSS_TO_PT:
        raise ValueError(f"Cannot convert {value}{u} to pt.")
    return value * _CSS_TO_PT[u]


def _apply_css(ctx: _Context, style_attr: str | None) -> _Context:
    css = parse_css(style_attr)
    if not css:
        return ctx
    kw = {}
    if "color" in css:
        kw["color"] = css["color"]
    if "font-family" in css:
        kw["family"] = css["font-family"].strip("'\"")
    if "font-size" in css:
        kw["fontsize"] = convert_css_unit_pt(css["font-size"])
    return replace(ctx, style=replace(ctx.style, **kw))


class _Builder(HTMLParser):
    """Walk the HTML and emit paragraphs of boxes"""

    def __init__(self, base: _Context):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, _Context]] = [("body", base)]
        self.paragraphs: list[Paragraph] = []
        # inline content that is not inside a <p>
        self._loose: Paragraph | None = None

    # helpers
    @property
    def ctx(self) -> _Context:
        return self.stack[-1][1]

    def _current(self) -> Paragraph:
        for tag, _ in reversed(self.stack):
            if tag == "p":
                return self.paragraphs[-1]
        if self._loose is None:
            self._loose = Paragraph(
                linespacing=self.ctx.style.lineheight * self.ctx.style.fontsize,
                halign=self.ctx.halign,
            )
            self.paragraphs.append(self._loose)
        return self._loose

    # parser callbacks
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in _SUPPORTED_TAGS:
            raise ValueError(_UNSUPPORTED_MSG.format(tag))
        attrs = dict(attrs)
        if tag == "br":
            self._br()
            return

        ctx = self.ctx
        if tag in ("sup", "sub"):
            # change font size before processing style, so that the
            # style can override it
            st = replace(ctx.style, fontsize=0.8 * ctx.style.fontsize)
            ctx = replace(ctx, style=st)
            ctx = _apply_css(ctx, attrs.get("style"))
            shift = font_ascent(ctx.style) / 2
            ctx = replace(ctx, yoff=ctx.yoff + (shift if tag == "sup" else -shift))
        else:
            ctx = _apply_css(ctx, attrs.get("style"))
            if tag in ("b", "strong"):
                ctx = replace(ctx, style=replace(ctx.style, weight="bold"))
            elif tag in ("i", "em"):
                ctx = replace(ctx, style=replace(ctx.style, style="italic"))

        if tag == "p":
            self._loose = None
            self.paragraphs.append(
                Paragraph(
                    linespacing=ctx.style.lineheight * ctx.style.fontsize,
                    halign=ctx.halign,
                )
            )
        self.stack.append((tag, ctx))

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "br":
            self._br()
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "br":
            return
        # pop to the matching tag
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i][0] == tag:
                ctx = self.stack[i][1]
                del self.stack[i:]
                if tag == "p":
                    # paragraphs end with a forced break
                    par = self.paragraphs[-1]
                    par.nodes.append(TextBox("", ctx.style, ctx.yoff))
                    par.nodes.append(Break())
                return

    def handle_data(self, data):
        if data == "":
            return
        # Whitespace between block elements (e.g. "\n" between </p><p>)
        if data.strip() == "" and not any(t == "p" for t, _ in self.stack):
            return
        ctx = self.ctx
        nodes = self._current().nodes
        tokens = data.split()
        boxes: list[Node] = []
        if data[:1].isspace():
            boxes.append(Glue(ctx.style))
        for tok in tokens:
            boxes.append(TextBox(tok, ctx.style, ctx.yoff))
            boxes.append(Glue(ctx.style))
        if not tokens:
            # whitespace only: a single glue
            boxes = [Glue(ctx.style)]
        elif not data[-1:].isspace():
            boxes.pop()
        nodes.extend(boxes)

    def _br(self):
        ctx = self.ctx
        nodes = self._current().nodes
        nodes.append(TextBox("", ctx.style, ctx.yoff))
        nodes.append(Break())


def to_html(text: str, use_markdown: bool = True) -> str:
    if use_markdown:
        return _markdown.markdown(text)
    return text


def parse(
    text: str | None,
    style: Style,
    halign: float = 0.0,
    use_markdown: bool = True,
) -> list[Paragraph]:
    """
    Parse markdown/HTML text into a list of paragraphs

    Parameters
    ----------
    text :
        Markdown (or HTML) text
    style :
        Base font style
    halign :
        Horizontal alignment of lines within a paragraph
    use_markdown :
        Whether to run the text through a markdown processor first
    """
    if text is None or (isinstance(text, float) and text != text):
        text = ""
    html = to_html(str(text), use_markdown)
    b = _Builder(_Context(style=style, halign=halign))
    b.feed(html)
    b.close()
    return b.paragraphs
