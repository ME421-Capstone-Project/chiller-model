"""Tests for WindVector component."""

import numpy as np
import pytest

from src.components.wind import WindVector, sinusoidal_direction_profile
from src.core.configs import WindConfig


class TestWindVector:

    def test_create_wind_vector(self) -> None:
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        assert wind.velocity_m_per_s == (5.0, 0.0)
        assert wind.ambient_temp_k == 298.15

    def test_is_immutable(self) -> None:
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        with pytest.raises(Exception):
            wind.ambient_temp_k = 300.0  # type: ignore

    def test_speed_calculation(self) -> None:
        wind = WindVector(velocity_m_per_s=(3.0, 4.0), ambient_temp_k=298.15)
        assert wind.speed_m_per_s == pytest.approx(5.0)

    def test_direction_is_unit_vector(self) -> None:
        wind = WindVector(velocity_m_per_s=(3.0, 4.0), ambient_temp_k=298.15)
        assert np.linalg.norm(wind.direction) == pytest.approx(1.0)

    def test_direction_points_correct_way(self) -> None:
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        np.testing.assert_allclose(wind.direction, [1.0, 0.0], atol=1e-10)

        wind = WindVector(velocity_m_per_s=(0.0, 5.0), ambient_temp_k=298.15)
        np.testing.assert_allclose(wind.direction, [0.0, 1.0], atol=1e-10)

    def test_temperature_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="Temperature must be > 0 K"):
            WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=0.0)
        with pytest.raises(ValueError, match="Temperature must be > 0 K"):
            WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=-10.0)

    def test_zero_velocity_rejected(self) -> None:
        with pytest.raises(ValueError, match="cannot be zero"):
            WindVector(velocity_m_per_s=(0.0, 0.0), ambient_temp_k=298.15)

    def test_from_config_factory(self) -> None:
        config = WindConfig(
            velocity_x_m_per_s=5.0, velocity_y_m_per_s=3.0, ambient_temp_k=300.0
        )
        wind = WindVector.from_config(config)
        assert wind.velocity_m_per_s == (5.0, 3.0)
        assert wind.ambient_temp_k == 300.0

    def test_from_speed_and_angle(self) -> None:
        wind = WindVector.from_speed_and_angle(
            speed_m_per_s=5.0, angle_deg=45.0, ambient_temp_k=298.15
        )
        expected_vx = 5.0 * np.cos(np.deg2rad(45))
        expected_vy = 5.0 * np.sin(np.deg2rad(45))
        assert wind.velocity_m_per_s[0] == pytest.approx(expected_vx)
        assert wind.velocity_m_per_s[1] == pytest.approx(expected_vy)
        assert wind.speed_m_per_s == pytest.approx(5.0)

    def test_velocity_array_property(self) -> None:
        wind = WindVector(velocity_m_per_s=(5.0, 3.0), ambient_temp_k=298.15)
        arr = wind.velocity_array
        assert isinstance(arr, np.ndarray)
        np.testing.assert_allclose(arr, [5.0, 3.0])


class TestSinusoidalDirectionProfile:

    def test_returns_callable(self) -> None:
        profile = sinusoidal_direction_profile(
            speed_m_per_s=5.0, angle_center_deg=90.0,
            angle_amplitude_deg=30.0, period_hours=24.0, ambient_temp_k=298.15,
        )
        assert callable(profile)

    def test_returns_wind_vector(self) -> None:
        profile = sinusoidal_direction_profile(
            speed_m_per_s=5.0, angle_center_deg=0.0,
            angle_amplitude_deg=0.0, period_hours=24.0, ambient_temp_k=298.15,
        )
        wind = profile(0.0)
        assert isinstance(wind, WindVector)
        assert wind.speed_m_per_s == pytest.approx(5.0)

    def test_direction_varies_with_time(self) -> None:
        profile = sinusoidal_direction_profile(
            speed_m_per_s=5.0, angle_center_deg=90.0,
            angle_amplitude_deg=45.0, period_hours=24.0, ambient_temp_k=298.15,
        )
        wind_0 = profile(0.0)
        wind_6 = profile(6.0)
        assert wind_0.velocity_m_per_s[0] == pytest.approx(0.0, abs=1e-10)
        assert wind_0.velocity_m_per_s[1] == pytest.approx(5.0)
        v0 = np.array(wind_0.velocity_m_per_s)
        v6 = np.array(wind_6.velocity_m_per_s)
        assert not np.allclose(v0, v6)

    def test_speed_constant(self) -> None:
        profile = sinusoidal_direction_profile(
            speed_m_per_s=5.0, angle_center_deg=0.0,
            angle_amplitude_deg=90.0, period_hours=24.0, ambient_temp_k=298.15,
        )
        for t in [0.0, 6.0, 12.0, 18.0]:
            assert profile(t).speed_m_per_s == pytest.approx(5.0)
