"""Immutable diagnostic values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from glyphkit.errors import ConfigurationError


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SourceRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if isinstance(self.start, bool) or isinstance(self.end, bool):
            raise ConfigurationError("source range offsets must be integers")
        if self.start < 0 or self.end < self.start:
            raise ConfigurationError("source range must satisfy 0 <= start <= end")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: DiagnosticSeverity
    message: str
    source_range: SourceRange | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ConfigurationError("diagnostic code must not be empty")
        if not self.message.strip():
            raise ConfigurationError("diagnostic message must not be empty")

