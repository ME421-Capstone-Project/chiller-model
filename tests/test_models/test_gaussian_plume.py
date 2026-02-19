"""Tests for GaussianPlumeModel interaction model."""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel


class TestGaussianPlumePhysics:
    """Physical sanity checks for the Gaussian plume model."""

    @pytest.fixture
    def model(self) -> GaussianPlumeModel:
        return GaussianPlumeModel(dispersion_coeff=1.2)

    @pytest.fixture
    def grid_positions(self) -> np.ndarray:
        x = np.arange(4) * 10.0
        y = np.arange(4) * 10.0
        xx, yy = np.meshgrid(x, y)
        return np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)

    @pytest.fixture
    def eastward_wind(self) -> WindVector:
        return WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

    def test_interaction_matrix_non_negative(
        self, model: GaussianPlumeModel, grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        assert np.all(A >= 0)

    def test_no_self_interaction(
        self, model: GaussianPlumeModel, grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        np.testing.assert_allclose(np.diag(A), 0.0, atol=1e-10)

    def test_upwind_units_no_effect(
        self, model: GaussianPlumeModel, eastward_wind: WindVector,
    ) -> None:
        """Upwind chiller should not be affected by downwind chiller."""
        positions = np.array([[0, 0], [20, 0]], dtype=np.float64)
        A = model.compute_interaction_matrix(positions, eastward_wind)
        assert A[0, 1] > 0
        assert A[1, 0] == pytest.approx(0.0)

    def test_interference_decreases_with_distance(
        self, model: GaussianPlumeModel, eastward_wind: WindVector,
    ) -> None:
        positions = np.array(
            [[0, 0], [10, 0], [20, 0], [30, 0]], dtype=np.float64
        )
        A = model.compute_interaction_matrix(positions, eastward_wind)
        assert A[0, 1] > A[0, 2] > A[0, 3] > 0

    def test_interference_decreases_with_lateral_offset(
        self, model: GaussianPlumeModel, eastward_wind: WindVector,
    ) -> None:
        positions = np.array(
            [[0, 0], [20, 0], [20, 5], [20, 10]], dtype=np.float64
        )
        A = model.compute_interaction_matrix(positions, eastward_wind)
        assert A[0, 1] > A[0, 2] > A[0, 3]

    def test_symmetric_lateral_positions(
        self, model: GaussianPlumeModel, eastward_wind: WindVector,
    ) -> None:
        positions = np.array([[0, 0], [20, 5], [20, -5]], dtype=np.float64)
        A = model.compute_interaction_matrix(positions, eastward_wind)
        assert A[0, 1] == pytest.approx(A[0, 2])

    def test_no_nan_or_inf_values(
        self, model: GaussianPlumeModel, grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        assert not np.any(np.isnan(A))
        assert not np.any(np.isinf(A))

    def test_handles_coincident_positions(self, model: GaussianPlumeModel) -> None:
        positions = np.array([[0, 0], [0, 0]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        A = model.compute_interaction_matrix(positions, wind)
        assert not np.any(np.isnan(A))
        np.testing.assert_allclose(np.diag(A), 0.0)


class TestGaussianPlumeParameters:

    def test_dispersion_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            GaussianPlumeModel(dispersion_coeff=0.0)
        with pytest.raises(ValueError, match="must be positive"):
            GaussianPlumeModel(dispersion_coeff=-1.0)

    def test_higher_dispersion_increases_spread(self) -> None:
        """Higher σ allows more plume to reach off-axis targets."""
        positions = np.array([[0, 0], [20, 5]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        A_low = GaussianPlumeModel(dispersion_coeff=0.5).compute_interaction_matrix(
            positions, wind
        )
        A_high = GaussianPlumeModel(dispersion_coeff=2.0).compute_interaction_matrix(
            positions, wind
        )
        assert A_high[0, 1] > A_low[0, 1]


class TestGaussianPlumeUtilities:

    def test_longitudinal_distances(self) -> None:
        model = GaussianPlumeModel()
        positions = np.array([[0, 0], [20, 0], [20, 10]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        long_dist = model.compute_longitudinal_distances(positions, wind)
        assert long_dist[0, 1] == pytest.approx(20.0)
        assert long_dist[1, 0] == pytest.approx(-20.0)
        assert long_dist[0, 0] == pytest.approx(0.0)

    def test_lateral_distances(self) -> None:
        model = GaussianPlumeModel()
        positions = np.array([[0, 0], [20, 0], [20, 10]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        lat_dist = model.compute_lateral_distances(positions, wind)
        assert lat_dist[0, 1] == pytest.approx(0.0)
        assert lat_dist[0, 2] == pytest.approx(10.0)
        assert lat_dist[0, 0] == pytest.approx(0.0)
