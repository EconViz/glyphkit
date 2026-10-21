"""Backend-neutral OpenType MATH box layout."""

# ruff: noqa: RUF001 -- mathematical symbols are intentional Unicode tokens.

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
    Space,
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
        "LowerLimitGapMin",
        "UpperLimitGapMin",
        "FractionNumeratorGapMin",
        "FractionNumDisplayStyleGapMin",
        "FractionDenominatorGapMin",
        "FractionDenomDisplayStyleGapMin",
        "SuperscriptBottomMin",
        "SubscriptTopMax",
        "SubSuperscriptGapMin",
        "SuperscriptBottomMaxWithSubscript",
        "SuperscriptBaselineDropMax",
        "SubscriptBaselineDropMin",
        "SpaceAfterScript",
        "DisplayOperatorMinHeight",
        "RadicalVerticalGap",
        "RadicalKernBeforeDegree",
        "RadicalKernAfterDegree",
        "OverbarRuleThickness",
        "UnderbarRuleThickness",
        "AccentBaseHeight",
        "RadicalRuleThickness",
        "OverbarVerticalGap",
        "UnderbarVerticalGap",
        "MatrixRowSpacing",
    }
)


LEVELS = ("display", "text", "script", "scriptscript")


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

    ``level`` is the TeX style the expression starts in: ``"display"`` (fractions and limits
    at full size, big operators enlarged), ``"text"``, ``"script"`` or ``"scriptscript"``.

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
        if self.level not in LEVELS:
            raise ConfigurationError(
                f"level must be one of {', '.join(LEVELS)}, got {self.level!r}"
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
    scale: float  # font units to points at the current size
    display: bool
    size: float  # the current size
    overrides: Mapping[str, float]
    units_per_em: float = 1000.0
    base_size: float = 0.0  # the size of the whole expression, from which script sizes derive

    def at(self, size: float) -> _MathData:
        """The same font data for a box set at ``size``: constants scale with the box."""
        if size == self.size:
            return self
        return replace(self, scale=size / self.units_per_em, size=size)

    def value(self, name: str, fallback: float) -> float:
        if name in self.overrides:
            return self.overrides[name] * self.size
        constants = self.font["MATH"].table.MathConstants
        record = getattr(constants, name, None)
        raw = getattr(record, "Value", record)
        if raw is None:
            return fallback  # already in points
        return float(raw) * self.scale

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


# Spacing between atoms by the class on the left and on the right, as TeX's codes:
# 1 thin (3 mu), 2 medium (4 mu), 3 thick (5 mu), where a mu is 1/18 em. A negative code is a
# space that exists only outside script styles (the parentheses in TeX's table).
_MU = {1: 3.0, 2: 4.0, 3: 5.0}
_ATOMS = ("ord", "op", "bin", "rel", "open", "close", "punct", "inner")
_SPACING = {
    "ord": (0, 1, -2, -3, 0, 0, 0, -1),
    "op": (1, 1, 0, -3, 0, 0, 0, -1),
    "bin": (-2, -2, 0, 0, -2, 0, 0, -2),
    "rel": (-3, -3, 0, 0, -3, 0, 0, -3),
    "open": (0, 0, 0, 0, 0, 0, 0, 0),
    "close": (0, 1, -2, -3, 0, 0, 0, -1),
    "punct": (-1, -1, 0, -1, -1, -1, -1, -1),
    "inner": (-1, 1, -2, -3, -1, 0, -1, -1),
}
_RELATIONS = frozenset("=<>≤≥≠≈≡∼≃≅∝≪≫∈∉∋⊂⊃⊆⊇→←↔⇒⇐⇔⟹⟺↦⊥∥∣")
_OPENING = frozenset("([⟨")
_CLOSING = frozenset(")]⟩")


def _symbol_class(symbol: Symbol) -> str:
    role, value = symbol.role, symbol.value
    if role in {"large-operator", "integral", "function"}:
        return "op"
    if role == "binary":
        return "bin"
    if role == "relation":
        return "rel"
    if role == "open":
        return "open"
    if role == "close":
        return "close"
    if role == "punct":
        return "punct"
    if role == "operator":  # the pre-1.0 role for both binary operators and relations
        return "rel" if value in _RELATIONS else "bin"
    return "ord"


def _atom_class(node: MathNode) -> str:
    if isinstance(node, Symbol):
        return _symbol_class(node)
    if isinstance(node, Script):
        return _atom_class(node.base)
    if isinstance(node, Limits):
        return "op"
    if isinstance(node, (Fraction, Delimited)):
        return "inner"
    return "ord"


def _atom_classes(children: tuple[MathNode, ...]) -> list[str]:
    """Each child's class, with a binary operator that has no left operand set as ordinary."""
    classes = [_atom_class(child) for child in children]
    for index, kind in enumerate(classes):
        if kind != "bin":
            continue
        before = classes[index - 1] if index else None
        after = classes[index + 1] if index + 1 < len(classes) else None
        if before in {None, "bin", "op", "rel", "open", "punct"} or after in {
            None,
            "rel",
            "close",
            "punct",
        }:
            classes[index] = "ord"
    return classes


def _gap(left: str, right: str, style: MathStyle) -> float:
    """The space between two atom classes, in points."""
    code = _SPACING[left][_ATOMS.index(right)]
    if code < 0:
        if style.level in {"script", "scriptscript"}:
            return 0.0
        code = -code
    return _MU.get(code, 0.0) * style.size / 18


def _enlarged(library: FontLibrary, symbol: Symbol, style: MathStyle, data: _MathData) -> MathBox:
    """A big operator: in display style large enough, and centred on the math axis."""
    box = _text_box(library, symbol.value, style, symbol.source_range)
    if symbol.role not in {"large-operator", "integral"} or len(symbol.value) != 1:
        return box
    if style.level != "display":
        return box
    ink = _ink(box)
    if ink is None:
        return box
    wanted = data.value("DisplayOperatorMinHeight", style.size * 1.4)
    height = ink.y_max - ink.y_min
    if height < wanted:
        box = _text_box(
            library,
            symbol.value,
            replace(style, size=style.size * wanted / height),
            symbol.source_range,
        )
        ink = _ink(box)
        assert ink is not None
    axis = data.value("AxisHeight", style.size * 0.25)
    shift = axis - (ink.y_max + ink.y_min) / 2
    return MathBox(
        "operator",
        _translate(box.bounds, (0.0, shift)),
        0.0,
        children=(replace(box, origin=(0.0, shift)),),
        source_range=symbol.source_range,
        glyph_id=box.glyph_id,
    )


def _sized_to(
    library: FontLibrary,
    text: str,
    style: MathStyle,
    source_range: SourceRange,
    *,
    top: float,
    bottom: float,
) -> MathBox:
    """A stretchy glyph (radical, bracket) set at a size whose ink spans ``bottom`` to ``top``.

    It is never set smaller than ``style.size``. The font's glyph variants would draw these
    better; scaling the plain glyph keeps the result a normal positioned glyph.
    """
    box = _text_box(library, text, style, source_range)
    ink = _ink(box)
    wanted = top - bottom
    if ink is None or ink.y_max - ink.y_min >= wanted:
        shift = top - ink.y_max if ink is not None and ink.y_max - ink.y_min >= wanted else 0.0
        return _shifted(box, shift)
    scaled = _text_box(
        library,
        text,
        replace(style, size=style.size * wanted / (ink.y_max - ink.y_min)),
        source_range,
    )
    ink = _ink(scaled)
    assert ink is not None
    return _shifted(scaled, top - ink.y_max)


def _shifted(box: MathBox, dy: float) -> MathBox:
    if dy == 0.0:
        return box
    return MathBox(
        "shifted",
        _translate(box.bounds, (0.0, dy)),
        0.0,
        children=(replace(box, origin=(0.0, dy)),),
        source_range=box.source_range,
        glyph_id=box.glyph_id,
    )


def _layout(library: FontLibrary, node: MathNode, style: MathStyle, data: _MathData) -> MathBox:
    data = data.at(style.size)
    if isinstance(node, Space):
        width = node.mu * style.size / 18
        return MathBox(
            "space",
            Bounds(0.0, 0.0, width, 0.0),
            0.0,
            source_range=node.source_range,
        )
    if isinstance(node, Symbol):
        if node.role in {"large-operator", "integral"}:
            return _enlarged(library, node, style, data)
        value = node.value
        if value == "-" and node.role in {"binary", "operator"} and 0x2212 in _covered(data):
            value = "\u2212"  # a true minus where the font has one
        upright = node.role in {"function", "upright"}
        return _text_box(library, value, style, node.source_range, upright=upright)
    if isinstance(node, Sequence):
        classes = _atom_classes(node.children)
        cursor = 0.0
        children: list[MathBox] = []
        translated: list[Bounds] = []
        previous: str | None = None
        for child_node, kind in zip(node.children, classes, strict=True):
            if previous is not None and not isinstance(child_node, Space):
                cursor += _gap(previous, kind, style)
            child = _layout(library, child_node, style, data)
            placed = replace(child, origin=(cursor, 0.0))
            children.append(placed)
            translated.append(_translate(child.bounds, placed.origin))
            cursor += _advance(child)
            previous = None if isinstance(child_node, Space) else kind
        return MathBox(
            "sequence",
            _union(translated, Bounds(0.0, -style.size * 0.2, cursor, style.size * 0.8)),
            0.0,
            children=tuple(children),
            source_range=node.source_range,
        )
    if isinstance(node, Fraction):
        inner = _fraction_style(data, style)
        numerator = _layout(library, node.numerator, inner, data)
        denominator = _layout(library, node.denominator, inner, data)
        display = style.level == "display"
        padding = style.size * 0.08
        width = max(_advance(numerator), _advance(denominator)) + 2 * padding
        axis = data.value("AxisHeight", style.size * 0.25)
        thickness = max(data.value("FractionRuleThickness", style.size * 0.06), style.size / 1000)
        num_gap = data.value(
            "FractionNumDisplayStyleGapMin" if display else "FractionNumeratorGapMin",
            thickness * (3 if display else 1),
        )
        den_gap = data.value(
            "FractionDenomDisplayStyleGapMin" if display else "FractionDenominatorGapMin",
            thickness * (3 if display else 1),
        )
        shift_up = data.value(
            "FractionNumeratorDisplayStyleShiftUp" if display else "FractionNumeratorShiftUp",
            style.size * 0.45,
        )
        shift_down = data.value(
            "FractionDenominatorDisplayStyleShiftDown"
            if display
            else "FractionDenominatorShiftDown",
            style.size * 0.45,
        )
        # The numerator clears the top of the rule and the denominator the bottom of it.
        numerator_y = max(shift_up, axis + thickness / 2 + num_gap + _depth(numerator))
        denominator_y = -max(shift_down, _height(denominator) - axis + thickness / 2 + den_gap)
        numerator_origin = ((width - _advance(numerator)) / 2, numerator_y)
        denominator_origin = ((width - _advance(denominator)) / 2, denominator_y)
        bounds = _union(
            [
                _translate(numerator.bounds, numerator_origin),
                _translate(denominator.bounds, denominator_origin),
            ],
            Bounds(0.0, -style.size * 0.5, width, style.size * 0.5),
        )
        bounds = Bounds(0.0, bounds.y_min, width, bounds.y_max)
        return MathBox(
            "fraction",
            bounds,
            axis,
            children=(
                replace(numerator, origin=numerator_origin),
                replace(denominator, origin=denominator_origin),
            ),
            rules=(MathRule((padding, axis), (width - padding, axis), thickness),),
            source_range=node.source_range,
        )
    if isinstance(node, Script):
        return _script(library, node, style, data)
    if isinstance(node, Limits):
        return _limits(library, node, style, data)
    if isinstance(node, Root):
        body = _layout(library, node.radicand, style, data)
        gap = data.value("RadicalVerticalGap", style.size * 0.1)
        thickness = data.value("RadicalRuleThickness", style.size * 0.05)
        rule_y = _height(body) + gap + thickness / 2
        # the radical sign spans from below the body up to the top of the bar
        radical = _sized_to(
            library,
            "√",
            style,
            node.source_range,
            top=rule_y + thickness / 2,
            bottom=-_depth(body) - gap / 2,
        )
        radical_width = _advance(radical)
        width = radical_width + _advance(body)
        root_children = [
            replace(radical, origin=(0.0, 0.0)),
            replace(body, origin=(radical_width, 0.0)),
        ]
        root_bounds = _union(
            [_translate(radical.bounds, (0.0, 0.0)), _translate(body.bounds, (radical_width, 0.0))],
            Bounds(0.0, body.bounds.y_min, width, rule_y + thickness / 2),
        )
        if node.index is not None:
            degree = _layout(library, node.index, _script_style(data, style), data)
            raise_by = (rule_y + _depth(body)) * data.percent("RadicalDegreeBottomRaisePercent", 60)
            origin = (
                max(0.0, data.value("RadicalKernBeforeDegree", style.size * 0.1)),
                raise_by - _depth(body),
            )
            shift = (
                _advance(degree)
                + origin[0]
                + data.value("RadicalKernAfterDegree", -style.size * 0.15)
            )
            if shift > 0:
                root_children = [
                    replace(child, origin=(child.origin[0] + shift, child.origin[1]))
                    for child in root_children
                ]
                width += shift
            root_children.append(replace(degree, origin=origin))
            root_bounds = Bounds(
                0.0,
                root_bounds.y_min,
                width,
                max(root_bounds.y_max, _height(degree) + origin[1]),
            )
        return MathBox(
            "root",
            root_bounds,
            0.0,
            children=tuple(root_children),
            rules=(
                MathRule(
                    (
                        radical_width + (shift if node.index is not None and shift > 0 else 0.0),
                        rule_y,
                    ),
                    (width, rule_y),
                    thickness,
                ),
            ),
            source_range=node.source_range,
        )
    if isinstance(node, Delimited):
        body = _layout(library, node.body, style, data)
        axis = data.value("AxisHeight", style.size * 0.25)
        # delimiters reach TeX's 90% of the content on both sides of the axis
        reach = max(_height(body) - axis, _depth(body) + axis) * 0.9
        top, bottom = axis + reach, axis - reach
        left = _sized_to(library, node.left, style, node.source_range, top=top, bottom=bottom)
        right = _sized_to(library, node.right, style, node.source_range, top=top, bottom=bottom)
        body_x = _advance(left)
        right_x = body_x + _advance(body)
        children = [
            replace(left, origin=(0.0, 0.0)),
            replace(body, origin=(body_x, 0.0)),
            replace(right, origin=(right_x, 0.0)),
        ]
        bounds = _union(
            [_translate(child.bounds, child.origin) for child in children],
            Bounds(0.0, 0.0, right_x + _advance(right), 0.0),
        )
        return MathBox(
            "delimited",
            Bounds(0.0, bounds.y_min, right_x + _advance(right), bounds.y_max),
            0.0,
            children=tuple(children),
            source_range=node.source_range,
        )
    if isinstance(node, Accent):
        body = _layout(library, node.body, style, data)
        if node.kind in {"overline", "underline"}:
            thickness = data.value(
                "OverbarRuleThickness" if node.kind == "overline" else "UnderbarRuleThickness",
                style.size * 0.05,
            )
            width = _advance(body)
            if node.kind == "overline":
                y = (
                    _height(body)
                    + data.value("OverbarVerticalGap", style.size * 0.1)
                    + thickness / 2
                )
            else:
                y = (
                    -_depth(body)
                    - data.value("UnderbarVerticalGap", style.size * 0.1)
                    - thickness / 2
                )
            bounds = _union(
                [body.bounds, Bounds(0.0, y - thickness / 2, width, y + thickness / 2)], body.bounds
            )
            return MathBox(
                node.kind,
                bounds,
                0.0,
                children=(replace(body, origin=(0.0, 0.0)),),
                rules=(MathRule((0.0, y), (width, y), thickness),),
                source_range=node.source_range,
            )
        accent_character = {"hat": "\u02c6", "bar": "¯", "vec": "→"}[node.kind]
        accent = _text_box(library, accent_character, style, node.source_range)
        ink = _ink(accent)
        attachment = data.top_accent_attachment(_math_glyph_id(data, body), _advance(body) / 2)
        # the accent's own ink sits just above the body, wherever the glyph draws it in its em box
        gap = data.value("AccentBaseHeight", style.size * 0.45)
        base = max(_height(body), min(gap, style.size)) if node.kind != "vec" else _height(body)
        lift = base + style.size * 0.05 - (ink.y_min if ink is not None else 0.0)
        accent_origin = (attachment - _advance(accent) / 2, lift)
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
            max((_advance(row[column]) for row in rows if len(row) > column), default=0.0)
            for column in range(columns)
        )
        row_gap = data.value("MatrixRowSpacing", style.size * 0.3)
        matrix_placed: list[MathBox] = []
        matrix_bounds: list[Bounds] = []
        y = 0.0
        for row in rows:
            x = 0.0
            for column, cell in enumerate(row):
                origin = (x + (widths[column] - _advance(cell)) / 2, y)
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


