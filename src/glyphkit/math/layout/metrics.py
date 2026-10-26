"""Box measurement and style helpers for math layout."""

from __future__ import annotations

from dataclasses import replace

from glyphkit.diagnostics import SourceRange
from glyphkit.fonts import FontLibrary
from glyphkit.geometry import Bounds
from glyphkit.layout import Paragraph, TextLayout, TextSpan, TextStyle, layout_paragraph
from glyphkit.math.layout.model import MathBox, MathStyle, _MathData


def _translate(bounds: Bounds, origin: tuple[float, float]) -> Bounds:
    return Bounds(
        bounds.x_min + origin[0],
        bounds.y_min + origin[1],
        bounds.x_max + origin[0],
        bounds.y_max + origin[1],
    )


def _union(bounds: list[Bounds], fallback: Bounds) -> Bounds:
    if not bounds:
        return fallback
    return Bounds(
        min(item.x_min for item in bounds),
        min(item.y_min for item in bounds),
        max(item.x_max for item in bounds),
        max(item.y_max for item in bounds),
    )


def _math_glyph_id(data: _MathData, box: MathBox) -> int | None:
    """The box's glyph id when it belongs to the MATH face, else ``None``.

    MATH glyph tables are indexed by glyph id of the MATH font itself, so a glyph drawn from
    another face (for example an italic companion) must not be looked up in them.
    """
    layout = box.text_layout
    if box.glyph_id is None or layout is None:
        return None
    for line in layout.lines:
        for run in line.runs:
            return box.glyph_id if run.face_id == data.face.id else None
    return None


def _first_glyph_id(layout: TextLayout) -> int | None:
    for line in layout.lines:
        for run in line.runs:
            if run.glyphs:
                return run.glyphs[0].glyph_id
    return None


def _text_box(
    library: FontLibrary,
    text: str,
    style: MathStyle,
    source_range: SourceRange,
    *,
    upright: bool = False,
) -> MathBox:
    slant = style.letter_slant if text.isalpha() and not upright else "normal"
    layout = layout_paragraph(
        library,
        Paragraph((TextSpan(text, TextStyle(style.families, style.size, slant=slant)),)),
    )
    return MathBox(
        "text",
        layout.logical_bounds,
        0.0,
        layout,
        source_range=source_range,
        glyph_id=_first_glyph_id(layout),
    )


def _ink(box: MathBox) -> Bounds | None:
    """The bounds of what a box draws, relative to its own origin; ``None`` if it draws nothing."""
    parts: list[Bounds] = []
    layout = box.text_layout
    if layout is not None:
        ink = layout.ink_bounds
        if ink.x_max > ink.x_min and ink.y_max > ink.y_min:
            parts.append(ink)
    for rule in box.rules:
        half = rule.thickness / 2
        parts.append(
            Bounds(
                min(rule.start[0], rule.end[0]),
                min(rule.start[1], rule.end[1]) - half,
                max(rule.start[0], rule.end[0]),
                max(rule.start[1], rule.end[1]) + half,
            )
        )
    for child in box.children:
        inner = _ink(child)
        if inner is not None:
            parts.append(_translate(inner, child.origin))
    if not parts:
        return None
    return _union(parts, parts[0])


def _height(box: MathBox) -> float:
    """How far a box's ink rises above its baseline."""
    ink = _ink(box)
    return ink.y_max if ink is not None else 0.0


def _depth(box: MathBox) -> float:
    """How far a box's ink hangs below its baseline (positive down)."""
    ink = _ink(box)
    return -ink.y_min if ink is not None else 0.0


def _advance(box: MathBox) -> float:
    return box.bounds.x_max if box.bounds.x_min >= 0 else box.bounds.width


def _script_style(data: _MathData, style: MathStyle) -> MathStyle:
    """Style for a script: script size from display and text, scriptscript from script."""
    deeper = style.level in {"script", "scriptscript"}
    override = style.script_script_scale if deeper else style.script_scale
    if override is not None:
        size = style.size * override
    else:
        percent = data.percent(
            "ScriptScriptPercentScaleDown" if deeper else "ScriptPercentScaleDown",
            50 if deeper else 70,
        )
        size = (data.base_size or style.size) * percent
    return replace(style, size=size, level="scriptscript" if deeper else "script")


def _fraction_style(data: _MathData, style: MathStyle) -> MathStyle:
    """Style for a numerator or denominator: text inside display, script inside text."""
    if style.level == "display":
        return replace(style, level="text")
    return _script_style(data, style)
