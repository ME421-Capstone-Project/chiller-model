"""Tests for the Optimizer class."""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel
from src.simulation.environment import SimulationEnvironment
from src.simulation.optimizer import OptimizationResult, Optimizer


class TestOptimizer:

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=10.0, base_cop=5.0, alpha=0.7
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        return Optimizer(env, total_load_kw=500.0)

    def test_create_optimizer(self, env: SimulationEnvironment) -> None:
        optimizer = Optimizer(env, total_load_kw=500.0)
        assert optimizer.total_load_kw == 500.0

    def test_load_must_be_positive(self, env: SimulationEnvironment) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            Optimizer(env, total_load_kw=0.0)


class TestGreedyOptimization:

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=5.0, base_cop=5.0, alpha=1.0
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=0.8)
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        return Optimizer(env, total_load_kw=500.0)

    def test_greedy_returns_valid_result(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        assert isinstance(result, OptimizationResult)
        assert result.optimal_work_kw > 0
        assert result.baseline_work_kw > 0
        assert 0 <= result.savings_fraction <= 1
        assert result.num_active >= 1

    def test_result_is_immutable(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        with pytest.raises(AttributeError):
            result.optimal_work_kw = 0.0  # type: ignore

    def test_optimal_not_worse_than_baseline(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        assert result.optimal_work_kw <= result.baseline_work_kw

    def test_savings_calculation_correct(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        expected_savings = (
            result.baseline_work_kw - result.optimal_work_kw
        ) / result.baseline_work_kw
        assert result.savings_fraction == pytest.approx(expected_savings)

    def test_respects_min_active(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy(min_active=5)
        assert result.num_active >= 5

    def test_min_active_must_be_valid(self, optimizer: Optimizer) -> None:
        with pytest.raises(ValueError):
            optimizer.optimize_greedy(min_active=0)
        with pytest.raises(ValueError):
            optimizer.optimize_greedy(min_active=100)

    def test_max_iterations_respected(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy(max_iterations=2)
        assert result.iterations <= 2

    def test_optimal_mask_has_correct_size(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        assert len(result.optimal_mask) == optimizer.environment.num_chillers

    def test_savings_kw_property(self, optimizer: Optimizer) -> None:
        result = optimizer.optimize_greedy()
        assert result.savings_kw == pytest.approx(
            result.baseline_work_kw - result.optimal_work_kw
        )


class TestOptimizerUtilities:

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def optimizer(self, env: SimulationEnvironment) -> Optimizer:
        return Optimizer(env, total_load_kw=100.0)

    def test_evaluate_configuration(self, optimizer: Optimizer) -> None:
        mask = np.array([True, True, False, False])
        result = optimizer.evaluate_configuration(mask)
        assert result.total_work_kw > 0
        assert result.load_per_unit_kw == pytest.approx(50.0)

    def test_compare_configurations(self, optimizer: Optimizer) -> None:
        masks = [
            np.array([True, True, True, True]),
            np.array([True, True, False, False]),
            np.array([True, False, True, False]),
        ]
        results = optimizer.compare_configurations(masks)
        assert len(results) == 3
        assert all(r.total_work_kw > 0 for r in results)

    def test_sensitivity_analysis(self, optimizer: Optimizer) -> None:
        mask = np.ones(4, dtype=bool)
        deltas = optimizer.sensitivity_analysis(mask)
        assert len(deltas) == 4
        assert not np.allclose(deltas, 0)

    def test_sensitivity_with_single_active(self, optimizer: Optimizer) -> None:
        mask = np.array([True, False, False, False])
        deltas = optimizer.sensitivity_analysis(mask)
        assert deltas[0] == float("inf")
