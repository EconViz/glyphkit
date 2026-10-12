"""Immutable shaping inputs and results."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit._validation import finite, positive
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
    letter_spacing: float = 0.0
    word_spacing: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "size", positive(self.size, name="font size"))
        object.__setattr__(
            self, "letter_spacing", finite(self.letter_spacing, name="letter spacing")
        )
        object.__setattr__(self, "word_spacing", finite(self.word_spacing, name="word spacing"))


@dataclass(frozen=True, slots=True)
class GlyphExtents:
    """Glyph ink bounds in the run's logical coordinate system."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass(frozen=True, slots=True)
class PositionedGlyph:
    face_id: FaceId
    glyph_id: int
    cluster: SourceRange
    x: float
    y: float
    x_advance: float
    y_advance: float
    x_offset: float
    y_offset: float
    ink_bounds: GlyphExtents | None = None


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
    variation_coordinates: tuple[tuple[str, float], ...] = ()
    bidi_level: int = 0

    @property
    def advance(self) -> float:
        return sum(glyph.x_advance for glyph in self.glyphs)
