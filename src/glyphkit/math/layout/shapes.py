"""Enlarged operators and stretchy glyphs."""

from __future__ import annotations

from dataclasses import replace

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontLibrary
from glyphkit.math.layout.metrics import _ink, _text_box, _translate
from glyphkit.math.layout.model import MathBox, MathStyle, _MathData
from glyphkit.math.nodes import (
    Symbol,
)


def _enlarged(library: FontLibrary, symbol: Symbol, style: MathStyle, data: _MathData) -> MathBox:
    """A big operator: in display style large enough, and centred on the math axis."""
    box = _text_box(library, symbol.value, style, symbol.source_range)
    if symbol.role not in {"large-operator", "integral"} or len(symbol.value) != 1:
        return box
    if style.level != "display":
        return box
    ink = _ink(box)
    if ink is None:
        return box
    wanted = data.value("DisplayOperatorMinHeight", style.size * 1.4)
    height = ink.y_max - ink.y_min
    if height < wanted:
        box = _text_box(
            library,
            symbol.value,
            replace(style, size=style.size * wanted / height),
            symbol.source_range,
        )
        ink = _ink(box)
        assert ink is not None
    axis = data.value("AxisHeight", style.size * 0.25)
    shift = axis - (ink.y_max + ink.y_min) / 2
    return MathBox(
        "operator",
        _translate(box.bounds, (0.0, shift)),
        0.0,
        children=(replace(box, origin=(0.0, shift)),),
        source_range=symbol.source_range,
        glyph_id=box.glyph_id,
    )


def _sized_to(
    library: FontLibrary,
    text: str,
    style: MathStyle,
    source_range: SourceRange,
    *,
    top: float,
    bottom: float,
) -> MathBox:
    """A stretchy glyph (radical, bracket) set at a size whose ink spans ``bottom`` to ``top``.

    It is never set smaller than ``style.size``. The font's glyph variants would draw these
    better; scaling the plain glyph keeps the result a normal positioned glyph.
    """
    box = _text_box(library, text, style, source_range)
    ink = _ink(box)
    wanted = top - bottom
    if ink is None or ink.y_max - ink.y_min >= wanted:
        shift = top - ink.y_max if ink is not None and ink.y_max - ink.y_min >= wanted else 0.0
        return _shifted(box, shift)
    scaled = _text_box(
        library,
        text,
        replace(style, size=style.size * wanted / (ink.y_max - ink.y_min)),
        source_range,
    )
    ink = _ink(scaled)
    assert ink is not None
    return _shifted(scaled, top - ink.y_max)


def _shifted(box: MathBox, dy: float) -> MathBox:
    if dy == 0.0:
        return box
    return MathBox(
        "shifted",
        _translate(box.bounds, (0.0, dy)),
        0.0,
        children=(replace(box, origin=(0.0, dy)),),
        source_range=box.source_range,
        glyph_id=box.glyph_id,
    )
