from glyphkit import FontLibrary, FontSource
from glyphkit.shaping import ShapingStyle, shape_text
from tests.helpers import make_test_font


def test_shapes_into_plain_immutable_glyph_values() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Shape"), label="shape"),)
    )
    runs = shape_text(library, "AB", ShapingStyle(("Shape",), 20))
    assert len(runs) == 1
    assert runs[0].text == "AB"
    assert runs[0].advance == 24
    assert tuple(glyph.cluster.start for glyph in runs[0].glyphs) == (0, 1)
    assert all(type(glyph).__module__.startswith("glyphkit") for glyph in runs[0].glyphs)

