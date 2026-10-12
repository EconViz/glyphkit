from io import BytesIO

import pytest

from glyphkit import ConfigurationError, FontFormatError, FontNotFoundError, FontSource
from glyphkit.sources import load as source_load
from glyphkit.sources import models as source_models
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


def test_source_size_limit_bounds_stream_and_path_ingestion(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(source_models, "MAX_FONT_BYTES", 4)
    monkeypatch.setattr(source_load, "MAX_FONT_BYTES", 4)
    with pytest.raises(ConfigurationError, match="safety limit"):
        FontSource.bytes(b"12345", label="oversized")
    path = tmp_path / "oversized.ttf"
    path.write_bytes(b"12345")
    with pytest.raises(FontFormatError, match="safety limit"):
        snapshot_source(FontSource.path(path))
