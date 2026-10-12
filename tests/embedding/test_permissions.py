from dataclasses import replace

import pytest

from glyphkit import EmbeddingRestrictedError, FontLibrary, FontSource
from glyphkit.embedding import EmbeddingUse, check_embedding
from glyphkit.fonts import EmbeddingPermission
from tests.helpers import make_test_font


def face():
    return FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Rights"), label="rights"),)
    ).faces[0]


def test_restricted_and_unknown_rights_refuse_bytes_by_default() -> None:
    with pytest.raises(EmbeddingRestrictedError):
        check_embedding(replace(face(), embedding=EmbeddingPermission.RESTRICTED), EmbeddingUse.WEB)
    with pytest.raises(EmbeddingRestrictedError):
        check_embedding(replace(face(), embedding=EmbeddingPermission.UNKNOWN), EmbeddingUse.WEB)


def test_unknown_rights_require_a_recorded_override() -> None:
    diagnostics = check_embedding(
        replace(face(), embedding=EmbeddingPermission.UNKNOWN),
        EmbeddingUse.WEB,
        allow_unknown=True,
    )
    assert diagnostics[0].code == "embedding.unknown-permission-override"
