from __future__ import annotations

from pathlib import Path

import pytest

from glyphkit import ConfigurationError, FontLibrary, FontSource
from glyphkit.fonts import FaceId, discover_system_fonts
from tests.helpers import make_test_font


class FakeProvider:
    def __init__(self, paths: tuple[Path, ...]) -> None:
        self.paths = paths
        self.by_id: dict[FaceId, FontSource] = {}

    def sources(self):
        return tuple(FontSource.path(path) for path in reversed(self.paths))

    def remember(self, face_id: FaceId, source: FontSource) -> None:
        self.by_id[face_id] = source

    def resolve(self, face_id: FaceId) -> FontSource:
        return self.by_id[face_id]


def test_discovery_is_explicit_sorted_and_restorable(tmp_path) -> None:
    zulu = tmp_path / "zulu.ttf"
    alpha = tmp_path / "alpha.ttf"
    zulu.write_bytes(make_test_font(family="Zulu"))
    alpha.write_bytes(make_test_font(family="Alpha"))
    provider = FakeProvider((zulu, alpha))
    manifest = discover_system_fonts(provider)
    assert tuple(entry.family for entry in manifest.faces) == ("Alpha", "Zulu")
    restored = FontLibrary.from_manifest(manifest, resolver=provider.resolve)
    assert tuple(face.family for face in restored.faces) == ("Alpha", "Zulu")


def test_manifest_restore_rejects_changed_bytes(tmp_path) -> None:
    path = tmp_path / "font.ttf"
    path.write_bytes(make_test_font(family="Before"))
    provider = FakeProvider((path,))
    manifest = discover_system_fonts(provider)
    path.write_bytes(make_test_font(family="After"))
    with pytest.raises(ConfigurationError, match="do not match"):
        FontLibrary.from_manifest(manifest, resolver=provider.resolve)
