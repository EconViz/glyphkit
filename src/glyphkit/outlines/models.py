"""Renderer-neutral exact outline values."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit.layout import Bounds


@dataclass(frozen=True, slots=True)
class MoveTo:
    point: tuple[float, float]


@dataclass(frozen=True, slots=True)
class LineTo:
    point: tuple[float, float]


@dataclass(frozen=True, slots=True)
class QuadraticTo:
    control: tuple[float, float]
    point: tuple[float, float]


@dataclass(frozen=True, slots=True)
class CubicTo:
    control1: tuple[float, float]
    control2: tuple[float, float]
    point: tuple[float, float]


@dataclass(frozen=True, slots=True)
class ClosePath:
    pass


PathCommand = MoveTo | LineTo | QuadraticTo | CubicTo | ClosePath


@dataclass(frozen=True, slots=True)
class Transform2D:
    xx: float = 1.0
    xy: float = 0.0
    yx: float = 0.0
    yy: float = 1.0
    dx: float = 0.0
    dy: float = 0.0


@dataclass(frozen=True, slots=True)
class GlyphOutline:
    glyph_id: int
    commands: tuple[PathCommand, ...]
    bounds: Bounds
    units_per_em: int


@dataclass(frozen=True, slots=True)
class Polyline:
    points: tuple[tuple[float, float], ...]
    closed: bool
