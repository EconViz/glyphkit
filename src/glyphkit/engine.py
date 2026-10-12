"""High-level composition facade; lower layers never import this module."""

from __future__ import annotations

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
        return extract_outline(self.face(glyph.face_id), glyph.glyph_id)

    def layout_math(self, expression: MathNode, *, style: MathStyle) -> MathBox:
        return layout_math(self, expression, style=style)
