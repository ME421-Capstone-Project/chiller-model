"""Tests for DynamicSimulation with varying load and chiller start-up."""

import numpy as np
import pytest

from src.components import ChillerArray, WindVector
from src.components.data_center import DataCenter
from src.models import GaussianPlumeModel
from src.simulation import DynamicSimulation, SimulationEnvironment


class TestDynamicSimulation:

    @pytest.fixture
    def env(self) -> SimulationEnvironment:
        array = ChillerArray.create_grid(
            rows=2, cols=2, spacing_m=15.0, base_cop=5.0,
            ages_years=np.zeros(4, dtype=np.float64),
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
        model = GaussianPlumeModel()
        return SimulationEnvironment(array, wind, model)

    @pytest.fixture
    def constant_load_dc(self) -> DataCenter:
        return DataCenter(base_load_kw=500.0)

    def test_create_dynamic_simulation(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc, time_step_hours=0.25,
        )
        assert sim.time_step_hours == 0.25
        assert sim.environment is env

    def test_step_returns_result(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc,
            time_step_hours=0.25, startup_time_hours=0.5,
        )
        result = sim.step(time_hours=0.0)
        assert result.time_hours == 0.0
        assert result.load_kw == 500.0
        assert result.active_mask.shape == (4,)
        assert result.total_work_kw > 0
        assert result.performance is not None

    def test_run_yields_steps(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc, time_step_hours=0.5,
        )
        steps = list(sim.run(duration_hours=2.0))
        assert len(steps) == 4
        assert steps[0].time_hours == 0.0
        assert steps[-1].time_hours == pytest.approx(1.5)

    def test_varying_load(self, env: SimulationEnvironment) -> None:
        dc = DataCenter.with_sinusoidal_profile(
            base_load_kw=300.0, peak_load_kw=700.0, period_hours=24.0,
        )
        sim = DynamicSimulation(
            environment=env, data_center=dc, time_step_hours=1.0,
        )
        steps = list(sim.run(duration_hours=3.0))
        loads = [s.load_kw for s in steps]
        assert min(loads) < max(loads)
        assert all(300 <= load <= 700 for load in loads)

    def test_startup_increases_work_initially(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc,
            time_step_hours=0.1, startup_time_hours=0.5,
        )
        steps = list(sim.run(duration_hours=1.0))
        if len(steps) >= 6:
            early_work = np.mean([s.total_work_kw for s in steps[:3]])
            late_work = np.mean([s.total_work_kw for s in steps[-3:]])
            assert early_work >= late_work * 0.9

    def test_time_step_must_be_positive(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        with pytest.raises(ValueError, match="time_step_hours"):
            DynamicSimulation(
                environment=env, data_center=constant_load_dc, time_step_hours=0.0,
            )

    def test_duration_must_be_positive(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc, time_step_hours=0.25,
        )
        with pytest.raises(ValueError, match="duration_hours"):
            list(sim.run(duration_hours=0.0))

    def test_varying_wind_direction(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        from src.components.wind import sinusoidal_direction_profile

        wind_profile = sinusoidal_direction_profile(
            speed_m_per_s=5.0, angle_center_deg=90.0,
            angle_amplitude_deg=45.0, period_hours=24.0, ambient_temp_k=298.15,
        )
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc,
            time_step_hours=2.0, wind_profile=wind_profile,
        )
        steps = list(sim.run(duration_hours=6.0))
        vx_values = [s.wind.velocity_m_per_s[0] for s in steps]
        vy_values = [s.wind.velocity_m_per_s[1] for s in steps]
        assert min(vx_values) != max(vx_values) or min(vy_values) != max(vy_values)
        speeds = [s.wind.speed_m_per_s for s in steps]
        assert all(s == pytest.approx(5.0) for s in speeds)

    def test_step_includes_wind(
        self, env: SimulationEnvironment, constant_load_dc: DataCenter,
    ) -> None:
        sim = DynamicSimulation(
            environment=env, data_center=constant_load_dc, time_step_hours=0.25,
        )
        result = sim.step(time_hours=0.0)
        assert result.wind is not None
        assert result.wind.speed_m_per_s == pytest.approx(5.0)
