"""Caller-controlled font source declarations."""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedIOBase
from os import PathLike
from pathlib import Path
from typing import BinaryIO

from glyphkit.errors import ConfigurationError

MAX_FONT_BYTES = 128 * 1024 * 1024


def _check_size(data: bytes, *, label: str) -> bytes:
    if len(data) > MAX_FONT_BYTES:
        raise ConfigurationError(
            f"font source {label!r} exceeds the {MAX_FONT_BYTES} byte safety limit"
        )
    return data


@dataclass(frozen=True, slots=True)
class FontSource:
    """An explicit source; streams and mutable buffers are snapshotted immediately."""

    _kind: str
    _value: Path | bytes
    label: str

    @classmethod
    def path(cls, path: str | PathLike[str]) -> FontSource:
        value = Path(path).expanduser()
        return cls("path", value, str(value))

    @classmethod
    def bytes(cls, data: bytes | bytearray | memoryview, *, label: str) -> FontSource:
        if not label.strip():
            raise ConfigurationError("font source label must not be empty")
        return cls("bytes", _check_size(bytes(data), label=label), label)

    @classmethod
    def stream(cls, stream: BinaryIO | BufferedIOBase, *, label: str) -> FontSource:
        if not label.strip():
            raise ConfigurationError("font source label must not be empty")
        try:
            data = stream.read(MAX_FONT_BYTES + 1)
        except (OSError, ValueError) as exc:
            raise ConfigurationError(f"cannot read font stream {label!r}") from exc
        if not isinstance(data, bytes):
            raise ConfigurationError("font stream must return bytes")
        return cls("bytes", _check_size(data, label=label), label)
