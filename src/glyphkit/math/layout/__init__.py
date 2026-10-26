"""Backend-neutral OpenType MATH box layout."""

from __future__ import annotations

from glyphkit.math.layout.api import layout_math
from glyphkit.math.layout.engine import _covered, _layout, _limits, _script
from glyphkit.math.layout.metrics import (
    _advance,
    _depth,
    _first_glyph_id,
    _fraction_style,
    _height,
    _ink,
    _math_glyph_id,
    _script_style,
    _text_box,
    _translate,
    _union,
)
from glyphkit.math.layout.model import (
    LEVELS,
    OVERRIDABLE_CONSTANTS,
    MathBox,
    MathRule,
    MathStyle,
    _MathData,
)
from glyphkit.math.layout.shapes import _enlarged, _shifted, _sized_to
from glyphkit.math.layout.spacing import (
    _ATOMS,
    _CLOSING,
    _MU,
    _OPENING,
    _RELATIONS,
    _SPACING,
    _atom_class,
    _atom_classes,
    _gap,
    _symbol_class,
)

__all__ = [
    "LEVELS",
    "OVERRIDABLE_CONSTANTS",
    "_ATOMS",
    "_CLOSING",
    "_MU",
    "_OPENING",
    "_RELATIONS",
    "_SPACING",
    "MathBox",
    "MathRule",
    "MathStyle",
    "_MathData",
    "_advance",
    "_atom_class",
    "_atom_classes",
    "_covered",
    "_depth",
    "_enlarged",
    "_first_glyph_id",
    "_fraction_style",
    "_gap",
    "_height",
    "_ink",
    "_layout",
    "_limits",
    "_math_glyph_id",
    "_script",
    "_script_style",
    "_shifted",
    "_sized_to",
    "_symbol_class",
    "_text_box",
    "_translate",
    "_union",
    "layout_math",
]
