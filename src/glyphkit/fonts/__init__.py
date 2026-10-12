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
    "VariableAxis",
    "load_faces",
]
