from __future__ import annotations

from typing import Protocol, runtime_checkable

_STARTUP_TIME_HOURS = 0.25


@runtime_checkable
class RampFn(Protocol):
    def __call__(self, time_since_start_hours: float) -> float:
        ...


def default_ramp_fn(time_since_start_hours: float) -> float:
    return min(1.0, time_since_start_hours / _STARTUP_TIME_HOURS)
