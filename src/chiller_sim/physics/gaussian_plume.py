from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.wind import WindConditions


@dataclass(frozen=True)
class GaussianPlumeModel:
    r"""Gaussian plume model for chiller thermal interaction.

    With σ_y held constant (``dispersion_coeff``), the per-pair influence is a
    simplified constant-σ form of the standard ground-level Gaussian plume:

    .. math::

        I_{k \to m} = \begin{cases}
            0 & u < u_{\min} \\
            \dfrac{1}{u\,(x + 1)} \exp\!\left(-\dfrac{y^2}{\sigma\,(x + 1)}\right)
                & x > 0,\ u \ge u_{\min} \\
            0 & \text{otherwise}
        \end{cases}

    where :math:`x` is the along-wind distance from chiller *k* to chiller *m*,
    :math:`y` is the cross-wind distance, :math:`u` is ``wind.speed_m_per_s``,
    :math:`\sigma` is ``dispersion_coeff``, and :math:`u_{\min}` is
    ``u_min_m_per_s``. The :math:`1/u` factor is the physical dilution term
    from the full Gaussian plume equation.

    ``u_min_m_per_s`` is a hard cutoff, not a floor: when the wind speed falls
    below it, the interaction matrix is returned as zero at every distance.
    """

    dispersion_coeff: float = 1.2
    u_min_m_per_s: float = 0.1

    def compute_interaction_matrix(
        self,
        positions_m: NDArray[np.float64],
        wind: WindConditions,
    ) -> NDArray[np.float64]:
        """Return N×N matrix where entry [k, m] is thermal influence of chiller k on chiller m."""
        n = positions_m.shape[0]
        u = wind.speed_m_per_s
        if u < self.u_min_m_per_s:
            return np.zeros((n, n), dtype=np.float64)

        uv = wind.unit_vector  # (2,) unit vector in wind direction
        perp = np.array([-uv[1], uv[0]])  # perpendicular unit vector

        # Pairwise displacement vectors: diff[k, m] = positions[m] - positions[k]
        diff = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]  # (n, n, 2)

        longitudinal = diff @ uv  # (n, n): along-wind distance from k to m
        lateral = diff @ perp  # (n, n): cross-wind distance from k to m

        sigma = self.dispersion_coeff
        denom = longitudinal + 1.0
        with np.errstate(divide="ignore", invalid="ignore"):
            influence = np.where(
                longitudinal > 0,
                np.exp(-(lateral**2) / (sigma * denom)) / (denom * u),
                0.0,
            )

        np.fill_diagonal(influence, 0.0)
        # Safety net: suppress any NaN/Inf from edge cases with coincident positions
        return np.nan_to_num(influence, nan=0.0, posinf=0.0, neginf=0.0)
