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
from glyphkit.fonts import EmbeddingPermission, FaceId, FontFace, FontMetrics, VariableAxis
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
    "FontFormatError",
    "FontNotFoundError",
    "FontMetrics",
    "FontSource",
    "GlyphKitError",
    "MathSyntaxError",
    "MissingGlyphError",
    "SourceRange",
    "UnsupportedFeatureError",
    "VariableAxis",
]

__version__ = "0.1.0.dev0"
