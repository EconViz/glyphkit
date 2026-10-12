from dataclasses import replace

from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle, VariableAxis
from glyphkit.embedding import EmbeddingUse
from tests.helpers import make_test_font


def test_declared_variable_coordinates_follow_glyph_outline_and_subset() -> None:
    base = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Variable"), label="variable"),)
    ).faces[0]
    library = FontLibrary((replace(base, axes=(VariableAxis("wght", 100, 400, 900),)),))
    layout = library.layout(
        Paragraph(
            (TextSpan("A", TextStyle(("Variable",), 20, weight=650)),),
        )
    )
    glyph = layout.lines[0].runs[0].glyphs[0]
    assert glyph.variation_coordinates == (("wght", 650.0),)
    assert library.outline(glyph).variation_coordinates == glyph.variation_coordinates
    bundle = library.subset(layout, embedding_use=EmbeddingUse.WEB)
    assert bundle.fonts[0].variation_coordinates == glyph.variation_coordinates
