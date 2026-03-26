from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChillerGrid:
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
    ) -> ChillerGrid:
        """Build a regular rectangular chiller grid with optional random ages."""
        if max_cooling_kw <= 0:
            raise ValueError(f"max_cooling_kw must be > 0, got {max_cooling_kw}")

        xs = np.arange(cols) * spacing_m
        ys = np.arange(rows) * spacing_m
        xx, yy = np.meshgrid(xs, ys)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        n = rows * cols
        if ages_years is not None:
            resolved_ages = np.asarray(ages_years, dtype=np.float64)
            if len(resolved_ages) != rows * cols:
                raise ValueError(
                    f"ages_years length {len(resolved_ages)} does not match "
                    f"grid size {rows * cols} ({rows}×{cols})"
                )
        else:
            rng = np.random.default_rng(seed)
            resolved_ages = rng.uniform(0.0, 20.0, size=n)

        return cls(
            positions_m=positions,
            base_cop=base_cop,
            alpha=alpha,
            ages_years=resolved_ages,
            max_cooling_kw=max_cooling_kw,
        )
