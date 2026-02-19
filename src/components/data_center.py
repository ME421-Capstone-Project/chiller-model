"""Data centre cooling-load model with optional time-varying profiles.

Reference
---------
ASHRAE Handbook - HVAC Applications, Chapter 43 (Data Centers)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray


@dataclass
class DataCenter:
    """Cooling load that the chiller array must satisfy.

    Attributes
    ----------
    base_load_kw : float
        Baseline (minimum) cooling load in kW.
    peak_load_kw : float | None
        Maximum cooling load. Defaults to *base_load_kw*.
    load_profile : Callable[[float], float] | None
        Maps time (hours) → load factor in [0, 1].
        ``None`` means constant load at *base_load_kw*.
    """

    base_load_kw: float
    peak_load_kw: float | None = None
    load_profile: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.base_load_kw <= 0:
            raise ValueError(f"base_load_kw must be > 0, got {self.base_load_kw}")
        if self.peak_load_kw is None:
            object.__setattr__(self, "peak_load_kw", self.base_load_kw)
        elif self.peak_load_kw < self.base_load_kw:
            raise ValueError(
                f"peak_load_kw ({self.peak_load_kw}) cannot be less than "
                f"base_load_kw ({self.base_load_kw})"
            )

    def get_load_kw(self, time_hours: float = 0.0) -> float:
        """Return cooling load in kW at the given time."""
        if self.load_profile is None:
            return self.base_load_kw

        factor = np.clip(self.load_profile(time_hours), 0.0, 1.0)
        assert self.peak_load_kw is not None
        return self.base_load_kw + factor * (self.peak_load_kw - self.base_load_kw)

    def get_load_series_kw(
        self,
        time_hours: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Vectorised load over a time array."""
        if self.load_profile is None:
            return np.full_like(time_hours, self.base_load_kw)

        vectorized_profile = np.vectorize(self.load_profile)
        factors = np.clip(vectorized_profile(time_hours), 0.0, 1.0)

        assert self.peak_load_kw is not None
        return self.base_load_kw + factors * (self.peak_load_kw - self.base_load_kw)

    @classmethod
    def with_daily_profile(
        cls,
        base_load_kw: float,
        peak_load_kw: float,
        peak_start_hour: float = 9.0,
        peak_end_hour: float = 17.0,
    ) -> DataCenter:
        """Step-function profile: peak during business hours, base otherwise."""

        def daily_profile(time_hours: float) -> float:
            hour = time_hours % 24.0
            if peak_start_hour <= hour < peak_end_hour:
                return 1.0
            return 0.0

        return cls(
            base_load_kw=base_load_kw,
            peak_load_kw=peak_load_kw,
            load_profile=daily_profile,
        )

    @classmethod
    def with_sinusoidal_profile(
        cls,
        base_load_kw: float,
        peak_load_kw: float,
        period_hours: float = 24.0,
        phase_hours: float = 0.0,
    ) -> DataCenter:
        """Smooth sinusoidal load oscillation between base and peak."""

        def sinusoidal_profile(time_hours: float) -> float:
            return 0.5 * (
                1 + np.sin(2 * np.pi * (time_hours - phase_hours) / period_hours)
            )

        return cls(
            base_load_kw=base_load_kw,
            peak_load_kw=peak_load_kw,
            load_profile=sinusoidal_profile,
        )
