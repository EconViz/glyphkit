"""Immutable portable-font payload values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from glyphkit.diagnostics import Diagnostic
from glyphkit.fonts import EmbeddingPermission, FaceId


class EmbeddingUse(str, Enum):
    EDITABLE = "editable"
    PREVIEW_PRINT = "preview-print"
    WEB = "web"


class FontContainer(str, Enum):
    SFNT = "sfnt"
    WOFF2 = "woff2"


@dataclass(frozen=True, slots=True)
class PortableFont:
    face_id: FaceId
    family: str
    subset_tag: str
    glyph_ids: tuple[int, ...]
    permission: EmbeddingPermission
    container: FontContainer
    mime_type: str
    data: bytes
    variation_coordinates: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True, slots=True)
class FontSubsetBundle:
    fonts: tuple[PortableFont, ...]
    diagnostics: tuple[Diagnostic, ...] = ()
