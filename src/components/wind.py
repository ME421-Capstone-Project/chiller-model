"""Wind vector model for atmospheric conditions.

This module defines the immutable WindVector class representing
atmospheric wind conditions that affect thermal plume dispersion
between chillers.

Reference
---------
ASHRAE Handbook - Fundamentals, Chapter 24 (Airflow Around Buildings)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from src.core.configs import WindConfig


@dataclass(frozen=True)
class WindVector:
    """Represents atmospheric wind conditions (immutable).

    The wind vector determines which chillers are "upwind"
    (sources of thermal contamination) vs "downwind" (receivers).
    Immutability ensures thermodynamic states are not accidentally modified.

    Attributes
    ----------
    velocity_m_per_s : tuple[float, float]
        2D velocity vector [vx, vy] in m/s. Uses tuple for immutability.
    ambient_temp_k : float
        Ambient dry-bulb temperature in Kelvin.

    Notes
    -----
    Wind direction convention:
    - Positive x: wind blowing from west to east
    - Positive y: wind blowing from south to north
    - The direction property gives unit vector in wind travel direction

    Reference
    ---------
    ASHRAE Handbook - Fundamentals, Chapter 24 (Airflow Around Buildings)

    Examples
    --------
    >>> wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    >>> wind.speed_m_per_s
    5.0
    >>> wind.direction
    array([1., 0.])
    """

    velocity_m_per_s: tuple[float, float]
    ambient_temp_k: float

    def __post_init__(self) -> None:
        """Validate wind parameters after initialization."""
        if self.ambient_temp_k <= 0:
            raise ValueError(
                f"Temperature must be > 0 K, got {self.ambient_temp_k} K"
            )
        speed = np.linalg.norm(self.velocity_m_per_s)
        if speed < 1e-10:
            raise ValueError(
                "Wind velocity cannot be zero (direction undefined)"
            )

    @property
    def direction(self) -> NDArray[np.float64]:
        """Unit vector in wind direction.

        Returns
        -------
        NDArray[np.float64]
            Normalized 2D direction vector, shape (2,).

        Notes
        -----
        The direction vector points in the direction the wind is blowing
        (not where it comes from). A chiller "downwind" of another has
        positive longitudinal distance in this direction.
        """
        vel = np.array(self.velocity_m_per_s, dtype=np.float64)
        return vel / np.linalg.norm(vel)

    @property
    def speed_m_per_s(self) -> float:
        """Wind speed magnitude in m/s.

        Returns
        -------
        float
            Scalar wind speed.
        """
        return float(np.linalg.norm(self.velocity_m_per_s))

    @property
    def velocity_array(self) -> NDArray[np.float64]:
        """Velocity as NumPy array.

        Returns
        -------
        NDArray[np.float64]
            Velocity vector as array, shape (2,).
        """
        return np.array(self.velocity_m_per_s, dtype=np.float64)

    @classmethod
    def from_config(cls, config: WindConfig) -> WindVector:
        """Factory method from validated Pydantic config.

        Parameters
        ----------
        config : WindConfig
            Validated wind configuration from Pydantic model.

        Returns
        -------
        WindVector
            Immutable wind vector instance.

        Examples
        --------
        >>> from src.core.configs import WindConfig
        >>> config = WindConfig(
        ...     velocity_x_m_per_s=5.0,
        ...     velocity_y_m_per_s=0.0,
        ...     ambient_temp_k=298.15
        ... )
        >>> wind = WindVector.from_config(config)
        """
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
        """Create wind vector from speed and angle.

        Parameters
        ----------
        speed_m_per_s : float
            Wind speed magnitude in m/s.
        angle_deg : float
            Wind direction in degrees, measured counterclockwise
            from positive x-axis (east).
        ambient_temp_k : float
            Ambient temperature in Kelvin.

        Returns
        -------
        WindVector
            Immutable wind vector instance.

        Examples
        --------
        >>> wind = WindVector.from_speed_and_angle(5.0, 45.0, 298.15)
        >>> np.isclose(wind.speed_m_per_s, 5.0)
        True
        """
        angle_rad = np.deg2rad(angle_deg)
        vx = speed_m_per_s * np.cos(angle_rad)
        vy = speed_m_per_s * np.sin(angle_rad)
        return cls(
            velocity_m_per_s=(float(vx), float(vy)),
            ambient_temp_k=ambient_temp_k,
        )
