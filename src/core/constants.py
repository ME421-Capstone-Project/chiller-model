"""Physical constants and COP degradation functions for chiller simulations.

All values in SI units. No hard-coded constants elsewhere in the codebase.

Reference
---------
ASHRAE Handbook - Fundamentals, 2021
"""

import math

import numpy as np

ABSOLUTE_ZERO_K: float = 0.0
"""Absolute zero temperature in Kelvin."""

STANDARD_TEMP_K: float = 298.15
"""Standard reference temperature (25 °C) in Kelvin."""

FREEZING_POINT_WATER_K: float = 273.15
"""Freezing point of water in Kelvin."""

STANDARD_PRESSURE_PA: float = 101325.0
"""Standard atmospheric pressure in Pascals."""

DEFAULT_BASE_COP: float = 4.0
"""Default Coefficient of Performance at rated conditions (AHRI 550/590)."""

DEFAULT_ALPHA: float = 0.7
"""Default sensitivity coefficient to inlet temperature rise (ASHRAE Ch. 43)."""

DEFAULT_DISPERSION_COEFF: float = 1.2
"""Default Gaussian plume dispersion coefficient sigma (ASHRAE Ch. 40)."""

MAX_REALISTIC_COP: float = 10.0
"""Maximum realistic COP for vapor compression cycles."""

MIN_REALISTIC_TEMP_K: float = 200.0
"""Minimum realistic operating temperature in Kelvin (-73 °C)."""

MAX_REALISTIC_TEMP_K: float = 350.0
"""Maximum realistic ambient temperature in Kelvin (77 °C)."""

AGE_MIN_YEARS: float = 0.0
"""Minimum chiller age in years for random assignment."""

AGE_MAX_YEARS: float = 20.0
"""Maximum chiller age in years for random assignment."""

COP_AGE_FRACTION_AT_1_YEAR: float = 0.8
"""COP fraction remaining after 1 year. Exponential decay: factor = exp(-rate * age)."""

COP_AGE_DECAY_TIMESCALE_YEARS: float = 1.0
"""Timescale in years for COP age degradation."""

CHILLER_STARTUP_TIME_HOURS: float = 0.25
"""Time in hours for chiller COP to ramp from 0 to full after turn-on."""

_AGE_DECAY_RATE: float = -math.log(COP_AGE_FRACTION_AT_1_YEAR) / COP_AGE_DECAY_TIMESCALE_YEARS


def compute_cop_age_factor(age_years: float) -> float:
    """Return COP multiplier in [0, 1] for a chiller of given age."""
    if age_years <= 0:
        return 1.0
    return math.exp(-_AGE_DECAY_RATE * age_years)


def compute_cop_age_factors_vectorized(ages_years: np.ndarray) -> np.ndarray:
    """Vectorised COP age factors. Negative ages are clipped to 0."""
    ages_clipped = np.maximum(ages_years, 0.0)
    return np.exp(-_AGE_DECAY_RATE * ages_clipped)


def compute_cop_startup_factor_linear(
    time_since_start_hours: float,
    startup_time_hours: float = CHILLER_STARTUP_TIME_HOURS,
) -> float:
    """Linear COP ramp: 0 at turn-on, 1 after startup_time_hours."""
    if time_since_start_hours <= 0:
        return 0.0
    if startup_time_hours <= 0:
        return 1.0
    return min(1.0, time_since_start_hours / startup_time_hours)


def compute_cop_startup_factors_vectorized(
    time_since_start_hours: np.ndarray,
    startup_time_hours: float = CHILLER_STARTUP_TIME_HOURS,
) -> np.ndarray:
    """Vectorised startup factors. Negative times yield factor 0."""
    factors = np.where(
        time_since_start_hours <= 0,
        0.0,
        np.minimum(1.0, time_since_start_hours / startup_time_hours),
    )
    return factors.astype(np.float64)
