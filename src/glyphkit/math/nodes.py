"""Immutable semantic mathematical expression tree."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from glyphkit.diagnostics import SourceRange


@runtime_checkable
class MathNode(Protocol):
    @property
    def source_range(self) -> SourceRange: ...


@dataclass(frozen=True, slots=True)
class Symbol:
    """One atom. ``role`` is its TeX class and decides spacing around it:

    ``ordinary`` and ``identifier`` (letters, digits), ``binary`` (``+``, ``\\times``),
    ``relation`` (``=``, ``\\le``), ``open`` and ``close`` (brackets), ``punct`` (``,``),
    ``large-operator`` (``\\sum``, ``\\lim``: limits above and below in display style),
    ``integral`` (``\\int``: scripts at the side), ``function`` (``\\sin``, set upright) and
    ``upright`` (``\\mathrm`` and ``\\text``). The older role ``operator`` is read as ``binary``
    or ``relation`` by its character.
    """

    value: str
    source_range: SourceRange
    role: str = "ordinary"


@dataclass(frozen=True, slots=True)
class Space:
    """Horizontal space of ``mu`` math units (1/18 em), as ``\\,`` (3), ``\\:`` (4), ``\\;`` (5)."""

    mu: float
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class Sequence:
    children: tuple[MathNode, ...]
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class Fraction:
    numerator: MathNode
    denominator: MathNode
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class Root:
    radicand: MathNode
    source_range: SourceRange
    index: MathNode | None = None


@dataclass(frozen=True, slots=True)
class Script:
    base: MathNode
    source_range: SourceRange
    subscript: MathNode | None = None
    superscript: MathNode | None = None


@dataclass(frozen=True, slots=True)
class Limits:
    operator: MathNode
    source_range: SourceRange
    lower: MathNode | None = None
    upper: MathNode | None = None


@dataclass(frozen=True, slots=True)
class Delimited:
    left: str
    body: MathNode
    right: str
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class Accent:
    kind: str
    body: MathNode
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class Matrix:
    rows: tuple[tuple[MathNode, ...], ...]
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class ExtensionNode:
    namespace: str
    kind: str
    payload: object
    source_range: SourceRange
