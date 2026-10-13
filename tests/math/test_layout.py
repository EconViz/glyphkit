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


def _first_face_id(box):  # type: ignore[no-untyped-def]
    return box.text_layout.lines[0].runs[0].face_id


def test_constants_override_replaces_font_values_in_em() -> None:
    library = FontLibrary.from_sources((FontSource.bytes(make_math_test_font(), label="math"),))
    families = ("GlyphKit Math",)
    style = MathStyle(
        20, families, constants={"SuperscriptShiftUp": 0.35, "SubscriptShiftDown": 0.2}
    )
    box = layout_math(library, parse_math("x_1^2"), style=style)
    subscript, superscript = box.children[1], box.children[2]
    assert subscript.origin[1] == pytest.approx(-4.0)
    assert superscript.origin[1] == pytest.approx(7.0)
    untouched = layout_math(library, parse_math("x_1^2"), style=MathStyle(20, families))
    assert untouched.children[2].origin[1] == pytest.approx(8.0)


@pytest.mark.parametrize(
    ("constants", "message"),
    [
        ({"NoSuchConstant": 0.1}, "NoSuchConstant"),
        ({"SuperscriptShiftUp": -0.1}, "SuperscriptShiftUp"),
        ({"SuperscriptShiftUp": float("nan")}, "SuperscriptShiftUp"),
    ],
)
def test_constants_override_rejects_unknown_or_invalid_values(
    constants: dict[str, float], message: str
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        MathStyle(20, ("GlyphKit Math",), constants=constants)


def test_letter_slant_selects_the_italic_face_for_letters_only() -> None:
    upright = make_math_test_font()
    italic = _as_italic(upright)
    library = FontLibrary.from_sources(
        (FontSource.bytes(upright, label="up"), FontSource.bytes(italic, label="it"))
    )
    families = ("GlyphKit Math",)
    plain = layout_math(library, parse_math("x2"), style=MathStyle(20, families))
    slanted = layout_math(
        library, parse_math("x2"), style=MathStyle(20, families, letter_slant="italic")
    )
    letter_plain, digit_plain = (_first_face_id(c) for c in plain.children)
    letter_slanted, digit_slanted = (_first_face_id(c) for c in slanted.children)
    assert letter_plain == digit_plain == digit_slanted
    assert letter_slanted != letter_plain


def test_letter_slant_must_be_a_known_slant() -> None:
    with pytest.raises(ConfigurationError, match="letter_slant"):
        MathStyle(20, ("GlyphKit Math",), letter_slant="slanted")


def _as_italic(font_bytes: bytes) -> bytes:
    from io import BytesIO

    from fontTools.ttLib import TTFont

    font = TTFont(BytesIO(font_bytes))
    font["OS/2"].fsSelection |= 0x01
    font["head"].macStyle |= 0x02
    name = font["name"]
    name.setName("GlyphKit Math Italic", 3, 3, 1, 0x409)
    name.setName("GlyphKit Math Italic", 3, 1, 0, 0x409)
    out = BytesIO()
    font.save(out)
    return out.getvalue()
