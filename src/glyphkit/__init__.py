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
from glyphkit.fonts import (
    EmbeddingPermission,
    FaceId,
    FontFace,
    FontLibrary,
    FontManifest,
    FontMatch,
    FontMetrics,
    FontQuery,
    VariableAxis,
)
from glyphkit.sources import FontSource

__all__ = [
    "CapabilityUnavailableError",
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
    "MathSyntaxError",
    "MissingGlyphError",
    "SourceRange",
    "UnsupportedFeatureError",
    "VariableAxis",
]

__version__ = "0.1.0.dev0"
