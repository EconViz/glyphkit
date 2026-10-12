"""Public, backend-neutral exception hierarchy."""


class GlyphKitError(Exception):
    """Base class for every expected GlyphKit failure."""


class ConfigurationError(GlyphKitError, ValueError):
    """Raised when caller configuration is invalid or contradictory."""


class FontNotFoundError(GlyphKitError, LookupError):
    """Raised when an explicitly requested font cannot be resolved."""


class FontFormatError(GlyphKitError, ValueError):
    """Raised when supplied font bytes are malformed or unsupported."""


class MissingGlyphError(GlyphKitError, LookupError):
    """Raised when no configured face covers required text."""


class UnsupportedFeatureError(GlyphKitError):
    """Raised for a valid request outside the implemented contract."""


class CapabilityUnavailableError(GlyphKitError):
    """Raised when an optional capability was not installed."""


class EmbeddingRestrictedError(GlyphKitError, PermissionError):
    """Raised when declared font permissions forbid embedding."""


class MathSyntaxError(GlyphKitError, ValueError):
    """Raised for unsupported or malformed structured math input."""

