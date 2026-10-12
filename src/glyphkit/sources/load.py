"""Source ingestion boundary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from glyphkit.errors import FontFormatError, FontNotFoundError
from glyphkit.sources.models import MAX_FONT_BYTES, FontSource


@dataclass(frozen=True, slots=True)
class FontSnapshot:
    data: bytes
    fingerprint: str
    label: str


def snapshot_source(source: FontSource) -> FontSnapshot:
    if source._kind == "path":
        try:
            value = source._value
            if not isinstance(value, Path):
                raise FontNotFoundError(f"invalid path source: {source.label}")
            data = value.read_bytes()
        except FileNotFoundError as exc:
            raise FontNotFoundError(f"font source not found: {source.label}") from exc
        except OSError as exc:
            raise FontNotFoundError(f"cannot read font source: {source.label}") from exc
    else:
        value = source._value
        if not isinstance(value, bytes):
            raise FontFormatError(f"invalid byte source: {source.label}")
        data = value
    if not data:
        raise FontFormatError(f"font source is empty: {source.label}")
    if len(data) > MAX_FONT_BYTES:
        raise FontFormatError(
            f"font source {source.label!r} exceeds the {MAX_FONT_BYTES} byte safety limit"
        )
    immutable = bytes(data)
    return FontSnapshot(immutable, hashlib.sha256(immutable).hexdigest(), source.label)
