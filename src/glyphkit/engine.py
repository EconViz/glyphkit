"""High-level composition facade; lower layers never import this module."""

from __future__ import annotations

from glyphkit.fonts.library import FontLibrary as FontCatalog
from glyphkit.layout import Paragraph, TextLayout, layout_paragraph


class FontLibrary(FontCatalog):
    """Explicit font catalog composed with renderer-neutral typography services."""

    def layout(self, paragraph: Paragraph) -> TextLayout:
        if not isinstance(paragraph, Paragraph):
            raise TypeError("paragraph must be a glyphkit.layout.Paragraph")
        return layout_paragraph(self, paragraph)
