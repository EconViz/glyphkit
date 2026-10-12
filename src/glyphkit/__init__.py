"""Deterministic typography data without rendering ownership."""

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
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
from glyphkit.engine import FontLibrary
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
from glyphkit.sources import FontSource
from glyphkit.shaping import GlyphRun, PositionedGlyph, ShapingStyle, shape_text
from glyphkit.layout import Bounds, LineLayout, Paragraph, TextLayout, TextMeasurement, TextSpan, TextStyle
from glyphkit.unicode import TextCluster, TextDirection

__all__ = [
    "CapabilityUnavailableError",
    "Bounds",
    "ConfigurationError",
    "Diagnostic",
    "DiagnosticSeverity",
    "EmbeddingRestrictedError",
    "EmbeddingPermission",
    "FaceId",
    "FontFace",
    "FontLibrary",
    "FontManifest",
    "FontMatch",
    "FontFormatError",
    "FontNotFoundError",
    "FontMetrics",
    "FontQuery",
    "FontSource",
    "GlyphKitError",
    "GlyphRun",
    "LineLayout",
    "MathSyntaxError",
    "MissingGlyphError",
    "PositionedGlyph",
    "Paragraph",
    "ShapingStyle",
    "SourceRange",
    "TextCluster",
    "TextDirection",
    "TextLayout",
    "TextMeasurement",
    "TextSpan",
    "TextStyle",
    "UnsupportedFeatureError",
    "VariableAxis",
    "shape_text",
]

__version__ = "0.1.0.dev0"
