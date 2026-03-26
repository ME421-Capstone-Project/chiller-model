from typing import Protocol, runtime_checkable


@runtime_checkable
class AmbientTempFn(Protocol):
    """Protocol for a callable that returns ambient temperature (K) at a given time."""

    def __call__(self, time_hours: float) -> float:
        """Return ambient temperature in Kelvin at the given simulation time."""
        ...
