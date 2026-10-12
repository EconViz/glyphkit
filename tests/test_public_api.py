from dataclasses import FrozenInstanceError

import pytest

from glyphkit import (
    ConfigurationError,
    Diagnostic,
    DiagnosticSeverity,
    GlyphKitError,
    SourceRange,
)
from glyphkit._validation import finite, positive


def test_public_values_are_immutable() -> None:
    value = Diagnostic("font.missing", DiagnosticSeverity.ERROR, "missing", SourceRange(1, 2))
    with pytest.raises(FrozenInstanceError):
        value.code = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("start,end", [(-1, 0), (2, 1)])
def test_source_range_rejects_invalid_offsets(start: int, end: int) -> None:
    with pytest.raises(ConfigurationError):
        SourceRange(start, end)


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_finite_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ConfigurationError):
        finite(value, name="value")


def test_positive_rejects_zero() -> None:
    with pytest.raises(ConfigurationError):
        positive(0, name="size")


def test_configuration_error_belongs_to_public_hierarchy() -> None:
    assert issubclass(ConfigurationError, GlyphKitError)

