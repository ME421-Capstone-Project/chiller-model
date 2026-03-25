from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class OptimizeResult:
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
    steps: list[OptimizeResult]

    @property
    def schedule(self) -> NDArray[np.bool_]:
        return np.array([s.active_mask for s in self.steps])

    @property
    def total_work_kw(self) -> NDArray[np.float64]:
        return np.array([s.total_work_kw for s in self.steps])

    @property
    def loads_kw(self) -> NDArray[np.float64]:
        return np.array([s.load_kw for s in self.steps])

    @property
    def savings_fraction(self) -> NDArray[np.float64]:
        return np.array([s.savings_fraction for s in self.steps])

    @property
    def cop_arrays(self) -> NDArray[np.float64]:
        return np.array([s.cop_array for s in self.steps])


@dataclass(frozen=True)
class InitialState:
    active_mask: NDArray[np.bool_]
    time_since_start_hours: NDArray[np.float64]
