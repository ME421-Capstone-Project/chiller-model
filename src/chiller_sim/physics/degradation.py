from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

# Rate chosen so degradation_fn(1.0) == 0.8
_DECAY_RATE = -math.log(0.8)  # ≈ 0.2231


@runtime_checkable
class DegradationFn(Protocol):
    def __call__(self, age_years: float) -> float:
        ...


def default_degradation_fn(age_years: float) -> float:
    return math.exp(-_DECAY_RATE * age_years)
