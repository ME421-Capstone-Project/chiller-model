"""Core thermodynamic constants and configuration validation."""

from .configs import ChillerConfig, SimulationConfig, WindConfig
from .constants import (
    ABSOLUTE_ZERO_K,
    AGE_MAX_YEARS,
    AGE_MIN_YEARS,
    CHILLER_STARTUP_TIME_HOURS,
    COP_AGE_DECAY_TIMESCALE_YEARS,
    COP_AGE_FRACTION_AT_1_YEAR,
    DEFAULT_ALPHA,
    DEFAULT_BASE_COP,
    DEFAULT_DISPERSION_COEFF,
    STANDARD_PRESSURE_PA,
    STANDARD_TEMP_K,
    compute_cop_age_factor,
    compute_cop_age_factors_vectorized,
    compute_cop_startup_factor_linear,
    compute_cop_startup_factors_vectorized,
)

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
    "CHILLER_STARTUP_TIME_HOURS",
    "compute_cop_age_factor",
    "compute_cop_age_factors_vectorized",
    "compute_cop_startup_factor_linear",
    "compute_cop_startup_factors_vectorized",
    "ChillerConfig",
    "SimulationConfig",
    "WindConfig",
]
