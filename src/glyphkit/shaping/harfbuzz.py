"""Private uharfbuzz adapter."""

from __future__ import annotations

import uharfbuzz as hb

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontFace
from glyphkit.shaping.models import GlyphRun, PositionedGlyph, ShapingStyle
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
) -> GlyphRun:
    hb_face = hb.Face(face.data, face.id.index)
    hb_font = hb.Font(hb_face)
    hb.ot_font_set_funcs(hb_font)
    upem = face.metrics.units_per_em
    hb_font.scale = (upem, upem)
    if style.axes:
        hb_font.set_variations(dict(style.axes))
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
    for info, position in zip(buffer.glyph_infos, buffer.glyph_positions, strict=True):
        cluster_start = source_range.start + min(info.cluster, len(text))
        cluster_end = min(source_range.end, cluster_start + 1)
        x_advance = position.x_advance * scale
        y_advance = position.y_advance * scale
        glyphs.append(
            PositionedGlyph(
                info.codepoint,
                SourceRange(cluster_start, cluster_end),
                pen_x + position.x_offset * scale,
                pen_y + position.y_offset * scale,
                x_advance,
                y_advance,
                position.x_offset * scale,
                position.y_offset * scale,
            )
        )
        pen_x += x_advance
        pen_y += y_advance
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
    )

