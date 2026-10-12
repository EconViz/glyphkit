from concurrent.futures import ThreadPoolExecutor

from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from tests.helpers import make_test_font


def test_built_library_supports_deterministic_concurrent_reads() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Concurrent"), label="concurrent"),)
    )
    paragraph = Paragraph((TextSpan("AB", TextStyle(("Concurrent",), 18)),))
    with ThreadPoolExecutor(max_workers=8) as executor:
        layouts = tuple(executor.map(lambda _: library.layout(paragraph), range(64)))
    assert all(layout == layouts[0] for layout in layouts)
