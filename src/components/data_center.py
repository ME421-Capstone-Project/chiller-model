"""Data center model with load profile.

This module defines the DataCenter class representing the cooling
load requirements that the chiller array must satisfy.

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
    """Data center cooling load profile.

    Represents the cooling demand that must be satisfied by the
    chiller array. Can model constant or time-varying loads.

    Attributes
    ----------
    base_load_kw : float
        Baseline cooling load in kilowatts.
    peak_load_kw : float
        Maximum cooling load in kilowatts.
    load_profile : Callable[[float], float] | None
        Optional function mapping time (hours) to load factor (0-1).
        If None, constant load at base_load_kw is assumed.

    Notes
    -----
    Data center cooling loads typically follow patterns based on:
    - IT equipment utilization
    - Time of day (business hours vs. off-peak)
    - Seasonal variations in ambient conditions

    Reference
    ---------
    ASHRAE Handbook - HVAC Applications, Chapter 43

    Examples
    --------
    >>> dc = DataCenter(base_load_kw=500.0, peak_load_kw=1000.0)
    >>> dc.get_load_kw(time_hours=12.0)
    500.0
    """

    base_load_kw: float
    peak_load_kw: float | None = None
    load_profile: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        """Validate data center parameters."""
        if self.base_load_kw <= 0:
            raise ValueError(
                f"base_load_kw must be > 0, got {self.base_load_kw}"
            )
        if self.peak_load_kw is None:
            object.__setattr__(self, "peak_load_kw", self.base_load_kw)
        elif self.peak_load_kw < self.base_load_kw:
            raise ValueError(
                f"peak_load_kw ({self.peak_load_kw}) cannot be less than "
                f"base_load_kw ({self.base_load_kw})"
            )

    def get_load_kw(self, time_hours: float = 0.0) -> float:
        """Get cooling load at a specific time.

        Parameters
        ----------
        time_hours : float
            Time in hours (for time-varying profiles).

        Returns
        -------
        float
            Cooling load in kilowatts at the specified time.

        Examples
        --------
        >>> dc = DataCenter(base_load_kw=500.0, peak_load_kw=1000.0)
        >>> dc.get_load_kw(0.0)
        500.0
        """
        if self.load_profile is None:
            return self.base_load_kw

        # Load profile returns factor between 0 and 1
        factor = self.load_profile(time_hours)
        factor = np.clip(factor, 0.0, 1.0)

        # Interpolate between base and peak
        assert self.peak_load_kw is not None  # Set in __post_init__
        return self.base_load_kw + factor * (self.peak_load_kw - self.base_load_kw)

    def get_load_series_kw(
        self,
        time_hours: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Get cooling load over a time series.

        Uses NumPy vectorization for efficiency with large arrays.

        Parameters
        ----------
        time_hours : NDArray[np.float64]
            Array of time points in hours.

        Returns
        -------
        NDArray[np.float64]
            Array of cooling loads in kW at each time point.

        Notes
        -----
        Implementation uses NumPy vectorization per project rules.
        NO explicit for-loops over time points.
        """
        if self.load_profile is None:
            return np.full_like(time_hours, self.base_load_kw)

        # Vectorize the load profile function
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
        """Create data center with typical daily load profile.

        Peak load during business hours, base load otherwise.

        Parameters
        ----------
        base_load_kw : float
            Off-peak cooling load in kW.
        peak_load_kw : float
            Peak cooling load during business hours in kW.
        peak_start_hour : float
            Hour when peak period begins (default 9:00).
        peak_end_hour : float
            Hour when peak period ends (default 17:00).

        Returns
        -------
        DataCenter
            Data center with daily profile.

        Examples
        --------
        >>> dc = DataCenter.with_daily_profile(500.0, 1000.0)
        >>> dc.get_load_kw(12.0)  # Midday
        1000.0
        >>> dc.get_load_kw(2.0)   # Night
        500.0
        """

        def daily_profile(time_hours: float) -> float:
            """Simple step function for daily profile."""
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
        """Create data center with sinusoidal load profile.

        Parameters
        ----------
        base_load_kw : float
            Minimum cooling load in kW.
        peak_load_kw : float
            Maximum cooling load in kW.
        period_hours : float
            Period of the sinusoidal variation (default 24 hours).
        phase_hours : float
            Phase offset in hours (default 0).

        Returns
        -------
        DataCenter
            Data center with sinusoidal profile.
        """

        def sinusoidal_profile(time_hours: float) -> float:
            """Sinusoidal load factor (0 to 1)."""
            return 0.5 * (1 + np.sin(2 * np.pi * (time_hours - phase_hours) / period_hours))

        return cls(
            base_load_kw=base_load_kw,
            peak_load_kw=peak_load_kw,
            load_profile=sinusoidal_profile,
        )
