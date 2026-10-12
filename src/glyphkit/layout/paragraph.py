"""Greedy first-release paragraph construction."""

from __future__ import annotations

from dataclasses import replace

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontLibrary
from glyphkit.layout.models import Bounds, LineLayout, Paragraph, TextLayout
from glyphkit.shaping import GlyphRun, PositionedGlyph, shape_text


def _offset_run(run: GlyphRun, *, source_offset: int) -> GlyphRun:
    return replace(
        run,
        source_range=SourceRange(
            run.source_range.start + source_offset, run.source_range.end + source_offset
        ),
        glyphs=tuple(
            replace(
                glyph,
                cluster=SourceRange(
                    glyph.cluster.start + source_offset, glyph.cluster.end + source_offset
                ),
            )
            for glyph in run.glyphs
        ),
    )


def _shift_run(run: GlyphRun, *, x: float, y: float) -> GlyphRun:
    return replace(
        run,
        glyphs=tuple(replace(glyph, x=glyph.x + x, y=glyph.y + y) for glyph in run.glyphs),
    )


def _split_run(run: GlyphRun, max_width: float | None) -> tuple[GlyphRun, ...]:
    if max_width is None or run.advance <= max_width:
        return (run,)
    pieces: list[GlyphRun] = []
    current: list[PositionedGlyph] = []
    current_width = 0.0
    for glyph in run.glyphs:
        if current and current_width + glyph.x_advance > max_width:
            pieces.append(_run_piece(run, current))
            current = []
            current_width = 0.0
        current.append(replace(glyph, x=current_width + glyph.x_offset))
        current_width += glyph.x_advance
    if current:
        pieces.append(_run_piece(run, current))
    return tuple(pieces)


def _run_piece(run: GlyphRun, glyphs: list[PositionedGlyph]) -> GlyphRun:
    return replace(
        run,
        source_range=SourceRange(glyphs[0].cluster.start, glyphs[-1].cluster.end),
        text=run.text,
        glyphs=tuple(glyphs),
    )


def layout_paragraph(library: FontLibrary, paragraph: Paragraph) -> TextLayout:
    text = "".join(span.text for span in paragraph.spans)
    raw_lines: list[list[GlyphRun]] = [[]]
    source_offset = 0
    max_size = max(span.style.size for span in paragraph.spans)
    for span in paragraph.spans:
        parts = span.text.split("\n")
        local_offset = 0
        for part_index, part in enumerate(parts):
            if part:
                runs = shape_text(
                    library,
                    part,
                    span.style.shaping_style(),
                    language=span.style.language,
                    script=span.style.script,
                )
                for run in runs:
                    offset_run = _offset_run(run, source_offset=source_offset + local_offset)
                    for piece in _split_run(offset_run, paragraph.max_width):
                        current_width = sum(item.advance for item in raw_lines[-1])
                        if (
                            paragraph.max_width is not None
                            and raw_lines[-1]
                            and current_width + piece.advance > paragraph.max_width
                        ):
                            raw_lines.append([])
                        raw_lines[-1].append(piece)
                local_offset += len(part)
            if part_index < len(parts) - 1:
                raw_lines.append([])
                local_offset += 1
        source_offset += len(span.text)

    line_height = paragraph.line_height or max_size * 1.2
    lines: list[LineLayout] = []
    for index, raw_runs in enumerate(raw_lines):
        advance = sum(run.advance for run in raw_runs)
        available = paragraph.max_width if paragraph.max_width is not None else advance
        alignment_x = {"start": 0.0, "center": (available - advance) / 2, "end": available - advance}[
            paragraph.align
        ]
        baseline = -index * line_height
        x = alignment_x
        runs: list[GlyphRun] = []
        for run in raw_runs:
            runs.append(_shift_run(run, x=x, y=baseline))
            x += run.advance
        top = baseline + max_size * 0.8
        bottom = baseline - max_size * 0.2
        bounds = Bounds(alignment_x, bottom, alignment_x + advance, top)
        overflow = max(0.0, advance - available)
        lines.append(LineLayout(tuple(runs), baseline, advance, bounds, bounds, overflow))

    if lines:
        x_min = min(line.logical_bounds.x_min for line in lines)
        y_min = min(line.logical_bounds.y_min for line in lines)
        x_max = max(line.logical_bounds.x_max for line in lines)
        y_max = max(line.logical_bounds.y_max for line in lines)
        bounds = Bounds(x_min, y_min, x_max, y_max)
    else:
        bounds = Bounds(0.0, 0.0, 0.0, 0.0)
    height = bounds.height
    vertical_overflow = max(0.0, height - paragraph.max_height) if paragraph.max_height else 0.0
    return TextLayout(text, tuple(lines), bounds, bounds, vertical_overflow=vertical_overflow)

