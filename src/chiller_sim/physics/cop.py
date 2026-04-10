from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CopFn(Protocol):
    """Protocol for a callable that computes effective COP given operating conditions."""

    def __call__(
        self,
        base_cop: float,
        temp_rise_k: float,
        ambient_temp_k: float,
        age_years: float = 0.0,
    ) -> float:
        """Return effective COP given base COP, thermal rise, ambient temperature, and age."""
        ...


def default_cop_fn(alpha: float, cop_loss_per_year: float = 0.012) -> CopFn:
    """Return the default COP function with thermal and age-based degradation.

    Parameters
    ----------
    alpha : float
        Sensitivity of COP to condenser inlet temperature rise (K⁻¹).
    cop_loss_per_year : float
        Fractional COP loss per year of chiller age.  Default 1.2 %/yr
        reflects typical centrifugal chiller performance decline due to
        refrigerant leakage, fouling, and mechanical wear
        (ASHRAE 2021 Handbook, Chapter 38).
    """

    def _cop(
        base_cop: float,
        temp_rise_k: float,
        ambient_temp_k: float,
        age_years: float = 0.0,
    ) -> float:
        age_factor = max(0.0, 1.0 - cop_loss_per_year * age_years)
        return base_cop * age_factor / (1.0 + alpha * temp_rise_k)

    return _cop
