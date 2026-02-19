"""Core thermodynamic engines and configuration models.

This module contains:
- Physical constants (centralized, NO hard-coding elsewhere)
- Pydantic validation models for configuration inputs
- Thermodynamic property functions (pure functions)
"""

from .constants import (
    ABSOLUTE_ZERO_K,
    AGE_MAX_YEARS,
    AGE_MIN_YEARS,
    COP_AGE_DECAY_TIMESCALE_YEARS,
    COP_AGE_FRACTION_AT_1_YEAR,
    DEFAULT_ALPHA,
    DEFAULT_BASE_COP,
    DEFAULT_DISPERSION_COEFF,
    STANDARD_PRESSURE_PA,
    STANDARD_TEMP_K,
    compute_cop_age_factor,
    compute_cop_age_factors_vectorized,
)
from .configs import ChillerConfig, WindConfig

__all__ = [
    "ABSOLUTE_ZERO_K",
    "STANDARD_TEMP_K",
    "STANDARD_PRESSURE_PA",
    "DEFAULT_BASE_COP",
    "DEFAULT_ALPHA",
    "DEFAULT_DISPERSION_COEFF",
    "AGE_MIN_YEARS",
    "AGE_MAX_YEARS",
    "COP_AGE_FRACTION_AT_1_YEAR",
    "COP_AGE_DECAY_TIMESCALE_YEARS",
    "compute_cop_age_factor",
    "compute_cop_age_factors_vectorized",
    "ChillerConfig",
    "WindConfig",
]
