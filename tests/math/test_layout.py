from pathlib import Path

import pytest

from glyphkit import FontLibrary, FontSource, UnsupportedFeatureError
from glyphkit.math import Fraction, MathStyle, layout_math, parse_math
from tests.helpers import make_test_font


def test_rejects_font_without_required_math_table() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Plain"), label="plain"),)
    )
    with pytest.raises(UnsupportedFeatureError, match="MATH table"):
        layout_math(library, parse_math(r"\frac{x}{y}"), style=MathStyle(18, ("Plain",)))


@pytest.mark.skipif(
    not Path("/System/Library/Fonts/Supplemental/STIXTwoMath.otf").exists(),
    reason="local integration font is unavailable",
)
def test_lays_out_fraction_with_rule_using_opentype_math_font() -> None:
    path = Path("/System/Library/Fonts/Supplemental/STIXTwoMath.otf")
    library = FontLibrary.from_sources((FontSource.path(path),))
    expression = parse_math(r"\frac{x_1}{x_2}")
    box = layout_math(library, expression, style=MathStyle(18, ("STIX Two Math",)))
    assert box.kind == "fraction"
    assert box.rules
    assert isinstance(expression, Fraction)
