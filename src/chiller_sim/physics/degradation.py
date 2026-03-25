from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

# Rate chosen so degradation_fn(1.0) == 0.8
_DECAY_RATE = -math.log(0.8)  # ≈ 0.2231


@runtime_checkable
class DegradationFn(Protocol):
    """Protocol for a callable that returns a COP multiplier based on chiller age."""

    def __call__(self, age_years: float) -> float:
        """Return a COP multiplier in (0, 1] for a chiller of the given age."""
        ...


def default_degradation_fn(age_years: float) -> float:
    """Return exponential COP degradation factor for a chiller of the given age."""
    return math.exp(-_DECAY_RATE * age_years)
