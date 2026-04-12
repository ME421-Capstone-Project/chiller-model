from __future__ import annotations

from typing import Protocol, runtime_checkable

_STARTUP_TIME_HOURS = 2.0
_INITIAL_RAMP = 0.1


@runtime_checkable
class RampFn(Protocol):
    """Protocol for a callable that returns a startup ramp multiplier."""

    def __call__(self, time_since_start_hours: float) -> float:
        """Return a ramp multiplier in [0, 1] based on time since chiller start."""
        ...


def default_ramp_fn(
    initial_ramp: float = _INITIAL_RAMP,
    startup_time_hours: float = _STARTUP_TIME_HOURS,
) -> RampFn:
    """Return a linear ramp function that starts at *initial_ramp* and reaches 1.0
    after *startup_time_hours*.  The multiplier stays at 1.0 beyond that point."""

    def _fn(time_since_start_hours: float) -> float:
        if time_since_start_hours >= startup_time_hours:
            return 1.0
        return initial_ramp + (1.0 - initial_ramp) * time_since_start_hours / startup_time_hours

    return _fn
