from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from glyphkit.shaping import ShapingStyle, shape_text
from tests.helpers import make_test_font


def _library(*, extra_codepoints: tuple[int, ...] = ()) -> FontLibrary:
    return FontLibrary.from_sources(
        (
            FontSource.bytes(
                make_test_font(family="Text Engine", extra_codepoints=extra_codepoints),
                label="text-engine",
            ),
        )
    )


def test_combining_cluster_retains_complete_source_range() -> None:
    library = _library(extra_codepoints=(0x0301,))
    runs = shape_text(library, "A\u0301", ShapingStyle(("Text Engine",), 20))
    assert {glyph.cluster for glyph in runs[0].glyphs} == {runs[0].source_range}
    assert (runs[0].source_range.start, runs[0].source_range.end) == (0, 2)


def test_wrapping_uses_unicode_breaks_and_preserves_reading_order() -> None:
    library = _library()
    style = TextStyle(("Text Engine",), 20)
    layout = library.layout(Paragraph((TextSpan("A A", style),), max_width=20))
    assert len(layout.lines) == 2
    assert tuple((line.source_range.start, line.source_range.end) for line in layout.lines) == (
        (0, 2),
        (2, 3),
    )
    assert tuple(item for line in layout.lines for item in line.reading_order)


def test_spacing_tabs_justification_and_font_use_are_data_only() -> None:
    library = _library()
    style = TextStyle(("Text Engine",), 20, letter_spacing=1, word_spacing=2)
    layout = library.layout(
        Paragraph(
            (TextSpan("A A\tB A", style),),
            max_width=65,
            align="justify",
            first_line_indent=3,
            tab_stops=(48,),
        )
    )
    assert len(layout.lines) >= 2
    assert layout.lines[0].logical_bounds.x_min == 3
    assert layout.font_uses[0].face_id == library.faces[0].id
    assert layout.font_uses[0].variation_coordinates == ()


def test_ink_bounds_are_derived_from_glyph_extents() -> None:
    library = _library()
    layout = library.layout(Paragraph((TextSpan("A", TextStyle(("Text Engine",), 20)),)))
    assert layout.ink_bounds.width < layout.logical_bounds.width
    assert layout.ink_bounds.y_max == 14
