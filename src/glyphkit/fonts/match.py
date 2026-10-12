"""Deterministic, explicit font matching policy."""

from __future__ import annotations

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity
from glyphkit.fonts.models import FontFace, FontMatch, FontQuery


def normalized_family(value: str) -> str:
    return " ".join(value.casefold().split())


def match_face(faces: tuple[FontFace, ...], query: FontQuery) -> FontMatch | None:
    family_order = {normalized_family(name): index for index, name in enumerate(query.families)}
    candidates: list[tuple[tuple[int, int, int, int], int, FontFace]] = []
    for source_order, face in enumerate(faces):
        family_index = family_order.get(normalized_family(face.family))
        if family_index is None:
            continue
        if query.axes and not face.axes:
            continue
        declared = {axis.tag: axis for axis in face.axes}
        if any(tag not in declared for tag, _ in query.axes):
            continue
        score = (
            family_index,
            0 if face.slant == query.slant else 1,
            abs(face.width - query.width),
            abs(face.weight - query.weight),
        )
        candidates.append((score, source_order, face))
    if not candidates:
        return None
    _, _, face = min(candidates, key=lambda item: (item[0], item[1]))
    declared = {axis.tag: axis for axis in face.axes}
    coordinates: list[tuple[str, float]] = []
    diagnostics: list[Diagnostic] = []
    for tag, requested in query.axes:
        axis = declared[tag]
        resolved = min(axis.maximum, max(axis.minimum, float(requested)))
        coordinates.append((tag, resolved))
        if resolved != requested:
            diagnostics.append(
                Diagnostic(
                    "font.axis-clamped",
                    DiagnosticSeverity.WARNING,
                    f"axis {tag} was clamped from {requested} to {resolved}",
                )
            )
    return FontMatch(face, tuple(coordinates), tuple(diagnostics))
