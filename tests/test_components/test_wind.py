"""Tests for WindVector component.

Validates immutability, property calculations, and physical constraints.
"""

import numpy as np
import pytest

from src.components.wind import WindVector
from src.core.configs import WindConfig


class TestWindVector:
    """Tests for WindVector class."""

    def test_create_wind_vector(self) -> None:
        """Basic wind vector creation should work."""
        wind = WindVector(
            velocity_m_per_s=(5.0, 0.0),
            ambient_temp_k=298.15,
        )
        assert wind.velocity_m_per_s == (5.0, 0.0)
        assert wind.ambient_temp_k == 298.15

    def test_is_immutable(self) -> None:
        """WindVector should be immutable (frozen dataclass)."""
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

        with pytest.raises(Exception):  # FrozenInstanceError
            wind.ambient_temp_k = 300.0  # type: ignore

    def test_speed_calculation(self) -> None:
        """Speed should be computed correctly from velocity components."""
        wind = WindVector(velocity_m_per_s=(3.0, 4.0), ambient_temp_k=298.15)
        assert wind.speed_m_per_s == pytest.approx(5.0)

    def test_direction_is_unit_vector(self) -> None:
        """Direction should be a unit vector."""
        wind = WindVector(velocity_m_per_s=(3.0, 4.0), ambient_temp_k=298.15)
        direction = wind.direction
        magnitude = np.linalg.norm(direction)
        assert magnitude == pytest.approx(1.0)

    def test_direction_points_correct_way(self) -> None:
        """Direction should point in wind travel direction."""
        # Wind blowing east (positive x)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        np.testing.assert_allclose(wind.direction, [1.0, 0.0], atol=1e-10)

        # Wind blowing north (positive y)
        wind = WindVector(velocity_m_per_s=(0.0, 5.0), ambient_temp_k=298.15)
        np.testing.assert_allclose(wind.direction, [0.0, 1.0], atol=1e-10)

    def test_temperature_must_be_positive(self) -> None:
        """Temperature <= 0 K should raise ValueError."""
        with pytest.raises(ValueError, match="Temperature must be > 0 K"):
            WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=0.0)

        with pytest.raises(ValueError, match="Temperature must be > 0 K"):
            WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=-10.0)

    def test_zero_velocity_rejected(self) -> None:
        """Zero velocity should raise ValueError (direction undefined)."""
        with pytest.raises(ValueError, match="cannot be zero"):
            WindVector(velocity_m_per_s=(0.0, 0.0), ambient_temp_k=298.15)

    def test_from_config_factory(self) -> None:
        """Factory method from_config should work correctly."""
        config = WindConfig(
            velocity_x_m_per_s=5.0,
            velocity_y_m_per_s=3.0,
            ambient_temp_k=300.0,
        )
        wind = WindVector.from_config(config)

        assert wind.velocity_m_per_s == (5.0, 3.0)
        assert wind.ambient_temp_k == 300.0

    def test_from_speed_and_angle(self) -> None:
        """Factory method from_speed_and_angle should work correctly."""
        # 45 degrees, 5 m/s
        wind = WindVector.from_speed_and_angle(
            speed_m_per_s=5.0,
            angle_deg=45.0,
            ambient_temp_k=298.15,
        )

        expected_vx = 5.0 * np.cos(np.deg2rad(45))
        expected_vy = 5.0 * np.sin(np.deg2rad(45))

        assert wind.velocity_m_per_s[0] == pytest.approx(expected_vx)
        assert wind.velocity_m_per_s[1] == pytest.approx(expected_vy)
        assert wind.speed_m_per_s == pytest.approx(5.0)

    def test_velocity_array_property(self) -> None:
        """velocity_array should return NumPy array."""
        wind = WindVector(velocity_m_per_s=(5.0, 3.0), ambient_temp_k=298.15)
        arr = wind.velocity_array

        assert isinstance(arr, np.ndarray)
        np.testing.assert_allclose(arr, [5.0, 3.0])
