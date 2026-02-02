"""Core thermodynamic engines and configuration models.

This module contains:
- Physical constants (centralized, NO hard-coding elsewhere)
- Pydantic validation models for configuration inputs
- Thermodynamic property functions (pure functions)
"""

from .constants import (
    ABSOLUTE_ZERO_K,
    DEFAULT_ALPHA,
    DEFAULT_BASE_COP,
    DEFAULT_DISPERSION_COEFF,
    STANDARD_PRESSURE_PA,
    STANDARD_TEMP_K,
)
from .configs import ChillerConfig, WindConfig

__all__ = [
    "ABSOLUTE_ZERO_K",
    "STANDARD_TEMP_K",
    "STANDARD_PRESSURE_PA",
    "DEFAULT_BASE_COP",
    "DEFAULT_ALPHA",
    "DEFAULT_DISPERSION_COEFF",
    "ChillerConfig",
    "WindConfig",
]
