import pytest

from glyphkit import ConfigurationError
from glyphkit.layout import Bounds
from glyphkit.outlines import ClosePath, GlyphOutline, MoveTo, QuadraticTo, flatten


def test_flattening_is_explicit_and_does_not_mutate_exact_commands() -> None:
    outline = GlyphOutline(
        1,
        (MoveTo((0, 0)), QuadraticTo((50, 100), (100, 0)), ClosePath()),
        Bounds(0, 0, 100, 100),
        1000,
    )
    polylines = flatten(outline, tolerance=1)
    assert polylines[0].closed
    assert len(polylines[0].points) > 3
    assert isinstance(outline.commands[1], QuadraticTo)


@pytest.mark.parametrize("tolerance", [0, -1, float("nan")])
def test_flattening_rejects_invalid_tolerance(tolerance: float) -> None:
    with pytest.raises(ConfigurationError):
        flatten(GlyphOutline(1, (), Bounds(0, 0, 0, 0), 1000), tolerance=tolerance)
