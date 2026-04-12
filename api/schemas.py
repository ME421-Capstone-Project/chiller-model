"""Pydantic request / response models for the simulation API."""

from __future__ import annotations

import math
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LoadProfileType(str, Enum):
    """Supported load-profile shapes."""

    constant = "constant"
    sinusoidal = "sinusoidal"
    step = "step"


class WindMode(str, Enum):
    """Supported wind modes."""

    constant = "constant"
    rotating = "rotating"


class SimulationRequest(BaseModel):
    """Parameters accepted by POST /api/simulate and /api/simulate/stream."""

    model_config = ConfigDict(frozen=True)

    # Grid layout
    rows: int = Field(ge=1, le=10, default=3)
    cols: int = Field(ge=1, le=10, default=5)
    spacing_m: float = Field(gt=0, le=100, default=10.0)

    # Chiller properties
    base_cop: float = Field(gt=0, le=10, default=4.0)
    max_cooling_kw: float = Field(gt=0, le=5000, default=500.0)
    alpha: float = Field(ge=0, le=5, default=0.7)

    # Chiller ages
    ages_seed: int | None = Field(default=42, ge=0, le=999999)

    # Wind
    wind_mode: WindMode = WindMode.rotating
    wind_speed: float = Field(ge=0, le=50, default=5.0)
    wind_angle: float = Field(ge=0, le=360, default=90.0)
    wind_center_angle: float = Field(ge=0, le=360, default=90.0)
    wind_amplitude_deg: float = Field(ge=0, le=180, default=60.0)
    wind_period_hours: float = Field(gt=0, le=168, default=12.0)

    # Ambient temperature (Kelvin)
    ambient_temp_k: float = Field(gt=200, lt=350, default=298.15)

    # Load profile
    load_profile: LoadProfileType = LoadProfileType.sinusoidal
    base_load_kw: float = Field(gt=0, le=50000, default=1200.0)
    amplitude_kw: float = Field(ge=0, le=50000, default=400.0)
    period_hours: float = Field(gt=0, le=168, default=12.0)

    # Simulation control
    duration_hours: float = Field(gt=0, le=168, default=24.0)
    time_step_hours: float = Field(gt=0, le=24, default=0.5)

    # Advanced (optional)
    dispersion_coeff: float | None = Field(default=None, ge=0.1, le=10.0)
    heat_rejection_scale: float | None = Field(default=None, ge=1.0, le=50.0)
    switching_threshold_kw: float | None = Field(default=None, ge=0)


class StepResponse(BaseModel):
    """Serialised OptimizeResult for a single time step."""

    model_config = ConfigDict(frozen=True)

    time_hours: float
    load_kw: float
    active_mask: list[bool]
    total_work_kw: float
    baseline_work_kw: float
    savings_fraction: float
    cop_array: list[float]
    temp_rise_array: list[float]
    wind_angle: float
    wind_speed: float
    ramp_factors: list[float]


class SimulationResponse(BaseModel):
    """Full simulation result returned by the synchronous endpoint."""

    model_config = ConfigDict(frozen=True)

    steps: list[StepResponse]
    num_chillers: int
    rows: int
    cols: int
    ages_years: list[float]


def build_load_fn(
    profile: LoadProfileType,
    base_load_kw: float,
    amplitude_kw: float,
    period_hours: float,
) -> callable:
    """Build a load function from the request parameters."""
    if profile == LoadProfileType.constant:
        return lambda t: base_load_kw

    if profile == LoadProfileType.sinusoidal:
        return lambda t: base_load_kw + amplitude_kw * math.sin(
            2 * math.pi * t / period_hours
        )

    def _step_load(t: float) -> float:
        phase = (t % period_hours) / period_hours
        return base_load_kw + amplitude_kw if phase < 0.5 else base_load_kw

    return _step_load


def build_wind_fn(
    center_angle: float,
    amplitude_deg: float,
    period_hours: float,
    speed: float,
) -> callable:
    """Build a rotating wind function."""

    def _rotating_wind(time_hours: float) -> tuple[float, float]:
        angle = center_angle + amplitude_deg * math.sin(
            2 * math.pi * time_hours / period_hours
        )
        return (speed, angle)

    return _rotating_wind
