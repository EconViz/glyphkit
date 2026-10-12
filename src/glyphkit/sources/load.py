"""Source ingestion boundary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from glyphkit.errors import FontNotFoundError, FontFormatError
from glyphkit.sources.models import FontSource


@dataclass(frozen=True, slots=True)
class FontSnapshot:
    data: bytes
    fingerprint: str
    label: str


def snapshot_source(source: FontSource) -> FontSnapshot:
    if source._kind == "path":
        try:
            data = source._value.read_bytes()  # type: ignore[union-attr]
        except FileNotFoundError as exc:
            raise FontNotFoundError(f"font source not found: {source.label}") from exc
        except OSError as exc:
            raise FontNotFoundError(f"cannot read font source: {source.label}") from exc
    else:
        data = source._value  # type: ignore[assignment]
    if not data:
        raise FontFormatError(f"font source is empty: {source.label}")
    immutable = bytes(data)
    return FontSnapshot(immutable, hashlib.sha256(immutable).hexdigest(), source.label)

