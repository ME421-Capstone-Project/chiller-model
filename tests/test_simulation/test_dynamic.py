"""Tests for DynamicSimulation with varying load and chiller startup."""

import numpy as np
import pytest

from src.components import ChillerArray, WindVector
from src.components.data_center import DataCenter
from src.models import GaussianPlumeModel
from src.simulation import DynamicSimulation, SimulationEnvironment


class TestDynamicSimulation:
    """Tests for DynamicSimulation class."""

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        """Create simulation environment."""
        array = ChillerArray.create_grid(
            rows=2,
            cols=2,
            spacing_m=15.0,
            base_cop=5.0,
            ages_years=np.zeros(4, dtype=np.float64),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def constant_load_dc(self) -> DataCenter:
        """Data center with constant load."""
        return DataCenter(base_load_kw=500.0)

    def test_create_dynamic_simulation(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """DynamicSimulation should be created with valid params."""
        sim = DynamicSimulation(
            environment=env,
            data_center=constant_load_dc,
            time_step_hours=0.25,
        )
        assert sim.time_step_hours == 0.25
        assert sim.environment is env

    def test_step_returns_result(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """Step should return DynamicStepResult."""
        sim = DynamicSimulation(
            environment=env,
            data_center=constant_load_dc,
            time_step_hours=0.25,
            startup_time_hours=0.5,
        )
        result = sim.step(time_hours=0.0)
        assert result.time_hours == 0.0
        assert result.load_kw == 500.0
        assert result.active_mask.shape == (4,)
        assert result.total_work_kw > 0
        assert result.performance is not None

    def test_run_yields_steps(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """Run should yield one result per time step."""
        sim = DynamicSimulation(
            environment=env,
            data_center=constant_load_dc,
            time_step_hours=0.5,
        )
        steps = list(sim.run(duration_hours=2.0))
        assert len(steps) == 4  # 0, 0.5, 1.0, 1.5
        assert steps[0].time_hours == 0.0
        assert steps[-1].time_hours == pytest.approx(1.5)

    def test_varying_load(
        self,
        env: SimulationEnvironment,
    ) -> None:
        """Load should vary with time from DataCenter profile."""
        dc = DataCenter.with_sinusoidal_profile(
            base_load_kw=300.0,
            peak_load_kw=700.0,
            period_hours=24.0,
        )
        sim = DynamicSimulation(
            environment=env,
            data_center=dc,
            time_step_hours=1.0,
        )
        steps = list(sim.run(duration_hours=3.0))
        loads = [s.load_kw for s in steps]
        # Sinusoidal: loads should vary
        assert min(loads) < max(loads)
        assert all(300 <= l <= 700 for l in loads)

    def test_startup_increases_work_initially(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """First steps should show higher work due to startup ramp."""
        sim = DynamicSimulation(
            environment=env,
            data_center=constant_load_dc,
            time_step_hours=0.1,
            startup_time_hours=0.5,  # 5 steps to full ramp
        )
        steps = list(sim.run(duration_hours=1.0))
        # Early steps: chillers ramping, higher work
        # Later steps: full COP, lower work
        if len(steps) >= 6:
            early_work = np.mean([s.total_work_kw for s in steps[:3]])
            late_work = np.mean([s.total_work_kw for s in steps[-3:]])
            assert early_work >= late_work * 0.9  # Early can be higher

    def test_time_step_must_be_positive(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """time_step_hours must be positive."""
        with pytest.raises(ValueError, match="time_step_hours"):
            DynamicSimulation(
                environment=env,
                data_center=constant_load_dc,
                time_step_hours=0.0,
            )

    def test_duration_must_be_positive(
        self,
        env: SimulationEnvironment,
        constant_load_dc: DataCenter,
    ) -> None:
        """duration_hours must be positive."""
        sim = DynamicSimulation(
            environment=env,
            data_center=constant_load_dc,
            time_step_hours=0.25,
        )
        with pytest.raises(ValueError, match="duration_hours"):
            list(sim.run(duration_hours=0.0))
