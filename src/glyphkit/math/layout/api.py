"""Entry point for math layout."""

from __future__ import annotations

from glyphkit.errors import UnsupportedFeatureError
from glyphkit.fonts import FontLibrary, FontQuery
from glyphkit.fonts.parsed import parsed_font
from glyphkit.math.layout.engine import _layout
from glyphkit.math.layout.model import MathBox, MathStyle, _MathData
from glyphkit.math.nodes import (
    MathNode,
)


def layout_math(library: FontLibrary, expression: MathNode, *, style: MathStyle) -> MathBox:
    face = library.match(FontQuery(style.families)).face
    if not face.has_math:
        raise UnsupportedFeatureError(f"font {face.family!r} has no OpenType MATH table")
    with parsed_font(face) as font:
        data = _MathData(
            font,
            face,
            style.size / face.metrics.units_per_em,
            style.level == "display",
            style.size,
            style.constants,
            units_per_em=float(face.metrics.units_per_em),
            base_size=style.size,
        )
        return _layout(library, expression, style, data)
