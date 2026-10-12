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
    value: str
    source_range: SourceRange
    role: str = "ordinary"


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
