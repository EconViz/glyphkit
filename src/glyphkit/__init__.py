"""Deterministic typography data without rendering ownership."""

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
from glyphkit.engine import FontLibrary
from glyphkit.errors import (
    CapabilityUnavailableError,
    ConfigurationError,
    EmbeddingRestrictedError,
    FontFormatError,
    FontNotFoundError,
    GlyphKitError,
    MathSyntaxError,
    MissingGlyphError,
    UnsupportedFeatureError,
)
from glyphkit.fonts import (
    EmbeddingPermission,
    FaceId,
    FontFace,
    FontManifest,
    FontMatch,
    FontMetrics,
    FontQuery,
    VariableAxis,
)
from glyphkit.layout import (
    Bounds,
    FontUse,
    LineLayout,
    Paragraph,
    TextLayout,
    TextMeasurement,
    TextSpan,
    TextStyle,
)
from glyphkit.protocols import TypographyEngine
from glyphkit.serialization import from_data, to_data
from glyphkit.shaping import GlyphExtents, GlyphRun, PositionedGlyph, ShapingStyle, shape_text
from glyphkit.sources import FontSource
from glyphkit.unicode import TextCluster, TextDirection

__all__ = [
    "Bounds",
    "CapabilityUnavailableError",
    "ConfigurationError",
    "Diagnostic",
    "DiagnosticSeverity",
    "EmbeddingPermission",
    "EmbeddingRestrictedError",
    "FaceId",
    "FontFace",
    "FontFormatError",
    "FontLibrary",
    "FontManifest",
    "FontMatch",
    "FontMetrics",
    "FontNotFoundError",
    "FontQuery",
    "FontSource",
    "FontUse",
    "GlyphExtents",
    "GlyphKitError",
    "GlyphRun",
    "LineLayout",
    "MathSyntaxError",
    "MissingGlyphError",
    "Paragraph",
    "PositionedGlyph",
    "ShapingStyle",
    "SourceRange",
    "TextCluster",
    "TextDirection",
    "TextLayout",
    "TextMeasurement",
    "TextSpan",
    "TextStyle",
    "TypographyEngine",
    "UnsupportedFeatureError",
    "VariableAxis",
    "from_data",
    "shape_text",
    "to_data",
]

__version__ = "1.0.0b2"
