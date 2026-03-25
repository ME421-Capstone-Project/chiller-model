from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.wind import WindConditions


@dataclass(frozen=True)
class GaussianPlumeModel:
    dispersion_coeff: float = 1.2

    def compute_interaction_matrix(
        self,
        positions_m: NDArray[np.float64],
        wind: WindConditions,
    ) -> NDArray[np.float64]:
        """Return N×N matrix A where A[k, m] = thermal influence of chiller k on chiller m."""
        n = len(positions_m)
        uv = wind.unit_vector                        # (2,) unit vector in wind direction
        perp = np.array([-uv[1], uv[0]])             # perpendicular unit vector

        # Pairwise displacement vectors: diff[k, m] = positions[m] - positions[k]
        diff = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]  # (n, n, 2)

        longitudinal = diff @ uv    # (n, n): along-wind distance from k to m
        lateral = diff @ perp       # (n, n): cross-wind distance from k to m

        sigma = self.dispersion_coeff
        denom = longitudinal + 1.0
        with np.errstate(divide='ignore', invalid='ignore'):
            A = np.where(
                longitudinal > 0,
                np.exp(-lateral**2 / (sigma * denom)) / denom,
                0.0,
            )

        np.fill_diagonal(A, 0.0)
        # Safety net: suppress any NaN/Inf from edge cases with coincident positions
        return np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)
