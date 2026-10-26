"""Math style, box types and the per-font MATH data."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from fontTools.ttLib import TTFont

from glyphkit.diagnostics import SourceRange
from glyphkit.errors import ConfigurationError
from glyphkit.fonts import FontFace
from glyphkit.geometry import Bounds
from glyphkit.layout import TextLayout

OVERRIDABLE_CONSTANTS = frozenset(
    {
        "AxisHeight",
        "FractionRuleThickness",
        "FractionNumeratorShiftUp",
        "FractionNumeratorDisplayStyleShiftUp",
        "FractionDenominatorShiftDown",
        "FractionDenominatorDisplayStyleShiftDown",
        "SubscriptShiftDown",
        "SuperscriptShiftUp",
        "LowerLimitBaselineDropMin",
        "UpperLimitBaselineRiseMin",
        "LowerLimitGapMin",
        "UpperLimitGapMin",
        "FractionNumeratorGapMin",
        "FractionNumDisplayStyleGapMin",
        "FractionDenominatorGapMin",
        "FractionDenomDisplayStyleGapMin",
        "SuperscriptBottomMin",
        "SubscriptTopMax",
        "SubSuperscriptGapMin",
        "SuperscriptBottomMaxWithSubscript",
        "SuperscriptBaselineDropMax",
        "SubscriptBaselineDropMin",
        "SpaceAfterScript",
        "DisplayOperatorMinHeight",
        "RadicalVerticalGap",
        "RadicalKernBeforeDegree",
        "RadicalKernAfterDegree",
        "OverbarRuleThickness",
        "UnderbarRuleThickness",
        "AccentBaseHeight",
        "RadicalRuleThickness",
        "OverbarVerticalGap",
        "UnderbarVerticalGap",
        "MatrixRowSpacing",
    }
)


LEVELS = ("display", "text", "script", "scriptscript")


@dataclass(frozen=True, slots=True)
class MathStyle:
    """Size, fonts and optional overrides for math layout.

    ``script_scale`` and ``script_script_scale`` replace the font's
    ``ScriptPercentScaleDown`` and ``ScriptScriptPercentScaleDown`` constants. Each is a
    fraction in ``(0, 1]`` of the enclosing size; ``None`` keeps the font's own value.

    ``constants`` replaces other OpenType MATH constants by their OpenType name (for
    example ``{"SuperscriptShiftUp": 0.4}``). Values are non-negative fractions of the
    font size (em), so they do not depend on the font's units per em. Use it for fonts whose
    MATH table is incomplete.

    ``level`` is the TeX style the expression starts in: ``"display"`` (fractions and limits
    at full size, big operators enlarged), ``"text"``, ``"script"`` or ``"scriptscript"``.

    ``letter_slant`` selects the face used for alphabetic symbols: ``"italic"`` or
    ``"oblique"`` picks the matching face of the same family (digits and operators stay
    upright), which suits fonts that lack the Unicode mathematical italic alphabet.
    """

    size: float
    families: tuple[str, ...]
    level: str = "display"
    script_scale: float | None = None
    script_script_scale: float | None = None
    constants: Mapping[str, float] = field(default_factory=dict, hash=False)
    letter_slant: str = "normal"

    def __post_init__(self) -> None:
        for name in ("script_scale", "script_script_scale"):
            value = getattr(self, name)
            if value is not None and not 0.0 < value <= 1.0:
                raise ConfigurationError(f"{name} must be a fraction in (0, 1], got {value!r}")
        for name, value in self.constants.items():
            if name not in OVERRIDABLE_CONSTANTS:
                raise ConfigurationError(f"unsupported math constant override {name!r}")
            if not math.isfinite(value) or value < 0.0:
                raise ConfigurationError(
                    f"math constant override {name} must be a finite non-negative em value"
                )
        if self.level not in LEVELS:
            raise ConfigurationError(
                f"level must be one of {', '.join(LEVELS)}, got {self.level!r}"
            )
        if self.letter_slant not in {"normal", "italic", "oblique"}:
            raise ConfigurationError("letter_slant must be normal, italic, or oblique")
        object.__setattr__(self, "constants", dict(self.constants))


@dataclass(frozen=True, slots=True)
class MathRule:
    start: tuple[float, float]
    end: tuple[float, float]
    thickness: float


@dataclass(frozen=True, slots=True)
class MathBox:
    """A semantic MATH box positioned relative to its parent baseline."""

    kind: str
    bounds: Bounds
    baseline: float
    text_layout: TextLayout | None = None
    children: tuple[MathBox, ...] = ()
    rules: tuple[MathRule, ...] = ()
    origin: tuple[float, float] = (0.0, 0.0)
    source_range: SourceRange | None = None
    glyph_id: int | None = None


@dataclass(slots=True)
class _MathData:
    font: TTFont
    face: FontFace
    scale: float  # font units to points at the current size
    display: bool
    size: float  # the current size
    overrides: Mapping[str, float]
    units_per_em: float = 1000.0
    base_size: float = 0.0  # the size of the whole expression, from which script sizes derive

    def at(self, size: float) -> _MathData:
        """The same font data for a box set at ``size``: constants scale with the box."""
        if size == self.size:
            return self
        return replace(self, scale=size / self.units_per_em, size=size)

    def value(self, name: str, fallback: float) -> float:
        if name in self.overrides:
            return self.overrides[name] * self.size
        constants = self.font["MATH"].table.MathConstants
        record = getattr(constants, name, None)
        raw = getattr(record, "Value", record)
        if raw is None:
            return fallback  # already in points
        return float(raw) * self.scale

    def percent(self, name: str, fallback: float) -> float:
        constants = self.font["MATH"].table.MathConstants
        return float(getattr(constants, name, fallback)) / 100.0

    def italic_correction(self, glyph_id: int | None) -> float:
        if glyph_id is None:
            return 0.0
        info = self.font["MATH"].table.MathGlyphInfo.MathItalicsCorrectionInfo
        if info is None or info.Coverage is None:
            return 0.0
        glyphs = info.Coverage.glyphs
        name = self.font.getGlyphOrder()[glyph_id]
        if name not in glyphs:
            return 0.0
        record = info.ItalicsCorrection[glyphs.index(name)]
        return float(record.Value) * self.scale

    def top_accent_attachment(self, glyph_id: int | None, fallback: float) -> float:
        if glyph_id is None:
            return fallback
        info = self.font["MATH"].table.MathGlyphInfo.MathTopAccentAttachment
        if info is None or info.TopAccentCoverage is None:
            return fallback
        glyphs = info.TopAccentCoverage.glyphs
        name = self.font.getGlyphOrder()[glyph_id]
        if name not in glyphs:
            return fallback
        return float(info.TopAccentAttachment[glyphs.index(name)].Value) * self.scale
