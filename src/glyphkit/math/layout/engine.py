"""Recursive math layout: sequences, scripts and limits."""

from __future__ import annotations

from dataclasses import replace

from glyphkit.errors import UnsupportedFeatureError
from glyphkit.fonts import FontLibrary
from glyphkit.geometry import Bounds
from glyphkit.math.layout.metrics import (
    _advance,
    _depth,
    _fraction_style,
    _height,
    _ink,
    _math_glyph_id,
    _script_style,
    _text_box,
    _translate,
    _union,
)
from glyphkit.math.layout.model import MathBox, MathRule, MathStyle, _MathData
from glyphkit.math.layout.shapes import _enlarged, _sized_to
from glyphkit.math.layout.spacing import _atom_classes, _gap
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
