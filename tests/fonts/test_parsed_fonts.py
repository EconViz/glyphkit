"""Fonts are parsed once and shared, and outlines are those of a freshly parsed font."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from fontTools.ttLib import TTFont

from glyphkit import FontLibrary, FontSource
from glyphkit.fonts import parsed
from glyphkit.fonts.parsed import clear_parsed_fonts, parsed_font
from glyphkit.outlines import extract_outline
from tests.helpers import make_test_font


def library(family: str, **kwargs) -> FontLibrary:
    return FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family=family, **kwargs), label=family),)
    )


@pytest.fixture(autouse=True)
def fresh_cache():
    clear_parsed_fonts()
    yield
    clear_parsed_fonts()


def test_a_face_is_parsed_once(monkeypatch: pytest.MonkeyPatch) -> None:
    face = library("Once").faces[0]
    opened = []
    real = parsed.TTFont
    monkeypatch.setattr(parsed, "TTFont", lambda *a, **k: opened.append(1) or real(*a, **k))
    for glyph in (1, 2, 2, 1, 2):
        extract_outline(face, glyph)
    assert len(opened) == 1


def test_the_same_font_bytes_share_one_parse() -> None:
    first, second = library("Shared").faces[0], library("Shared").faces[0]
    with parsed_font(first) as a, parsed_font(second) as b:
        assert a is b


def test_different_fonts_do_not_share() -> None:
    with parsed_font(library("A").faces[0]) as a, parsed_font(library("B").faces[0]) as b:
        assert a is not b


def test_outlines_equal_those_of_a_freshly_parsed_font() -> None:
    face = library("Fresh", extra_codepoints=(0x41, 0x42)).faces[0]
    fresh = TTFont(BytesIO(face.data), fontNumber=face.id.index, lazy=False)
    try:
        for glyph_id in range(len(fresh.getGlyphOrder())):
            cached = extract_outline(face, glyph_id)
            again = extract_outline(face, glyph_id)
            assert cached == again
            clear_parsed_fonts()
            assert cached == extract_outline(face, glyph_id)
    finally:
        fresh.close()


def test_the_cache_is_bounded_and_closes_what_it_drops(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parsed, "_LIMIT", 2)
    faces = [library(f"F{i}").faces[0] for i in range(4)]
    for face in faces:
        with parsed_font(face):
            pass
    assert len(parsed._fonts) == 2


def test_concurrent_extraction_is_deterministic() -> None:
    face = library("Threads").faces[0]
    expected = extract_outline(face, 2)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: extract_outline(face, 2), range(200)))
    assert all(result == expected for result in results)


def test_an_unknown_glyph_still_raises() -> None:
    from glyphkit.errors import FontFormatError

    with pytest.raises(FontFormatError):
        extract_outline(library("Bad").faces[0], 10_000)
