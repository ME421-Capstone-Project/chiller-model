from typing import Protocol, runtime_checkable


@runtime_checkable
class LoadFn(Protocol):
    """Protocol for a callable that returns total facility load (kW) at a given time."""

    def __call__(self, time_hours: float) -> float:
        """Return total facility load in kW at the given simulation time."""
        ...
