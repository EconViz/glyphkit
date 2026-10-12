"""Immutable public font values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from glyphkit.diagnostics import Diagnostic
from glyphkit.errors import ConfigurationError


class EmbeddingPermission(str, Enum):
    INSTALLABLE = "installable"
    EDITABLE = "editable"
    PREVIEW_PRINT = "preview-print"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True, order=True)
class FaceId:
    fingerprint: str
    index: int = 0


@dataclass(frozen=True, slots=True)
class VariableAxis:
    tag: str
    minimum: float
    default: float
    maximum: float
    name: str | None = None


@dataclass(frozen=True, slots=True)
class FontMetrics:
    units_per_em: int
    ascender: int
    descender: int
    line_gap: int


@dataclass(frozen=True, slots=True)
class FontFace:
    id: FaceId
    family: str
    subfamily: str
    full_name: str
    postscript_name: str | None
    weight: int
    width: int
    slant: str
    metrics: FontMetrics
    coverage: frozenset[int]
    axes: tuple[VariableAxis, ...]
    embedding: EmbeddingPermission
    has_math: bool
    names: Mapping[int, str]
    _data: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "names", MappingProxyType(dict(self.names)))

    @property
    def data(self) -> bytes:
        """Return immutable source bytes for internal adapters and explicit consumers."""
        return self._data


@dataclass(frozen=True, slots=True)
class FontQuery:
    families: tuple[str, ...]
    weight: int = 400
    width: int = 100
    slant: str = "normal"
    axes: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        families = tuple(value.strip() for value in self.families if value.strip())
        if not families:
            raise ConfigurationError("font query requires at least one family")
        if not 1 <= self.weight <= 1000:
            raise ConfigurationError("font weight must be between 1 and 1000")
        if not 25 <= self.width <= 200:
            raise ConfigurationError("font width must be between 25 and 200")
        if self.slant not in {"normal", "italic", "oblique"}:
            raise ConfigurationError("font slant must be normal, italic, or oblique")
        if len({tag for tag, _ in self.axes}) != len(self.axes):
            raise ConfigurationError("font query contains duplicate axes")
        object.__setattr__(self, "families", families)


@dataclass(frozen=True, slots=True)
class FontMatch:
    face: FontFace
    coordinates: tuple[tuple[str, float], ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class FontManifestEntry:
    face_id: FaceId
    family: str
    subfamily: str
    weight: int
    width: int
    slant: str


@dataclass(frozen=True, slots=True)
class FontManifest:
    faces: tuple[FontManifestEntry, ...]
    generic_families: tuple[tuple[str, tuple[str, ...]], ...]
    diagnostics: tuple[Diagnostic, ...] = ()
