"""Face selection, fallback grouping, and shaping coordination."""

from __future__ import annotations

import unicodedata

from glyphkit.diagnostics import SourceRange
from glyphkit.errors import MissingGlyphError
from glyphkit.fonts import FontFace, FontLibrary, FontQuery
from glyphkit.shaping.harfbuzz import shape_span
from glyphkit.shaping.models import GlyphRun, ShapingStyle
from glyphkit.unicode import TextCluster, TextDirection, graphemes, text_direction


def _is_coverage_character(character: str) -> bool:
    return unicodedata.category(character) not in {"Cc", "Cf"}


def _covers(face: FontFace, text: str) -> bool:
    return all(ord(char) in face.coverage for char in text if _is_coverage_character(char))


def _candidates(library: FontLibrary, style: ShapingStyle) -> tuple[FontFace, ...]:
    result: list[FontFace] = []
    for family in style.families:
        try:
            face = library.match(
                FontQuery((family,), style.weight, style.width, style.slant, style.axes)
            ).face
        except LookupError:
            continue
        if face.id not in {item.id for item in result}:
            result.append(face)
    return tuple(result)


def _assign_faces(
    clusters: tuple[TextCluster, ...], candidates: tuple[FontFace, ...], direction: TextDirection
) -> tuple[tuple[TextCluster, FontFace], ...]:
    whole_text = "".join(cluster.text for cluster in clusters)
    if direction is TextDirection.RTL:
        whole_face = next((face for face in candidates if _covers(face, whole_text)), None)
        if whole_face is None:
            raise MissingGlyphError("no single configured face covers the RTL shaping run")
        return tuple((cluster, whole_face) for cluster in clusters)
    assignments: list[tuple[TextCluster, FontFace]] = []
    for cluster in clusters:
        face = next((item for item in candidates if _covers(item, cluster.text)), None)
        if face is None:
            points = " ".join(f"U+{ord(char):04X}" for char in cluster.text)
            raise MissingGlyphError(f"no configured face covers {points}")
        assignments.append((cluster, face))
    return tuple(assignments)


def shape_text(
    library: FontLibrary,
    text: str,
    style: ShapingStyle,
    *,
    language: str | None = None,
    script: str | None = None,
    direction: TextDirection | None = None,
) -> tuple[GlyphRun, ...]:
    if not text:
        return ()
    resolved_direction = direction or text_direction(text)
    clusters = graphemes(text)
    candidates = _candidates(library, style)
    if not candidates:
        raise MissingGlyphError(f"none of the configured families exist: {style.families!r}")
    assigned = _assign_faces(clusters, candidates, resolved_direction)
    spans: list[tuple[FontFace, int, int, str]] = []
    for cluster, face in assigned:
        if spans and spans[-1][0].id == face.id and spans[-1][2] == cluster.source_range.start:
            old_face, start, _, old_text = spans[-1]
            spans[-1] = (old_face, start, cluster.source_range.end, old_text + cluster.text)
        else:
            spans.append((face, cluster.source_range.start, cluster.source_range.end, cluster.text))
    return tuple(
        shape_span(
            face,
            span_text,
            SourceRange(start, end),
            style,
            direction=resolved_direction,
            script=script,
            language=language,
        )
        for face, start, end, span_text in spans
    )

