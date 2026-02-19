"""Tests for SimulationEnvironment (plant transfer function)."""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel
from src.simulation.environment import PerformanceResult, SimulationEnvironment


class TestSimulationEnvironment:

    @pytest.fixture
    def basic_env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(rows=3, cols=3, spacing_m=10.0, base_cop=5.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    def test_create_environment(self, basic_env: SimulationEnvironment) -> None:
        assert basic_env.num_chillers == 9
        assert basic_env.interaction_matrix.shape == (9, 9)

    def test_interaction_matrix_precomputed(
        self, basic_env: SimulationEnvironment
    ) -> None:
        assert basic_env.interaction_matrix is not None
        assert basic_env.interaction_matrix.shape == (9, 9)


class TestPerformanceCalculation:

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(
            rows=3, cols=3, spacing_m=10.0, base_cop=5.0, alpha=0.7
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    def test_all_active_returns_valid_result(
        self, env: SimulationEnvironment
    ) -> None:
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert isinstance(result, PerformanceResult)
        assert result.total_work_kw > 0
        assert result.load_per_unit_kw == pytest.approx(100.0 / 9)

    def test_result_is_immutable(self, env: SimulationEnvironment) -> None:
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        with pytest.raises(AttributeError):
            result.total_work_kw = 0.0  # type: ignore

    def test_cop_always_positive(self, env: SimulationEnvironment) -> None:
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert np.all(result.cop_array > 0)

    def test_cop_never_exceeds_base(self, env: SimulationEnvironment) -> None:
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert np.all(result.cop_array <= env.chiller_array.base_cop)

    def test_temp_rise_non_negative(self, env: SimulationEnvironment) -> None:
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert np.all(result.temp_rise_array >= 0)

    def test_fewer_active_may_reduce_work(
        self, env: SimulationEnvironment
    ) -> None:
        """Thermal interference can make fewer chillers more efficient."""
        all_active = np.ones(9, dtype=bool)
        result_all = env.compute_performance(all_active, total_load_kw=100.0)
        for i in range(9):
            some_active = all_active.copy()
            some_active[i] = False
            result_some = env.compute_performance(some_active, total_load_kw=100.0)
            if result_some.total_work_kw < result_all.total_work_kw:
                return

    def test_no_active_returns_infinity(
        self, env: SimulationEnvironment
    ) -> None:
        active_mask = np.zeros(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert result.total_work_kw == float("inf")
        assert result.load_per_unit_kw == 0.0

    def test_single_chiller_no_interference(self) -> None:
        """Single new chiller achieves full base COP."""
        array = ChillerArray.create_grid(
            rows=1, cols=1, spacing_m=10.0, base_cop=5.0,
            ages_years=np.array([0.0]),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        env = SimulationEnvironment(array, wind, model)

        active_mask = np.ones(1, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)
        assert result.cop_array[0] == pytest.approx(5.0)
        assert result.total_work_kw == pytest.approx(20.0)

    def test_age_reduces_cop(self) -> None:
        """Older chillers have lower COP due to age degradation."""
        base_cop = 5.0
        array_new = ChillerArray.create_grid(
            rows=1, cols=1, spacing_m=10.0, base_cop=base_cop,
            ages_years=np.array([0.0], dtype=np.float64),
        )
        array_1yr = ChillerArray.create_grid(
            rows=1, cols=1, spacing_m=10.0, base_cop=base_cop,
            ages_years=np.array([1.0], dtype=np.float64),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()

        env_new = SimulationEnvironment(array_new, wind, model)
        env_1yr = SimulationEnvironment(array_1yr, wind, model)

        active_mask = np.ones(1, dtype=bool)
        result_new = env_new.compute_performance(active_mask, total_load_kw=100.0)
        result_1yr = env_1yr.compute_performance(active_mask, total_load_kw=100.0)

        assert result_new.cop_array[0] == pytest.approx(base_cop)
        assert result_1yr.cop_array[0] == pytest.approx(0.8 * base_cop)
        assert result_1yr.cop_array[0] < result_new.cop_array[0]

    def test_startup_factors_reduce_cop(self) -> None:
        """Start-up ramp reduces effective COP."""
        array = ChillerArray.create_grid(
            rows=1, cols=1, spacing_m=10.0, base_cop=5.0,
            ages_years=np.array([0.0], dtype=np.float64),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        env = SimulationEnvironment(array, wind, model)

        active_mask = np.ones(1, dtype=bool)
        result_full = env.compute_performance(active_mask, total_load_kw=100.0)
        result_half = env.compute_performance(
            active_mask, total_load_kw=100.0,
            startup_factors=np.array([0.5], dtype=np.float64),
        )

        assert result_half.cop_array[0] == pytest.approx(2.5)
        assert result_full.cop_array[0] == pytest.approx(5.0)
        assert result_half.total_work_kw > result_full.total_work_kw


class TestEnvironmentFactories:

    def test_with_new_wind(self) -> None:
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind1 = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        wind2 = WindVector(velocity_m_per_s=(0.0, 5.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()

        env1 = SimulationEnvironment(array, wind1, model)
        env2 = env1.with_new_wind(wind2)

        assert env1 is not env2
        assert env1.wind != env2.wind
        assert not np.allclose(env1.interaction_matrix, env2.interaction_matrix)

    def test_with_new_model(self) -> None:
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model1 = GaussianPlumeModel(dispersion_coeff=1.0)
        model2 = GaussianPlumeModel(dispersion_coeff=2.0)

        env1 = SimulationEnvironment(array, wind, model1)
        env2 = env1.with_new_model(model2)

        assert env1 is not env2
        assert env1.interaction_model.dispersion_coeff != env2.interaction_model.dispersion_coeff


class TestPerformanceResultProperties:

    def test_mean_cop(self) -> None:
        result = PerformanceResult(
            total_work_kw=100.0,
            cop_array=np.array([4.0, 5.0, 6.0]),
            temp_rise_array=np.array([0.1, 0.2, 0.3]),
            load_per_unit_kw=50.0,
        )
        assert result.mean_cop == pytest.approx(5.0)

    def test_effective_cop(self) -> None:
        result = PerformanceResult(
            total_work_kw=20.0,
            cop_array=np.array([4.0, 5.0, 6.0]),
            temp_rise_array=np.array([0.1, 0.2, 0.3]),
            load_per_unit_kw=50.0,
        )
        assert result.effective_cop == pytest.approx(7.5)
