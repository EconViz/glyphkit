"""Opt-in system discovery isolated from ordinary catalog construction."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity
from glyphkit.errors import GlyphKitError
from glyphkit.fonts.models import FaceId, FontManifest, FontManifestEntry
from glyphkit.fonts.parse import load_faces
from glyphkit.sources import FontSource


class SystemFontProvider(Protocol):
    def sources(self) -> Iterable[FontSource]: ...

    def resolve(self, face_id: FaceId) -> FontSource: ...


class PlatformFontProvider:
    """Filesystem-only platform adapter with deterministic candidate ordering."""

    __slots__ = ("_resolved",)

    def __init__(self) -> None:
        self._resolved: dict[FaceId, FontSource] = {}

    def _roots(self) -> tuple[Path, ...]:
        home = Path.home()
        if sys.platform == "darwin":
            return (Path("/System/Library/Fonts"), Path("/Library/Fonts"), home / "Library/Fonts")
        if sys.platform == "win32":
            return (Path(Path.home().anchor) / "Windows/Fonts",)
        return (
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            home / ".local/share/fonts",
        )

    def sources(self) -> Iterable[FontSource]:
        suffixes = {".ttf", ".otf", ".ttc", ".otc"}
        paths = sorted(
            path
            for root in self._roots()
            if root.exists()
            for path in root.rglob("*")
            if path.is_file() and path.suffix.casefold() in suffixes
        )
        return tuple(FontSource.path(path) for path in paths)

    def remember(self, face_id: FaceId, source: FontSource) -> None:
        self._resolved[face_id] = source

    def resolve(self, face_id: FaceId) -> FontSource:
        return self._resolved[face_id]


def discover_system_fonts(provider: SystemFontProvider | None = None) -> FontManifest:
    selected = provider or PlatformFontProvider()
    entries: list[FontManifestEntry] = []
    diagnostics: list[Diagnostic] = []
    for source in selected.sources():
        try:
            faces = load_faces(source)
        except GlyphKitError as exc:
            diagnostics.append(
                Diagnostic(
                    "discovery.unreadable-font",
                    DiagnosticSeverity.WARNING,
                    f"font candidate could not be loaded: {type(exc).__name__}",
                )
            )
            continue
        for face in faces:
            entries.append(
                FontManifestEntry(
                    face.id, face.family, face.subfamily, face.weight, face.width, face.slant
                )
            )
            remember = getattr(selected, "remember", None)
            if remember is not None:
                remember(face.id, source)
    entries.sort(key=lambda item: (item.family.casefold(), item.subfamily.casefold(), item.face_id))
    return FontManifest(tuple(entries), (), tuple(diagnostics))
