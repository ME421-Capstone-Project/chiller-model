"""Tests for ChillerArray component.

Validates array creation, grid generation, and physical constraints.
"""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray


class TestChillerArray:
    """Tests for ChillerArray class."""

    def test_create_from_positions(self) -> None:
        """Create array from explicit positions."""
        positions = np.array([[0, 0], [10, 0], [20, 0]], dtype=np.float64)
        array = ChillerArray(positions_m=positions, base_cop=5.0, alpha=0.7)

        assert array.num_chillers == 3
        assert array.base_cop == 5.0
        assert array.alpha == 0.7

    def test_positions_must_be_2d(self) -> None:
        """Positions must have shape (N, 2)."""
        with pytest.raises(ValueError, match="shape"):
            ChillerArray(positions_m=np.array([1, 2, 3]))

    def test_at_least_one_chiller(self) -> None:
        """Array must have at least one chiller."""
        with pytest.raises(ValueError, match="at least one"):
            ChillerArray(positions_m=np.empty((0, 2)))

    def test_cop_bounds(self) -> None:
        """COP must be in valid range (0, 10]."""
        positions = np.array([[0, 0]], dtype=np.float64)

        with pytest.raises(ValueError):
            ChillerArray(positions_m=positions, base_cop=0.0)

        with pytest.raises(ValueError):
            ChillerArray(positions_m=positions, base_cop=11.0)

    def test_alpha_must_be_positive(self) -> None:
        """Alpha must be positive."""
        positions = np.array([[0, 0]], dtype=np.float64)

        with pytest.raises(ValueError, match="alpha must be > 0"):
            ChillerArray(positions_m=positions, alpha=0.0)

    def test_x_y_position_properties(self) -> None:
        """x_positions_m and y_positions_m should work correctly."""
        positions = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float64)
        array = ChillerArray(positions_m=positions)

        np.testing.assert_allclose(array.x_positions_m, [1, 3, 5])
        np.testing.assert_allclose(array.y_positions_m, [2, 4, 6])

    def test_centroid_calculation(self) -> None:
        """Centroid should be geometric center."""
        positions = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float64)
        array = ChillerArray(positions_m=positions)

        np.testing.assert_allclose(array.centroid_m, [5.0, 5.0])

    def test_bounding_box(self) -> None:
        """Bounding box should contain all positions."""
        positions = np.array([[1, 2], [5, 8], [3, 4]], dtype=np.float64)
        array = ChillerArray(positions_m=positions)

        x_min, y_min, x_max, y_max = array.get_bounding_box()
        assert x_min == pytest.approx(1.0)
        assert y_min == pytest.approx(2.0)
        assert x_max == pytest.approx(5.0)
        assert y_max == pytest.approx(8.0)


class TestChillerArrayGrid:
    """Tests for ChillerArray.create_grid factory."""

    def test_create_grid_basic(self) -> None:
        """Create a basic grid of chillers."""
        array = ChillerArray.create_grid(rows=3, cols=4, spacing_m=10.0)

        assert array.num_chillers == 12

    def test_grid_dimensions(self) -> None:
        """Grid should have correct spatial extent."""
        array = ChillerArray.create_grid(rows=4, cols=5, spacing_m=10.0)

        x_min, y_min, x_max, y_max = array.get_bounding_box()
        assert x_max - x_min == pytest.approx(40.0)  # 4 gaps of 10m
        assert y_max - y_min == pytest.approx(30.0)  # 3 gaps of 10m

    def test_grid_with_origin(self) -> None:
        """Grid with custom origin should be offset correctly."""
        array = ChillerArray.create_grid(
            rows=2,
            cols=2,
            spacing_m=10.0,
            origin_m=(100.0, 200.0),
        )

        x_min, y_min, _, _ = array.get_bounding_box()
        assert x_min == pytest.approx(100.0)
        assert y_min == pytest.approx(200.0)

    def test_grid_with_custom_cop(self) -> None:
        """Grid should use specified COP and alpha."""
        array = ChillerArray.create_grid(
            rows=2,
            cols=2,
            spacing_m=10.0,
            base_cop=6.0,
            alpha=0.5,
        )

        assert array.base_cop == 6.0
        assert array.alpha == 0.5

    def test_grid_rows_cols_must_be_positive(self) -> None:
        """Rows and cols must be positive."""
        with pytest.raises(ValueError):
            ChillerArray.create_grid(rows=0, cols=2, spacing_m=10.0)

        with pytest.raises(ValueError):
            ChillerArray.create_grid(rows=2, cols=0, spacing_m=10.0)

    def test_grid_spacing_must_be_positive(self) -> None:
        """Spacing must be positive."""
        with pytest.raises(ValueError):
            ChillerArray.create_grid(rows=2, cols=2, spacing_m=0.0)


