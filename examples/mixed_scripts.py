"""Return a mixed-script data layout with caller-configured fallback."""

from pathlib import Path

from glyphkit import FontLibrary, FontSource, Paragraph, TextLayout, TextSpan, TextStyle


def build_layout(latin_font: Path, traditional_chinese_font: Path, arabic_font: Path) -> TextLayout:
    library = FontLibrary.from_sources(
        (
            FontSource.path(latin_font),
            FontSource.path(traditional_chinese_font),
            FontSource.path(arabic_font),
        )
    )
    families = tuple(face.family for face in library.faces)
    return library.layout(
        Paragraph((TextSpan("效用 U(x) — المنفعة", TextStyle(families, 18)),), max_width=360)
    )
