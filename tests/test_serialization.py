import json

import pytest

from glyphkit import ConfigurationError, FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from glyphkit.serialization import from_data, to_data
from tests.helpers import make_test_font


def test_layout_round_trips_through_json_ordinary_data() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Wire"), label="wire"),)
    )
    layout = library.layout(Paragraph((TextSpan("AB", TextStyle(("Wire",), 18)),)))
    encoded = to_data(layout)
    decoded = from_data("TextLayout", json.loads(json.dumps(encoded)))
    assert decoded == layout


def test_unknown_schema_major_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="schema"):
        from_data("SourceRange", {"schema_version": "2.0", "kind": "SourceRange", "value": {}})
