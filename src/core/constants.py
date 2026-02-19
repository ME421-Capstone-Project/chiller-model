"""Physical constants for chiller simulations.

All values in SI units. NO hard-coded constants elsewhere in the codebase.
Import constants from this module to ensure consistency across the package.

Reference
---------
ASHRAE Handbook - Fundamentals, 2021
"""

# =============================================================================
# Temperature Constants
# =============================================================================

ABSOLUTE_ZERO_K: float = 0.0
"""Absolute zero temperature in Kelvin."""

STANDARD_TEMP_K: float = 298.15
"""Standard reference temperature (25°C) in Kelvin."""

FREEZING_POINT_WATER_K: float = 273.15
"""Freezing point of water in Kelvin."""

# =============================================================================
# Pressure Constants
# =============================================================================

STANDARD_PRESSURE_PA: float = 101325.0
"""Standard atmospheric pressure in Pascals."""

# =============================================================================
# Default Chiller Parameters
# =============================================================================

DEFAULT_BASE_COP: float = 4.0
"""Default Coefficient of Performance at rated conditions.

Reference: Typical range for water-cooled centrifugal chillers is 5-7,
air-cooled chillers is 2.5-4.0 (AHRI Standard 550/590-2015).
"""

DEFAULT_ALPHA: float = 0.7
"""Default sensitivity coefficient to inlet temperature rise.

This coefficient determines how much the COP degrades per unit 
temperature rise at the chiller inlet. Higher values indicate 
greater sensitivity to thermal interference.

Reference: ASHRAE Handbook - HVAC Applications, Chapter 43
"""

DEFAULT_DISPERSION_COEFF: float = 1.2
"""Default Gaussian plume dispersion coefficient (sigma).

Controls the lateral spread of thermal plumes. Higher values 
indicate faster dispersion (less concentrated plumes).

Reference: ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
"""

# =============================================================================
# Physical Limits for Validation
# =============================================================================

MAX_REALISTIC_COP: float = 10.0
"""Maximum realistic COP for vapor compression cycles.

Carnot efficiency limits COP based on temperature lift. Values 
above 10 are non-physical for practical HVAC applications.
"""

MIN_REALISTIC_TEMP_K: float = 200.0
"""Minimum realistic operating temperature in Kelvin (-73°C).

Below this, refrigerant properties become problematic.
"""

MAX_REALISTIC_TEMP_K: float = 350.0
"""Maximum realistic ambient temperature in Kelvin (77°C).

Above this, standard chiller operation is not feasible.
"""

# =============================================================================
# Chiller Age and COP Degradation
# =============================================================================

AGE_MIN_YEARS: float = 0.0
"""Minimum chiller age in years for random assignment.

Used when ages are not manually specified at simulation start.
"""

AGE_MAX_YEARS: float = 20.0
"""Maximum chiller age in years for random assignment.

Used when ages are not manually specified at simulation start.
"""

COP_AGE_FRACTION_AT_1_YEAR: float = 0.8
"""COP fraction remaining after 1 year of operation.

COP decays exponentially with age. At age=0, factor=1.0 (100%).
At age=1 year, factor=0.8 (80%). Change this to adjust degradation rate.

Reference: Typical chiller efficiency loss 1-2% per year (ASHRAE).
"""

COP_AGE_DECAY_TIMESCALE_YEARS: float = 1.0
"""Timescale in years for COP age degradation.

Time over which COP decays from 100% to COP_AGE_FRACTION_AT_1_YEAR.
Change this to stretch or compress the decay curve.
"""


def compute_cop_age_factor(age_years: float) -> float:
    """Compute COP multiplier from chiller age (exponential decay).

    COP decays from 100% at age=0 to COP_AGE_FRACTION_AT_1_YEAR at age=1 year.
    Formula: factor = exp(-decay_rate * age_years) where decay_rate is derived
    from the constants above.

    Parameters
    ----------
    age_years : float
        Chiller age in years (must be >= 0).

    Returns
    -------
    float
        COP multiplier in [0, 1]. Multiply base_cop by this for age-degraded COP.

    Notes
    -----
    All numerical constants (fraction at 1 year, timescale) are in this module.
    """
    import math

    if age_years <= 0:
        return 1.0
    decay_rate = -math.log(COP_AGE_FRACTION_AT_1_YEAR) / COP_AGE_DECAY_TIMESCALE_YEARS
    return math.exp(-decay_rate * age_years)


def compute_cop_age_factors_vectorized(ages_years: "np.ndarray") -> "np.ndarray":
    """Compute COP multipliers for an array of chiller ages (vectorized).

    Uses NumPy for performance. Same formula as compute_cop_age_factor.

    Parameters
    ----------
    ages_years : np.ndarray
        Chiller ages in years, shape (N,). Values < 0 are treated as 0.

    Returns
    -------
    np.ndarray
        COP multipliers, shape (N,). Multiply base_cop element-wise for age-degraded COP.
    """
    import numpy as np

    decay_rate = -np.log(COP_AGE_FRACTION_AT_1_YEAR) / COP_AGE_DECAY_TIMESCALE_YEARS
    ages_clipped = np.maximum(ages_years, 0.0)
    return np.exp(-decay_rate * ages_clipped)
