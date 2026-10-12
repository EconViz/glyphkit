"""Validation shared by immutable public values."""

from __future__ import annotations

import math

from glyphkit.errors import ConfigurationError


def finite(value: float | int, *, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ConfigurationError(f"{name} must be finite")
    return result


def non_negative(value: float | int, *, name: str) -> float:
    result = finite(value, name=name)
    if result < 0:
        raise ConfigurationError(f"{name} must be non-negative")
    return result


def positive(value: float | int, *, name: str) -> float:
    result = finite(value, name=name)
    if result <= 0:
        raise ConfigurationError(f"{name} must be positive")
    return result

