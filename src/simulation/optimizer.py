"""Greedy optimiser for chiller-array activation patterns.

Determines which chillers to run to minimise total electrical work
while satisfying the cooling load.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from simulation.environment import PerformanceResult, SimulationEnvironment


class OptimizationResult(NamedTuple):
    """Immutable result of an optimisation run."""

    optimal_mask: NDArray[np.bool_]
    optimal_work_kw: float
    baseline_work_kw: float
    savings_fraction: float
    performance: PerformanceResult
    iterations: int

    @property
    def num_active(self) -> int:
        """Number of active chillers in the optimal solution."""
        return int(np.sum(self.optimal_mask))

    @property
    def savings_kw(self) -> float:
        """Absolute energy savings: baseline − optimal."""
        return self.baseline_work_kw - self.optimal_work_kw


@dataclass
class Optimizer:
    """Greedy removal optimiser for a ``SimulationEnvironment``.

    Starting with all chillers active, iteratively removes the unit
    whose deactivation most reduces total work.
    """

    environment: SimulationEnvironment
    total_load_kw: float

    def __post_init__(self) -> None:
        if self.total_load_kw <= 0:
            raise ValueError(f"total_load_kw must be positive, got {self.total_load_kw}")

    def optimize_greedy(
        self,
        min_active: int = 1,
        max_iterations: int | None = None,
    ) -> OptimizationResult:
        """Find the best activation mask via greedy chiller removal."""
        num_chillers = self.environment.num_chillers

        if min_active < 1:
            raise ValueError(f"min_active must be >= 1, got {min_active}")
        if min_active > num_chillers:
            raise ValueError(
                f"min_active ({min_active}) cannot exceed num_chillers ({num_chillers})"
            )

        active_mask = np.ones(num_chillers, dtype=bool)
        baseline_result = self.environment.compute_performance(
            active_mask, self.total_load_kw
        )
        baseline_work = baseline_result.total_work_kw

        best_mask = active_mask.copy()
        best_work = baseline_work
        best_result = baseline_result

        iteration = 0
        max_iter = max_iterations if max_iterations is not None else num_chillers

        while np.sum(active_mask) > min_active and iteration < max_iter:
            iteration += 1

            best_removal_idx = -1
            best_removal_work = best_work
            active_indices = np.where(active_mask)[0]

            for idx in active_indices:
                test_mask = active_mask.copy()
                test_mask[idx] = False
                result = self.environment.compute_performance(
                    test_mask, self.total_load_kw
                )
                if result.total_work_kw < best_removal_work:
                    best_removal_work = result.total_work_kw
                    best_removal_idx = idx

            if best_removal_idx < 0 or best_removal_work >= best_work:
                break

            active_mask[best_removal_idx] = False
            best_mask = active_mask.copy()
            best_work = best_removal_work
            best_result = self.environment.compute_performance(
                best_mask, self.total_load_kw
            )

        savings_fraction = (baseline_work - best_work) / baseline_work

        return OptimizationResult(
            optimal_mask=best_mask,
            optimal_work_kw=best_work,
            baseline_work_kw=baseline_work,
            savings_fraction=savings_fraction,
            performance=best_result,
            iterations=iteration,
        )

    def evaluate_configuration(
        self, active_mask: NDArray[np.bool_]
    ) -> PerformanceResult:
        """Evaluate the transfer function for one activation pattern."""
        return self.environment.compute_performance(active_mask, self.total_load_kw)

    def compare_configurations(
        self, masks: list[NDArray[np.bool_]]
    ) -> list[PerformanceResult]:
        """Evaluate multiple activation patterns side by side."""
        return [self.evaluate_configuration(mask) for mask in masks]

    def sensitivity_analysis(
        self, active_mask: NDArray[np.bool_]
    ) -> NDArray[np.float64]:
        """Work-change when each chiller's state is toggled, shape (N,)."""
        base_work = self.environment.compute_performance(
            active_mask, self.total_load_kw
        ).total_work_kw

        deltas = np.zeros(self.environment.num_chillers)

        for idx in range(self.environment.num_chillers):
            toggled_mask = active_mask.copy()
            toggled_mask[idx] = not toggled_mask[idx]

            if np.sum(toggled_mask) == 0:
                deltas[idx] = float("inf")
                continue

            toggled_work = self.environment.compute_performance(
                toggled_mask, self.total_load_kw
            ).total_work_kw
            deltas[idx] = toggled_work - base_work

        return deltas
