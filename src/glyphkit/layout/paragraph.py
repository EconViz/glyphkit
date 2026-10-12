"""Unicode-aware greedy paragraph construction over immutable shaped values."""

from __future__ import annotations

from dataclasses import dataclass, replace

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontLibrary
from glyphkit.geometry import Bounds
from glyphkit.layout.models import LineLayout, Paragraph, TextLayout
from glyphkit.shaping import GlyphExtents, GlyphRun, PositionedGlyph, shape_text
from glyphkit.unicode import line_break_opportunities, reorder_line


@dataclass(frozen=True, slots=True)
class _Atom:
    run: GlyphRun | None
    glyphs: tuple[PositionedGlyph, ...]
    source_range: SourceRange
    text: str
    advance: float
    break_after: bool
    bidi_level: int
    is_tab: bool = False


@dataclass(frozen=True, slots=True)
class _RawLine:
    atoms: tuple[_Atom, ...]
    explicitly_terminated: bool
    final_in_hard_line: bool


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


def _atoms_for_run(run: GlyphRun, text: str, breaks: frozenset[int]) -> list[_Atom]:
    grouped: dict[SourceRange, list[PositionedGlyph]] = {}
    for glyph in run.glyphs:
        grouped.setdefault(glyph.cluster, []).append(glyph)
    atoms: list[_Atom] = []
    for source_range in sorted(grouped, key=lambda item: item.start):
        glyphs = grouped[source_range]
        anchor = min(glyph.x - glyph.x_offset for glyph in glyphs)
        normalized: list[PositionedGlyph] = []
        for glyph in glyphs:
            ink = glyph.ink_bounds
            if ink is not None:
                ink = GlyphExtents(
                    ink.x_min - anchor,
                    ink.y_min,
                    ink.x_max - anchor,
                    ink.y_max,
                )
            normalized.append(replace(glyph, x=glyph.x - anchor, ink_bounds=ink))
        atom_text = text[source_range.start : source_range.end]
        atoms.append(
            _Atom(
                run,
                tuple(normalized),
                source_range,
                atom_text,
                sum(glyph.x_advance for glyph in normalized),
                source_range.end in breaks,
                run.bidi_level,
            )
        )
    return atoms


def _tab_advance(x: float, paragraph: Paragraph, em: float) -> float:
    for stop in paragraph.tab_stops:
        if stop > x:
            return stop - x
    width = paragraph.default_tab_width or em * 4
    return width - (x % width) if x % width else width


def _line_width(atoms: list[_Atom], paragraph: Paragraph, indent: float, em: float) -> float:
    x = indent
    for atom in atoms:
        x += _tab_advance(x, paragraph, em) if atom.is_tab else atom.advance
    return x - indent


def _wrap(
    atoms: list[_Atom],
    paragraph: Paragraph,
    *,
    first_line_index: int,
    em: float,
) -> list[list[_Atom]]:
    if not atoms:
        return [[]]
    result: list[list[_Atom]] = []
    current: list[_Atom] = []
    for atom in atoms:
        current.append(atom)
        while paragraph.max_width is not None:
            indent = (
                paragraph.first_line_indent
                if first_line_index + len(result) == 0
                else paragraph.hanging_indent
            )
            available = max(0.0, paragraph.max_width - indent)
            if _line_width(current, paragraph, indent, em) <= available or len(current) == 1:
                break
            legal = [index for index, item in enumerate(current[:-1], 1) if item.break_after]
            split = legal[-1] if legal else len(current) - 1
            result.append(current[:split])
            current = current[split:]
    result.append(current)
    return result


def _shift_glyph(glyph: PositionedGlyph, *, x: float, y: float) -> PositionedGlyph:
    ink = glyph.ink_bounds
    if ink is not None:
        ink = GlyphExtents(ink.x_min + x, ink.y_min + y, ink.x_max + x, ink.y_max + y)
    return replace(glyph, x=glyph.x + x, y=glyph.y + y, ink_bounds=ink)


def _bounds_union(bounds: list[Bounds]) -> Bounds:
    if not bounds:
        return Bounds(0.0, 0.0, 0.0, 0.0)
    return Bounds(
        min(item.x_min for item in bounds),
        min(item.y_min for item in bounds),
        max(item.x_max for item in bounds),
        max(item.y_max for item in bounds),
    )


