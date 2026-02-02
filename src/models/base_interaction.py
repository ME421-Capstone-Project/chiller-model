"""Abstract base class for thermal interaction models.

This module defines the interface that all interaction models must
implement. Use this to create custom performance degradation models
based on position, wind speed, temperature, or other factors.

Design Pattern
--------------
The SimulationEnvironment HOLDS an interaction model instance
(composition) rather than inheriting from it. This allows easy
swapping of models at runtime.

Reference
---------
ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from src.components.wind import WindVector


class BaseInteractionModel(ABC):
    """Abstract base class for thermal interaction models.

    Subclass this to implement custom performance degradation
    models based on position, wind speed, temperature, etc.

    The interaction matrix A represents thermal coupling:
    - A[k, m] = impact of chiller k's exhaust on chiller m's inlet
    - Only downwind units (positive longitudinal distance) are affected
    - Diagonal elements (self-interaction) should be zero

    Design Note
    -----------
    This uses composition - the SimulationEnvironment HOLDS an
    interaction model instance rather than inheriting from it.
    This follows the project's "Composition over Inheritance" rule.

    Notes
    -----
    All implementations MUST use NumPy vectorized operations.
    NO explicit for-loops over large arrays per project rules.

    Reference
    ---------
    ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40

    Examples
    --------
    To create a custom interaction model:

    >>> class MyModel(BaseInteractionModel):
    ...     def compute_interaction_matrix(self, positions_m, wind):
    ...         # Custom physics implementation
    ...         n = len(positions_m)
    ...         return np.zeros((n, n))
    """

    @abstractmethod
    def compute_interaction_matrix(
        self,
        positions_m: NDArray[np.float64],
        wind: WindVector,
    ) -> NDArray[np.float64]:
        """Compute the N x N interaction matrix A.

        This method must be implemented by all subclasses to define
        the thermal coupling physics between chillers.

        Parameters
        ----------
        positions_m : NDArray[np.float64]
            Chiller positions in meters, shape (N, 2).
            First column is x-coordinate, second is y-coordinate.
        wind : WindVector
            Current wind conditions including velocity and temperature.

        Returns
        -------
        NDArray[np.float64]
            Interaction matrix A, shape (N, N), where A[k, m] is
            the thermal impact factor of chiller k on chiller m.

        Notes
        -----
        Implementation requirements:

        1. **Vectorization**: Use NumPy operations, NO for-loops.
        2. **Diagonal**: A[k, k] = 0 (no self-interaction).
        3. **Non-negative**: All A[k, m] >= 0.
        4. **Downwind only**: A[k, m] = 0 if m is upwind of k.

        The matrix is used in COP calculation as:

        .. math::

            COP_m = \\frac{COP_{base}}{1 + \\alpha \\sum_k A_{km} \\cdot active_k}

        Reference
        ---------
        ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
        """
        pass

    def validate_matrix(
        self,
        matrix: NDArray[np.float64],
        num_chillers: int,
    ) -> None:
        """Validate that an interaction matrix meets requirements.

        Parameters
        ----------
        matrix : NDArray[np.float64]
            The interaction matrix to validate.
        num_chillers : int
            Expected number of chillers (matrix should be NxN).

        Raises
        ------
        ValueError
            If matrix doesn't meet physical requirements.

        Notes
        -----
        Checks performed:
        - Shape is (N, N)
        - All values are non-negative
        - Diagonal is zero
        """
        expected_shape = (num_chillers, num_chillers)
        if matrix.shape != expected_shape:
            raise ValueError(
                f"Matrix shape {matrix.shape} doesn't match expected "
                f"{expected_shape}"
            )

        if np.any(matrix < 0):
            raise ValueError(
                "Interaction matrix contains negative values, which is "
                "non-physical for thermal interference"
            )

        if not np.allclose(np.diag(matrix), 0):
            raise ValueError(
                "Interaction matrix diagonal must be zero (no self-interaction)"
            )
