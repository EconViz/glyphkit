"""Small structural ports for independent consumers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from glyphkit.embedding import EmbeddingUse, FontContainer, FontSubsetBundle
from glyphkit.layout import Paragraph, TextLayout
from glyphkit.math import MathBox, MathNode, MathStyle
from glyphkit.outlines import GlyphOutline
from glyphkit.shaping import PositionedGlyph


@runtime_checkable
class TypographyEngine(Protocol):
    def layout(self, paragraph: Paragraph) -> TextLayout: ...
    def layout_math(self, expression: MathNode, *, style: MathStyle) -> MathBox: ...
    def outline(self, glyph: PositionedGlyph) -> GlyphOutline: ...
    def subset(
        self,
        layout: TextLayout,
        *,
        embedding_use: EmbeddingUse,
        container: FontContainer = FontContainer.SFNT,
        allow_unknown: bool = False,
    ) -> FontSubsetBundle: ...
