from glyphkit import FontSource
from glyphkit.fonts import EmbeddingPermission, load_faces
from tests.helpers import make_test_font


def test_loads_plain_metadata_without_leaking_fonttools_objects(tmp_path) -> None:
    data = make_test_font(family="Exact Family", weight=700)
    path = tmp_path / "font.ttf"
    path.write_bytes(data)
    from_path = load_faces(FontSource.path(path))[0]
    from_bytes = load_faces(FontSource.bytes(data, label="bytes"))[0]

    assert from_path.id == from_bytes.id
    assert from_path.family == "Exact Family"
    assert from_path.weight == 700
    assert from_path.coverage == frozenset({32, 65, 66})
    assert from_path.embedding is EmbeddingPermission.INSTALLABLE
    assert from_path.metrics.units_per_em == 1000
