from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class WindConditions:
    """Snapshot of wind speed and direction at a single point in time."""

    speed_m_per_s: float
    angle_deg: float  # CCW from east

    @property
    def unit_vector(self) -> NDArray[np.float64]:
        """Return a unit vector pointing in the wind direction."""
        rad = np.deg2rad(self.angle_deg)
        return np.array([np.cos(rad), np.sin(rad)])

    @property
    def velocity_vector(self) -> NDArray[np.float64]:
        """Return the wind velocity vector (speed × direction)."""
        return self.speed_m_per_s * self.unit_vector


@runtime_checkable
class WindFn(Protocol):
    """Protocol for a callable that returns wind conditions at a given time."""

    def __call__(self, time_hours: float) -> tuple[float, float]:
        """Return (speed_m_per_s, angle_deg) at the given time."""
        ...
