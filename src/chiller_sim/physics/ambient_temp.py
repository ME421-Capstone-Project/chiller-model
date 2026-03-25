from typing import Protocol, runtime_checkable


@runtime_checkable
class AmbientTempFn(Protocol):
    def __call__(self, time_hours: float) -> float:
        ...
