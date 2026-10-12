"""Explicit tolerance-bounded curve flattening."""

from __future__ import annotations

import math

from glyphkit._validation import positive
from glyphkit.outlines.models import (
    ClosePath,
    CubicTo,
    GlyphOutline,
    LineTo,
    MoveTo,
    Polyline,
    QuadraticTo,
)

Point = tuple[float, float]


def _distance(point: Point, start: Point, end: Point) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    if dx == dy == 0:
        return math.dist(point, start)
    return abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]) / math.hypot(
        dx, dy
    )


def _quadratic(start: Point, control: Point, end: Point, tolerance: float) -> list[Point]:
    if _distance(control, start, end) <= tolerance:
        return [end]
    a = ((start[0] + control[0]) / 2, (start[1] + control[1]) / 2)
    b = ((control[0] + end[0]) / 2, (control[1] + end[1]) / 2)
    middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return _quadratic(start, a, middle, tolerance) + _quadratic(middle, b, end, tolerance)


def _cubic(start: Point, c1: Point, c2: Point, end: Point, tolerance: float) -> list[Point]:
    if max(_distance(c1, start, end), _distance(c2, start, end)) <= tolerance:
        return [end]
    p01 = ((start[0] + c1[0]) / 2, (start[1] + c1[1]) / 2)
    p12 = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
    p23 = ((c2[0] + end[0]) / 2, (c2[1] + end[1]) / 2)
    p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
    p123 = ((p12[0] + p23[0]) / 2, (p12[1] + p23[1]) / 2)
    middle = ((p012[0] + p123[0]) / 2, (p012[1] + p123[1]) / 2)
    return _cubic(start, p01, p012, middle, tolerance) + _cubic(middle, p123, p23, end, tolerance)


def flatten(outline: GlyphOutline, *, tolerance: float) -> tuple[Polyline, ...]:
    resolved_tolerance = positive(tolerance, name="flattening tolerance")
    contours: list[Polyline] = []
    points: list[Point] = []
    current = (0.0, 0.0)
    for command in outline.commands:
        if isinstance(command, MoveTo):
            if points:
                contours.append(Polyline(tuple(points), False))
            points = [command.point]
            current = command.point
        elif isinstance(command, LineTo):
            points.append(command.point)
            current = command.point
        elif isinstance(command, QuadraticTo):
            points.extend(_quadratic(current, command.control, command.point, resolved_tolerance))
            current = command.point
        elif isinstance(command, CubicTo):
            points.extend(
                _cubic(
                    current, command.control1, command.control2, command.point, resolved_tolerance
                )
            )
            current = command.point
        elif isinstance(command, ClosePath) and points:
            contours.append(Polyline(tuple(points), True))
            points = []
    if points:
        contours.append(Polyline(tuple(points), False))
    return tuple(contours)
