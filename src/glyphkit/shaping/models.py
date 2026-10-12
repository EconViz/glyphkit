"""Immutable shaping inputs and results."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit._validation import positive
from glyphkit.diagnostics import Diagnostic, SourceRange
from glyphkit.fonts import FaceId
from glyphkit.unicode import TextDirection


@dataclass(frozen=True, slots=True)
class ShapingStyle:
    families: tuple[str, ...]
    size: float
    weight: int = 400
    width: int = 100
    slant: str = "normal"
    axes: tuple[tuple[str, float], ...] = ()
    features: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "size", positive(self.size, name="font size"))


@dataclass(frozen=True, slots=True)
class PositionedGlyph:
    glyph_id: int
    cluster: SourceRange
    x: float
    y: float
    x_advance: float
    y_advance: float
    x_offset: float
    y_offset: float


@dataclass(frozen=True, slots=True)
class GlyphRun:
    face_id: FaceId
    family: str
    size: float
    direction: TextDirection
    script: str | None
    language: str | None
    source_range: SourceRange
    text: str
    glyphs: tuple[PositionedGlyph, ...]
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def advance(self) -> float:
        return sum(glyph.x_advance for glyph in self.glyphs)

