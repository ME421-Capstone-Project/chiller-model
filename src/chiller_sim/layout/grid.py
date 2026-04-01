from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChillerLayout:
    """Immutable description of a chiller array layout and its ageing state."""

    positions_m: NDArray[np.float64]  # shape (n_chillers, 2)
    base_cop: float
    alpha: float
    ages_years: NDArray[np.float64]  # shape (n_chillers,)
    max_cooling_kw: float  # nameplate capacity of a brand-new chiller (same for all)

    @property
    def num_chillers(self) -> int:
        """Return the total number of chillers in the grid."""
        return len(self.positions_m)

    @classmethod
    def from_positions(
        cls,
        positions_m: NDArray[np.float64],
        ages_years: NDArray[np.float64],
        base_cop: float,
        max_cooling_kw: float,
        alpha: float = 0.7,
    ) -> ChillerLayout:
        """Build a layout from explicit (x, y) positions.

        Parameters
        ----------
        positions_m : ndarray, shape (n, 2)
            Each row is an (x, y) coordinate in metres.
        ages_years : ndarray, shape (n,)
            Age of each chiller in years.
        base_cop : float
            Nameplate COP for a brand-new chiller.
        max_cooling_kw : float
            Nameplate cooling capacity in kW (must be > 0).
        alpha : float, optional
            Age-degradation exponent, by default 0.7.

        Returns
        -------
        ChillerLayout
        """
        positions_m = np.asarray(positions_m, dtype=np.float64)
        ages_years = np.asarray(ages_years, dtype=np.float64)

        if positions_m.ndim != 2 or positions_m.shape[1] != 2:
            raise ValueError(f"positions_m must have shape (n, 2), got {positions_m.shape}")
        if ages_years.shape[0] != positions_m.shape[0]:
            raise ValueError(
                f"ages_years length {len(ages_years)} does not match "
                f"{positions_m.shape[0]} positions"
            )
        if max_cooling_kw <= 0:
            raise ValueError(f"max_cooling_kw must be > 0, got {max_cooling_kw}")

        return cls(
            positions_m=positions_m,
            base_cop=base_cop,
            alpha=alpha,
            ages_years=ages_years,
            max_cooling_kw=max_cooling_kw,
        )

    @classmethod
    def create_grid(
        cls,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float,
        max_cooling_kw: float,
        alpha: float = 0.7,
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
    ) -> ChillerLayout:
        """Build a regular rectangular chiller grid with optional random ages."""
        xs = np.arange(cols) * spacing_m
        ys = np.arange(rows) * spacing_m
        xx, yy = np.meshgrid(xs, ys)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        n = rows * cols
        if ages_years is None:
            rng = np.random.default_rng(seed)
            resolved_ages = rng.uniform(0.0, 20.0, size=n)
        else:
            resolved_ages = np.asarray(ages_years, dtype=np.float64)
            if len(resolved_ages) != n:
                raise ValueError(
                    f"ages_years length {len(resolved_ages)} does not match "
                    f"grid size {n} ({rows}×{cols})"
                )

        return cls.from_positions(
            positions_m=positions,
            ages_years=resolved_ages,
            base_cop=base_cop,
            max_cooling_kw=max_cooling_kw,
            alpha=alpha,
        )
