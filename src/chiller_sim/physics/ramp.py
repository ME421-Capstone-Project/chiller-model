from __future__ import annotations

from typing import Protocol, runtime_checkable

_STARTUP_TIME_HOURS = 0.25


@runtime_checkable
class RampFn(Protocol):
    """Protocol for a callable that returns a startup ramp multiplier."""

    def __call__(self, time_since_start_hours: float) -> float:
        """Return a ramp multiplier in [0, 1] based on time since chiller start."""
        ...


def default_ramp_fn(time_since_start_hours: float) -> float:
    """Return a linear ramp multiplier that reaches 1.0 after the startup period."""
    return min(1.0, time_since_start_hours / _STARTUP_TIME_HOURS)
