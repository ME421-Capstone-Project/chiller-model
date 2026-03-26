from __future__ import annotations

import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class DegradationFn(Protocol):
    """Protocol for a callable that returns a capacity multiplier based on chiller age."""

    def __call__(self, age_years: float) -> float:
        """Return a capacity multiplier in (0, 1] for a chiller of the given age."""
        ...


def default_capacity_degradation_fn(years_to_80_pct: float) -> DegradationFn:
    """Return a capacity degradation function that reaches 80% at years_to_80_pct years."""
    rate = -math.log(0.8) / years_to_80_pct

    def _fn(age_years: float) -> float:
        return math.exp(-rate * age_years)

    return _fn