def layout_paragraph(library: FontLibrary, paragraph: Paragraph) -> TextLayout:
    text = "".join(span.text for span in paragraph.spans)
    breaks = frozenset(line_break_opportunities(text))
    hard_lines: list[tuple[list[_Atom], bool]] = [([], False)]
    source_offset = 0
    max_size = max(span.style.size for span in paragraph.spans)
    for span in paragraph.spans:
        parts = span.text.split("\n")
        local_offset = 0
        for part_index, part in enumerate(parts):
            # Tabs are layout controls, so shape only the surrounding text.
            tab_parts = part.split("\t")
            for tab_index, fragment in enumerate(tab_parts):
                if fragment:
                    runs = shape_text(
                        library,
                        fragment,
                        span.style.shaping_style(),
                        language=span.style.language,
                        script=span.style.script,
                        direction=span.style.direction,
                    )
                    for run in runs:
                        offset = source_offset + local_offset
                        absolute = _offset_run(run, source_offset=offset)
                        hard_lines[-1][0].extend(_atoms_for_run(absolute, text, breaks))
                    local_offset += len(fragment)
                if tab_index < len(tab_parts) - 1:
                    tab_range = SourceRange(
                        source_offset + local_offset, source_offset + local_offset + 1
                    )
                    hard_lines[-1][0].append(
                        _Atom(None, (), tab_range, "\t", 0.0, True, 0, is_tab=True)
                    )
                    local_offset += 1
            if part_index < len(parts) - 1:
                atoms, _ = hard_lines[-1]
                hard_lines[-1] = (atoms, True)
                hard_lines.append(([], False))
                local_offset += 1
        source_offset += len(span.text)

    raw_lines: list[_RawLine] = []
    for hard_atoms, terminated in hard_lines:
        wrapped = _wrap(hard_atoms, paragraph, first_line_index=len(raw_lines), em=max_size)
        for index, atoms in enumerate(wrapped):
            raw_lines.append(
                _RawLine(
                    tuple(atoms),
                    terminated and index == len(wrapped) - 1,
                    index == len(wrapped) - 1,
                )
            )

    line_height = paragraph.line_height or max_size * 1.2
    lines: list[LineLayout] = []
    baseline = 0.0
    for index, raw in enumerate(raw_lines):
        indent = paragraph.first_line_indent if index == 0 else paragraph.hanging_indent
        natural = _line_width(list(raw.atoms), paragraph, indent, max_size)
        content_width = (
            max(0.0, paragraph.max_width - indent) if paragraph.max_width is not None else natural
        )
        alignment_x = (
            indent
            + {
                "start": 0.0,
                "center": (content_width - natural) / 2,
                "end": content_width - natural,
                "justify": 0.0,
            }[paragraph.align]
        )
        justify = paragraph.align == "justify" and not raw.final_in_hard_line
        spaces = [atom for atom in raw.atoms if atom.text.isspace() and not atom.is_tab]
        extra_per_space = (
            max(0.0, content_width - natural) / len(spaces) if justify and spaces else 0.0
        )
        visual = reorder_line(raw.atoms, [atom.bidi_level for atom in raw.atoms])
        x = alignment_x
        placed_runs: list[GlyphRun] = []
        ink_bounds: list[Bounds] = []
        logical_top = baseline
        logical_bottom = baseline
        for atom in visual:
            advance = _tab_advance(x, paragraph, max_size) if atom.is_tab else atom.advance
            if atom.run is not None:
                face = library.face(atom.run.face_id)
                scale = atom.run.size / face.metrics.units_per_em
                logical_top = max(logical_top, baseline + face.metrics.ascender * scale)
                logical_bottom = min(logical_bottom, baseline + face.metrics.descender * scale)
                glyphs = tuple(_shift_glyph(glyph, x=x, y=baseline) for glyph in atom.glyphs)
                if extra_per_space and atom.text.isspace() and glyphs:
                    last = glyphs[-1]
                    glyphs = (
                        *glyphs[:-1],
                        replace(last, x_advance=last.x_advance + extra_per_space),
                    )
                    advance += extra_per_space
                placed_runs.append(
                    replace(
                        atom.run,
                        source_range=atom.source_range,
                        text=atom.text,
                        glyphs=glyphs,
                    )
                )
                for glyph in glyphs:
                    if glyph.ink_bounds is not None:
                        ink_bounds.append(
                            Bounds(
                                glyph.ink_bounds.x_min,
                                glyph.ink_bounds.y_min,
                                glyph.ink_bounds.x_max,
                                glyph.ink_bounds.y_max,
                            )
                        )
            x += advance
        advance = x - alignment_x
        logical = Bounds(alignment_x, logical_bottom, alignment_x + advance, logical_top)
        ink = _bounds_union(ink_bounds)
        available = paragraph.max_width if paragraph.max_width is not None else x
        overflow = max(0.0, x - available)
        source_ranges = tuple(
            sorted((atom.source_range for atom in raw.atoms), key=lambda r: r.start)
        )
        source_range = (
            SourceRange(source_ranges[0].start, source_ranges[-1].end) if source_ranges else None
        )
        lines.append(
            LineLayout(
                tuple(placed_runs),
                baseline,
                advance,
                logical,
                ink,
                overflow,
                source_range,
                raw.explicitly_terminated,
                source_ranges,
            )
        )
        baseline -= line_height
        if raw.explicitly_terminated:
            baseline -= paragraph.paragraph_spacing

    logical = _bounds_union([line.logical_bounds for line in lines])
    ink = _bounds_union(
        [line.ink_bounds for line in lines if line.ink_bounds.width or line.ink_bounds.height]
    )
    vertical_overflow = (
        max(0.0, logical.height - paragraph.max_height) if paragraph.max_height is not None else 0.0
    )
    return TextLayout(text, tuple(lines), logical, ink, vertical_overflow=vertical_overflow)
