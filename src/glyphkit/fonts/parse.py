"""Private FontTools adapter producing ordinary GlyphKit values."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from typing import cast

from fontTools.ttLib import TTCollection, TTFont, TTLibError

from glyphkit.errors import FontFormatError
from glyphkit.fonts.models import (
    EmbeddingPermission,
    FaceId,
    FontFace,
    FontMetrics,
    VariableAxis,
)
from glyphkit.sources import FontSource, snapshot_source


def _name(font: TTFont, name_id: int, fallback: str = "") -> str:
    table = font.get("name")
    if table is None:
        return fallback
    value = table.getDebugName(name_id)
    return value.strip() if value else fallback


def _all_names(font: TTFont) -> dict[int, str]:
    table = font.get("name")
    if table is None:
        return {}
    result: dict[int, str] = {}
    for record in table.names:
        if record.nameID not in result:
            try:
                result[record.nameID] = record.toUnicode()
            except UnicodeError:
                continue
    return result


def _permission(font: TTFont) -> EmbeddingPermission:
    os2 = font.get("OS/2")
    if os2 is None or not hasattr(os2, "fsType"):
        return EmbeddingPermission.UNKNOWN
    value = int(os2.fsType)
    if value & 0x0002:
        return EmbeddingPermission.RESTRICTED
    if value & 0x0008:
        return EmbeddingPermission.EDITABLE
    if value & 0x0004:
        return EmbeddingPermission.PREVIEW_PRINT
    return EmbeddingPermission.INSTALLABLE


def _slant(font: TTFont) -> str:
    os2 = font.get("OS/2")
    head = font.get("head")
    if os2 is not None and int(getattr(os2, "fsSelection", 0)) & 0x01:
        return "italic"
    if head is not None and int(getattr(head, "macStyle", 0)) & 0x02:
        return "italic"
    return "normal"


def _axes(font: TTFont) -> tuple[VariableAxis, ...]:
    fvar = font.get("fvar")
    if fvar is None:
        return ()
    return tuple(
        VariableAxis(
            axis.axisTag,
            float(axis.minValue),
            float(axis.defaultValue),
            float(axis.maxValue),
            _name(font, axis.axisNameID) or None,
        )
        for axis in fvar.axes
    )


def _font_face(font: TTFont, *, data: bytes, fingerprint: str, index: int) -> FontFace:
    head = font.get("head")
    hhea = font.get("hhea")
    if head is None or hhea is None:
        raise FontFormatError("font is missing required head or hhea tables")
    os2 = font.get("OS/2")
    best_cmap = font.getBestCmap() or {}
    return FontFace(
        id=FaceId(fingerprint, index),
        family=_name(font, 16) or _name(font, 1, "Unknown"),
        subfamily=_name(font, 17) or _name(font, 2, "Regular"),
        full_name=_name(font, 4) or _name(font, 1, "Unknown"),
        postscript_name=_name(font, 6) or None,
        weight=int(getattr(os2, "usWeightClass", 400)),
        width=int(getattr(os2, "usWidthClass", 5)) * 25,
        slant=_slant(font),
        metrics=FontMetrics(
            int(head.unitsPerEm),
            int(hhea.ascent),
            int(hhea.descent),
            int(hhea.lineGap),
        ),
        coverage=frozenset(best_cmap),
        axes=_axes(font),
        embedding=_permission(font),
        names=_all_names(font),
        _data=data,
    )


def _open_fonts(data: bytes) -> Iterable[TTFont]:
    if data[:4] == b"ttcf":
        return cast(Iterable[TTFont], TTCollection(BytesIO(data), lazy=False).fonts)
    return (TTFont(BytesIO(data), lazy=False, recalcBBoxes=False, recalcTimestamp=False),)


def load_faces(source: FontSource) -> tuple[FontFace, ...]:
    snapshot = snapshot_source(source)
    try:
        fonts = tuple(_open_fonts(snapshot.data))
        return tuple(
            _font_face(font, data=snapshot.data, fingerprint=snapshot.fingerprint, index=index)
            for index, font in enumerate(fonts)
        )
    except (TTLibError, KeyError, ValueError, OverflowError) as exc:
        raise FontFormatError(f"invalid font source: {snapshot.label}") from exc
    finally:
        for font in locals().get("fonts", ()):
            font.close()
