from itertools import pairwise
from pathlib import Path

import pytest

from glyphkit import ConfigurationError, FontLibrary, FontSource, UnsupportedFeatureError
from glyphkit.math import Fraction, Limits, MathBox, MathStyle, layout_math, parse_math
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


def _ink(box: MathBox):  # type: ignore[no-untyped-def]
    from glyphkit.math.layout import _ink as ink

    return ink(box)


def _top(box: MathBox) -> float:
    return _ink(box).y_max


def _bottom(box: MathBox) -> float:
    return _ink(box).y_min


def _library() -> FontLibrary:
    return FontLibrary.from_sources((FontSource.bytes(make_math_test_font(), label="math"),))


STYLE = MathStyle(20, ("GlyphKit Math",))


def test_fraction_rule_uses_the_font_constants_and_numerator_and_denominator_clear_it() -> None:
    fraction = layout_math(_library(), parse_math(r"\frac{x_1}{y^2}"), style=STYLE)
    rule = fraction.rules[0]
    assert rule.thickness == 1.2
    assert rule.start[1] == rule.end[1] == 5  # AxisHeight 250 of 1000 at size 20
    numerator, denominator = fraction.children
    rule_top, rule_bottom = rule.start[1] + 0.6, rule.start[1] - 0.6
    # the test font sets the gap minimums to zero, so the parts touch the rule's edges exactly
    assert numerator.origin[1] + _bottom(numerator) == pytest.approx(rule_top)
    assert denominator.origin[1] + _top(denominator) <= rule_bottom + 1e-9
    assert numerator.origin[1] >= 11  # never less than FractionNumeratorDisplayStyleShiftUp
    assert denominator.origin[1] <= -11


def test_display_fractions_set_their_parts_at_full_size_and_text_fractions_smaller() -> None:
    library = _library()
    display = layout_math(library, parse_math(r"\frac{x}{y}"), style=STYLE)
    text = layout_math(
        library, parse_math(r"\frac{x}{y}"), style=MathStyle(20, STYLE.families, level="text")
    )
    size = lambda box: box.children[0].text_layout.lines[0].runs[0].size  # noqa: E731
    assert size(display) == 20
    assert size(text) == pytest.approx(14)  # ScriptPercentScaleDown 70


def test_big_operator_limits_clear_the_operator_and_are_centred() -> None:
    expression = parse_math(r"\sum_{x}^{y}")
    assert isinstance(expression, Limits)
    limits = layout_math(_library(), expression, style=STYLE)
    assert limits.kind == "limits"
    operator, lower, upper = limits.children
    op_top = operator.origin[1] + _top(operator)
    op_bottom = operator.origin[1] + _bottom(operator)
    assert upper.origin[1] + _bottom(upper) >= op_top  # the upper limit sits above the operator
    assert lower.origin[1] + _top(lower) <= op_bottom  # and the lower one below it
    assert upper.origin[1] - op_top >= 10  # UpperLimitBaselineRiseMin 500 of 1000 at 20
    assert op_bottom - lower.origin[1] >= 10
    centre = limits.bounds.width / 2
    for box in (operator, lower, upper):
        assert box.origin[0] + box.bounds.width / 2 == pytest.approx(centre)


def test_limits_become_scripts_outside_display_style() -> None:
    text = layout_math(
        _library(), parse_math(r"\sum_{x}^{y}"), style=MathStyle(20, STYLE.families, level="text")
    )
    assert text.kind == "script"


def test_integrals_take_scripts_at_the_side_even_in_display_style() -> None:
    box = layout_math(_library(), parse_math(r"\int_{x}^{y}"), style=STYLE)
    assert box.kind == "script"


def test_sub_and_superscripts_keep_the_minimum_gap_apart() -> None:
    box = layout_math(_library(), parse_math("x_1^2"), style=STYLE)
    _, sub, sup = box.children
    gap = (sup.origin[1] + _bottom(sup)) - (sub.origin[1] + _top(sub))
    assert gap >= 3 - 1e-9  # SubSuperscriptGapMin falls back to 0.15 em


def test_superscript_follows_the_italic_correction_and_subscript_does_not() -> None:
    box = layout_math(_library(), parse_math("x_1^2"), style=STYLE)
    base, sub, sup = box.children
    assert sub.origin[0] == pytest.approx(base.bounds.width)
    assert sup.origin[0] == pytest.approx(base.bounds.width + 1.0)  # italic correction 50 of 1000


def _gaps(library: FontLibrary, source: str, level: str = "display") -> list[float]:
    box = layout_math(library, parse_math(source), style=MathStyle(18, STYLE.families, level=level))
    placed = sorted(box.children, key=lambda child: child.origin[0])
    return [round(b.origin[0] - (a.origin[0] + a.bounds.width), 6) for a, b in pairwise(placed)]


