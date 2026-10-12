"""Return a plain-text layout; the caller owns all drawing and output."""

from pathlib import Path

from glyphkit import FontLibrary, FontSource, Paragraph, TextLayout, TextSpan, TextStyle


def build_layout(font_path: Path) -> TextLayout:
    library = FontLibrary.from_sources((FontSource.path(font_path),))
    return library.layout(
        Paragraph(
            (TextSpan("Deterministic typography", TextStyle((library.faces[0].family,), 18)),)
        )
    )
