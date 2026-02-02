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