def test_relations_get_thick_spaces_and_binary_operators_medium_spaces() -> None:
    library = _library()
    thick, medium = 5 * 18 / 18, 4 * 18 / 18
    assert _gaps(library, "x=y") == [thick, thick]
    assert _gaps(library, "x+y") == [medium, medium]


def test_a_binary_operator_without_a_left_operand_is_ordinary() -> None:
    assert _gaps(_library(), "+y") == [0.0]
    assert _gaps(_library(), "x=+y")[2] == 0.0  # no space between a unary + and its operand
    assert _gaps(_library(), "(-y)") == [0.0, 0.0, 0.0]


def test_punctuation_gets_a_thin_space_after_it_only() -> None:
    assert _gaps(_library(), "x,y") == [0.0, 3 * 18 / 18]


def test_script_styles_have_no_optional_spaces() -> None:
    library = _library()
    scripted = layout_math(library, parse_math("x^{x=y}"), style=STYLE)
    inner = scripted.children[1]
    assert [
        round(b.origin[0] - (a.origin[0] + a.bounds.width), 6)
        for a, b in zip(inner.children, inner.children[1:], strict=False)
    ] == [0.0, 0.0]


def test_explicit_spaces_have_the_width_of_their_math_units() -> None:
    library = _library()
    narrow = layout_math(library, parse_math("xy"), style=STYLE).bounds.width
    spaced = layout_math(library, parse_math(r"x\;y"), style=STYLE).bounds.width
    assert spaced - narrow == pytest.approx(5 * 20 / 18)


def test_a_true_minus_is_used_when_the_font_has_one() -> None:
    def minus_text(font: bytes) -> str:
        library = FontLibrary.from_sources((FontSource.bytes(font, label="math"),))
        box = layout_math(library, parse_math("x-y"), style=STYLE)
        return box.children[1].text_layout.lines[0].runs[0].text

    assert minus_text(make_math_test_font()) == "-"  # no U+2212 glyph: the hyphen stays
    assert minus_text(make_math_test_font(extra_codepoints=(0x2212,))) == "\u2212"


def test_script_size_derives_from_the_whole_expression_not_the_enclosing_script() -> None:
    box = layout_math(_library(), parse_math("x^{y^2}"), style=STYLE)
    inner = box.children[1].children[1]
    assert inner.text_layout.lines[0].runs[0].size == pytest.approx(10)  # 50% of 20, not 35%


def test_math_level_must_be_known() -> None:
    with pytest.raises(ConfigurationError, match="level"):
        MathStyle(20, STYLE.families, level="inline")


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
    # the test font declares ScriptScriptPercentScaleDown = 50 (of 20); the override is a
    # fraction of the enclosing script, which is 14 points: 3.5 instead of 10
    assert nested_width(MathStyle(20, families, script_script_scale=0.25)) == pytest.approx(
        default * 0.35
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
        20,
        families,
        constants={
            "SuperscriptShiftUp": 0.35,
            "SubscriptShiftDown": 0.2,
            "SubSuperscriptGapMin": 0.0,
            "SuperscriptBottomMin": 0.0,
            "SubscriptTopMax": 1.0,
        },
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


def test_the_radical_sign_reaches_the_bar_and_the_bar_clears_the_body() -> None:
    box = layout_math(_library(), parse_math(r"\sqrt{x}"), style=STYLE)
    radical, body = box.children
    rule = box.rules[0]
    assert rule.start[1] > body.origin[1] + _top(body)  # the bar is above the body
    bar_top = rule.start[1] + rule.thickness / 2
    assert radical.origin[1] + _top(radical) == pytest.approx(bar_top, abs=0.05)
    assert rule.start[0] == pytest.approx(radical.bounds.width)  # the bar starts at the sign


def test_delimiters_grow_with_their_content() -> None:
    small = layout_math(_library(), parse_math(r"\left( x \right)"), style=STYLE)
    tall = layout_math(_library(), parse_math(r"\left( \frac{x}{y} \right)"), style=STYLE)
    left_small, _, _ = small.children
    left_tall, body, _ = tall.children
    assert _top(left_tall) - _bottom(left_tall) > _top(left_small) - _bottom(left_small)
    assert _top(left_tall) + left_tall.origin[1] >= (_top(body) - _bottom(body)) * 0.9 / 2


def test_overline_and_underline_are_rules_as_wide_as_their_body() -> None:
    over = layout_math(_library(), parse_math(r"\overline{xy}"), style=STYLE)
    under = layout_math(_library(), parse_math(r"\underline{xy}"), style=STYLE)
    body = over.children[0]
    assert over.rules[0].end[0] - over.rules[0].start[0] == pytest.approx(body.bounds.width)
    assert over.rules[0].start[1] > _top(body)
    assert under.rules[0].start[1] < _bottom(body)


def test_an_accent_sits_above_its_body_wherever_the_glyph_draws() -> None:
    box = layout_math(_library(), parse_math(r"\hat{x}"), style=STYLE)
    body, accent = box.children
    assert accent.origin[1] + _bottom(accent) >= _top(body) - 1e-9
