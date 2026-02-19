"""Dynamic simulation with time-varying load, wind, and chiller startup.

This module provides DynamicSimulation for stepping through time with:
- Varying heat loads from the data center
- Varying wind (optional) or constant wind
- Chiller startup delay (linear COP ramp from 0 to full)

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43 (Building Operations)
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
    """Result of a single dynamic simulation step.

    Attributes
    ----------
    time_hours : float
        Simulation time at end of step.
    load_kw : float
        Data center cooling load at this step.
    wind : WindVector
        Wind conditions at this step.
    active_mask : NDArray[np.bool_]
        Which chillers were active.
    performance : PerformanceResult
        Performance metrics (with startup factors applied).
    total_work_kw : float
        Total electrical work (convenience from performance).
    """

    time_hours: float
    load_kw: float
    wind: WindVector
    active_mask: NDArray[np.bool_]
    performance: PerformanceResult
    total_work_kw: float


@dataclass
class DynamicSimulation:
    """Dynamic simulation with varying load, wind, and chiller startup.

    Steps through time with:
    - Time-varying heat load from DataCenter
    - Time-varying wind (if wind_profile provided) or constant wind
    - Chiller startup: COP ramps linearly from 0 to full over startup time

    Attributes
    ----------
    environment : SimulationEnvironment
        Composed chiller array, wind, interaction model. Wind used when
        wind_profile is None; otherwise wind_profile(time) overrides.
    data_center : DataCenter
        Provides load_kw(time) for varying heat load.
    time_step_hours : float
        Duration of each step in hours.
    startup_time_hours : float
        Time for chiller COP to ramp from 0 to full after turn-on.
    wind_profile : Callable[[float], WindVector] | None, optional
        If provided, wind at each step = wind_profile(time_hours).
        If None, use constant wind from environment.

    Notes
    -----
    Tracks time_since_start_hours per chiller. When a chiller turns on,
    this resets to 0. Each step it increases by time_step_hours for
    active chillers. When a chiller turns off, it resets to -1.

    Reference
    ---------
    ASHRAE Handbook - HVAC Applications, Chapter 43

    Examples
    --------
    >>> env = SimulationEnvironment(array, wind, model)
    >>> dc = DataCenter.with_sinusoidal_profile(500.0, 1000.0)
    >>> sim = DynamicSimulation(env, dc, time_step_hours=0.25)
    >>> for step in sim.run(duration_hours=24.0):
    ...     print(step.time_hours, step.load_kw, step.total_work_kw)
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
        """Validate and initialize state."""
        if self.time_step_hours <= 0:
            raise ValueError(
                f"time_step_hours must be > 0, got {self.time_step_hours}"
            )
        if self.startup_time_hours <= 0:
            raise ValueError(
                f"startup_time_hours must be > 0, got {self.startup_time_hours}"
            )
        n = self.environment.num_chillers
        self._time_since_start = np.full(n, -1.0, dtype=np.float64)

    def _get_startup_factors(self, active_mask: NDArray[np.bool_]) -> NDArray[np.float64]:
        """Compute startup factors from time_since_start.

        Active chillers: factor = min(1, time_since_start / startup_time).
        Inactive: factor 0 (not used in work calc).
        """
        return compute_cop_startup_factors_vectorized(
            self._time_since_start,
            self.startup_time_hours,
        )

    def _update_time_since_start(
        self,
        active_mask: NDArray[np.bool_],
        prev_active_mask: NDArray[np.bool_],
    ) -> None:
        """Update time_since_start after a step.

        - Just turned on: set to 0
        - Was active, still active: add time_step
        - Just turned off: set to -1
        """
        # Newly active: reset to 0
        newly_on = active_mask & ~prev_active_mask
        self._time_since_start[newly_on] = 0.0

        # Still active: add time step
        still_on = active_mask & prev_active_mask
        self._time_since_start[still_on] += self.time_step_hours

        # Turned off: set to -1
        turned_off = ~active_mask
        self._time_since_start[turned_off] = -1.0

    def _choose_active_mask(
        self,
        load_kw: float,
        env: SimulationEnvironment,
    ) -> NDArray[np.bool_]:
        """Choose which chillers to activate for given load.

        Uses greedy optimizer to minimize work.
        """
        optimizer = Optimizer(env, total_load_kw=load_kw)
        result = optimizer.optimize_greedy(min_active=1)
        return result.optimal_mask

    def _get_env_for_step(self, time_hours: float) -> SimulationEnvironment:
        """Get environment with wind for current time step."""
        if self.wind_profile is None:
            return self.environment
        wind = self.wind_profile(time_hours)
        return self.environment.with_new_wind(wind)

    def step(
        self,
        time_hours: float,
        active_mask: NDArray[np.bool_] | None = None,
    ) -> DynamicStepResult:
        """Execute one simulation step.

        Parameters
        ----------
        time_hours : float
            Current simulation time (hours). Used to get load from data center.
        active_mask : NDArray[np.bool_] | None, optional
            Which chillers to activate. If None, use optimizer.

        Returns
        -------
        DynamicStepResult
            Result of this step.
        """
        load_kw = self.data_center.get_load_kw(time_hours)
        env = self._get_env_for_step(time_hours)
        wind = env.wind

        prev_active = np.zeros(self.environment.num_chillers, dtype=bool)
        if self._time_since_start.size > 0:
            prev_active = self._time_since_start >= 0

        if active_mask is None:
            active_mask = self._choose_active_mask(load_kw, env)

        startup_factors = self._get_startup_factors(active_mask)
        performance = env.compute_performance(
            active_mask,
            load_kw,
            startup_factors=startup_factors,
        )

        self._update_time_since_start(active_mask, prev_active)

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
        """Run dynamic simulation over time.

        Parameters
        ----------
        duration_hours : float
            Total simulation duration in hours.
        initial_time_hours : float
            Start time in hours (default 0).

        Yields
        ------
        DynamicStepResult
            Result at each time step.

        Examples
        --------
        >>> for step in sim.run(duration_hours=24.0):
        ...     print(f"t={step.time_hours:.1f}h load={step.load_kw:.0f}kW")
        """
        if duration_hours <= 0:
            raise ValueError(
                f"duration_hours must be > 0, got {duration_hours}"
            )

        # Reset startup state at run start
        n = self.environment.num_chillers
        self._time_since_start = np.full(n, -1.0, dtype=np.float64)

        t = initial_time_hours
        while t < initial_time_hours + duration_hours:
            yield self.step(t)
            t += self.time_step_hours
