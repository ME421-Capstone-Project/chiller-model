from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.physics.cop import CopFn
from chiller_sim.physics.degradation import DegradationFn
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel
from chiller_sim.physics.load import LoadFn
from chiller_sim.physics.ramp import RampFn
from chiller_sim.simulation.results import InitialState, OptimizeResult, SimulationResult

if TYPE_CHECKING:
    from chiller_sim.simulation.builder import SimulatorBuilder


class Simulator:
    def __init__(
        self,
        builder: SimulatorBuilder,
        grid: ChillerGrid,
        initial_wind: WindConditions,
        model: GaussianPlumeModel,
        load_fn: LoadFn,
        cop_fn: CopFn,
        degradation_fn: DegradationFn,
        ramp_fn: RampFn,
        wind_fn: WindFn | None,
        ambient_temp_k: float | None,
        ambient_temp_fn: AmbientTempFn | None,
        min_savings_kw: float,
    ) -> None:
        self._builder = builder
        self._grid = grid
        self._model = model
        self._load_fn = load_fn
        self._cop_fn = cop_fn
        self._degradation_fn = degradation_fn
        self._ramp_fn = ramp_fn
        self._wind_fn = wind_fn
        self._ambient_temp_k = ambient_temp_k
        self._ambient_temp_fn = ambient_temp_fn
        self._min_savings_kw = min_savings_kw

        # Precompute interaction matrix for initial wind
        self._current_wind = initial_wind
        self._interaction_matrix = model.compute_interaction_matrix(grid.positions_m, initial_wind)

        # Optimizer state — reset at start of each stream()/simulate() call
        self._is_first_call = True
        self._active_mask: NDArray[np.bool_] = np.zeros(grid.num_chillers, dtype=bool)
        self._time_since_start: NDArray[np.float64] = np.zeros(grid.num_chillers)

    # Builder re-entry: allow sim.with_wind(...).build()
    def with_wind(self, speed_m_per_s: float, angle_deg: float) -> SimulatorBuilder:
        return self._builder.with_wind(speed_m_per_s=speed_m_per_s, angle_deg=angle_deg)

    def with_wind_fn(self, fn: WindFn) -> SimulatorBuilder:
        return self._builder.with_wind_fn(fn)

    def with_ambient_temp(self, temp_k: float) -> SimulatorBuilder:
        return self._builder.with_ambient_temp(temp_k=temp_k)

    def with_ambient_temp_fn(self, fn: AmbientTempFn) -> SimulatorBuilder:
        return self._builder.with_ambient_temp_fn(fn)

    def _get_ambient_temp(self, time_hours: float) -> float:
        if self._ambient_temp_fn is not None:
            return self._ambient_temp_fn(time_hours)
        return self._ambient_temp_k  # type: ignore[return-value]

    def _get_wind(self, time_hours: float) -> WindConditions:
        if self._wind_fn is not None:
            speed, angle = self._wind_fn(time_hours)
            return WindConditions(speed_m_per_s=speed, angle_deg=angle)
        return self._current_wind

    def _update_wind_if_changed(self, time_hours: float) -> None:
        new_wind = self._get_wind(time_hours)
        if new_wind != self._current_wind:
            self._current_wind = new_wind
            self._interaction_matrix = self._model.compute_interaction_matrix(
                self._grid.positions_m, new_wind
            )

    def _evaluate_work(
        self,
        active_mask: NDArray[np.bool_],
        time_since_start: NDArray[np.float64],
        load_kw: float,
        ambient_temp_k: float,
        use_steady_state_ramp: bool = False,
    ) -> tuple[float, NDArray[np.float64], NDArray[np.float64]]:
        """Return (total_work_kw, cop_array, temp_rise_array)."""
        n = len(active_mask)
        n_active = int(active_mask.sum())

        if n_active == 0:
            return float("inf"), np.zeros(n), np.zeros(n)

        load_per_unit = load_kw / n_active
        temp_rise = active_mask.astype(np.float64) @ self._interaction_matrix

        ramp_factors = (
            np.ones(n)
            if use_steady_state_ramp
            else np.array([self._ramp_fn(t) for t in time_since_start])
        )
        deg_factors = np.array([self._degradation_fn(a) for a in self._grid.ages_years])

        cop_array = np.array([
            self._cop_fn(self._grid.base_cop, temp_rise[i], ambient_temp_k)
            * deg_factors[i]
            * ramp_factors[i]
            for i in range(n)
        ])
        cop_array = np.maximum(cop_array, 1e-6)

        total_work = float(np.sum(load_per_unit / cop_array[active_mask]))
        return total_work, cop_array, temp_rise

    def _greedy_optimize(
        self,
        load_kw: float,
        ambient_temp_k: float,
    ) -> tuple[NDArray[np.bool_], NDArray[np.float64]]:
        n = self._grid.num_chillers

        # On the first call, start all-on at steady-state ramp throughout the
        # entire greedy loop — ensures custom ramp_fn values do not affect
        # first-call behavior, matching the spec guarantee.
        is_first = self._is_first_call
        if is_first:
            active_mask = np.ones(n, dtype=bool)
            time_since_start = np.full(n, np.inf)
            self._is_first_call = False
        else:
            active_mask = self._active_mask.copy()
            time_since_start = self._time_since_start.copy()

        current_work, _, _ = self._evaluate_work(
            active_mask, time_since_start, load_kw, ambient_temp_k,
            use_steady_state_ramp=is_first,
        )

        improved = True
        while improved:
            improved = False
            best_work = current_work
            best_mask: NDArray[np.bool_] | None = None
            best_times: NDArray[np.float64] | None = None

            for i in range(n):
                candidate_mask = active_mask.copy()
                candidate_times = time_since_start.copy()
                candidate_mask[i] = not candidate_mask[i]

                if candidate_mask[i]:  # activating
                    candidate_times[i] = 0.0
                # deactivating: time value irrelevant for inactive chillers

                candidate_work, _, _ = self._evaluate_work(
                    candidate_mask, candidate_times, load_kw, ambient_temp_k,
                    use_steady_state_ramp=is_first,
                )
                savings = current_work - candidate_work

                if savings >= self._min_savings_kw and candidate_work < best_work:
                    best_work = candidate_work
                    best_mask = candidate_mask
                    best_times = candidate_times

            if best_mask is not None:
                active_mask = best_mask
                time_since_start = best_times  # type: ignore[assignment]
                current_work = best_work
                improved = True

        return active_mask, time_since_start

    def optimize(
        self,
        time_hours: float,
        load_kw: float | None = None,
    ) -> OptimizeResult:
        self._update_wind_if_changed(time_hours)
        ambient_temp_k = self._get_ambient_temp(time_hours)
        resolved_load = load_kw if load_kw is not None else self._load_fn(time_hours)

        # Baseline: all chillers on at steady-state ramp
        n = self._grid.num_chillers
        all_on = np.ones(n, dtype=bool)
        steady_times = np.full(n, np.inf)
        baseline_work, _, _ = self._evaluate_work(
            all_on, steady_times, resolved_load, ambient_temp_k, use_steady_state_ramp=True
        )

        active_mask, time_since_start = self._greedy_optimize(resolved_load, ambient_temp_k)
        total_work, cop_array, temp_rise = self._evaluate_work(
            active_mask, time_since_start, resolved_load, ambient_temp_k
        )

        savings_fraction = (
            (baseline_work - total_work) / baseline_work if baseline_work > 0 else 0.0
        )

        # Persist state for next optimize() call
        self._active_mask = active_mask
        self._time_since_start = time_since_start

        return OptimizeResult(
            time_hours=time_hours,
            load_kw=resolved_load,
            active_mask=active_mask,
            total_work_kw=total_work,
            baseline_work_kw=baseline_work,
            savings_fraction=savings_fraction,
            cop_array=cop_array,
            temp_rise_array=temp_rise,
        )

    def _reset_state(self, initial_state: InitialState | None) -> None:
        """Reset internal optimizer state at start of stream()/simulate()."""
        n = self._grid.num_chillers
        if initial_state is not None:
            self._active_mask = initial_state.active_mask.copy()
            self._time_since_start = initial_state.time_since_start_hours.copy()
            self._is_first_call = False
        else:
            self._active_mask = np.zeros(n, dtype=bool)
            self._time_since_start = np.zeros(n)
            self._is_first_call = True

    def stream(
        self,
        duration_hours: float,
        time_step_hours: float = 1.0,
        initial_time_hours: float = 0.0,
        initial_state: InitialState | None = None,
    ) -> Generator[OptimizeResult, None, None]:
        self._reset_state(initial_state)
        t = initial_time_hours
        while t < initial_time_hours + duration_hours - 1e-9:
            result = self.optimize(time_hours=t)
            # Advance startup clocks for active chillers
            self._time_since_start[self._active_mask] += time_step_hours
            self._time_since_start[~self._active_mask] = 0.0
            yield result
            t += time_step_hours

    def simulate(
        self,
        duration_hours: float,
        time_step_hours: float = 1.0,
        initial_time_hours: float = 0.0,
        initial_state: InitialState | None = None,
    ) -> SimulationResult:
        steps = list(self.stream(
            duration_hours=duration_hours,
            time_step_hours=time_step_hours,
            initial_time_hours=initial_time_hours,
            initial_state=initial_state,
        ))
        return SimulationResult(steps=steps)
