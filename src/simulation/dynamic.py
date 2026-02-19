"""Time-stepping simulation with varying load, wind, and chiller start-up.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, NamedTuple

import numpy as np
from numpy.typing import NDArray

from components.data_center import DataCenter
from components.wind import WindVector
from core.constants import (
    CHILLER_STARTUP_TIME_HOURS,
    compute_cop_startup_factors_vectorized,
)
from simulation.environment import PerformanceResult, SimulationEnvironment
from simulation.optimizer import Optimizer


class DynamicStepResult(NamedTuple):
    """Immutable snapshot of one simulation time-step."""

    time_hours: float
    load_kw: float
    wind: WindVector
    active_mask: NDArray[np.bool_]
    performance: PerformanceResult
    total_work_kw: float


@dataclass
class DynamicSimulation:
    """Step through time with varying load, wind, and COP start-up ramp.

    Each step:
    1. Query the data centre for the current cooling load.
    2. Optionally update wind from a time-varying profile.
    3. Choose which chillers to activate (via greedy optimiser).
    4. Apply start-up COP ramp factors.
    5. Evaluate the plant transfer function.
    """

    environment: SimulationEnvironment
    data_center: DataCenter
    time_step_hours: float
    startup_time_hours: float = CHILLER_STARTUP_TIME_HOURS
    wind_profile: Callable[[float], WindVector] | None = None

    _time_since_start: NDArray[np.float64] = field(
        init=False, repr=False, default_factory=lambda: np.array([])
    )

    def __post_init__(self) -> None:
        if self.time_step_hours <= 0:
            raise ValueError(f"time_step_hours must be > 0, got {self.time_step_hours}")
        if self.startup_time_hours <= 0:
            raise ValueError(
                f"startup_time_hours must be > 0, got {self.startup_time_hours}"
            )
        n = self.environment.num_chillers
        self._time_since_start = np.full(n, -1.0, dtype=np.float64)

    def _startup_factors(self, active_mask: NDArray[np.bool_]) -> NDArray[np.float64]:
        """COP ramp multipliers based on how long each chiller has been on."""
        return compute_cop_startup_factors_vectorized(
            self._time_since_start,
            self.startup_time_hours,
        )

    def _update_startup_tracking(
        self,
        active_mask: NDArray[np.bool_],
        previous_active_mask: NDArray[np.bool_],
    ) -> None:
        """Advance the per-chiller start-up clock after each step."""
        just_turned_on = active_mask & ~previous_active_mask
        self._time_since_start[just_turned_on] = 0.0

        still_running = active_mask & previous_active_mask
        self._time_since_start[still_running] += self.time_step_hours

        turned_off = ~active_mask
        self._time_since_start[turned_off] = -1.0

    def _choose_active_chillers(
        self,
        load_kw: float,
        env: SimulationEnvironment,
    ) -> NDArray[np.bool_]:
        """Select chillers via greedy optimisation."""
        optimizer = Optimizer(env, total_load_kw=load_kw)
        return optimizer.optimize_greedy(min_active=1).optimal_mask

    def _environment_at_time(self, time_hours: float) -> SimulationEnvironment:
        """Return the environment with wind conditions at *time_hours*."""
        if self.wind_profile is None:
            return self.environment
        return self.environment.with_new_wind(self.wind_profile(time_hours))

    def step(
        self,
        time_hours: float,
        active_mask: NDArray[np.bool_] | None = None,
    ) -> DynamicStepResult:
        """Execute one simulation time-step."""
        load_kw = self.data_center.get_load_kw(time_hours)
        env = self._environment_at_time(time_hours)
        wind = env.wind

        previous_active = self._time_since_start >= 0

        if active_mask is None:
            active_mask = self._choose_active_chillers(load_kw, env)

        startup_factors = self._startup_factors(active_mask)
        performance = env.compute_performance(
            active_mask,
            load_kw,
            startup_factors=startup_factors,
        )

        self._update_startup_tracking(active_mask, previous_active)

        return DynamicStepResult(
            time_hours=time_hours,
            load_kw=load_kw,
            wind=wind,
            active_mask=active_mask.copy(),
            performance=performance,
            total_work_kw=performance.total_work_kw,
        )

    def run(
        self,
        duration_hours: float,
        initial_time_hours: float = 0.0,
    ):
        """Yield a ``DynamicStepResult`` for every time-step in the run."""
        if duration_hours <= 0:
            raise ValueError(f"duration_hours must be > 0, got {duration_hours}")

        n = self.environment.num_chillers
        self._time_since_start = np.full(n, -1.0, dtype=np.float64)

        t = initial_time_hours
        while t < initial_time_hours + duration_hours:
            yield self.step(t)
            t += self.time_step_hours
