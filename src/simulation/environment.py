"""Chiller-plant transfer function.

Composes chiller array + wind + interaction model into a single
mapping:

    (active_mask, total_load) → (total_power, COP array, temperature rise)

The interaction matrix is precomputed at construction for efficiency.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from components.chiller_array import ChillerArray
from components.wind import WindVector
from models.gaussian_plume import GaussianPlumeModel


class PerformanceResult(NamedTuple):
    """Immutable output of the plant transfer function."""

    total_work_kw: float
    cop_array: NDArray[np.float64]
    temp_rise_array: NDArray[np.float64]
    load_per_unit_kw: float

    @property
    def mean_cop(self) -> float:
        """Average COP across all chillers (including inactive)."""
        return float(np.mean(self.cop_array))

    @property
    def effective_cop(self) -> float:
        """System-level COP = total cooling / total electrical work."""
        if self.total_work_kw <= 0:
            return 0.0
        total_cooling = self.load_per_unit_kw * np.sum(self.cop_array > 0)
        return total_cooling / self.total_work_kw


@dataclass
class SimulationEnvironment:
    """Chiller plant transfer function.

    Precomputes the interaction matrix on construction so that
    ``compute_performance`` can be called many times (e.g. during
    optimisation) without re-deriving it.

    Transfer-function pipeline
    --------------------------
    1. active_mask → temperature rise  (via interaction matrix)
    2. base_cop × age_factors → age-degraded COP
    3. age-degraded COP / (1 + α · temperature_rise) → effective COP
    4. total_load / n_active / effective_cop → power per unit
    5. Σ power → total electrical work
    """

    chiller_array: ChillerArray
    wind: WindVector
    interaction_model: GaussianPlumeModel
    _interaction_matrix: NDArray[np.float64] = field(
        init=False, repr=False, default_factory=lambda: np.array([])
    )

    def __post_init__(self) -> None:
        self._interaction_matrix = self.interaction_model.compute_interaction_matrix(
            self.chiller_array.positions_m,
            self.wind,
        )

    @property
    def num_chillers(self) -> int:
        """Number of chillers in the composed array."""
        return self.chiller_array.num_chillers

    @property
    def interaction_matrix(self) -> NDArray[np.float64]:
        """Precomputed interaction matrix A of shape (N, N)."""
        return self._interaction_matrix

    def compute_performance(
        self,
        active_mask: NDArray[np.bool_],
        total_load_kw: float,
        startup_factors: NDArray[np.float64] | None = None,
    ) -> PerformanceResult:
        """Evaluate the plant transfer function for a given operating point.

        Parameters
        ----------
        active_mask : bool array, shape (N,)
            Which chillers are running.
        total_load_kw : float
            Total cooling demand distributed evenly among active units.
        startup_factors : float array, shape (N,), optional
            COP ramp-up multipliers in [0, 1] during chiller start-up.
        """
        n_active = int(np.sum(active_mask))

        if n_active == 0:
            return PerformanceResult(
                total_work_kw=float("inf"),
                cop_array=np.zeros(self.num_chillers),
                temp_rise_array=np.zeros(self.num_chillers),
                load_per_unit_kw=0.0,
            )

        load_per_unit_kw = total_load_kw / n_active

        temperature_rise = active_mask.astype(np.float64) @ self._interaction_matrix

        age_degraded_cop = self.chiller_array.base_cop * self.chiller_array.cop_age_factors
        effective_cop = age_degraded_cop / (1.0 + self.chiller_array.alpha * temperature_rise)

        if startup_factors is not None:
            if startup_factors.shape != (self.num_chillers,):
                raise ValueError(
                    f"startup_factors shape {startup_factors.shape} "
                    f"must match num_chillers ({self.num_chillers})"
                )
            effective_cop = effective_cop * np.maximum(startup_factors, 0.01)

        total_work_kw = float(np.sum(load_per_unit_kw / effective_cop[active_mask]))

        return PerformanceResult(
            total_work_kw=total_work_kw,
            cop_array=effective_cop,
            temp_rise_array=temperature_rise,
            load_per_unit_kw=load_per_unit_kw,
        )

    def compute_cop_at_position(
        self,
        position_idx: int,
        active_mask: NDArray[np.bool_],
    ) -> float:
        """Return the effective COP at one chiller position."""
        if position_idx < 0 or position_idx >= self.num_chillers:
            raise IndexError(
                f"position_idx {position_idx} out of range [0, {self.num_chillers})"
            )

        temperature_rise = np.dot(
            active_mask.astype(np.float64),
            self._interaction_matrix[:, position_idx],
        )
        age_degraded_cop = (
            self.chiller_array.base_cop
            * self.chiller_array.cop_age_factors[position_idx]
        )
        return age_degraded_cop / (1.0 + self.chiller_array.alpha * temperature_rise)

    def get_thermal_impact_on(self, target_idx: int) -> NDArray[np.float64]:
        """Return column of the interaction matrix for one target chiller."""
        return self._interaction_matrix[:, target_idx].copy()

    def with_new_wind(self, wind: WindVector) -> SimulationEnvironment:
        """Return a new environment with different wind (recomputes A)."""
        return SimulationEnvironment(
            chiller_array=self.chiller_array,
            wind=wind,
            interaction_model=self.interaction_model,
        )

    def with_new_model(
        self, interaction_model: GaussianPlumeModel
    ) -> SimulationEnvironment:
        """Return a new environment with a different interaction model."""
        return SimulationEnvironment(
            chiller_array=self.chiller_array,
            wind=self.wind,
            interaction_model=interaction_model,
        )
