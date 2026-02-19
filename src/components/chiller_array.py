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

from core.constants import (
    AGE_MAX_YEARS,
    AGE_MIN_YEARS,
    DEFAULT_ALPHA,
    DEFAULT_BASE_COP,
    compute_cop_age_factors_vectorized,
)


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
    ages_years: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Validate array parameters and initialize ages if not provided."""
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

        # Initialize ages: random uniform [AGE_MIN, AGE_MAX] if not provided
        n = len(self.positions_m)
        if self.ages_years is None:
            rng = np.random.default_rng()
            ages = rng.uniform(AGE_MIN_YEARS, AGE_MAX_YEARS, size=n)
            object.__setattr__(self, "ages_years", ages.astype(np.float64))
        else:
            ages = np.asarray(self.ages_years, dtype=np.float64)
            if ages.shape != (n,):
                raise ValueError(
                    f"ages_years must have shape ({n},), got {ages.shape}"
                )
            if np.any(ages < 0):
                raise ValueError("ages_years must be non-negative")
            object.__setattr__(self, "ages_years", ages)

    @property
    def cop_age_factors(self) -> NDArray[np.float64]:
        """COP multipliers from age degradation for each chiller.

        Returns
        -------
        NDArray[np.float64]
            Age-based COP multipliers, shape (N,). Multiply base_cop element-wise.
        """
        return compute_cop_age_factors_vectorized(self.ages_years)

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
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
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
        ages_years : NDArray[np.float64] | None, optional
            Chiller ages in years, shape (rows*cols,). If None, random uniform
            [AGE_MIN_YEARS, AGE_MAX_YEARS] using seed.
        seed : int | None, optional
            Random seed for age assignment when ages_years is None.

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

        if ages_years is None:
            rng = np.random.default_rng(seed)
            n = rows * cols
            ages_years = rng.uniform(AGE_MIN_YEARS, AGE_MAX_YEARS, size=n).astype(
                np.float64
            )

        return cls(
            positions_m=positions.astype(np.float64),
            base_cop=base_cop,
            alpha=alpha,
            ages_years=ages_years,
        )

    @classmethod
    def create_random(
        cls,
        num_chillers: int,
        area_size_m: tuple[float, float],
        base_cop: float = DEFAULT_BASE_COP,
        alpha: float = DEFAULT_ALPHA,
        seed: int | None = None,
        ages_years: NDArray[np.float64] | None = None,
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
            Random seed for reproducibility of positions (and ages if ages_years None).
        ages_years : NDArray[np.float64] | None, optional
            Chiller ages in years, shape (num_chillers,). If None, random uniform
            [AGE_MIN_YEARS, AGE_MAX_YEARS] using same RNG as positions.

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

        if ages_years is None:
            ages_years = rng.uniform(
                AGE_MIN_YEARS, AGE_MAX_YEARS, size=num_chillers
            ).astype(np.float64)

        return cls(
            positions_m=positions.astype(np.float64),
            base_cop=base_cop,
            alpha=alpha,
            ages_years=ages_years,
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
