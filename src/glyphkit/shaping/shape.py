"""Face selection, Unicode itemization, fallback, and shaping coordination."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from glyphkit.diagnostics import SourceRange
from glyphkit.errors import MissingGlyphError
from glyphkit.fonts import FontFace, FontLibrary, FontMatch, FontQuery
from glyphkit.shaping.harfbuzz import shape_span
from glyphkit.shaping.models import GlyphRun, ShapingStyle
from glyphkit.unicode import (
    TextCluster,
    TextDirection,
    graphemes,
    resolve_bidi_levels,
    script_runs,
)

_CONTEXTUAL_SCRIPTS = frozenset(
    {
        "Arab",
        "Beng",
        "Deva",
        "Gujr",
        "Guru",
        "Khmr",
        "Knda",
        "Laoo",
        "Mlym",
        "Mong",
        "Mymr",
        "Orya",
        "Sinh",
        "Syrc",
        "Taml",
        "Telu",
        "Thaa",
        "Thai",
    }
)


@dataclass(frozen=True, slots=True)
class _Item:
    text: str
    source_range: SourceRange
    script: str | None
    direction: TextDirection
    bidi_level: int


def _is_coverage_character(character: str) -> bool:
    return unicodedata.category(character) not in {"Cc", "Cf"}


def _covers(face: FontFace, text: str) -> bool:
    return all(ord(char) in face.coverage for char in text if _is_coverage_character(char))


def _candidates(library: FontLibrary, style: ShapingStyle) -> tuple[FontMatch, ...]:
    result: list[FontMatch] = []
    for family in style.families:
        try:
            match = library.match(
                FontQuery((family,), style.weight, style.width, style.slant, style.axes)
            )
        except LookupError:
            continue
        if match.face.id not in {item.face.id for item in result}:
            result.append(match)
    return tuple(result)


def _itemize(
    text: str,
    *,
    script: str | None,
    direction: TextDirection | None,
) -> tuple[_Item, ...]:
    if not text:
        return ()
    levels = resolve_bidi_levels(text, base_direction=direction)
    scripts = [script] * len(text)
    if script is None:
        for run in script_runs(text):
            scripts[run.source_range.start : run.source_range.end] = [run.script] * len(run.text)
    items: list[_Item] = []
    start = 0
    for index in range(1, len(text) + 1):
        split = index == len(text)
        if not split:
            split = scripts[index] != scripts[start] or levels[index].level != levels[start].level
        if split:
            level = levels[start].level
            resolved = TextDirection.RTL if level % 2 else TextDirection.LTR
            items.append(
                _Item(text[start:index], SourceRange(start, index), scripts[start], resolved, level)
            )
            start = index
    return tuple(items)


def _assign_faces(
    clusters: tuple[TextCluster, ...],
    candidates: tuple[FontMatch, ...],
    *,
    contextual: bool,
) -> tuple[tuple[TextCluster, FontMatch], ...]:
    whole_text = "".join(cluster.text for cluster in clusters)
    if contextual:
        whole_match = next((match for match in candidates if _covers(match.face, whole_text)), None)
        if whole_match is None:
            raise MissingGlyphError("no single configured face covers the contextual shaping run")
        return tuple((cluster, whole_match) for cluster in clusters)
    assignments: list[tuple[TextCluster, FontMatch]] = []
    for cluster in clusters:
        match = next((item for item in candidates if _covers(item.face, cluster.text)), None)
        if match is None:
            points = " ".join(f"U+{ord(char):04X}" for char in cluster.text)
            raise MissingGlyphError(f"no configured face covers {points}")
        assignments.append((cluster, match))
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
    """Shape logical Unicode text into backend-neutral, source-mapped glyph runs."""

    if not text:
        return ()
    candidates = _candidates(library, style)
    if not candidates:
        raise MissingGlyphError(f"none of the configured families exist: {style.families!r}")
    output: list[GlyphRun] = []
    for item in _itemize(text, script=script, direction=direction):
        assigned = _assign_faces(
            graphemes(item.text),
            candidates,
            contextual=(item.script in _CONTEXTUAL_SCRIPTS),
        )
        spans: list[tuple[FontMatch, int, int, str]] = []
        for cluster, match in assigned:
            if (
                spans
                and spans[-1][0].face.id == match.face.id
                and spans[-1][2] == cluster.source_range.start
            ):
                old_match, start, _, old_text = spans[-1]
                spans[-1] = (old_match, start, cluster.source_range.end, old_text + cluster.text)
            else:
                spans.append(
                    (match, cluster.source_range.start, cluster.source_range.end, cluster.text)
                )
        for match, start, end, span_text in spans:
            absolute = SourceRange(
                item.source_range.start + start,
                item.source_range.start + end,
            )
            output.append(
                shape_span(
                    match.face,
                    span_text,
                    absolute,
                    style,
                    direction=item.direction,
                    script=item.script,
                    language=language,
                    coordinates=match.coordinates,
                    bidi_level=item.bidi_level,
                )
            )
    return tuple(output)
