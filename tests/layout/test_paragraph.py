from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from tests.helpers import make_test_font


def setup() -> tuple[FontLibrary, TextStyle]:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Layout"), label="layout"),)
    )
    return library, TextStyle(("Layout",), 20)


def test_layout_is_y_up_and_preserves_source_ranges() -> None:
    library, style = setup()
    layout = library.layout(Paragraph((TextSpan("AB\nA", style),)))
    assert len(layout.lines) == 2
    assert layout.lines[0].baseline == 0
    assert layout.lines[1].baseline < 0
    glyphs = [glyph for line in layout.lines for run in line.runs for glyph in run.glyphs]
    assert tuple(glyph.cluster.start for glyph in glyphs) == (0, 1, 3)


def test_width_constraint_wraps_without_clipping() -> None:
    library, style = setup()
    layout = library.layout(Paragraph((TextSpan("AB", style),), max_width=12))
    assert len(layout.lines) == 2
    assert "".join(run.text for line in layout.lines for run in line.runs)

