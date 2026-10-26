"""Atom classes and inter-atom spacing."""

# ruff: noqa: RUF001 -- mathematical symbols are intentional Unicode tokens.

from __future__ import annotations

from glyphkit.math.layout.model import MathStyle
from glyphkit.math.nodes import (
    Delimited,
    Fraction,
    Limits,
    MathNode,
    Script,
    Symbol,
)

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
