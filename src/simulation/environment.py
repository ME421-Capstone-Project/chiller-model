"""Simulation environment for chiller array thermal interactions.

This module provides the central SimulationEnvironment class that
composes all components (chiller array, wind, interaction model)
and performs performance calculations.

Design Pattern
--------------
Uses COMPOSITION rather than inheritance. The environment HOLDS
instances of component classes and orchestrates their interaction.
This follows the project's architectural principles.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43 (Building Operations)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from components.chiller_array import ChillerArray
from components.wind import WindVector
from models.base_interaction import BaseInteractionModel


class PerformanceResult(NamedTuple):
    """Immutable result of performance calculation.

    Attributes
    ----------
    total_work_kw : float
        Total electrical power consumption in kW.
    cop_array : NDArray[np.float64]
        Individual COP values for each chiller, shape (N,).
    temp_rise_array : NDArray[np.float64]
        Temperature rise at each chiller inlet due to interference.
    load_per_unit_kw : float
        Cooling load assigned to each active chiller in kW.

    Notes
    -----
    Uses NamedTuple for immutability per project rules.
    A new result is created for each calculation.
    """

    total_work_kw: float
    cop_array: NDArray[np.float64]
    temp_rise_array: NDArray[np.float64]
    load_per_unit_kw: float

    @property
    def mean_cop(self) -> float:
        """Mean COP across all chillers (including inactive).

        Returns
        -------
        float
            Average COP value.
        """
        return float(np.mean(self.cop_array))

    @property
    def effective_cop(self) -> float:
        """Effective system COP (total cooling / total work).

        Returns
        -------
        float
            System-level COP.
        """
        if self.total_work_kw <= 0:
            return 0.0
        total_cooling = self.load_per_unit_kw * np.sum(self.cop_array > 0)
        return total_cooling / self.total_work_kw


@dataclass
class SimulationEnvironment:
    """Central simulation environment using COMPOSITION.

    This class composes instances of component classes rather
    than using deep inheritance, per project architectural rules.
    It orchestrates the calculation of thermal interference effects
    and chiller performance.

    Attributes
    ----------
    chiller_array : ChillerArray
        Array of chillers with spatial positions.
    wind : WindVector
        Current atmospheric wind conditions.
    interaction_model : BaseInteractionModel
        Pluggable model for computing thermal interference.

    Notes
    -----
    The interaction matrix is pre-computed on initialization for
    efficiency. If wind or positions change, create a new environment.

    All calculations use NumPy vectorized operations.
    NO explicit for-loops for performance calculations.

    Reference
    ---------
    ASHRAE Handbook - HVAC Applications, Chapter 43

    Examples
    --------
    >>> from components import ChillerArray, WindVector
    >>> from models import GaussianPlumeModel
    >>>
    >>> array = ChillerArray.create_grid(rows=4, cols=4, spacing_m=10.0)
    >>> wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    >>> model = GaussianPlumeModel(dispersion_coeff=1.2)
    >>>
    >>> env = SimulationEnvironment(array, wind, model)
    >>> result = env.compute_performance(
    ...     active_mask=np.ones(16, dtype=bool),
    ...     total_load_kw=500.0
    ... )
    """

    chiller_array: ChillerArray
    wind: WindVector
    interaction_model: BaseInteractionModel
    _interaction_matrix: NDArray[np.float64] = field(
        init=False, repr=False, default_factory=lambda: np.array([])
    )

    def __post_init__(self) -> None:
        """Pre-compute interaction matrix on initialization.

        This is done once to avoid redundant computation during
        repeated performance evaluations (e.g., optimization).
        """
        self._interaction_matrix = self.interaction_model.compute_interaction_matrix(
            self.chiller_array.positions_m,
            self.wind,
        )

    @property
    def num_chillers(self) -> int:
        """Number of chillers in the array.

        Returns
        -------
        int
            Total chiller count.
        """
        return self.chiller_array.num_chillers

    @property
    def interaction_matrix(self) -> NDArray[np.float64]:
        """Pre-computed interaction matrix (read-only).

        Returns
        -------
        NDArray[np.float64]
            Interaction matrix A, shape (N, N).
        """
        return self._interaction_matrix

    def compute_performance(
        self,
        active_mask: NDArray[np.bool_],
        total_load_kw: float,
        startup_factors: NDArray[np.float64] | None = None,
    ) -> PerformanceResult:
        """Calculate total energy and individual COPs.

        Computes the performance of the chiller array given which
        chillers are active and the total cooling load to satisfy.

        Parameters
        ----------
        active_mask : NDArray[np.bool_]
            Boolean array indicating which chillers are ON, shape (N,).
        total_load_kw : float
            Total cooling load to distribute across active chillers.
        startup_factors : NDArray[np.float64] | None, optional
            COP ramp-up factors [0,1] per chiller during startup, shape (N,).
            If None, all active chillers use factor 1 (fully ramped).

        Returns
        -------
        PerformanceResult
            Immutable result with total_work_kw, cop_array, etc.

        Notes
        -----
        Physics:

        1. Load is distributed evenly among active chillers
        2. Temperature rise at each unit is computed from interaction matrix
        3. COP degrades based on temperature rise
        4. Total work is sum of individual power consumptions

        The COP degradation follows:

        .. math::

            COP_m = \\frac{COP_{base}}{1 + \\alpha \\sum_k A_{km} \\cdot active_k}

        where :math:`A_{km}` is the thermal impact of chiller k on m.

        Reference
        ---------
        ASHRAE Handbook - HVAC Applications, Chapter 43

        Examples
        --------
        >>> result = env.compute_performance(
        ...     active_mask=np.array([True, True, False, True]),
        ...     total_load_kw=300.0
        ... )
        >>> result.total_work_kw
        75.5  # Example value
        """
        n_active = int(np.sum(active_mask))

        # Handle edge case: no active chillers
        if n_active == 0:
            return PerformanceResult(
                total_work_kw=float("inf"),
                cop_array=np.zeros(self.num_chillers),
                temp_rise_array=np.zeros(self.num_chillers),
                load_per_unit_kw=0.0,
            )

        # Distribute load evenly among active chillers
        load_per_unit_kw = total_load_kw / n_active

        # =====================================================================
        # Compute temperature rise at each unit (vectorized)
        # temp_rise[m] = sum over k of (A[k,m] * active[k])
        # Shape: (N,)
        # =====================================================================
        active_float = active_mask.astype(np.float64)
        temp_rise = np.dot(active_float, self._interaction_matrix)

        # =====================================================================
        # Compute degraded COP (vectorized)
        # COP_m = (base_cop * age_factor[m]) / (1 + alpha * temp_rise[m])
        # Age factor decays exponentially from 100% at age=0 to 80% at age=1yr.
        # Shape: (N,)
        # =====================================================================
        base_cop = self.chiller_array.base_cop
        alpha = self.chiller_array.alpha
        age_factors = self.chiller_array.cop_age_factors
        base_cop_per_unit = base_cop * age_factors
        cop_array = base_cop_per_unit / (1.0 + alpha * temp_rise)

        # Apply startup ramp (linear: 0 to 1 over startup time)
        if startup_factors is not None:
            if startup_factors.shape != (self.num_chillers,):
                raise ValueError(
                    f"startup_factors shape {startup_factors.shape} "
                    f"must match num_chillers ({self.num_chillers})"
                )
            # Minimum factor to avoid division by zero; models minimal cooling at t=0
            factors = np.maximum(startup_factors, 0.01)
            cop_array = cop_array * factors

        # =====================================================================
        # Total work = sum(load / COP) for active chillers only
        # =====================================================================
        # Avoid division by zero for inactive chillers
        cop_active = cop_array[active_mask]
        total_work_kw = float(np.sum(load_per_unit_kw / cop_active))

        return PerformanceResult(
            total_work_kw=total_work_kw,
            cop_array=cop_array,
            temp_rise_array=temp_rise,
            load_per_unit_kw=load_per_unit_kw,
        )

    def compute_cop_at_position(
        self,
        position_idx: int,
        active_mask: NDArray[np.bool_],
    ) -> float:
        """Compute COP at a specific chiller position.

        Utility method for analyzing individual chiller performance.

        Parameters
        ----------
        position_idx : int
            Index of the chiller to analyze.
        active_mask : NDArray[np.bool_]
            Boolean array indicating which chillers are active.

        Returns
        -------
        float
            COP at the specified position.
        """
        if position_idx < 0 or position_idx >= self.num_chillers:
            raise IndexError(
                f"position_idx {position_idx} out of range "
                f"[0, {self.num_chillers})"
            )

        active_float = active_mask.astype(np.float64)
        temp_rise = np.dot(active_float, self._interaction_matrix[:, position_idx])
        age_factor = self.chiller_array.cop_age_factors[position_idx]
        base_cop_aged = self.chiller_array.base_cop * age_factor
        return base_cop_aged / (1.0 + self.chiller_array.alpha * temp_rise)

    def get_thermal_impact_on(
        self,
        target_idx: int,
    ) -> NDArray[np.float64]:
        """Get thermal impact from all chillers on a target chiller.

        Parameters
        ----------
        target_idx : int
            Index of the target chiller.

        Returns
        -------
        NDArray[np.float64]
            Impact values from each chiller, shape (N,).
            Entry k is the impact of chiller k on the target.
        """
        return self._interaction_matrix[:, target_idx].copy()

    def with_new_wind(
        self,
        wind: WindVector,
    ) -> SimulationEnvironment:
        """Create new environment with different wind conditions.

        Parameters
        ----------
        wind : WindVector
            New wind conditions.

        Returns
        -------
        SimulationEnvironment
            New environment with updated wind.

        Notes
        -----
        This creates a new environment rather than modifying the
        existing one, maintaining immutability principles.
        """
        return SimulationEnvironment(
            chiller_array=self.chiller_array,
            wind=wind,
            interaction_model=self.interaction_model,
        )

    def with_new_model(
        self,
        interaction_model: BaseInteractionModel,
    ) -> SimulationEnvironment:
        """Create new environment with different interaction model.

        Parameters
        ----------
        interaction_model : BaseInteractionModel
            New interaction model.

        Returns
        -------
        SimulationEnvironment
            New environment with updated model.
        """
        return SimulationEnvironment(
            chiller_array=self.chiller_array,
            wind=self.wind,
            interaction_model=interaction_model,
        )
