"""Tests for Optimizer class.

Validates greedy optimization strategy and result properties.
"""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel
from src.simulation.environment import SimulationEnvironment
from src.simulation.optimizer import OptimizationResult, Optimizer


class TestOptimizer:
    """Tests for Optimizer class."""

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        """Create environment for optimization tests."""
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=10.0, base_cop=5.0, alpha=0.7
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        """Create optimizer for tests."""
        return Optimizer(env, total_load_kw=500.0)

    def test_create_optimizer(self, env: SimulationEnvironment) -> None:
        """Basic optimizer creation should work."""
        optimizer = Optimizer(env, total_load_kw=500.0)
        assert optimizer.total_load_kw == 500.0

    def test_load_must_be_positive(self, env: SimulationEnvironment) -> None:
        """Total load must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            Optimizer(env, total_load_kw=0.0)


class TestGreedyOptimization:
    """Tests for greedy optimization algorithm."""

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        """Create environment with significant thermal interference."""
        # Dense grid with high alpha = lots of interference
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=5.0, base_cop=5.0, alpha=1.0
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=0.8)
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        """Create optimizer for tests."""
        return Optimizer(env, total_load_kw=500.0)

    def test_greedy_returns_valid_result(self, optimizer: Optimizer) -> None:
        """Greedy optimization should return valid result."""
        result = optimizer.optimize_greedy()

        assert isinstance(result, OptimizationResult)
        assert result.optimal_work_kw > 0
        assert result.baseline_work_kw > 0
        assert 0 <= result.savings_fraction <= 1
        assert result.num_active >= 1

    def test_result_is_immutable(self, optimizer: Optimizer) -> None:
        """OptimizationResult should be immutable."""
        result = optimizer.optimize_greedy()

        with pytest.raises(AttributeError):
            result.optimal_work_kw = 0.0  # type: ignore

    def test_optimal_not_worse_than_baseline(self, optimizer: Optimizer) -> None:
        """Optimal solution should not be worse than baseline."""
        result = optimizer.optimize_greedy()

        assert result.optimal_work_kw <= result.baseline_work_kw

    def test_savings_calculation_correct(self, optimizer: Optimizer) -> None:
        """Savings fraction should be calculated correctly."""
        result = optimizer.optimize_greedy()

        expected_savings = (
            result.baseline_work_kw - result.optimal_work_kw
        ) / result.baseline_work_kw
        assert result.savings_fraction == pytest.approx(expected_savings)

    def test_respects_min_active(self, optimizer: Optimizer) -> None:
        """Optimization should respect min_active constraint."""
        result = optimizer.optimize_greedy(min_active=5)

        assert result.num_active >= 5

    def test_min_active_must_be_valid(self, optimizer: Optimizer) -> None:
        """min_active must be in valid range."""
        with pytest.raises(ValueError):
            optimizer.optimize_greedy(min_active=0)

        with pytest.raises(ValueError):
            optimizer.optimize_greedy(min_active=100)  # More than num_chillers

    def test_max_iterations_respected(self, optimizer: Optimizer) -> None:
        """max_iterations should limit iterations."""
        result = optimizer.optimize_greedy(max_iterations=2)

        assert result.iterations <= 2

    def test_optimal_mask_has_correct_size(self, optimizer: Optimizer) -> None:
        """Optimal mask should match number of chillers."""
        result = optimizer.optimize_greedy()

        assert len(result.optimal_mask) == optimizer.environment.num_chillers

    def test_savings_kw_property(self, optimizer: Optimizer) -> None:
        """savings_kw should be baseline - optimal."""
        result = optimizer.optimize_greedy()

        assert result.savings_kw == pytest.approx(
            result.baseline_work_kw - result.optimal_work_kw
        )


class TestOptimizerUtilities:
    """Tests for optimizer utility methods."""

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        """Create small environment for utility tests."""
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        """Create optimizer for tests."""
        return Optimizer(env, total_load_kw=100.0)

    def test_evaluate_configuration(self, optimizer: Optimizer) -> None:
        """evaluate_configuration should work correctly."""
        mask = np.array([True, True, False, False])
        result = optimizer.evaluate_configuration(mask)

        assert result.total_work_kw > 0
        assert result.load_per_unit_kw == pytest.approx(50.0)  # 100 / 2 active

    def test_compare_configurations(self, optimizer: Optimizer) -> None:
        """compare_configurations should return results for all."""
        masks = [
            np.array([True, True, True, True]),
            np.array([True, True, False, False]),
            np.array([True, False, True, False]),
        ]
        results = optimizer.compare_configurations(masks)

        assert len(results) == 3
        assert all(r.total_work_kw > 0 for r in results)

    def test_sensitivity_analysis(self, optimizer: Optimizer) -> None:
        """sensitivity_analysis should return deltas for each chiller."""
        mask = np.ones(4, dtype=bool)
        deltas = optimizer.sensitivity_analysis(mask)

        assert len(deltas) == 4
        # Toggling should cause some change (positive or negative)
        assert not np.allclose(deltas, 0)

    def test_sensitivity_with_single_active(self, optimizer: Optimizer) -> None:
        """Toggling the only active chiller should give infinity."""
        mask = np.array([True, False, False, False])
        deltas = optimizer.sensitivity_analysis(mask)

        # Turning off the only active chiller = infinite work
        assert deltas[0] == float("inf")
