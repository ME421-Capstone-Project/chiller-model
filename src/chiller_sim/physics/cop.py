from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CopFn(Protocol):
    def __call__(self, base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        ...


def default_cop_fn(alpha: float) -> CopFn:
    """Factory returning the default COP function closed over alpha."""
    def _cop(base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        return base_cop / (1.0 + alpha * temp_rise_k)
    return _cop
