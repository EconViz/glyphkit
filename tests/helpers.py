from __future__ import annotations

from io import BytesIO

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


def make_test_font(*, family: str = "GlyphKit Test", weight: int = 400) -> bytes:
    units = 1000
    builder = FontBuilder(units, isTTF=True)
    glyph_order = [".notdef", "space", "A", "B"]
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap({32: "space", 65: "A", 66: "B"})
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)
        if name in {"A", "B", ".notdef"}:
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
