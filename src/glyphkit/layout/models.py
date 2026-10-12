"""Immutable paragraph inputs and layout results."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit._validation import finite, non_negative, positive
from glyphkit.diagnostics import Diagnostic, SourceRange
from glyphkit.errors import ConfigurationError
from glyphkit.fonts import FaceId
from glyphkit.shaping import GlyphRun, ShapingStyle
from glyphkit.unicode import TextDirection


@dataclass(frozen=True, slots=True)
class Bounds:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        for name in ("x_min", "y_min", "x_max", "y_max"):
            object.__setattr__(self, name, finite(getattr(self, name), name=name))
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise ConfigurationError("bounds maxima must not be smaller than minima")

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
    direction: TextDirection | None = None
    letter_spacing: float = 0.0
    word_spacing: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "size", positive(self.size, name="font size"))
        object.__setattr__(
            self, "letter_spacing", finite(self.letter_spacing, name="letter spacing")
        )
        object.__setattr__(self, "word_spacing", finite(self.word_spacing, name="word spacing"))

    def shaping_style(self) -> ShapingStyle:
        return ShapingStyle(
            self.families,
            self.size,
            self.weight,
            self.width,
            self.slant,
            self.axes,
            self.features,
            self.letter_spacing,
            self.word_spacing,
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
    first_line_indent: float = 0.0
    hanging_indent: float = 0.0
    paragraph_spacing: float = 0.0
    tab_stops: tuple[float, ...] = ()
    default_tab_width: float | None = None

    def __post_init__(self) -> None:
        if not self.spans:
            raise ConfigurationError("paragraph requires at least one span")
        if self.max_width is not None:
            object.__setattr__(self, "max_width", positive(self.max_width, name="max width"))
        if self.max_height is not None:
            object.__setattr__(self, "max_height", non_negative(self.max_height, name="max height"))
        if self.line_height is not None:
            object.__setattr__(self, "line_height", positive(self.line_height, name="line height"))
        if self.align not in {"start", "center", "end", "justify"}:
            raise ConfigurationError("alignment must be start, center, end, or justify")
        for name in ("first_line_indent", "hanging_indent", "paragraph_spacing"):
            object.__setattr__(self, name, finite(getattr(self, name), name=name.replace("_", " ")))
        stops = tuple(positive(stop, name="tab stop") for stop in self.tab_stops)
        if tuple(sorted(set(stops))) != stops:
            raise ConfigurationError("tab stops must be strictly increasing")
        object.__setattr__(self, "tab_stops", stops)
        if self.default_tab_width is not None:
            object.__setattr__(
                self,
                "default_tab_width",
                positive(self.default_tab_width, name="default tab width"),
            )


@dataclass(frozen=True, slots=True)
class LineLayout:
    runs: tuple[GlyphRun, ...]
    baseline: float
    advance: float
    logical_bounds: Bounds
    ink_bounds: Bounds
    horizontal_overflow: float = 0.0
    source_range: SourceRange | None = None
    explicitly_terminated: bool = False
    reading_order: tuple[SourceRange, ...] = ()


@dataclass(frozen=True, slots=True)
class FontUse:
    face_id: FaceId
    source_ranges: tuple[SourceRange, ...]
    variation_coordinates: tuple[tuple[str, float], ...] = ()


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

    @property
    def font_uses(self) -> tuple[FontUse, ...]:
        grouped: dict[tuple[FaceId, tuple[tuple[str, float], ...]], list[SourceRange]] = {}
        for line in self.lines:
            for run in line.runs:
                key = (run.face_id, run.variation_coordinates)
                ranges = grouped.setdefault(key, [])
                for glyph in run.glyphs:
                    if glyph.cluster not in ranges:
                        ranges.append(glyph.cluster)
        return tuple(FontUse(face, tuple(ranges), axes) for (face, axes), ranges in grouped.items())
