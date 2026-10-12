"""Mechanical OpenType fsType policy; not legal advice."""

from __future__ import annotations

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity
from glyphkit.embedding.models import EmbeddingUse
from glyphkit.errors import EmbeddingRestrictedError
from glyphkit.fonts import EmbeddingPermission, FontFace


def check_embedding(
    face: FontFace, embedding_use: EmbeddingUse, *, allow_unknown: bool = False
) -> tuple[Diagnostic, ...]:
    permission = face.embedding
    if permission is EmbeddingPermission.RESTRICTED:
        raise EmbeddingRestrictedError(f"font {face.family!r} declares restricted embedding")
    if permission is EmbeddingPermission.UNKNOWN:
        if not allow_unknown:
            raise EmbeddingRestrictedError(f"font {face.family!r} has unknown embedding rights")
        return (
            Diagnostic(
                "embedding.unknown-permission-override",
                DiagnosticSeverity.WARNING,
                f"embedding permission for {face.family!r} was overridden by the caller",
            ),
        )
    if (
        permission is EmbeddingPermission.PREVIEW_PRINT
        and embedding_use is not EmbeddingUse.PREVIEW_PRINT
    ):
        raise EmbeddingRestrictedError(f"font {face.family!r} permits preview/print embedding only")
    return ()
