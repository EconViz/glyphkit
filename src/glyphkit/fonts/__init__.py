"""Font metadata, catalogs, deterministic matching, and manifests."""

from glyphkit.fonts.models import (
    EmbeddingPermission,
    FaceId,
    FontFace,
    FontMetrics,
    VariableAxis,
)
from glyphkit.fonts.parse import load_faces

__all__ = [
    "EmbeddingPermission",
    "FaceId",
    "FontFace",
    "FontMetrics",
    "VariableAxis",
    "load_faces",
]
