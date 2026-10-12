from glyphkit import FontLibrary, FontSource
from glyphkit.outlines import ClosePath, LineTo, MoveTo, extract_outline
from tests.helpers import make_test_font


def test_extracts_self_contained_glyph_commands_and_bounds() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Outline"), label="outline"),)
    )
    face = library.faces[0]
    outline = extract_outline(face, 2)
    assert isinstance(outline.commands[0], MoveTo)
    assert any(isinstance(command, LineTo) for command in outline.commands)
    assert isinstance(outline.commands[-1], ClosePath)
    assert outline.bounds.width == 500
    assert outline.units_per_em == 1000


def test_whitespace_has_an_empty_outline() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Outline"), label="outline"),)
    )
    outline = extract_outline(library.faces[0], 1)
    assert outline.commands == ()
    assert outline.bounds.width == 0
