"""Pydantic validation models for chiller simulation configurations.

All inputs are validated for physical plausibility before being used
in simulations. Internal units follow SI standards (K, Pa, kg/s, J).

Reference
---------
AHRI Standard 550/590-2015 for chiller rating conditions
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
    """Validated chiller configuration.

    All inputs validated for physical plausibility.
    Internal units: SI (K, Pa, kg/s, J).

    Attributes
    ----------
    base_cop : float
        Coefficient of Performance at rated conditions.
        Must be positive and <= 10 (thermodynamic limit).
    rated_capacity_kw : float
        Rated cooling capacity in kilowatts.
    alpha : float
        Sensitivity coefficient to inlet temperature rise.
        Determines COP degradation rate.

    Reference
    ---------
    AHRI Standard 550/590-2015

    Examples
    --------
    >>> config = ChillerConfig(base_cop=5.0, rated_capacity_kw=500.0)
    >>> config.alpha
    0.7
    """

    base_cop: float = Field(
        default=DEFAULT_BASE_COP,
        gt=0,
        le=MAX_REALISTIC_COP,
        description="COP at rated conditions",
    )
    rated_capacity_kw: float = Field(
        ...,
        gt=0,
        description="Rated cooling capacity in kW",
    )
    alpha: float = Field(
        default=DEFAULT_ALPHA,
        gt=0,
        le=2.0,
        description="Inlet temperature sensitivity coefficient",
    )

    @field_validator("base_cop")
    @classmethod
    def validate_cop_physical(cls, v: float) -> float:
        """Validate COP is physically realistic.

        Parameters
        ----------
        v : float
            The COP value to validate.

        Returns
        -------
        float
            The validated COP value.

        Raises
        ------
        ValueError
            If COP exceeds thermodynamic limits.
        """
        if v > MAX_REALISTIC_COP:
            raise ValueError(
                f"COP > {MAX_REALISTIC_COP} is non-physical for vapor compression cycles"
            )
        return v


class WindConfig(BaseModel):
    """Validated wind configuration.

    Attributes
    ----------
    velocity_x_m_per_s : float
        X-component of wind velocity in m/s.
    velocity_y_m_per_s : float
        Y-component of wind velocity in m/s.
    ambient_temp_k : float
        Ambient dry-bulb temperature in Kelvin.
        Must be above absolute zero.

    Reference
    ---------
    ASHRAE Handbook - Fundamentals, Chapter 24 (Airflow)

    Examples
    --------
    >>> config = WindConfig(
    ...     velocity_x_m_per_s=5.0,
    ...     velocity_y_m_per_s=0.0,
    ...     ambient_temp_k=298.15
    ... )
    """

    velocity_x_m_per_s: float = Field(
        ...,
        description="X-component of wind velocity in m/s",
    )
    velocity_y_m_per_s: float = Field(
        ...,
        description="Y-component of wind velocity in m/s",
    )
    ambient_temp_k: float = Field(
        ...,
        gt=0,
        description="Ambient temperature in Kelvin",
    )

    @field_validator("ambient_temp_k")
    @classmethod
    def validate_temp_physical(cls, v: float) -> float:
        """Validate temperature is physically realistic.

        Parameters
        ----------
        v : float
            The temperature value to validate.

        Returns
        -------
        float
            The validated temperature value.

        Raises
        ------
        ValueError
            If temperature is below absolute zero or outside
            realistic operating range.
        """
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
    """Configuration for a complete simulation run.

    Attributes
    ----------
    dispersion_coeff : float
        Gaussian plume dispersion coefficient (sigma).
    total_load_kw : float
        Total cooling load to be distributed across chillers.

    Reference
    ---------
    ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
    """

    dispersion_coeff: float = Field(
        default=DEFAULT_DISPERSION_COEFF,
        gt=0,
        le=5.0,
        description="Gaussian plume dispersion coefficient",
    )
    total_load_kw: float = Field(
        ...,
        gt=0,
        description="Total cooling load in kW",
    )
