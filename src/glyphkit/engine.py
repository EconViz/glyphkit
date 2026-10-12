"""High-level composition facade; lower layers never import this module."""

from __future__ import annotations

from glyphkit.embedding import EmbeddingUse, FontContainer, FontSubsetBundle, subset_layout
from glyphkit.fonts.library import FontLibrary as FontCatalog
from glyphkit.layout import Paragraph, TextLayout, layout_paragraph
from glyphkit.math import MathBox, MathNode, MathStyle, layout_math
from glyphkit.outlines import GlyphOutline, extract_outline
from glyphkit.shaping import PositionedGlyph


class FontLibrary(FontCatalog):
    """Explicit font catalog composed with renderer-neutral typography services."""

    def layout(self, paragraph: Paragraph) -> TextLayout:
        if not isinstance(paragraph, Paragraph):
            raise TypeError("paragraph must be a glyphkit.layout.Paragraph")
        return layout_paragraph(self, paragraph)

    def outline(self, glyph: PositionedGlyph) -> GlyphOutline:
        return extract_outline(
            self.face(glyph.face_id),
            glyph.glyph_id,
            variation_coordinates=glyph.variation_coordinates,
        )

    def layout_math(self, expression: MathNode, *, style: MathStyle) -> MathBox:
        return layout_math(self, expression, style=style)

    def subset(
        self,
        layout: TextLayout,
        *,
        embedding_use: EmbeddingUse,
        container: FontContainer = FontContainer.SFNT,
        allow_unknown: bool = False,
    ) -> FontSubsetBundle:
        return subset_layout(
            self,
            layout,
            embedding_use=embedding_use,
            container=container,
            allow_unknown=allow_unknown,
        )
