from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CopFn(Protocol):
    """Protocol for a callable that computes effective COP given operating conditions."""

    def __call__(self, base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        """Return effective COP given base COP, thermal rise, and ambient temperature."""
        ...


def default_cop_fn(alpha: float) -> CopFn:
    """Return the default COP function closed over the degradation coefficient alpha."""

    def _cop(base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        return base_cop / (1.0 + alpha * temp_rise_k)

    return _cop
