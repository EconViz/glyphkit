"""Font metadata, catalogs, deterministic matching, and manifests."""

from glyphkit.fonts.library import FontLibrary
from glyphkit.fonts.models import (
    EmbeddingPermission,
    FaceId,
    FontFace,
    FontManifest,
    FontManifestEntry,
    FontMatch,
    FontMetrics,
    FontQuery,
    VariableAxis,
)
from glyphkit.fonts.parse import load_faces
from glyphkit.fonts.system import PlatformFontProvider, SystemFontProvider, discover_system_fonts

__all__ = [
    "EmbeddingPermission",
    "FaceId",
    "FontFace",
    "FontLibrary",
    "FontManifest",
    "FontManifestEntry",
    "FontMatch",
    "FontMetrics",
    "FontQuery",
    "PlatformFontProvider",
    "SystemFontProvider",
    "VariableAxis",
    "discover_system_fonts",
    "load_faces",
]
