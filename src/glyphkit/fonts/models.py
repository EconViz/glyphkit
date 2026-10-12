"""Immutable public font values."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


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
    names: Mapping[int, str]
    _data: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "names", MappingProxyType(dict(self.names)))

    @property
    def data(self) -> bytes:
        """Return immutable source bytes for internal adapters and explicit consumers."""
        return self._data

