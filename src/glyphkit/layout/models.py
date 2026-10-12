"""Immutable paragraph inputs and layout results."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit._validation import non_negative, positive
from glyphkit.diagnostics import Diagnostic
from glyphkit.errors import ConfigurationError
from glyphkit.shaping import GlyphRun, ShapingStyle


@dataclass(frozen=True, slots=True)
class Bounds:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


@dataclass(frozen=True, slots=True)
class TextStyle:
    families: tuple[str, ...]
    size: float
    weight: int = 400
    width: int = 100
    slant: str = "normal"
    axes: tuple[tuple[str, float], ...] = ()
    features: tuple[tuple[str, int], ...] = ()
    language: str | None = None
    script: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "size", positive(self.size, name="font size"))

    def shaping_style(self) -> ShapingStyle:
        return ShapingStyle(
            self.families,
            self.size,
            self.weight,
            self.width,
            self.slant,
            self.axes,
            self.features,
        )


@dataclass(frozen=True, slots=True)
class TextSpan:
    text: str
    style: TextStyle
    semantic_role: str | None = None


@dataclass(frozen=True, slots=True)
class Paragraph:
    spans: tuple[TextSpan, ...]
    max_width: float | None = None
    max_height: float | None = None
    align: str = "start"
    line_height: float | None = None

    def __post_init__(self) -> None:
        if not self.spans:
            raise ConfigurationError("paragraph requires at least one span")
        if self.max_width is not None:
            object.__setattr__(self, "max_width", positive(self.max_width, name="max width"))
        if self.max_height is not None:
            object.__setattr__(self, "max_height", non_negative(self.max_height, name="max height"))
        if self.line_height is not None:
            object.__setattr__(self, "line_height", positive(self.line_height, name="line height"))
        if self.align not in {"start", "center", "end"}:
            raise ConfigurationError("alignment must be start, center, or end")


@dataclass(frozen=True, slots=True)
class LineLayout:
    runs: tuple[GlyphRun, ...]
    baseline: float
    advance: float
    logical_bounds: Bounds
    ink_bounds: Bounds
    horizontal_overflow: float = 0.0


@dataclass(frozen=True, slots=True)
class TextMeasurement:
    advance: float
    logical_bounds: Bounds
    ink_bounds: Bounds
    baselines: tuple[float, ...]
    horizontal_overflow: float
    vertical_overflow: float


@dataclass(frozen=True, slots=True)
class TextLayout:
    text: str
    lines: tuple[LineLayout, ...]
    logical_bounds: Bounds
    ink_bounds: Bounds
    diagnostics: tuple[Diagnostic, ...] = ()
    vertical_overflow: float = 0.0

    def measure(self) -> TextMeasurement:
        return TextMeasurement(
            max((line.advance for line in self.lines), default=0.0),
            self.logical_bounds,
            self.ink_bounds,
            tuple(line.baseline for line in self.lines),
            max((line.horizontal_overflow for line in self.lines), default=0.0),
            self.vertical_overflow,
        )
