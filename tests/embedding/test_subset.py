import importlib.util

import pytest
from fontTools.ttLib import TTFont

from glyphkit import (
    CapabilityUnavailableError,
    FontLibrary,
    FontSource,
    Paragraph,
    TextSpan,
    TextStyle,
)
from glyphkit.embedding import EmbeddingUse, FontContainer
from tests.helpers import make_test_font


def test_subset_is_deterministic_and_contains_only_used_glyph_closure(tmp_path) -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Portable"), label="portable"),)
    )
    layout = library.layout(Paragraph((TextSpan("A", TextStyle(("Portable",), 18)),)))
    first = library.subset(layout, embedding_use=EmbeddingUse.WEB)
    second = library.subset(layout, embedding_use=EmbeddingUse.WEB)
    assert first == second
    assert first.fonts[0].glyph_ids == (0, 2)
    path = tmp_path / "subset.ttf"
    path.write_bytes(first.fonts[0].data)
    assert TTFont(path).getGlyphOrder() == [".notdef", "A"]


def test_woff2_is_a_capability_named_output() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Portable"), label="portable"),)
    )
    layout = library.layout(Paragraph((TextSpan("A", TextStyle(("Portable",), 18)),)))
    if importlib.util.find_spec("brotli") is None:
        with pytest.raises(CapabilityUnavailableError):
            library.subset(layout, embedding_use=EmbeddingUse.WEB, container=FontContainer.WOFF2)
        return
    bundle = library.subset(layout, embedding_use=EmbeddingUse.WEB, container=FontContainer.WOFF2)
    assert bundle.fonts[0].mime_type == "font/woff2"
    assert bundle.fonts[0].data[:4] == b"wOF2"
