from __future__ import annotations

from io import BytesIO

from fontTools.fontBuilder import FontBuilder
from fontTools.otlLib.builder import buildMathTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def make_test_font(
    *,
    family: str = "GlyphKit Test",
    weight: int = 400,
    extra_codepoints: tuple[int, ...] = (),
) -> bytes:
    units = 1000
    builder = FontBuilder(units, isTTF=True)
    extra_names = [f"uni{codepoint:04X}" for codepoint in extra_codepoints]
    glyph_order = [".notdef", "space", "A", "B", *extra_names]
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(
        {32: "space", 65: "A", 66: "B"} | dict(zip(extra_codepoints, extra_names, strict=True))
    )
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)
        if name != "space":
            pen.moveTo((50, 0))
            pen.lineTo((300, 700))
            pen.lineTo((550, 0))
            pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(
        {name: (600 if name != "space" else 300, 0) for name in glyph_order}
    )
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable(
        {
            "familyName": family,
            "styleName": "Regular" if weight == 400 else "Bold",
            "uniqueFontIdentifier": f"{family}-{weight}",
            "fullName": f"{family} {weight}",
            "psName": f"{family.replace(' ', '')}-{weight}",
        }
    )
    builder.setupOS2(
        fsType=0,
        sTypoAscender=800,
        sTypoDescender=-200,
        usWinAscent=800,
        usWinDescent=200,
        usWeightClass=weight,
    )
    builder.setupPost()
    builder.setupMaxp()
    stream = BytesIO()
    builder.save(stream)
    return stream.getvalue()


def make_math_test_font(
    *, family: str = "GlyphKit Math", extra_codepoints: tuple[int, ...] = ()
) -> bytes:
    """Create a deterministic test-only font with a real OpenType MATH table."""

    data = make_test_font(
        family=family,
        extra_codepoints=(
            ord("x"),
            ord("y"),
            ord("1"),
            ord("2"),
            ord("√"),
            ord("∑"),
            ord("\u02c6"),
            ord("¯"),
            ord("→"),
            ord("_"),
            ord("("),
            ord(")"),
            ord("="),
            ord("+"),
            ord(","),
            ord("-"),
            ord("∫"),
            *extra_codepoints,
        ),
    )
    font = TTFont(BytesIO(data))
    try:
        x_name = font.getBestCmap()[ord("x")]
        buildMathTable(
            font,
            constants={
                "AxisHeight": 250,
                "FractionRuleThickness": 60,
                "FractionNumeratorShiftUp": 450,
                "FractionNumeratorDisplayStyleShiftUp": 550,
                "FractionDenominatorShiftDown": 450,
                "FractionDenominatorDisplayStyleShiftDown": 550,
                "ScriptPercentScaleDown": 70,
                "ScriptScriptPercentScaleDown": 50,
                "SubscriptShiftDown": 250,
                "SuperscriptShiftUp": 400,
                "UpperLimitBaselineRiseMin": 500,
                "LowerLimitBaselineDropMin": 500,
                "RadicalVerticalGap": 80,
                "RadicalRuleThickness": 50,
                "RadicalDegreeBottomRaisePercent": 60,
                "OverbarVerticalGap": 80,
                "UnderbarVerticalGap": 80,
            },
            italicsCorrections={x_name: 50},
            topAccentAttachments={x_name: 300},
        )
        stream = BytesIO()
        font.save(stream)
        return stream.getvalue()
    finally:
        font.close()
