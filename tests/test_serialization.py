import json

import pytest

from glyphkit import ConfigurationError, FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from glyphkit.layout import FontUse
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


def test_same_major_additive_fields_are_ignored_but_invalid_payloads_are_rejected() -> None:
    encoded = to_data(FontUse(library_face_id(), ()))
    value = encoded["value"]
    assert isinstance(value, dict)
    value["future_field"] = {"safe": True}
    restored = from_data("FontUse", encoded)
    assert isinstance(restored, FontUse)
    with pytest.raises(ConfigurationError, match="base64"):
        from_data(
            "SourceRange",
            {
                "schema_version": "1.0",
                "kind": "SourceRange",
                "value": {"$bytes": "not base64"},
            },
        )


def library_face_id():
    return (
        FontLibrary.from_sources((FontSource.bytes(make_test_font(family="Data"), label="data"),))
        .faces[0]
        .id
    )
