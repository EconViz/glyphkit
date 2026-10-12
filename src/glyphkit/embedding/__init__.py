"""Permission-aware portable font assets."""

from glyphkit.embedding.models import (
    EmbeddingUse,
    FontContainer,
    FontSubsetBundle,
    PortableFont,
)
from glyphkit.embedding.permissions import check_embedding
from glyphkit.embedding.subset import subset_layout

__all__ = [
    "EmbeddingUse",
    "FontContainer",
    "FontSubsetBundle",
    "PortableFont",
    "check_embedding",
    "subset_layout",
]
