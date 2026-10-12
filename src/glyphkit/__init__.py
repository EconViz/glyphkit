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

__all__ = [
    "CapabilityUnavailableError",
    "ConfigurationError",
    "Diagnostic",
    "DiagnosticSeverity",
    "EmbeddingRestrictedError",
    "FontFormatError",
    "FontNotFoundError",
    "GlyphKitError",
    "MathSyntaxError",
    "MissingGlyphError",
    "SourceRange",
    "UnsupportedFeatureError",
]

__version__ = "0.1.0.dev0"

