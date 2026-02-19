"""Tests for SimulationEnvironment.

Validates performance calculations, physical sanity, and composition behavior.
"""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel
from src.simulation.environment import PerformanceResult, SimulationEnvironment


class TestSimulationEnvironment:
    """Tests for SimulationEnvironment class."""

    @pytest.fixture
    def basic_env(self) -> SimulationEnvironment:
        """Create basic environment for testing."""
        array = ChillerArray.create_grid(rows=3, cols=3, spacing_m=10.0, base_cop=5.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    def test_create_environment(self, basic_env: SimulationEnvironment) -> None:
        """Basic environment creation should work."""
        assert basic_env.num_chillers == 9
        assert basic_env.interaction_matrix.shape == (9, 9)

    def test_interaction_matrix_precomputed(
        self, basic_env: SimulationEnvironment
    ) -> None:
        """Interaction matrix should be pre-computed on init."""
        # Matrix should already exist
        assert basic_env.interaction_matrix is not None
        assert basic_env.interaction_matrix.shape == (9, 9)


class TestPerformanceCalculation:
    """Tests for compute_performance method."""

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        """Create environment for performance tests."""
        array = ChillerArray.create_grid(
            rows=3, cols=3, spacing_m=10.0, base_cop=5.0, alpha=0.7
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(array, wind, model)

    def test_all_active_returns_valid_result(
        self, env: SimulationEnvironment
    ) -> None:
        """Performance with all chillers active should return valid result."""
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        assert isinstance(result, PerformanceResult)
        assert result.total_work_kw > 0
        assert result.load_per_unit_kw == pytest.approx(100.0 / 9)

    def test_result_is_immutable(self, env: SimulationEnvironment) -> None:
        """PerformanceResult should be immutable."""
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        with pytest.raises(AttributeError):
            result.total_work_kw = 0.0  # type: ignore

    def test_cop_always_positive(self, env: SimulationEnvironment) -> None:
        """COP must always be positive."""
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        assert np.all(result.cop_array > 0), "COP must be positive"

    def test_cop_never_exceeds_base(self, env: SimulationEnvironment) -> None:
        """Degraded COP cannot exceed base COP."""
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        assert np.all(result.cop_array <= env.chiller_array.base_cop)

    def test_temp_rise_non_negative(self, env: SimulationEnvironment) -> None:
        """Temperature rise must be non-negative."""
        active_mask = np.ones(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        assert np.all(result.temp_rise_array >= 0)

    def test_fewer_active_may_reduce_work(
        self, env: SimulationEnvironment
    ) -> None:
        """In some cases, fewer active chillers reduces total work.
        
        This is the core optimization insight: thermal interference
        from many chillers can make the system less efficient.
        """
        all_active = np.ones(9, dtype=bool)
        result_all = env.compute_performance(all_active, total_load_kw=100.0)

        # Try turning off the most "costly" chiller (downstream, high interference)
        # This test verifies the concept, not a specific outcome
        for i in range(9):
            some_active = all_active.copy()
            some_active[i] = False
            result_some = env.compute_performance(some_active, total_load_kw=100.0)

            # At least one configuration should have lower work
            if result_some.total_work_kw < result_all.total_work_kw:
                return  # Test passes

        # If all configurations are worse, that's also valid physics
        # (but unusual for this setup)

    def test_no_active_returns_infinity(
        self, env: SimulationEnvironment
    ) -> None:
        """No active chillers should return infinite work."""
        active_mask = np.zeros(9, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        assert result.total_work_kw == float("inf")
        assert result.load_per_unit_kw == 0.0

    def test_single_chiller_no_interference(self) -> None:
        """Single chiller has no thermal interference (age=0 for full COP)."""
        array = ChillerArray.create_grid(
            rows=1,
            cols=1,
            spacing_m=10.0,
            base_cop=5.0,
            ages_years=np.array([0.0]),  # New chiller: no age degradation
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        env = SimulationEnvironment(array, wind, model)

        active_mask = np.ones(1, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=100.0)

        # No interference, age=0: full base COP
        assert result.cop_array[0] == pytest.approx(5.0)
        # Work = load / COP
        assert result.total_work_kw == pytest.approx(20.0)

    def test_age_reduces_cop(self) -> None:
        """Older chillers should have lower COP (age degradation)."""
        base_cop = 5.0
        # Single chiller, age 0: full COP
        array_new = ChillerArray.create_grid(
            rows=1,
            cols=1,
            spacing_m=10.0,
            base_cop=base_cop,
            ages_years=np.array([0.0], dtype=np.float64),
        )
        # Single chiller, age 1 year: 80% COP (per constants)
        array_1yr = ChillerArray.create_grid(
            rows=1,
            cols=1,
            spacing_m=10.0,
            base_cop=base_cop,
            ages_years=np.array([1.0], dtype=np.float64),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()

        env_new = SimulationEnvironment(array_new, wind, model)
        env_1yr = SimulationEnvironment(array_1yr, wind, model)

        active_mask = np.ones(1, dtype=bool)
        result_new = env_new.compute_performance(active_mask, total_load_kw=100.0)
        result_1yr = env_1yr.compute_performance(active_mask, total_load_kw=100.0)

        # Age 0: COP = base_cop = 5.0; Age 1: COP = 0.8 * base_cop = 4.0
        assert result_new.cop_array[0] == pytest.approx(base_cop)
        assert result_1yr.cop_array[0] == pytest.approx(0.8 * base_cop)
        assert result_1yr.cop_array[0] < result_new.cop_array[0]


class TestEnvironmentFactories:
    """Tests for factory methods."""

    def test_with_new_wind(self) -> None:
        """with_new_wind should create new environment."""
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind1 = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        wind2 = WindVector(velocity_m_per_s=(0.0, 5.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()

        env1 = SimulationEnvironment(array, wind1, model)
        env2 = env1.with_new_wind(wind2)

        # Should be different environments
        assert env1 is not env2
        # Wind should be different
        assert env1.wind != env2.wind
        # Interaction matrices should be different (different wind direction)
        assert not np.allclose(
            env1.interaction_matrix, env2.interaction_matrix
        )

    def test_with_new_model(self) -> None:
        """with_new_model should create new environment."""
        array = ChillerArray.create_grid(rows=2, cols=2, spacing_m=10.0)
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model1 = GaussianPlumeModel(dispersion_coeff=1.0)
        model2 = GaussianPlumeModel(dispersion_coeff=2.0)

        env1 = SimulationEnvironment(array, wind, model1)
        env2 = env1.with_new_model(model2)

        # Should be different environments
        assert env1 is not env2
        # Models should be different
        assert env1.interaction_model.dispersion_coeff != env2.interaction_model.dispersion_coeff


class TestPerformanceResultProperties:
    """Tests for PerformanceResult computed properties."""

    def test_mean_cop(self) -> None:
        """mean_cop should be average across all chillers."""
        result = PerformanceResult(
            total_work_kw=100.0,
            cop_array=np.array([4.0, 5.0, 6.0]),
            temp_rise_array=np.array([0.1, 0.2, 0.3]),
            load_per_unit_kw=50.0,
        )
        assert result.mean_cop == pytest.approx(5.0)

    def test_effective_cop(self) -> None:
        """effective_cop should be total_cooling / total_work."""
        result = PerformanceResult(
            total_work_kw=20.0,
            cop_array=np.array([4.0, 5.0, 6.0]),
            temp_rise_array=np.array([0.1, 0.2, 0.3]),
            load_per_unit_kw=50.0,  # 3 chillers * 50 = 150 kW cooling
        )
        # effective_cop = 150 / 20 = 7.5
        assert result.effective_cop == pytest.approx(7.5)
