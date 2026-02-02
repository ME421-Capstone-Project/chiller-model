"""Optimization strategies for chiller array operation.

This module provides the Optimizer class that implements strategies
for determining which chillers to operate to minimize energy
consumption while satisfying the cooling load.

Algorithm
---------
The primary strategy is a greedy removal algorithm:
1. Start with all chillers active
2. Iteratively deactivate the chiller whose removal most reduces work
3. Stop when no further improvement is possible

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from src.simulation.environment import PerformanceResult, SimulationEnvironment


class OptimizationResult(NamedTuple):
    """Immutable result of optimization.

    Attributes
    ----------
    optimal_mask : NDArray[np.bool_]
        Boolean array indicating which chillers should be active.
    optimal_work_kw : float
        Total work required with optimal configuration.
    baseline_work_kw : float
        Work required with all chillers active (baseline).
    savings_fraction : float
        Fractional energy savings: (baseline - optimal) / baseline.
    performance : PerformanceResult
        Detailed performance metrics at optimal configuration.
    iterations : int
        Number of iterations to reach optimal solution.

    Notes
    -----
    Uses NamedTuple for immutability per project rules.
    """

    optimal_mask: NDArray[np.bool_]
    optimal_work_kw: float
    baseline_work_kw: float
    savings_fraction: float
    performance: PerformanceResult
    iterations: int

    @property
    def num_active(self) -> int:
        """Number of active chillers in optimal solution.

        Returns
        -------
        int
            Count of active chillers.
        """
        return int(np.sum(self.optimal_mask))

    @property
    def savings_kw(self) -> float:
        """Absolute energy savings in kW.

        Returns
        -------
        float
            baseline_work_kw - optimal_work_kw
        """
        return self.baseline_work_kw - self.optimal_work_kw


@dataclass
class Optimizer:
    """Optimizer for chiller array operation.

    Implements strategies for determining optimal chiller activation
    patterns to minimize energy consumption.

    Attributes
    ----------
    environment : SimulationEnvironment
        The simulation environment to optimize.
    total_load_kw : float
        Total cooling load that must be satisfied.

    Notes
    -----
    The optimizer uses greedy algorithms which are efficient but
    may not find the global optimum for all configurations.

    Reference
    ---------
    ASHRAE Handbook - HVAC Applications, Chapter 43

    Examples
    --------
    >>> optimizer = Optimizer(env, total_load_kw=500.0)
    >>> result = optimizer.optimize_greedy()
    >>> print(f"Savings: {result.savings_fraction:.1%}")
    """

    environment: SimulationEnvironment
    total_load_kw: float

    def __post_init__(self) -> None:
        """Validate optimizer parameters."""
        if self.total_load_kw <= 0:
            raise ValueError(
                f"total_load_kw must be positive, got {self.total_load_kw}"
            )

    def optimize_greedy(
        self,
        min_active: int = 1,
        max_iterations: int | None = None,
    ) -> OptimizationResult:
        """Find optimal configuration using greedy removal strategy.

        Starting with all chillers active, iteratively deactivates
        the chiller whose removal most reduces total work.

        Parameters
        ----------
        min_active : int
            Minimum number of chillers that must remain active.
            Default is 1 to ensure load can be served.
        max_iterations : int | None
            Maximum iterations before stopping. None means continue
            until no improvement is possible.

        Returns
        -------
        OptimizationResult
            Immutable result containing optimal configuration.

        Notes
        -----
        Algorithm complexity: O(N^2) where N is number of chillers,
        as each iteration evaluates N possible removals.

        The algorithm terminates when:
        1. Removing any chiller would increase work, OR
        2. Only min_active chillers remain, OR
        3. max_iterations is reached

        Reference
        ---------
        ASHRAE Handbook - HVAC Applications, Chapter 43

        Examples
        --------
        >>> result = optimizer.optimize_greedy(min_active=2)
        >>> result.savings_fraction
        0.15  # 15% energy savings
        """
        num_chillers = self.environment.num_chillers

        if min_active < 1:
            raise ValueError(f"min_active must be >= 1, got {min_active}")
        if min_active > num_chillers:
            raise ValueError(
                f"min_active ({min_active}) cannot exceed "
                f"num_chillers ({num_chillers})"
            )

        # Initialize: all chillers active
        active_mask = np.ones(num_chillers, dtype=bool)

        # Compute baseline performance
        baseline_result = self.environment.compute_performance(
            active_mask, self.total_load_kw
        )
        baseline_work = baseline_result.total_work_kw

        # Track best solution found
        best_mask = active_mask.copy()
        best_work = baseline_work
        best_result = baseline_result

        iteration = 0
        max_iter = max_iterations if max_iterations is not None else num_chillers

        while np.sum(active_mask) > min_active and iteration < max_iter:
            iteration += 1

            # Find best chiller to deactivate
            best_removal_idx = -1
            best_removal_work = best_work

            # Get indices of currently active chillers
            active_indices = np.where(active_mask)[0]

            for idx in active_indices:
                # Try deactivating this chiller
                test_mask = active_mask.copy()
                test_mask[idx] = False

                result = self.environment.compute_performance(
                    test_mask, self.total_load_kw
                )

                if result.total_work_kw < best_removal_work:
                    best_removal_work = result.total_work_kw
                    best_removal_idx = idx

            # If no improvement, stop
            if best_removal_idx < 0 or best_removal_work >= best_work:
                break

            # Apply best removal
            active_mask[best_removal_idx] = False
            best_mask = active_mask.copy()
            best_work = best_removal_work
            best_result = self.environment.compute_performance(
                best_mask, self.total_load_kw
            )

        # Compute savings
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
        self,
        active_mask: NDArray[np.bool_],
    ) -> PerformanceResult:
        """Evaluate a specific chiller configuration.

        Parameters
        ----------
        active_mask : NDArray[np.bool_]
            Boolean array indicating which chillers are active.

        Returns
        -------
        PerformanceResult
            Performance metrics for the configuration.
        """
        return self.environment.compute_performance(active_mask, self.total_load_kw)

    def compare_configurations(
        self,
        masks: list[NDArray[np.bool_]],
    ) -> list[PerformanceResult]:
        """Compare multiple chiller configurations.

        Parameters
        ----------
        masks : list[NDArray[np.bool_]]
            List of boolean arrays, each representing a configuration.

        Returns
        -------
        list[PerformanceResult]
            Performance results for each configuration.
        """
        return [self.evaluate_configuration(mask) for mask in masks]

    def sensitivity_analysis(
        self,
        active_mask: NDArray[np.bool_],
    ) -> NDArray[np.float64]:
        """Analyze sensitivity of work to each chiller's state.

        For each chiller, computes the change in work if its state
        (active/inactive) is toggled.

        Parameters
        ----------
        active_mask : NDArray[np.bool_]
            Current configuration.

        Returns
        -------
        NDArray[np.float64]
            Array of work deltas, shape (N,).
            Positive means toggling increases work.
            Negative means toggling decreases work.
        """
        base_result = self.environment.compute_performance(
            active_mask, self.total_load_kw
        )
        base_work = base_result.total_work_kw

        deltas = np.zeros(self.environment.num_chillers)

        for idx in range(self.environment.num_chillers):
            test_mask = active_mask.copy()
            test_mask[idx] = not test_mask[idx]

            # Ensure at least one chiller is active
            if np.sum(test_mask) == 0:
                deltas[idx] = float("inf")
                continue

            result = self.environment.compute_performance(
                test_mask, self.total_load_kw
            )
            deltas[idx] = result.total_work_kw - base_work

        return deltas
