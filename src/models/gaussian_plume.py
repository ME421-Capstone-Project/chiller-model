"""Gaussian plume dispersion model for thermal wake interactions.

Transfer function: (chiller positions, wind) → interaction matrix A[N×N].

Physics
-------
Exhaust heat from an upwind chiller disperses laterally as it travels
downwind, following a Gaussian profile:

    A[k, m] = exp(-lateral² / (σ · (longitudinal + 1))) / (longitudinal + 1)

Only downwind pairs (longitudinal > 0) have nonzero coupling.
Diagonal entries are always zero (no self-interaction).

Reference
---------
ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
EPA AP-42, Chapter 1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from core.constants import DEFAULT_DISPERSION_COEFF

if TYPE_CHECKING:
    from components.wind import WindVector


class GaussianPlumeModel:
    """Compute the N×N thermal interaction matrix via Gaussian plume dispersion.

    Parameters
    ----------
    dispersion_coeff : float
        Plume spread parameter σ. Higher values → faster lateral spread → less
        concentrated interference on downwind neighbours.
    """

    def __init__(self, dispersion_coeff: float = DEFAULT_DISPERSION_COEFF) -> None:
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
        """Return the interaction matrix A of shape (N, N).

        A[k, m] is the thermal impact of chiller k on chiller m.
        Fully vectorised — no Python loops.
        """
        wind_direction = wind.direction

        pairwise_displacement = (
            positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]
        )

        longitudinal_distance = np.einsum(
            "ijk,k->ij", pairwise_displacement, wind_direction
        )

        longitudinal_projection = (
            longitudinal_distance[:, :, np.newaxis] * wind_direction
        )
        lateral_displacement = pairwise_displacement - longitudinal_projection
        lateral_distance = np.linalg.norm(lateral_displacement, axis=2)

        denominator = longitudinal_distance + 1.0

        with np.errstate(divide="ignore", invalid="ignore"):
            exponent = -(lateral_distance ** 2) / (self.dispersion_coeff * denominator)
            interaction = np.exp(exponent) / denominator

        interaction = np.where(longitudinal_distance > 0, interaction, 0.0)
        np.fill_diagonal(interaction, 0.0)
        interaction = np.nan_to_num(interaction, nan=0.0, posinf=0.0, neginf=0.0)

        return interaction

    def compute_longitudinal_distances(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Pairwise longitudinal (along-wind) distances, shape (N, N)."""
        displacement = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]
        return np.einsum("ijk,k->ij", displacement, wind.direction)

    def compute_lateral_distances(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Pairwise lateral (cross-wind) distances, shape (N, N)."""
        displacement = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]
        longitudinal = np.einsum("ijk,k->ij", displacement, wind.direction)
        longitudinal_projection = longitudinal[:, :, np.newaxis] * wind.direction
        lateral_displacement = displacement - longitudinal_projection
        return np.linalg.norm(lateral_displacement, axis=2)
