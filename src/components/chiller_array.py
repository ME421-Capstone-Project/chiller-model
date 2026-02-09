"""Chiller array model with spatial positions.

This module defines the ChillerArray class representing a collection
of chillers at specific 2D positions. The array manages the spatial
layout that affects thermal interference patterns.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43 (Data Centers)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from core.constants import DEFAULT_ALPHA, DEFAULT_BASE_COP


@dataclass
class ChillerArray:
    """Array of chillers with spatial positions.

    Represents a collection of identical chillers arranged in 2D space.
    The positions determine thermal interference patterns based on
    wind direction.

    Attributes
    ----------
    positions_m : NDArray[np.float64]
        2D positions of each chiller in meters, shape (N, 2).
        First column is x-coordinate, second is y-coordinate.
    base_cop : float
        Base Coefficient of Performance for all chillers.
    alpha : float
        Temperature sensitivity coefficient for all chillers.

    Notes
    -----
    Currently assumes homogeneous array (all chillers identical).
    Future versions may support heterogeneous specifications.

    Reference
    ---------
    ASHRAE Handbook - HVAC Applications, Chapter 43

    Examples
    --------
    >>> positions = np.array([[0, 0], [10, 0], [20, 0]], dtype=np.float64)
    >>> array = ChillerArray(positions_m=positions, base_cop=5.0, alpha=0.7)
    >>> array.num_chillers
    3
    """

    positions_m: NDArray[np.float64]
    base_cop: float = DEFAULT_BASE_COP
    alpha: float = DEFAULT_ALPHA

    def __post_init__(self) -> None:
        """Validate array parameters."""
        if self.positions_m.ndim != 2 or self.positions_m.shape[1] != 2:
            raise ValueError(
                f"positions_m must have shape (N, 2), got {self.positions_m.shape}"
            )
        if len(self.positions_m) == 0:
            raise ValueError("ChillerArray must have at least one chiller")
        if self.base_cop <= 0 or self.base_cop > 10:
            raise ValueError(
                f"base_cop must be in (0, 10], got {self.base_cop}"
            )
        if self.alpha <= 0:
            raise ValueError(f"alpha must be > 0, got {self.alpha}")

        # Ensure float64 for numerical stability
        if self.positions_m.dtype != np.float64:
            object.__setattr__(
                self,
                "positions_m",
                self.positions_m.astype(np.float64),
            )

    @property
    def num_chillers(self) -> int:
        """Number of chillers in the array.

        Returns
        -------
        int
            Total count of chillers.
        """
        return len(self.positions_m)

    @property
    def x_positions_m(self) -> NDArray[np.float64]:
        """X-coordinates of all chillers in meters.

        Returns
        -------
        NDArray[np.float64]
            Array of x-coordinates, shape (N,).
        """
        return self.positions_m[:, 0]

    @property
    def y_positions_m(self) -> NDArray[np.float64]:
        """Y-coordinates of all chillers in meters.

        Returns
        -------
        NDArray[np.float64]
            Array of y-coordinates, shape (N,).
        """
        return self.positions_m[:, 1]

    @property
    def centroid_m(self) -> NDArray[np.float64]:
        """Geometric center of the array in meters.

        Returns
        -------
        NDArray[np.float64]
            Centroid position [x, y], shape (2,).
        """
        return np.mean(self.positions_m, axis=0)

    @classmethod
    def create_grid(
        cls,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float = DEFAULT_BASE_COP,
        alpha: float = DEFAULT_ALPHA,
        origin_m: tuple[float, float] = (0.0, 0.0),
    ) -> ChillerArray:
        """Create a rectangular grid of chillers.

        Parameters
        ----------
        rows : int
            Number of rows in the grid.
        cols : int
            Number of columns in the grid.
        spacing_m : float
            Distance between adjacent chillers in meters.
        base_cop : float, optional
            Base COP for all chillers (default from constants).
        alpha : float, optional
            Temperature sensitivity (default from constants).
        origin_m : tuple[float, float], optional
            Bottom-left corner of the grid (default (0, 0)).

        Returns
        -------
        ChillerArray
            Grid-arranged chiller array.

        Examples
        --------
        >>> array = ChillerArray.create_grid(rows=4, cols=4, spacing_m=10.0)
        >>> array.num_chillers
        16
        """
        if rows <= 0 or cols <= 0:
            raise ValueError(
                f"rows and cols must be positive, got rows={rows}, cols={cols}"
            )
        if spacing_m <= 0:
            raise ValueError(f"spacing_m must be positive, got {spacing_m}")

        x = np.arange(cols) * spacing_m + origin_m[0]
        y = np.arange(rows) * spacing_m + origin_m[1]
        xx, yy = np.meshgrid(x, y)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        return cls(
            positions_m=positions.astype(np.float64),
            base_cop=base_cop,
            alpha=alpha,
        )

    @classmethod
    def create_random(
        cls,
        num_chillers: int,
        area_size_m: tuple[float, float],
        base_cop: float = DEFAULT_BASE_COP,
        alpha: float = DEFAULT_ALPHA,
        seed: int | None = None,
    ) -> ChillerArray:
        """Create randomly positioned chillers within an area.

        Parameters
        ----------
        num_chillers : int
            Number of chillers to place.
        area_size_m : tuple[float, float]
            Size of the area (width, height) in meters.
        base_cop : float, optional
            Base COP for all chillers.
        alpha : float, optional
            Temperature sensitivity.
        seed : int | None, optional
            Random seed for reproducibility.

        Returns
        -------
        ChillerArray
            Randomly arranged chiller array.
        """
        if num_chillers <= 0:
            raise ValueError(
                f"num_chillers must be positive, got {num_chillers}"
            )
        if area_size_m[0] <= 0 or area_size_m[1] <= 0:
            raise ValueError(
                f"area_size_m dimensions must be positive, got {area_size_m}"
            )

        rng = np.random.default_rng(seed)
        positions = rng.random((num_chillers, 2)) * np.array(area_size_m)

        return cls(
            positions_m=positions.astype(np.float64),
            base_cop=base_cop,
            alpha=alpha,
        )

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """Get bounding box of the array.

        Returns
        -------
        tuple[float, float, float, float]
            (x_min, y_min, x_max, y_max) in meters.
        """
        x_min = float(np.min(self.x_positions_m))
        x_max = float(np.max(self.x_positions_m))
        y_min = float(np.min(self.y_positions_m))
        y_max = float(np.max(self.y_positions_m))
        return (x_min, y_min, x_max, y_max)
