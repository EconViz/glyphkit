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