def _covered(data: _MathData) -> frozenset[int]:
    return data.face.coverage


def _script(library: FontLibrary, node: Script, style: MathStyle, data: _MathData) -> MathBox:
    """Scripts placed by TeX's rule 18 with the font's MATH constants."""
    base = _layout(library, node.base, style, data)
    script_style = _script_style(data, style)
    advance = _advance(base)
    children = [replace(base, origin=(0.0, 0.0))]
    boxes = [base.bounds]
    sub = (
        _layout(library, node.subscript, script_style, data) if node.subscript is not None else None
    )
    sup = (
        _layout(library, node.superscript, script_style, data)
        if node.superscript is not None
        else None
    )
    simple = isinstance(node.base, Symbol) and node.base.role not in {"integral", "large-operator"}
    drop_up = 0.0 if simple else _height(base) - data.value("SuperscriptBaselineDropMax", 0.0)
    drop_down = 0.0 if simple else _depth(base) + data.value("SubscriptBaselineDropMin", 0.0)
    up = down = 0.0
    if sup is not None:
        up = max(
            data.value("SuperscriptShiftUp", style.size * 0.5),
            drop_up,
            _depth(sup) + data.value("SuperscriptBottomMin", style.size * 0.1),
        )
    if sub is not None:
        down = max(
            data.value("SubscriptShiftDown", style.size * 0.3),
            drop_down,
            _height(sub) - data.value("SubscriptTopMax", style.size * 0.8),
        )
    if sub is not None and sup is not None:
        gap_min = data.value("SubSuperscriptGapMin", style.size * 0.15)
        gap = (up - _depth(sup)) - (_height(sub) - down)
        if gap < gap_min:
            down += gap_min - gap
            lift = data.value("SuperscriptBottomMaxWithSubscript", style.size * 0.4) - (
                up - _depth(sup)
            )
            if lift > 0:
                up += lift
                down -= lift
    correction = data.italic_correction(_math_glyph_id(data, base))
    after = data.value("SpaceAfterScript", style.size * 0.04)
    extent = advance
    if sub is not None:
        origin = (advance, -down)
        children.append(replace(sub, origin=origin))
        boxes.append(_translate(sub.bounds, origin))
        extent = max(extent, advance + _advance(sub))
    if sup is not None:
        origin = (advance + correction, up)
        children.append(replace(sup, origin=origin))
        boxes.append(_translate(sup.bounds, origin))
        extent = max(extent, advance + correction + _advance(sup))
    bounds = _union(boxes, base.bounds)
    return MathBox(
        "script",
        Bounds(bounds.x_min, bounds.y_min, max(bounds.x_max, extent + after), bounds.y_max),
        0.0,
        children=tuple(children),
        source_range=node.source_range,
    )


