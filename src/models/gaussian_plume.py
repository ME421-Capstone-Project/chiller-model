"""Gaussian plume dispersion model for thermal wake effects.

This module implements the default interaction model based on
Gaussian plume dispersion theory. The model calculates how exhaust
heat from upwind chillers affects the inlet conditions of downwind
chillers.

Physics Background
------------------
When hot exhaust air from a chiller is carried downwind, it disperses
laterally following a Gaussian distribution. The concentration of
thermal pollution at any point depends on:

1. Distance along the wind direction (longitudinal)
2. Distance perpendicular to wind (lateral)
3. Dispersion coefficient (atmospheric stability)

Reference
---------
ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
EPA AP-42, Chapter 1 (Industrial Source Complex Dispersion Model)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from src.core.constants import DEFAULT_DISPERSION_COEFF
from src.models.base_interaction import BaseInteractionModel

if TYPE_CHECKING:
    from src.components.wind import WindVector


class GaussianPlumeModel(BaseInteractionModel):
    """Gaussian plume dispersion model for thermal wake effects.

    Physics
    -------
    The exhaust plume from an upwind chiller disperses laterally
    as it travels downwind, following:

    .. math::

        A_{km} = \\frac{\\exp(-d_{lat}^2 / (\\sigma (d_{long} + 1)))}{d_{long} + 1}

    where:

    - :math:`d_{long}`: Longitudinal distance along wind direction (m)
    - :math:`d_{lat}`: Lateral distance perpendicular to wind (m)
    - :math:`\\sigma`: Dispersion coefficient (default 1.2)

    The model only applies to downwind units (d_long > 0).
    The +1 term prevents division by zero when chillers are close.

    Parameters
    ----------
    dispersion_coeff : float
        Plume dispersion coefficient sigma (default 1.2).
        Higher values = faster lateral spread = less interference.

    Attributes
    ----------
    dispersion_coeff : float
        The configured dispersion coefficient.

    Notes
    -----
    Implementation uses fully vectorized NumPy operations:
    - Pairwise displacement via broadcasting
    - Longitudinal projection via einsum
    - Lateral distance via vector subtraction

    NO explicit for-loops per project rules.

    Reference
    ---------
    ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40

    Examples
    --------
    >>> from src.components import WindVector, ChillerArray
    >>> model = GaussianPlumeModel(dispersion_coeff=1.2)
    >>> wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    >>> array = ChillerArray.create_grid(rows=4, cols=4, spacing_m=10.0)
    >>> A = model.compute_interaction_matrix(array.positions_m, wind)
    >>> A.shape
    (16, 16)
    """

    def __init__(self, dispersion_coeff: float = DEFAULT_DISPERSION_COEFF) -> None:
        """Initialize the Gaussian plume model.

        Parameters
        ----------
        dispersion_coeff : float
            Plume dispersion coefficient sigma.
            Must be positive.

        Raises
        ------
        ValueError
            If dispersion_coeff is not positive.
        """
        if dispersion_coeff <= 0:
            raise ValueError(
                f"dispersion_coeff must be positive, got {dispersion_coeff}"
            )
        self.dispersion_coeff = dispersion_coeff

    def compute_interaction_matrix(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Compute interaction matrix using vectorized NumPy operations.

        This method calculates the thermal interference between all
        pairs of chillers based on their relative positions and wind.

        Parameters
        ----------
        positions_m : NDArray[np.float64]
            Chiller positions in meters, shape (N, 2).
        wind : WindVector
            Current wind conditions.

        Returns
        -------
        NDArray[np.float64]
            Interaction matrix A, shape (N, N).
            A[k, m] is the thermal impact of chiller k on chiller m.

        Notes
        -----
        Algorithm steps (all vectorized):

        1. Compute pairwise displacement vectors d_km[k,m] = pos[m] - pos[k]
        2. Project onto wind direction for longitudinal distance
        3. Compute lateral distance as perpendicular component
        4. Apply Gaussian plume formula
        5. Zero out upwind and self-interactions

        Complexity: O(N^2) space and time, but highly optimized via NumPy.

        Reference
        ---------
        ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
        """
        num_chillers = len(positions_m)
        wind_dir = wind.direction  # Unit vector, shape (2,)

        # =====================================================================
        # Step 1: Compute all pairwise displacement vectors
        # d_km[k, m, :] = positions[m] - positions[k]
        # Shape: (N, N, 2)
        # =====================================================================
        d_km = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]

        # =====================================================================
        # Step 2: Longitudinal distance along wind direction
        # long_dist[k, m] = dot(d_km[k, m], wind_dir)
        # Positive means m is downwind of k
        # Shape: (N, N)
        # =====================================================================
        long_dist = np.einsum("ijk,k->ij", d_km, wind_dir)

        # =====================================================================
        # Step 3: Lateral distance perpendicular to wind
        # lat_vec = d_km - (long_dist * wind_dir)
        # lat_dist = ||lat_vec||
        # Shape: (N, N)
        # =====================================================================
        long_vec = long_dist[:, :, np.newaxis] * wind_dir  # Shape (N, N, 2)
        lat_vec = d_km - long_vec
        lat_dist = np.linalg.norm(lat_vec, axis=2)

        # =====================================================================
        # Step 4: Apply Gaussian plume formula
        # A_km = exp(-lat^2 / (sigma * (long + 1))) / (long + 1)
        # The +1 prevents division by zero for nearby chillers
        # =====================================================================
        sigma = self.dispersion_coeff
        denominator = long_dist + 1.0

        # Suppress warnings for negative long_dist (handled below)
        with np.errstate(divide="ignore", invalid="ignore"):
            exponent = -(lat_dist**2) / (sigma * denominator)
            interaction = np.exp(exponent) / denominator

        # =====================================================================
        # Step 5: Zero out invalid entries
        # - Upwind units (long_dist <= 0): no thermal impact
        # - Self-interaction (diagonal): zero by definition
        # =====================================================================
        interaction = np.where(long_dist > 0, interaction, 0.0)
        np.fill_diagonal(interaction, 0.0)

        # Replace any NaN/inf that might have occurred
        interaction = np.nan_to_num(interaction, nan=0.0, posinf=0.0, neginf=0.0)

        return interaction

    def compute_longitudinal_distances(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Compute longitudinal distances between all chiller pairs.

        Utility method for analysis and visualization.

        Parameters
        ----------
        positions_m : NDArray[np.float64]
            Chiller positions, shape (N, 2).
        wind : WindVector
            Wind conditions.

        Returns
        -------
        NDArray[np.float64]
            Longitudinal distance matrix, shape (N, N).
            Positive values indicate downwind direction.
        """
        d_km = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]
        return np.einsum("ijk,k->ij", d_km, wind.direction)

    def compute_lateral_distances(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Compute lateral distances between all chiller pairs.

        Utility method for analysis and visualization.

        Parameters
        ----------
        positions_m : NDArray[np.float64]
            Chiller positions, shape (N, 2).
        wind : WindVector
            Wind conditions.

        Returns
        -------
        NDArray[np.float64]
            Lateral distance matrix, shape (N, N).
        """
        wind_dir = wind.direction
        d_km = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]
        long_dist = np.einsum("ijk,k->ij", d_km, wind_dir)
        long_vec = long_dist[:, :, np.newaxis] * wind_dir
        lat_vec = d_km - long_vec
        return np.linalg.norm(lat_vec, axis=2)
