"""Immutable wind vector and time-varying wind profiles.

Reference
---------
ASHRAE Handbook - Fundamentals, Chapter 24 (Airflow Around Buildings)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from src.core.configs import WindConfig


@dataclass(frozen=True)
class WindVector:
    """Immutable 2-D wind condition: velocity vector + ambient temperature.

    Positive x = west → east, positive y = south → north.
    """

    velocity_m_per_s: tuple[float, float]
    ambient_temp_k: float

    def __post_init__(self) -> None:
        if self.ambient_temp_k <= 0:
            raise ValueError(
                f"Temperature must be > 0 K, got {self.ambient_temp_k} K"
            )
        if np.linalg.norm(self.velocity_m_per_s) < 1e-10:
            raise ValueError(
                "Wind velocity cannot be zero (direction undefined)"
            )

    @property
    def direction(self) -> NDArray[np.float64]:
        """Unit vector in the wind travel direction."""
        vel = np.array(self.velocity_m_per_s, dtype=np.float64)
        return vel / np.linalg.norm(vel)

    @property
    def speed_m_per_s(self) -> float:
        """Scalar wind speed in m/s."""
        return float(np.linalg.norm(self.velocity_m_per_s))

    @property
    def velocity_array(self) -> NDArray[np.float64]:
        """Velocity as a NumPy array of shape (2,)."""
        return np.array(self.velocity_m_per_s, dtype=np.float64)

    @classmethod
    def from_config(cls, config: WindConfig) -> WindVector:
        """Create from a validated Pydantic WindConfig."""
        return cls(
            velocity_m_per_s=(config.velocity_x_m_per_s, config.velocity_y_m_per_s),
            ambient_temp_k=config.ambient_temp_k,
        )

    @classmethod
    def from_speed_and_angle(
        cls,
        speed_m_per_s: float,
        angle_deg: float,
        ambient_temp_k: float,
    ) -> WindVector:
        """Create from scalar speed and angle (degrees CCW from east)."""
        angle_rad = np.deg2rad(angle_deg)
        vx = speed_m_per_s * np.cos(angle_rad)
        vy = speed_m_per_s * np.sin(angle_rad)
        return cls(
            velocity_m_per_s=(float(vx), float(vy)),
            ambient_temp_k=ambient_temp_k,
        )


def sinusoidal_direction_profile(
    speed_m_per_s: float,
    angle_center_deg: float,
    angle_amplitude_deg: float,
    period_hours: float,
    ambient_temp_k: float,
    phase_hours: float = 0.0,
) -> Callable[[float], WindVector]:
    """Return a callable ``wind_at_time(hours) -> WindVector``.

    Speed is constant; direction oscillates sinusoidally around
    *angle_center_deg* with amplitude *angle_amplitude_deg*.
    """

    def wind_at_time(time_hours: float) -> WindVector:
        angle_rad = np.deg2rad(
            angle_center_deg
            + angle_amplitude_deg
            * np.sin(2 * np.pi * (time_hours - phase_hours) / period_hours)
        )
        vx = speed_m_per_s * np.cos(angle_rad)
        vy = speed_m_per_s * np.sin(angle_rad)
        return WindVector(
            velocity_m_per_s=(float(vx), float(vy)),
            ambient_temp_k=ambient_temp_k,
        )

    return wind_at_time
