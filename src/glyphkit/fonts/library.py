"""Immutable explicit font catalog and public facade."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType

from glyphkit.errors import ConfigurationError, FontNotFoundError
from glyphkit.fonts.match import match_face, normalized_family
from glyphkit.fonts.models import (
    FontFace,
    FontManifest,
    FontManifestEntry,
    FontMatch,
    FontQuery,
)
from glyphkit.fonts.parse import load_faces
from glyphkit.sources import FontSource


class FontLibrary:
    """A catalog whose matching result depends only on explicit inputs."""

    __slots__ = ("_faces", "_generic_families", "_strict")

    def __init__(
        self,
        faces: Iterable[FontFace],
        *,
        generic_families: Mapping[str, Iterable[str]] | None = None,
        strict: bool = True,
    ) -> None:
        self._faces = tuple(faces)
        if not self._faces:
            raise ConfigurationError("font library requires at least one face")
        aliases = {
            normalized_family(key): tuple(value) for key, value in (generic_families or {}).items()
        }
        if any(not values for values in aliases.values()):
            raise ConfigurationError("generic family aliases must not be empty")
        self._generic_families = MappingProxyType(aliases)
        self._strict = strict

    @classmethod
    def from_sources(
        cls,
        sources: Iterable[FontSource],
        *,
        generic_families: Mapping[str, Iterable[str]] | None = None,
        strict: bool = True,
    ) -> FontLibrary:
        faces = tuple(face for source in sources for face in load_faces(source))
        return cls(faces, generic_families=generic_families, strict=strict)

    @property
    def faces(self) -> tuple[FontFace, ...]:
        return self._faces

    def _expand_families(self, families: tuple[str, ...]) -> tuple[str, ...]:
        expanded: list[str] = []
        for family in families:
            alias = self._generic_families.get(normalized_family(family))
            expanded.extend(alias if alias is not None else (family,))
        return tuple(expanded)

    def match(self, query: FontQuery) -> FontMatch:
        expanded = FontQuery(
            self._expand_families(query.families),
            query.weight,
            query.width,
            query.slant,
            query.axes,
        )
        result = match_face(self._faces, expanded)
        if result is None:
            raise FontNotFoundError(f"no configured face matches {query.families!r}")
        return result

    def manifest(self) -> FontManifest:
        entries = tuple(
            FontManifestEntry(
                face.id, face.family, face.subfamily, face.weight, face.width, face.slant
            )
            for face in self._faces
        )
        return FontManifest(entries, tuple(sorted(self._generic_families.items())))
