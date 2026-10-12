import pytest

from glyphkit import FontLibrary, FontSource, MissingGlyphError
from glyphkit.shaping import ShapingStyle, shape_text
from tests.helpers import make_test_font


def test_arabic_contextual_run_is_not_spliced_between_fonts() -> None:
    library = FontLibrary.from_sources(
        (
            FontSource.bytes(
                make_test_font(family="Arabic One", extra_codepoints=(0x0627,)), label="one"
            ),
            FontSource.bytes(
                make_test_font(family="Arabic Two", extra_codepoints=(0x0628,)), label="two"
            ),
        )
    )
    with pytest.raises(MissingGlyphError, match="contextual shaping run"):
        shape_text(library, "اب", ShapingStyle(("Arabic One", "Arabic Two"), 16))
