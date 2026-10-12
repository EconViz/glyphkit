"""Caller-controlled font source declarations."""

from __future__ import annotations

from dataclasses import dataclass
from io import BufferedIOBase
from os import PathLike
from pathlib import Path
from typing import BinaryIO

from glyphkit.errors import ConfigurationError


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
        return cls("bytes", bytes(data), label)

    @classmethod
    def stream(cls, stream: BinaryIO | BufferedIOBase, *, label: str) -> FontSource:
        if not label.strip():
            raise ConfigurationError("font source label must not be empty")
        try:
            data = stream.read()
        except (OSError, ValueError) as exc:
            raise ConfigurationError(f"cannot read font stream {label!r}") from exc
        if not isinstance(data, bytes):
            raise ConfigurationError("font stream must return bytes")
        return cls("bytes", data, label)

