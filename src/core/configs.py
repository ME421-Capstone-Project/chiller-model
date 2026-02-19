"""Pydantic validation models for simulation inputs.

All inputs are validated for physical plausibility. Internal units are SI.

Reference
---------
AHRI Standard 550/590-2015
"""

from pydantic import BaseModel, Field, field_validator

from .constants import (
    DEFAULT_ALPHA,
    DEFAULT_BASE_COP,
    DEFAULT_DISPERSION_COEFF,
    MAX_REALISTIC_COP,
    MAX_REALISTIC_TEMP_K,
    MIN_REALISTIC_TEMP_K,
)


class ChillerConfig(BaseModel):
    """Validated chiller configuration (COP, capacity, sensitivity)."""

    base_cop: float = Field(
        default=DEFAULT_BASE_COP,
        gt=0,
        le=MAX_REALISTIC_COP,
    )
    rated_capacity_kw: float = Field(..., gt=0)
    alpha: float = Field(default=DEFAULT_ALPHA, gt=0, le=2.0)

    @field_validator("base_cop")
    @classmethod
    def validate_cop_physical(cls, v: float) -> float:
        """Reject COP values that exceed thermodynamic limits."""
        if v > MAX_REALISTIC_COP:
            raise ValueError(
                f"COP > {MAX_REALISTIC_COP} is non-physical for vapor compression cycles"
            )
        return v


class WindConfig(BaseModel):
    """Validated wind configuration (velocity components, ambient temperature)."""

    velocity_x_m_per_s: float
    velocity_y_m_per_s: float
    ambient_temp_k: float = Field(..., gt=0)

    @field_validator("ambient_temp_k")
    @classmethod
    def validate_temp_physical(cls, v: float) -> float:
        """Reject temperatures outside realistic operating range."""
        if v <= 0:
            raise ValueError("Temperature must be > 0 K (above absolute zero)")
        if v < MIN_REALISTIC_TEMP_K:
            raise ValueError(
                f"Temperature {v} K is below realistic operating range "
                f"(min: {MIN_REALISTIC_TEMP_K} K)"
            )
        if v > MAX_REALISTIC_TEMP_K:
            raise ValueError(
                f"Temperature {v} K is above realistic operating range "
                f"(max: {MAX_REALISTIC_TEMP_K} K)"
            )
        return v


class SimulationConfig(BaseModel):
    """Validated simulation-run configuration (dispersion, total load)."""

    dispersion_coeff: float = Field(
        default=DEFAULT_DISPERSION_COEFF, gt=0, le=5.0
    )
    total_load_kw: float = Field(..., gt=0)
