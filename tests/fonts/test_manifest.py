from glyphkit import FontLibrary, FontSource
from tests.helpers import make_test_font


def test_manifest_preserves_explicit_order_and_contains_no_paths(tmp_path) -> None:
    first = make_test_font(family="First")
    second = make_test_font(family="Second")
    path = tmp_path / "private-location.ttf"
    path.write_bytes(first)
    library = FontLibrary.from_sources(
        (FontSource.path(path), FontSource.bytes(second, label="second")),
        generic_families={"sans-serif": ("First", "Second")},
    )
    manifest = library.manifest()
    assert tuple(face.family for face in manifest.faces) == ("First", "Second")
    assert "private-location" not in repr(manifest)
