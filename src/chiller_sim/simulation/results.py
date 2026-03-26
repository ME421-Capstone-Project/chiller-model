from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class OptimizeResult:
    """Output of a single optimization step."""

    time_hours: float
    load_kw: float
    active_mask: NDArray[np.bool_]
    total_work_kw: float
    baseline_work_kw: float
    savings_fraction: float
    cop_array: NDArray[np.float64]
    temp_rise_array: NDArray[np.float64]


@dataclass
class SimulationResult:
    """Aggregated results across all steps of a dynamic simulation."""

    steps: list[OptimizeResult]

    @property
    def schedule(self) -> NDArray[np.bool_]:
        """Return 2-D boolean array of active masks, shape (n_steps, n_chillers)."""
        return np.array([s.active_mask for s in self.steps])

    @property
    def total_work_kw(self) -> NDArray[np.float64]:
        """Return total work per step in kW, shape (n_steps,)."""
        return np.array([s.total_work_kw for s in self.steps])

    @property
    def loads_kw(self) -> NDArray[np.float64]:
        """Return facility load per step in kW, shape (n_steps,)."""
        return np.array([s.load_kw for s in self.steps])

    @property
    def savings_fraction(self) -> NDArray[np.float64]:
        """Return savings fraction per step, shape (n_steps,)."""
        return np.array([s.savings_fraction for s in self.steps])

    @property
    def cop_arrays(self) -> NDArray[np.float64]:
        """Return per-chiller COP array per step, shape (n_steps, n_chillers)."""
        return np.array([s.cop_array for s in self.steps])


@dataclass(frozen=True)
class InitialState:
    """Optional warm-start state for stream()/simulate() calls."""

    active_mask: NDArray[np.bool_]
    time_since_start_hours: NDArray[np.float64]
