from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChillerGrid:
    positions_m: NDArray[np.float64]   # shape (n_chillers, 2)
    base_cop: float
    alpha: float
    ages_years: NDArray[np.float64]    # shape (n_chillers,)

    @property
    def num_chillers(self) -> int:
        return len(self.positions_m)

    @classmethod
    def create_grid(
        cls,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float,
        alpha: float = 0.7,
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
    ) -> ChillerGrid:
        xs = np.arange(cols) * spacing_m
        ys = np.arange(rows) * spacing_m
        xx, yy = np.meshgrid(xs, ys)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        n = rows * cols
        if ages_years is not None:
            resolved_ages = np.asarray(ages_years, dtype=np.float64)
        else:
            rng = np.random.default_rng(seed)
            resolved_ages = rng.uniform(0.0, 20.0, size=n)

        return cls(
            positions_m=positions,
            base_cop=base_cop,
            alpha=alpha,
            ages_years=resolved_ages,
        )
