"""Deterministic FontTools subsetting adapter returning bytes only."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from io import BytesIO

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

from glyphkit.diagnostics import Diagnostic
from glyphkit.embedding.models import (
    EmbeddingUse,
    FontContainer,
    FontSubsetBundle,
    PortableFont,
)
from glyphkit.embedding.permissions import check_embedding
from glyphkit.errors import CapabilityUnavailableError, FontFormatError
from glyphkit.fonts import FaceId, FontLibrary
from glyphkit.layout import TextLayout


def _tag(face_id: FaceId, glyph_ids: tuple[int, ...]) -> str:
    material = f"{face_id.fingerprint}:{face_id.index}:{','.join(map(str, glyph_ids))}".encode()
    digest = hashlib.sha256(material).digest()
    return "".join(chr(65 + value % 26) for value in digest[:6])


def _subset_bytes(
    face_data: bytes, face_index: int, glyph_ids: tuple[int, ...], container: FontContainer
) -> bytes:
    if container is FontContainer.WOFF2:
        try:
            import brotli  # noqa: F401
        except ImportError as exc:
            raise CapabilityUnavailableError(
                "WOFF2 output requires the portable installation profile"
            ) from exc
    try:
        font = TTFont(BytesIO(face_data), fontNumber=face_index, recalcTimestamp=False)
        options = Options()
        options.recalc_timestamp = False
        options.canonical_order = True
        options.notdef_glyph = True
        options.notdef_outline = True
        options.recommended_glyphs = False
        subsetter = Subsetter(options=options)
        subsetter.populate(gids=list(glyph_ids))
        subsetter.subset(font)
        if "head" in font:
            font["head"].modified = 0
            font["head"].created = 0
        font.flavor = "woff2" if container is FontContainer.WOFF2 else None
        stream = BytesIO()
        font.save(stream, reorderTables=True)
        return stream.getvalue()
    except (KeyError, ValueError) as exc:
        raise FontFormatError("font subsetting failed") from exc
    finally:
        if "font" in locals():
            font.close()


def subset_layout(
    library: FontLibrary,
    layout: TextLayout,
    *,
    embedding_use: EmbeddingUse,
    container: FontContainer = FontContainer.SFNT,
    allow_unknown: bool = False,
) -> FontSubsetBundle:
    used: dict[FaceId, set[int]] = defaultdict(set)
    for line in layout.lines:
        for run in line.runs:
            used[run.face_id].update(glyph.glyph_id for glyph in run.glyphs)
    fonts: list[PortableFont] = []
    diagnostics: list[Diagnostic] = []
    for face_id in sorted(used):
        face = library.face(face_id)
        diagnostics.extend(check_embedding(face, embedding_use, allow_unknown=allow_unknown))
        glyph_ids = tuple(sorted(used[face_id] | {0}))
        tag = _tag(face_id, glyph_ids)
        data = _subset_bytes(face.data, face.id.index, glyph_ids, container)
        fonts.append(
            PortableFont(
                face.id,
                face.family,
                tag,
                glyph_ids,
                face.embedding,
                container,
                "font/woff2" if container is FontContainer.WOFF2 else "font/sfnt",
                data,
            )
        )
    return FontSubsetBundle(tuple(fonts), tuple(diagnostics))
