"""Backend-neutral OpenType MATH box layout."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from io import BytesIO

from fontTools.ttLib import TTFont

from glyphkit.diagnostics import SourceRange
from glyphkit.errors import ConfigurationError, UnsupportedFeatureError
from glyphkit.fonts import FontFace, FontLibrary, FontQuery
from glyphkit.geometry import Bounds
from glyphkit.layout import Paragraph, TextLayout, TextSpan, TextStyle, layout_paragraph
from glyphkit.math.nodes import (
    Accent,
    Delimited,
    Fraction,
    Limits,
    MathNode,
    Matrix,
    Root,
    Script,
    Sequence,
    Symbol,
)

OVERRIDABLE_CONSTANTS = frozenset(
    {
        "AxisHeight",
        "FractionRuleThickness",
        "FractionNumeratorShiftUp",
        "FractionNumeratorDisplayStyleShiftUp",
        "FractionDenominatorShiftDown",
        "FractionDenominatorDisplayStyleShiftDown",
        "SubscriptShiftDown",
        "SuperscriptShiftUp",
        "LowerLimitBaselineDropMin",
        "UpperLimitBaselineRiseMin",
        "RadicalVerticalGap",
        "RadicalKernBeforeDegree",
        "RadicalRuleThickness",
        "OverbarVerticalGap",
        "UnderbarVerticalGap",
        "MatrixRowSpacing",
    }
)


@dataclass(frozen=True, slots=True)
class MathStyle:
    """Size, fonts and optional overrides for math layout.

    ``script_scale`` and ``script_script_scale`` replace the font's
    ``ScriptPercentScaleDown`` and ``ScriptScriptPercentScaleDown`` constants. Each is a
    fraction in ``(0, 1]`` of the enclosing size; ``None`` keeps the font's own value.

    ``constants`` replaces other OpenType MATH constants by their OpenType name (for
    example ``{"SuperscriptShiftUp": 0.4}``). Values are non-negative fractions of the
    font size (em), so they do not depend on the font's units per em. Use it for fonts whose
    MATH table is incomplete.

    ``letter_slant`` selects the face used for alphabetic symbols: ``"italic"`` or
    ``"oblique"`` picks the matching face of the same family (digits and operators stay
    upright), which suits fonts that lack the Unicode mathematical italic alphabet.
    """

    size: float
    families: tuple[str, ...]
    level: str = "display"
    script_scale: float | None = None
    script_script_scale: float | None = None
    constants: Mapping[str, float] = field(default_factory=dict, hash=False)
    letter_slant: str = "normal"

    def __post_init__(self) -> None:
        for name in ("script_scale", "script_script_scale"):
            value = getattr(self, name)
            if value is not None and not 0.0 < value <= 1.0:
                raise ConfigurationError(f"{name} must be a fraction in (0, 1], got {value!r}")
        for name, value in self.constants.items():
            if name not in OVERRIDABLE_CONSTANTS:
                raise ConfigurationError(f"unsupported math constant override {name!r}")
            if not math.isfinite(value) or value < 0.0:
                raise ConfigurationError(
                    f"math constant override {name} must be a finite non-negative em value"
                )
        if self.letter_slant not in {"normal", "italic", "oblique"}:
            raise ConfigurationError("letter_slant must be normal, italic, or oblique")
        object.__setattr__(self, "constants", dict(self.constants))


@dataclass(frozen=True, slots=True)
class MathRule:
    start: tuple[float, float]
    end: tuple[float, float]
    thickness: float


@dataclass(frozen=True, slots=True)
class MathBox:
    """A semantic MATH box positioned relative to its parent baseline."""

    kind: str
    bounds: Bounds
    baseline: float
    text_layout: TextLayout | None = None
    children: tuple[MathBox, ...] = ()
    rules: tuple[MathRule, ...] = ()
    origin: tuple[float, float] = (0.0, 0.0)
    source_range: SourceRange | None = None
    glyph_id: int | None = None


@dataclass(slots=True)
class _MathData:
    font: TTFont
    face: FontFace
    scale: float
    display: bool
    size: float
    overrides: Mapping[str, float]

    def value(self, name: str, fallback: float) -> float:
        if name in self.overrides:
            return self.overrides[name] * self.size
        constants = self.font["MATH"].table.MathConstants
        record = getattr(constants, name, None)
        raw = getattr(record, "Value", record)
        return float(raw if raw is not None else fallback) * self.scale

    def percent(self, name: str, fallback: float) -> float:
        constants = self.font["MATH"].table.MathConstants
        return float(getattr(constants, name, fallback)) / 100.0

    def italic_correction(self, glyph_id: int | None) -> float:
        if glyph_id is None:
            return 0.0
        info = self.font["MATH"].table.MathGlyphInfo.MathItalicsCorrectionInfo
        if info is None or info.Coverage is None:
            return 0.0
        glyphs = info.Coverage.glyphs
        name = self.font.getGlyphOrder()[glyph_id]
        if name not in glyphs:
            return 0.0
        record = info.ItalicsCorrection[glyphs.index(name)]
        return float(record.Value) * self.scale

    def top_accent_attachment(self, glyph_id: int | None, fallback: float) -> float:
        if glyph_id is None:
            return fallback
        info = self.font["MATH"].table.MathGlyphInfo.MathTopAccentAttachment
        if info is None or info.TopAccentCoverage is None:
            return fallback
        glyphs = info.TopAccentCoverage.glyphs
        name = self.font.getGlyphOrder()[glyph_id]
        if name not in glyphs:
            return fallback
        return float(info.TopAccentAttachment[glyphs.index(name)].Value) * self.scale


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
    library: FontLibrary, text: str, style: MathStyle, source_range: SourceRange
) -> MathBox:
    slant = style.letter_slant if text.isalpha() else "normal"
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


def _script_style(data: _MathData, style: MathStyle) -> MathStyle:
    display = style.level == "display"
    override = style.script_scale if display else style.script_script_scale
    percent = (
        override
        if override is not None
        else data.percent(
            "ScriptPercentScaleDown" if display else "ScriptScriptPercentScaleDown",
            70 if display else 50,
        )
    )
    return replace(style, size=style.size * percent, level="script")


def _layout(library: FontLibrary, node: MathNode, style: MathStyle, data: _MathData) -> MathBox:
    if isinstance(node, Symbol):
        return _text_box(library, node.value, style, node.source_range)
    if isinstance(node, Sequence):
        cursor = 0.0
        children: list[MathBox] = []
        translated: list[Bounds] = []
        for child_node in node.children:
            child = _layout(library, child_node, style, data)
            placed = replace(child, origin=(cursor, 0.0))
            children.append(placed)
            translated.append(_translate(child.bounds, placed.origin))
            cursor += child.bounds.width
        return MathBox(
            "sequence",
            _union(translated, Bounds(0.0, -style.size * 0.2, cursor, style.size * 0.8)),
            0.0,
            children=tuple(children),
            source_range=node.source_range,
        )
    if isinstance(node, Fraction):
        smaller = _script_style(data, style)
        numerator = _layout(library, node.numerator, smaller, data)
        denominator = _layout(library, node.denominator, smaller, data)
        width = max(numerator.bounds.width, denominator.bounds.width) + style.size * 0.2
        axis = data.value("AxisHeight", style.size * 0.25)
        rule_thickness = max(
            data.value("FractionRuleThickness", style.size * 0.06), style.size / 1000
        )
        numerator_y = data.value(
            "FractionNumeratorDisplayStyleShiftUp" if data.display else "FractionNumeratorShiftUp",
            style.size * 0.45,
        )
        denominator_y = -data.value(
            "FractionDenominatorDisplayStyleShiftDown"
            if data.display
            else "FractionDenominatorShiftDown",
            style.size * 0.45,
        )
        numerator_origin = ((width - numerator.bounds.width) / 2, numerator_y)
        denominator_origin = ((width - denominator.bounds.width) / 2, denominator_y)
        bounds = _union(
            [
                _translate(numerator.bounds, numerator_origin),
                _translate(denominator.bounds, denominator_origin),
            ],
            Bounds(0.0, -style.size * 0.5, width, style.size * 0.5),
        )
        return MathBox(
            "fraction",
            bounds,
            axis,
            children=(
                replace(numerator, origin=numerator_origin),
                replace(denominator, origin=denominator_origin),
            ),
            rules=(MathRule((0.0, axis), (width, axis), rule_thickness),),
            source_range=node.source_range,
        )
    if isinstance(node, Script):
        base = _layout(library, node.base, style, data)
        script_style = _script_style(data, style)
        script_children = [replace(base, origin=(0.0, 0.0))]
        script_bounds = [base.bounds]
        script_x = base.bounds.width + data.italic_correction(_math_glyph_id(data, base))
        if node.subscript is not None:
            sub = _layout(library, node.subscript, script_style, data)
            origin = (script_x, -data.value("SubscriptShiftDown", style.size * 0.3))
            script_children.append(replace(sub, origin=origin))
            script_bounds.append(_translate(sub.bounds, origin))
        if node.superscript is not None:
            sup = _layout(library, node.superscript, script_style, data)
            origin = (script_x, data.value("SuperscriptShiftUp", style.size * 0.5))
            script_children.append(replace(sup, origin=origin))
            script_bounds.append(_translate(sup.bounds, origin))
        return MathBox(
            "script",
            _union(script_bounds, base.bounds),
            0.0,
            children=tuple(script_children),
            source_range=node.source_range,
        )
    if isinstance(node, Limits):
        operator = _layout(library, node.operator, style, data)
        limit_children = [replace(operator, origin=(0.0, 0.0))]
        limit_bounds = [operator.bounds]
        if node.lower is not None:
            lower = _layout(library, node.lower, _script_style(data, style), data)
            origin = (
                (operator.bounds.width - lower.bounds.width) / 2,
                -data.value("LowerLimitBaselineDropMin", style.size * 0.5),
            )
            limit_children.append(replace(lower, origin=origin))
            limit_bounds.append(_translate(lower.bounds, origin))
        if node.upper is not None:
            upper = _layout(library, node.upper, _script_style(data, style), data)
            origin = (
                (operator.bounds.width - upper.bounds.width) / 2,
                data.value("UpperLimitBaselineRiseMin", style.size * 0.5),
            )
            limit_children.append(replace(upper, origin=origin))
            limit_bounds.append(_translate(upper.bounds, origin))
        return MathBox(
            "limits",
            _union(limit_bounds, operator.bounds),
            0.0,
            children=tuple(limit_children),
            source_range=node.source_range,
        )
    if isinstance(node, Root):
        body = _layout(library, node.radicand, style, data)
        radical = _text_box(library, "√", style, node.source_range)
        gap = data.value("RadicalVerticalGap", style.size * 0.1)
        radical_origin = (0.0, 0.0)
        body_origin = (radical.bounds.width, 0.0)
        rule_y = body.bounds.y_max + gap
        root_children = [replace(radical, origin=radical_origin), replace(body, origin=body_origin)]
        root_bounds = _union(
            [_translate(radical.bounds, radical_origin), _translate(body.bounds, body_origin)],
            Bounds(0.0, body.bounds.y_min, radical.bounds.width + body.bounds.width, rule_y),
        )
        if node.index is not None:
            degree = _layout(library, node.index, _script_style(data, style), data)
            origin = (
                -degree.bounds.width + data.value("RadicalKernBeforeDegree", 0.0),
                body.bounds.y_max * data.percent("RadicalDegreeBottomRaisePercent", 60),
            )
            root_children.append(replace(degree, origin=origin))
            root_bounds = _union([root_bounds, _translate(degree.bounds, origin)], root_bounds)
        width = radical.bounds.width + body.bounds.width
        return MathBox(
            "root",
            root_bounds,
            0.0,
            children=tuple(root_children),
            rules=(
                MathRule(
                    (radical.bounds.width, rule_y),
                    (width, rule_y),
                    data.value("RadicalRuleThickness", style.size * 0.05),
                ),
            ),
            source_range=node.source_range,
        )
    if isinstance(node, Delimited):
        # MATH variants are selected by consumers from the face's MATH table; the base glyph
        # remains a normal positioned glyph so the result stays in the shared text contract.
        return _layout(
            library,
            Sequence(
                (
                    Symbol(node.left, node.source_range),
                    node.body,
                    Symbol(node.right, node.source_range),
                ),
                node.source_range,
            ),
            style,
            data,
        )
    if isinstance(node, Accent):
        body = _layout(library, node.body, style, data)
        accent_character = {
            "hat": "\u02c6",
            "bar": "¯",
            "vec": "→",
            "overline": "¯",
            "underline": "_",
        }[node.kind]
        accent = _text_box(library, accent_character, style, node.source_range)
        attachment = data.top_accent_attachment(_math_glyph_id(data, body), body.bounds.width / 2)
        accent_origin = (
            attachment - accent.bounds.width / 2,
            body.bounds.y_max + data.value("OverbarVerticalGap", style.size * 0.1),
        )
        if node.kind == "underline":
            accent_origin = (
                attachment - accent.bounds.width / 2,
                body.bounds.y_min - data.value("UnderbarVerticalGap", style.size * 0.1),
            )
        bounds = _union([body.bounds, _translate(accent.bounds, accent_origin)], body.bounds)
        return MathBox(
            node.kind,
            bounds,
            0.0,
            children=(replace(body, origin=(0.0, 0.0)), replace(accent, origin=accent_origin)),
            source_range=node.source_range,
        )
    if isinstance(node, Matrix):
        rows = tuple(
            tuple(_layout(library, cell, style, data) for cell in row) for row in node.rows
        )
        columns = max((len(row) for row in rows), default=0)
        widths = tuple(
            max((row[column].bounds.width for row in rows if len(row) > column), default=0.0)
            for column in range(columns)
        )
        row_gap = data.value("MatrixRowSpacing", style.size * 0.3)
        matrix_placed: list[MathBox] = []
        matrix_bounds: list[Bounds] = []
        y = 0.0
        for row in rows:
            x = 0.0
            for column, cell in enumerate(row):
                origin = (x + (widths[column] - cell.bounds.width) / 2, y)
                matrix_placed.append(replace(cell, origin=origin))
                matrix_bounds.append(_translate(cell.bounds, origin))
                x += widths[column] + style.size * 0.5
            y -= style.size + row_gap
        return MathBox(
            "matrix",
            _union(matrix_bounds, Bounds(0.0, 0.0, 0.0, 0.0)),
            0.0,
            children=tuple(matrix_placed),
            source_range=node.source_range,
        )
    raise UnsupportedFeatureError(f"math node is not supported: {type(node).__name__}")


def layout_math(library: FontLibrary, expression: MathNode, *, style: MathStyle) -> MathBox:
    face = library.match(FontQuery(style.families)).face
    if not face.has_math:
        raise UnsupportedFeatureError(f"font {face.family!r} has no OpenType MATH table")
    font = TTFont(BytesIO(face.data), fontNumber=face.id.index, lazy=False)
    try:
        data = _MathData(
            font,
            face,
            style.size / face.metrics.units_per_em,
            style.level == "display",
            style.size,
            style.constants,
        )
        return _layout(library, expression, style, data)
    finally:
        font.close()
