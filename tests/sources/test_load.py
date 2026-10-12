from io import BytesIO

import pytest

from glyphkit import FontFormatError, FontNotFoundError, FontSource
from glyphkit.sources import snapshot_source
from tests.helpers import make_test_font


def test_mutable_bytes_and_streams_are_snapshotted() -> None:
    original = bytearray(make_test_font())
    source = FontSource.bytes(original, label="memory")
    original[:] = b"changed"
    assert snapshot_source(source).data[:4] != b"chan"

    stream = BytesIO(make_test_font())
    streamed = FontSource.stream(stream, label="stream")
    stream.seek(0)
    stream.write(b"changed")
    assert snapshot_source(streamed).data[:4] != b"chan"


def test_missing_and_empty_sources_raise_structured_errors(tmp_path) -> None:
    with pytest.raises(FontNotFoundError):
        snapshot_source(FontSource.path(tmp_path / "missing.ttf"))
    with pytest.raises(FontFormatError):
        snapshot_source(FontSource.bytes(b"", label="empty"))

