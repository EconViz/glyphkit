"""Renderer-independent Unicode analysis values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from glyphkit.diagnostics import SourceRange


class TextDirection(str, Enum):
    LTR = "ltr"
    RTL = "rtl"


@dataclass(frozen=True, slots=True)
class TextCluster:
    text: str
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class BidiLevel:
    source_index: int
    level: int

    @property
    def direction(self) -> TextDirection:
        return TextDirection.RTL if self.level % 2 else TextDirection.LTR


@dataclass(frozen=True, slots=True)
class RunSegment:
    text: str
    source_range: SourceRange
    script: str
