"""Private uharfbuzz adapter."""

from __future__ import annotations

import uharfbuzz as hb

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontFace
from glyphkit.shaping.models import GlyphExtents, GlyphRun, PositionedGlyph, ShapingStyle
from glyphkit.unicode import TextDirection


def shape_span(
    face: FontFace,
    text: str,
    source_range: SourceRange,
    style: ShapingStyle,
    *,
    direction: TextDirection,
    script: str | None,
    language: str | None,
    coordinates: tuple[tuple[str, float], ...] = (),
    bidi_level: int = 0,
) -> GlyphRun:
    hb_face = hb.Face(face.data, face.id.index)
    hb_font = hb.Font(hb_face)
    hb.ot_font_set_funcs(hb_font)
    upem = face.metrics.units_per_em
    hb_font.scale = (upem, upem)
    if coordinates:
        hb_font.set_variations(dict(coordinates))
    buffer = hb.Buffer()
    buffer.add_codepoints([ord(character) for character in text])
    buffer.direction = direction.value
    if script:
        buffer.script = script
    if language:
        buffer.language = language
    buffer.guess_segment_properties()
    hb.shape(hb_font, buffer, dict(style.features))
    scale = style.size / upem
    pen_x = 0.0
    pen_y = 0.0
    glyphs: list[PositionedGlyph] = []
    cluster_starts = sorted({min(info.cluster, len(text)) for info in buffer.glyph_infos})
    cluster_ends = {
        start: (cluster_starts[index + 1] if index + 1 < len(cluster_starts) else len(text))
        for index, start in enumerate(cluster_starts)
    }
    for info, position in zip(buffer.glyph_infos, buffer.glyph_positions, strict=True):
        local_start = min(info.cluster, len(text))
        cluster_start = source_range.start + local_start
        cluster_end = source_range.start + cluster_ends.get(local_start, len(text))
        x_advance = position.x_advance * scale
        y_advance = position.y_advance * scale
        extents = hb_font.get_glyph_extents(info.codepoint)
        ink_bounds = None
        if extents is not None:
            x_min = (pen_x + position.x_offset + extents.x_bearing) * scale
            y_max = (pen_y + position.y_offset + extents.y_bearing) * scale
            ink_bounds = GlyphExtents(
                x_min,
                y_max + extents.height * scale,
                x_min + extents.width * scale,
                y_max,
            )
        glyphs.append(
            PositionedGlyph(
                face.id,
                info.codepoint,
                SourceRange(cluster_start, cluster_end),
                pen_x + position.x_offset * scale,
                pen_y + position.y_offset * scale,
                x_advance,
                y_advance,
                position.x_offset * scale,
                position.y_offset * scale,
                ink_bounds,
            )
        )
        pen_x += x_advance
        pen_y += y_advance
    # Apply tracking once per source cluster, never between glyphs inside a ligature.
    if glyphs:
        last_for_cluster: dict[SourceRange, int] = {}
        for index, glyph in enumerate(glyphs):
            last_for_cluster[glyph.cluster] = index
        ordered_clusters = sorted(last_for_cluster, key=lambda item: item.start)
        for cluster_index, cluster in enumerate(ordered_clusters):
            extra = 0.0
            if cluster_index + 1 < len(ordered_clusters):
                extra += style.letter_spacing
            local_text = text[cluster.start - source_range.start : cluster.end - source_range.start]
            if local_text.isspace():
                extra += style.word_spacing
            index = last_for_cluster[cluster]
            glyph = glyphs[index]
            glyphs[index] = PositionedGlyph(
                glyph.face_id,
                glyph.glyph_id,
                glyph.cluster,
                glyph.x,
                glyph.y,
                glyph.x_advance + extra,
                glyph.y_advance,
                glyph.x_offset,
                glyph.y_offset,
                glyph.ink_bounds,
            )
    return GlyphRun(
        face.id,
        face.family,
        style.size,
        direction,
        script,
        language,
        source_range,
        text,
        tuple(glyphs),
        variation_coordinates=coordinates,
        bidi_level=bidi_level,
    )
