"""Bridge between the API layer and the chiller_sim package."""

from __future__ import annotations

import math
from collections.abc import Generator

import numpy as np
from numpy.typing import NDArray

from chiller_sim import Simulator
from chiller_sim.physics.ramp import default_ramp_fn
from chiller_sim.simulation.results import OptimizeResult

from schemas import (
    SimulationRequest,
    StepResponse,
    WindMode,
    build_load_fn,
    build_wind_fn,
)

_DEFAULT_RAMP = default_ramp_fn()


class _RampTracker:
    """Tracks per-chiller time_since_start across steps to compute ramp factors."""

    def __init__(self, n: int, time_step_hours: float) -> None:
        self._n = n
        self._dt = time_step_hours
        self._time_since_start: NDArray[np.float64] = np.zeros(n)
        self._prev_active: NDArray[np.bool_] = np.zeros(n, dtype=bool)
        self._is_first = True

    def update(self, active_mask: list[bool]) -> list[float]:
        mask = np.array(active_mask, dtype=bool)

        if self._is_first:
            self._time_since_start[mask] = np.inf
            self._time_since_start[~mask] = 0.0
            self._is_first = False
        else:
            newly_on = mask & ~self._prev_active
            still_on = mask & self._prev_active
            self._time_since_start[newly_on] = 0.0
            self._time_since_start[still_on] += self._dt
            self._time_since_start[~mask] = 0.0

        self._prev_active = mask.copy()

        factors = np.array(
            [_DEFAULT_RAMP(t) if m else 0.0
             for t, m in zip(self._time_since_start, mask)]
        )
        return factors.tolist()


def _step_to_response(
    step: OptimizeResult,
    wind_speed: float,
    wind_angle: float,
    ramp_factors: list[float],
) -> StepResponse:
    """Convert a chiller_sim OptimizeResult into a serialisable StepResponse."""
    return StepResponse(
        time_hours=step.time_hours,
        load_kw=step.load_kw,
        active_mask=step.active_mask.tolist(),
        total_work_kw=step.total_work_kw,
        baseline_work_kw=step.baseline_work_kw,
        savings_fraction=step.savings_fraction,
        cop_array=step.cop_array.tolist(),
        temp_rise_array=step.temp_rise_array.tolist(),
        wind_angle=wind_angle,
        wind_speed=wind_speed,
        ramp_factors=ramp_factors,
    )


def _resolve_wind_at(req: SimulationRequest, time_hours: float) -> tuple[float, float]:
    """Compute (speed, angle_deg) at the given time."""
    if req.wind_mode == WindMode.rotating:
        angle = req.wind_center_angle + req.wind_amplitude_deg * math.sin(
            2 * math.pi * time_hours / req.wind_period_hours
        )
        return (req.wind_speed, angle)
    return (req.wind_speed, req.wind_angle)


def build_simulator(req: SimulationRequest):
    """Construct a chiller_sim Simulator from request parameters."""
    builder = Simulator().with_grid(
        rows=req.rows,
        cols=req.cols,
        spacing_m=req.spacing_m,
        base_cop=req.base_cop,
        max_cooling_kw=req.max_cooling_kw,
        alpha=req.alpha,
        seed=req.ages_seed,
    )

    if req.wind_mode == WindMode.rotating:
        wind_fn = build_wind_fn(
            center_angle=req.wind_center_angle,
            amplitude_deg=req.wind_amplitude_deg,
            period_hours=req.wind_period_hours,
            speed=req.wind_speed,
        )
        builder = builder.with_wind_fn(wind_fn)
    else:
        builder = builder.with_wind(
            speed_m_per_s=req.wind_speed,
            angle_deg=req.wind_angle,
        )

    builder = builder.with_ambient_temp(temp_k=req.ambient_temp_k).with_load_fn(
        build_load_fn(
            req.load_profile,
            req.base_load_kw,
            req.amplitude_kw,
            req.period_hours,
        )
    )

    if req.dispersion_coeff is not None:
        builder = builder.with_dispersion(coeff=req.dispersion_coeff)
    if req.heat_rejection_scale is not None:
        builder = builder.with_heat_rejection_scale(req.heat_rejection_scale)
    if req.switching_threshold_kw is not None:
        builder = builder.with_switching_threshold(
            min_savings_kw=req.switching_threshold_kw
        )

    return builder.build()


def get_ages_years(req: SimulationRequest) -> list[float]:
    """Retrieve the ages that will be used for this config."""
    n = req.rows * req.cols
    if req.ages_seed is not None:
        rng = np.random.default_rng(req.ages_seed)
        return rng.uniform(0.0, 20.0, size=n).tolist()
    return [0.0] * n


def run_simulation(req: SimulationRequest) -> list[StepResponse]:
    """Run the full simulation and return all steps."""
    sim = build_simulator(req)
    result = sim.simulate(
        duration_hours=req.duration_hours,
        time_step_hours=req.time_step_hours,
    )
    tracker = _RampTracker(req.rows * req.cols, req.time_step_hours)
    responses = []
    for s in result.steps:
        ramp = tracker.update(s.active_mask.tolist())
        speed, angle = _resolve_wind_at(req, s.time_hours)
        responses.append(_step_to_response(s, speed, angle, ramp))
    return responses


def stream_simulation(
    req: SimulationRequest,
) -> Generator[StepResponse, None, None]:
    """Yield one StepResponse per optimisation step."""
    sim = build_simulator(req)
    tracker = _RampTracker(req.rows * req.cols, req.time_step_hours)
    for step in sim.stream(
        duration_hours=req.duration_hours,
        time_step_hours=req.time_step_hours,
    ):
        ramp = tracker.update(step.active_mask.tolist())
        speed, angle = _resolve_wind_at(req, step.time_hours)
        yield _step_to_response(step, speed, angle, ramp)
