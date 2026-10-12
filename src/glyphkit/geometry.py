"""Small renderer-neutral geometric values shared across package layers."""

from __future__ import annotations

from dataclasses import dataclass

from glyphkit._validation import finite
from glyphkit.errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class Bounds:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        for name in ("x_min", "y_min", "x_max", "y_max"):
            object.__setattr__(self, name, finite(getattr(self, name), name=name))
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise ConfigurationError("bounds maxima must not be smaller than minima")

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min