def _limits(library: FontLibrary, node: Limits, style: MathStyle, data: _MathData) -> MathBox:
    """Limits above and below a big operator in display style, scripts beside it otherwise."""
    if style.level != "display":
        return _script(
            library,
            Script(node.operator, node.source_range, node.lower, node.upper),
            style,
            data,
        )
    operator = _layout(library, node.operator, style, data)
    limit_style = _script_style(data, style)
    lower = _layout(library, node.lower, limit_style, data) if node.lower is not None else None
    upper = _layout(library, node.upper, limit_style, data) if node.upper is not None else None
    width = max(
        [_advance(operator)] + [_advance(limit) for limit in (lower, upper) if limit is not None]
    )
    ink = _ink(operator)
    top = ink.y_max if ink is not None else style.size * 0.7
    bottom = ink.y_min if ink is not None else 0.0
    children = [replace(operator, origin=((width - _advance(operator)) / 2, 0.0))]
    boxes = [_translate(operator.bounds, children[0].origin)]
    if lower is not None:
        drop = max(
            data.value("LowerLimitGapMin", style.size * 0.1) + _height(lower),
            data.value("LowerLimitBaselineDropMin", style.size * 0.4),
        )
        origin = ((width - _advance(lower)) / 2, bottom - drop)
        children.append(replace(lower, origin=origin))
        boxes.append(_translate(lower.bounds, origin))
    if upper is not None:
        rise = max(
            data.value("UpperLimitGapMin", style.size * 0.1) + _depth(upper),
            data.value("UpperLimitBaselineRiseMin", style.size * 0.4),
        )
        origin = ((width - _advance(upper)) / 2, top + rise)
        children.append(replace(upper, origin=origin))
        boxes.append(_translate(upper.bounds, origin))
    bounds = _union(boxes, operator.bounds)
    return MathBox(
        "limits",
        Bounds(0.0, bounds.y_min, width, bounds.y_max),
        0.0,
        children=tuple(children),
        source_range=node.source_range,
    )


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
            units_per_em=float(face.metrics.units_per_em),
            base_size=style.size,
        )
        return _layout(library, expression, style, data)
    finally:
        font.close()
