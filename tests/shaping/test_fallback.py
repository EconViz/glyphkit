import pytest

from glyphkit import FontLibrary, FontSource, MissingGlyphError
from glyphkit.shaping import ShapingStyle, shape_text
from tests.helpers import make_test_font


def test_missing_cluster_is_never_silently_substituted() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Latin"), label="latin"),)
    )
    with pytest.raises(MissingGlyphError, match="U\\+4E2D"):
        shape_text(library, "A中", ShapingStyle(("Latin",), 12))
