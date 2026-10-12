from pathlib import Path

import pytest

from glyphkit import ConfigurationError, FontLibrary, FontSource, UnsupportedFeatureError
from glyphkit.math import Fraction, Limits, MathStyle, layout_math, parse_math
from tests.helpers import make_math_test_font, make_test_font


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


def test_uses_opentype_math_constants_for_fraction_scripts_and_limits() -> None:
    library = FontLibrary.from_sources((FontSource.bytes(make_math_test_font(), label="math"),))
    fraction = layout_math(
        library,
        parse_math(r"\frac{x_1}{y^2}"),
        style=MathStyle(20, ("GlyphKit Math",)),
    )
    assert fraction.rules[0].thickness == 1.2
    assert fraction.children[0].origin[1] == 11
    assert fraction.children[1].origin[1] == -11
    expression = parse_math(r"\sum_{x}^{y}")
    assert isinstance(expression, Limits)
    limits = layout_math(library, expression, style=MathStyle(20, ("GlyphKit Math",)))
    assert limits.kind == "limits"
    assert len(limits.children) == 3


def _script_width(library: FontLibrary, style: MathStyle) -> float:
    box = layout_math(library, parse_math("x^2"), style=style)
    script = box.children[1]
    return script.bounds.width


def test_script_scale_overrides_the_font_percentage() -> None:
    library = FontLibrary.from_sources((FontSource.bytes(make_math_test_font(), label="math"),))
    families = ("GlyphKit Math",)
    default = _script_width(library, MathStyle(20, families))
    # the test font declares ScriptPercentScaleDown = 70
    smaller = _script_width(library, MathStyle(20, families, script_scale=0.35))
    assert smaller == pytest.approx(default / 2)
    same = _script_width(library, MathStyle(20, families, script_scale=0.7))
    assert same == pytest.approx(default)


def test_script_script_scale_applies_to_nested_scripts() -> None:
    library = FontLibrary.from_sources((FontSource.bytes(make_math_test_font(), label="math"),))
    families = ("GlyphKit Math",)

    def nested_width(style: MathStyle) -> float:
        box = layout_math(library, parse_math("x^{y^2}"), style=style)
        return box.children[1].children[1].bounds.width

    default = nested_width(MathStyle(20, families))
    # the test font declares ScriptScriptPercentScaleDown = 50
    assert nested_width(MathStyle(20, families, script_script_scale=0.25)) == pytest.approx(
        default / 2
    )


@pytest.mark.parametrize("value", [0.0, -0.5, 1.5, float("nan")])
def test_script_scale_must_be_a_fraction_in_zero_to_one(value: float) -> None:
    with pytest.raises(ConfigurationError, match="script_scale"):
        MathStyle(20, ("GlyphKit Math",), script_scale=value)
    with pytest.raises(ConfigurationError, match="script_script_scale"):
        MathStyle(20, ("GlyphKit Math",), script_script_scale=value)
