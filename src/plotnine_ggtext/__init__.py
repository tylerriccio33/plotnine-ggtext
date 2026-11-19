"""
plotnine-ggtext: rich text (markdown / html) for plotnine

A port of the R package ggtext (https://github.com/wilkelab/ggtext).
The markup parsing and layout live in ggir
(https://github.com/snake-case-ggtext/ggIR).
"""

from ggir import unit

from .geom_richtext import geom_richtext
from .geom_textbox import geom_textbox

__all__ = ("geom_richtext", "geom_textbox", "unit")
