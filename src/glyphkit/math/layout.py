"""Backend-neutral mathematical box layout."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit.errors import UnsupportedFeatureError
from glyphkit.fonts import FontLibrary, FontQuery
from glyphkit.layout import Bounds, Paragraph, TextLayout, TextSpan, TextStyle, layout_paragraph
from glyphkit.math.nodes import (
    Accent,
    Delimited,
    Fraction,
    MathNode,
    Matrix,
    Root,
    Script,
    Sequence,
    Symbol,
)


@dataclass(frozen=True, slots=True)
class MathStyle:
    size: float
    families: tuple[str, ...]
    level: str = "display"


@dataclass(frozen=True, slots=True)
class MathRule:
    start: tuple[float, float]
    end: tuple[float, float]
    thickness: float


@dataclass(frozen=True, slots=True)
class MathBox:
    kind: str
    bounds: Bounds
    baseline: float
    text_layout: TextLayout | None = None
    children: tuple[MathBox, ...] = ()
    rules: tuple[MathRule, ...] = ()


def _text_box(library: FontLibrary, text: str, style: MathStyle) -> MathBox:
    layout = layout_paragraph(
        library,
        Paragraph((TextSpan(text, TextStyle(style.families, style.size)),)),
    )
    return MathBox("text", layout.logical_bounds, 0.0, layout)


def _layout(library: FontLibrary, node: MathNode, style: MathStyle) -> MathBox:
    if isinstance(node, Symbol):
        return _text_box(library, node.value, style)
    if isinstance(node, Sequence):
        children = tuple(_layout(library, child, style) for child in node.children)
        width = sum(child.bounds.width for child in children)
        height = max((child.bounds.height for child in children), default=style.size)
        return MathBox(
            "sequence", Bounds(0, -style.size * 0.2, width, height), 0, children=children
        )
    if isinstance(node, Fraction):
        smaller = MathStyle(style.size * 0.8, style.families, "text")
        numerator = _layout(library, node.numerator, smaller)
        denominator = _layout(library, node.denominator, smaller)
        width = max(numerator.bounds.width, denominator.bounds.width) + style.size * 0.4
        gap = style.size * 0.25
        bounds = Bounds(0, -(denominator.bounds.height + gap), width, numerator.bounds.height + gap)
        rule = MathRule((0, 0), (width, 0), max(1.0, style.size * 0.06))
        return MathBox("fraction", bounds, 0, children=(numerator, denominator), rules=(rule,))
    if isinstance(node, Script):
        base = _layout(library, node.base, style)
        script_style = MathStyle(style.size * 0.7, style.families, "script")
        script_children = [base]
        if node.subscript is not None:
            script_children.append(_layout(library, node.subscript, script_style))
        if node.superscript is not None:
            script_children.append(_layout(library, node.superscript, script_style))
        width = base.bounds.width + max(
            (child.bounds.width for child in script_children[1:]), default=0
        )
        return MathBox(
            "script",
            Bounds(0, -style.size * 0.5, width, style.size * 1.2),
            0,
            children=tuple(script_children),
        )
    if isinstance(node, Root):
        body = _layout(library, node.radicand, style)
        radical = _text_box(library, "√", style)
        width = radical.bounds.width + body.bounds.width
        rule = MathRule(
            (radical.bounds.width, body.bounds.y_max),
            (width, body.bounds.y_max),
            max(1.0, style.size * 0.05),
        )
        return MathBox(
            "root",
            Bounds(0, body.bounds.y_min, width, body.bounds.y_max + style.size * 0.1),
            0,
            children=(radical, body),
            rules=(rule,),
        )
    if isinstance(node, Delimited):
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
        )
    if isinstance(node, Accent):
        body = _layout(library, node.body, style)
        return MathBox(
            node.kind,
            Bounds(0, body.bounds.y_min, body.bounds.width, body.bounds.y_max + style.size * 0.25),
            0,
            children=(body,),
        )
    if isinstance(node, Matrix):
        rows = tuple(tuple(_layout(library, cell, style) for cell in row) for row in node.rows)
        flat = tuple(cell for row in rows for cell in row)
        columns = max((len(row) for row in rows), default=0)
        width = (
            columns * max((cell.bounds.width for cell in flat), default=0)
            + max(0, columns - 1) * style.size * 0.5
        )
        height = len(rows) * style.size * 1.3
        return MathBox("matrix", Bounds(0, -height / 2, width, height / 2), 0, children=flat)
    raise UnsupportedFeatureError(f"math node is not supported: {type(node).__name__}")


def layout_math(library: FontLibrary, expression: MathNode, *, style: MathStyle) -> MathBox:
    face = library.match(FontQuery(style.families)).face
    if not face.has_math:
        raise UnsupportedFeatureError(f"font {face.family!r} has no OpenType MATH table")
    return _layout(library, expression, style)
