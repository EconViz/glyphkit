"""FontTools outline adapter with self-contained compound decomposition."""

from __future__ import annotations

from fontTools.pens.basePen import BasePen

from glyphkit.errors import FontFormatError
from glyphkit.fonts import FontFace
from glyphkit.fonts.parsed import parsed_font
from glyphkit.geometry import Bounds
from glyphkit.outlines.models import (
    ClosePath,
    CubicTo,
    GlyphOutline,
    LineTo,
    MoveTo,
    PathCommand,
    QuadraticTo,
)

Point = tuple[float, float]


def _point(value: Point) -> Point:
    return (float(value[0]), float(value[1]))


class _OutlinePen(BasePen):  # type: ignore[misc]
    def __init__(self, glyph_set: object) -> None:
        super().__init__(glyph_set)
        self.commands: list[PathCommand] = []

    def _moveTo(self, point: Point) -> None:
        self.commands.append(MoveTo(_point(point)))

    def _lineTo(self, point: Point) -> None:
        self.commands.append(LineTo(_point(point)))

    def _curveToOne(self, point1: Point, point2: Point, point3: Point) -> None:
        self.commands.append(
            CubicTo(
                _point(point1),
                _point(point2),
                _point(point3),
            )
        )

    def _qCurveToOne(self, point1: Point, point2: Point) -> None:
        self.commands.append(QuadraticTo(_point(point1), _point(point2)))

    def _closePath(self) -> None:
        self.commands.append(ClosePath())


def _points(command: PathCommand) -> tuple[Point, ...]:
    if isinstance(command, (MoveTo, LineTo)):
        return (command.point,)
    if isinstance(command, QuadraticTo):
        return (command.control, command.point)
    if isinstance(command, CubicTo):
        return (command.control1, command.control2, command.point)
    return ()


def extract_outline(
    face: FontFace,
    glyph_id: int,
    *,
    variation_coordinates: tuple[tuple[str, float], ...] = (),
) -> GlyphOutline:
    try:
        with parsed_font(face) as font:
            glyph_order = font.getGlyphOrder()
            if not 0 <= glyph_id < len(glyph_order):
                raise FontFormatError(f"glyph id {glyph_id} is outside the font glyph order")
            glyph_set = font.getGlyphSet(location=dict(variation_coordinates))
            pen = _OutlinePen(glyph_set)
            glyph_set[glyph_order[glyph_id]].draw(pen)
        commands = tuple(pen.commands)
        points = tuple(point for command in commands for point in _points(command))
        if points:
            xs, ys = zip(*points, strict=True)
            bounds = Bounds(min(xs), min(ys), max(xs), max(ys))
        else:
            bounds = Bounds(0.0, 0.0, 0.0, 0.0)
        return GlyphOutline(
            glyph_id,
            commands,
            bounds,
            face.metrics.units_per_em,
            variation_coordinates,
        )
    except (KeyError, ValueError) as exc:
        raise FontFormatError(f"cannot extract glyph {glyph_id}") from exc
