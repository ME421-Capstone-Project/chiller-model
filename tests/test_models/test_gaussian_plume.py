"""Tests for GaussianPlumeModel interaction model.

Validates physical sanity of the Gaussian plume dispersion model
including non-negativity, self-interaction, and downwind behavior.
"""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel


class TestGaussianPlumePhysics:
    """Physical sanity checks for Gaussian plume model."""

    @pytest.fixture
    def model(self) -> GaussianPlumeModel:
        """Create model with default parameters."""
        return GaussianPlumeModel(dispersion_coeff=1.2)

    @pytest.fixture
    def grid_positions(self) -> np.ndarray:
        """4x4 grid of positions."""
        x = np.arange(4) * 10.0
        y = np.arange(4) * 10.0
        xx, yy = np.meshgrid(x, y)
        return np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)

    @pytest.fixture
    def eastward_wind(self) -> WindVector:
        """Wind blowing east (positive x)."""
        return WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

    def test_interaction_matrix_non_negative(
        self,
        model: GaussianPlumeModel,
        grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        """Interaction coefficients must be >= 0."""
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        assert np.all(A >= 0), "Interaction matrix has negative values"

    def test_no_self_interaction(
        self,
        model: GaussianPlumeModel,
        grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        """Diagonal of interaction matrix must be zero."""
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        np.testing.assert_allclose(
            np.diag(A),
            0.0,
            atol=1e-10,
            err_msg="Self-interaction should be zero",
        )

    def test_upwind_units_no_effect(
        self,
        model: GaussianPlumeModel,
        eastward_wind: WindVector,
    ) -> None:
        """Upwind units should have zero effect on downwind units.
        
        If wind blows from A to B, then A affects B but B does NOT affect A.
        """
        # Two chillers: one upwind, one downwind
        positions = np.array([[0, 0], [20, 0]], dtype=np.float64)
        A = model.compute_interaction_matrix(positions, eastward_wind)

        # Chiller 0 is upwind of chiller 1
        # A[0, 1] should be > 0 (chiller 0 affects chiller 1)
        assert A[0, 1] > 0, "Upwind chiller should affect downwind"

        # A[1, 0] should be 0 (chiller 1 does not affect chiller 0)
        assert A[1, 0] == pytest.approx(
            0.0
        ), "Downwind chiller should not affect upwind"

    def test_interference_decreases_with_distance(
        self,
        model: GaussianPlumeModel,
        eastward_wind: WindVector,
    ) -> None:
        """Interference should decrease with longitudinal distance."""
        # Source chiller at origin, targets at increasing distances
        positions = np.array(
            [[0, 0], [10, 0], [20, 0], [30, 0]],
            dtype=np.float64,
        )
        A = model.compute_interaction_matrix(positions, eastward_wind)

        # Effect from chiller 0 on others should decrease with distance
        effect_at_10m = A[0, 1]
        effect_at_20m = A[0, 2]
        effect_at_30m = A[0, 3]

        assert effect_at_10m > effect_at_20m > effect_at_30m > 0

    def test_interference_decreases_with_lateral_offset(
        self,
        model: GaussianPlumeModel,
        eastward_wind: WindVector,
    ) -> None:
        """Interference should decrease with lateral distance."""
        # Source at origin, targets at same downwind distance but different lateral offsets
        positions = np.array(
            [[0, 0], [20, 0], [20, 5], [20, 10]],
            dtype=np.float64,
        )
        A = model.compute_interaction_matrix(positions, eastward_wind)

        # Effect on directly downwind chiller should be highest
        effect_on_axis = A[0, 1]
        effect_offset_5m = A[0, 2]
        effect_offset_10m = A[0, 3]

        assert effect_on_axis > effect_offset_5m > effect_offset_10m

    def test_symmetric_lateral_positions(
        self,
        model: GaussianPlumeModel,
        eastward_wind: WindVector,
    ) -> None:
        """Symmetric lateral positions should have equal interference."""
        positions = np.array(
            [[0, 0], [20, 5], [20, -5]],
            dtype=np.float64,
        )
        A = model.compute_interaction_matrix(positions, eastward_wind)

        # Symmetric positions should have equal effect from source
        assert A[0, 1] == pytest.approx(A[0, 2])

    def test_no_nan_or_inf_values(
        self,
        model: GaussianPlumeModel,
        grid_positions: np.ndarray,
        eastward_wind: WindVector,
    ) -> None:
        """Interaction matrix should not contain NaN or Inf."""
        A = model.compute_interaction_matrix(grid_positions, eastward_wind)
        assert not np.any(np.isnan(A)), "Matrix contains NaN"
        assert not np.any(np.isinf(A)), "Matrix contains Inf"

    def test_handles_coincident_positions(self, model: GaussianPlumeModel) -> None:
        """Model should handle (not crash on) coincident positions."""
        # Two chillers at same position - edge case
        positions = np.array([[0, 0], [0, 0]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

        A = model.compute_interaction_matrix(positions, wind)

        # Should not crash, diagonal should still be zero
        assert not np.any(np.isnan(A))
        np.testing.assert_allclose(np.diag(A), 0.0)


class TestGaussianPlumeParameters:
    """Tests for GaussianPlumeModel parameters and configuration."""

    def test_dispersion_must_be_positive(self) -> None:
        """Dispersion coefficient must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            GaussianPlumeModel(dispersion_coeff=0.0)

        with pytest.raises(ValueError, match="must be positive"):
            GaussianPlumeModel(dispersion_coeff=-1.0)

    def test_higher_dispersion_increases_spread(self) -> None:
        """Higher dispersion coefficient spreads plume wider.

        Physics: Higher sigma allows more of the plume to reach
        off-axis positions. The effect on interference depends on
        whether the target is on-axis or off-axis:
        - On-axis (lat=0): no effect from sigma (lat^2 = 0)
        - Off-axis: higher sigma = more plume reaches target

        This is consistent with Gaussian dispersion physics.
        """
        positions = np.array([[0, 0], [20, 5]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

        low_dispersion = GaussianPlumeModel(dispersion_coeff=0.5)
        high_dispersion = GaussianPlumeModel(dispersion_coeff=2.0)

        A_low = low_dispersion.compute_interaction_matrix(positions, wind)
        A_high = high_dispersion.compute_interaction_matrix(positions, wind)

        # Higher dispersion = wider spread = more reaches off-axis target
        assert A_high[0, 1] > A_low[0, 1]


class TestGaussianPlumeUtilities:
    """Tests for utility methods."""

    def test_longitudinal_distances(self) -> None:
        """Test longitudinal distance calculation."""
        model = GaussianPlumeModel()
        positions = np.array([[0, 0], [20, 0], [20, 10]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

        long_dist = model.compute_longitudinal_distances(positions, wind)

        # From chiller 0 to 1: 20m downwind
        assert long_dist[0, 1] == pytest.approx(20.0)
        # From chiller 1 to 0: 20m upwind (negative)
        assert long_dist[1, 0] == pytest.approx(-20.0)
        # Self-distance is 0
        assert long_dist[0, 0] == pytest.approx(0.0)

    def test_lateral_distances(self) -> None:
        """Test lateral distance calculation."""
        model = GaussianPlumeModel()
        positions = np.array([[0, 0], [20, 0], [20, 10]], dtype=np.float64)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

        lat_dist = model.compute_lateral_distances(positions, wind)

        # From chiller 0 to 1: directly downwind, lateral = 0
        assert lat_dist[0, 1] == pytest.approx(0.0)
        # From chiller 0 to 2: 10m lateral offset
        assert lat_dist[0, 2] == pytest.approx(10.0)
        # Self-distance is 0
        assert lat_dist[0, 0] == pytest.approx(0.0)
