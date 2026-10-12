"""Return semantic OpenType MATH geometry without rendering it."""

from pathlib import Path

from glyphkit import FontLibrary, FontSource
from glyphkit.math import MathBox, MathStyle, parse_math


def build_math(math_font: Path) -> MathBox:
    library = FontLibrary.from_sources((FontSource.path(math_font),))
    expression = parse_math(r"U(x_1, x_2) = x_1^\alpha x_2^{1-\alpha}")
    return library.layout_math(expression, style=MathStyle(18, (library.faces[0].family,)))