class TestChillerArrayRandom:
    """Tests for ChillerArray.create_random factory."""

    def test_create_random_basic(self) -> None:
        """Create random array with specified count."""
        array = ChillerArray.create_random(
            num_chillers=10,
            area_size_m=(100.0, 100.0),
            seed=42,
        )

        assert array.num_chillers == 10

    def test_random_positions_in_bounds(self) -> None:
        """Random positions should be within specified area."""
        array = ChillerArray.create_random(
            num_chillers=50,
            area_size_m=(100.0, 200.0),
            seed=42,
        )

        x_min, y_min, x_max, y_max = array.get_bounding_box()
        assert x_min >= 0
        assert y_min >= 0
        assert x_max <= 100.0
        assert y_max <= 200.0

    def test_random_reproducible_with_seed(self) -> None:
        """Same seed should produce same positions."""
        array1 = ChillerArray.create_random(
            num_chillers=10,
            area_size_m=(100.0, 100.0),
            seed=42,
        )
        array2 = ChillerArray.create_random(
            num_chillers=10,
            area_size_m=(100.0, 100.0),
            seed=42,
        )

        np.testing.assert_allclose(array1.positions_m, array2.positions_m)

    def test_random_num_chillers_must_be_positive(self) -> None:
        """Number of chillers must be positive."""
        with pytest.raises(ValueError):
            ChillerArray.create_random(
                num_chillers=0,
                area_size_m=(100.0, 100.0),
            )


class TestChillerArrayAge:
    """Tests for chiller age parameter and COP degradation."""

    def test_manual_ages_assignment(self) -> None:
        """Manually assigned ages should be preserved."""
        positions = np.array([[0, 0], [10, 0]], dtype=np.float64)
        ages = np.array([0.0, 5.0], dtype=np.float64)
        array = ChillerArray(
            positions_m=positions,
            base_cop=5.0,
            alpha=0.7,
            ages_years=ages,
        )
        np.testing.assert_allclose(array.ages_years, [0.0, 5.0])

    def test_ages_shape_must_match_positions(self) -> None:
        """ages_years must have same length as positions."""
        positions = np.array([[0, 0], [10, 0], [20, 0]], dtype=np.float64)
        ages_wrong = np.array([0.0, 1.0], dtype=np.float64)  # length 2, need 3

        with pytest.raises(ValueError, match="shape"):
            ChillerArray(
                positions_m=positions,
                base_cop=5.0,
                ages_years=ages_wrong,
            )

    def test_ages_must_be_non_negative(self) -> None:
        """ages_years must be non-negative."""
        positions = np.array([[0, 0]], dtype=np.float64)
        ages_negative = np.array([-1.0], dtype=np.float64)

        with pytest.raises(ValueError, match="non-negative"):
            ChillerArray(
                positions_m=positions,
                base_cop=5.0,
                ages_years=ages_negative,
            )

    def test_random_ages_when_not_provided(self) -> None:
        """When ages not provided, they are random uniform [0, 20]."""
        positions = np.array([[0, 0], [10, 0]], dtype=np.float64)
        array = ChillerArray(positions_m=positions, base_cop=5.0)

        assert array.ages_years.shape == (2,)
        assert np.all(array.ages_years >= 0)
        assert np.all(array.ages_years <= 20.0)

    def test_create_grid_with_manual_ages(self) -> None:
        """create_grid accepts manual ages."""
        array = ChillerArray.create_grid(
            rows=2,
            cols=2,
            spacing_m=10.0,
            ages_years=np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float64),
        )
        np.testing.assert_allclose(array.ages_years, [0.0, 1.0, 2.0, 3.0])

    def test_create_grid_random_ages_reproducible_with_seed(self) -> None:
        """create_grid with seed produces reproducible random ages."""
        array1 = ChillerArray.create_grid(
            rows=2, cols=2, spacing_m=10.0, seed=42
        )
        array2 = ChillerArray.create_grid(
            rows=2, cols=2, spacing_m=10.0, seed=42
        )
        np.testing.assert_allclose(array1.ages_years, array2.ages_years)

    def test_create_random_ages_reproducible_with_seed(self) -> None:
        """create_random produces reproducible ages with same seed."""
        array1 = ChillerArray.create_random(
            num_chillers=5,
            area_size_m=(100.0, 100.0),
            seed=123,
        )
        array2 = ChillerArray.create_random(
            num_chillers=5,
            area_size_m=(100.0, 100.0),
            seed=123,
        )
        np.testing.assert_allclose(array1.ages_years, array2.ages_years)

    def test_cop_age_factors_property(self) -> None:
        """cop_age_factors returns correct multipliers."""
        positions = np.array([[0, 0]], dtype=np.float64)
        # Age 0: factor 1.0; Age 1: factor 0.8 (from constants)
        array = ChillerArray(
            positions_m=positions,
            base_cop=5.0,
            ages_years=np.array([0.0], dtype=np.float64),
        )
        factors = array.cop_age_factors
        assert factors[0] == pytest.approx(1.0)

        array_1yr = ChillerArray(
            positions_m=positions,
            base_cop=5.0,
            ages_years=np.array([1.0], dtype=np.float64),
        )
        factors_1yr = array_1yr.cop_age_factors
        assert factors_1yr[0] == pytest.approx(0.8)
