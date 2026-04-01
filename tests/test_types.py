import numpy as np
import pytest
from chiller_sim.simulation.results import OptimizeResult, SimulationResult, InitialState


def _make_result(time_hours: float = 0.0, n: int = 4) -> OptimizeResult:
    return OptimizeResult(
        time_hours=time_hours,
        load_kw=500.0,
        active_mask=np.array([True, True, False, False]),
        total_work_kw=100.0,
        baseline_work_kw=120.0,
        savings_fraction=1 / 6,
        cop_array=np.array([4.0, 3.5, 0.0, 0.0]),
        temp_rise_array=np.array([0.0, 0.5, 0.0, 0.0]),
    )


def test_optimize_result_stores_fields():
    r = _make_result()
    assert r.time_hours == 0.0
    assert r.load_kw == 500.0
    assert r.total_work_kw == 100.0
    assert r.baseline_work_kw == 120.0
    assert abs(r.savings_fraction - 1 / 6) < 1e-9
    assert r.active_mask.dtype == bool
    assert len(r.cop_array) == 4


def test_simulation_result_schedule_property():
    steps = [_make_result(t) for t in [0.0, 1.0, 2.0]]
    result = SimulationResult(steps=steps)
    schedule = result.schedule
    assert schedule.shape == (3, 4)
    assert schedule.dtype == bool
    assert np.all(schedule[:, 0])  # chiller 0 always on
    assert not np.any(schedule[:, 2])  # chiller 2 always off


def test_simulation_result_total_work_property():
    steps = [_make_result(t) for t in [0.0, 1.0]]
    result = SimulationResult(steps=steps)
    np.testing.assert_array_equal(result.total_work_kw, [100.0, 100.0])


def test_simulation_result_loads_kw_property():
    steps = [_make_result(t) for t in [0.0, 1.0]]
    result = SimulationResult(steps=steps)
    np.testing.assert_array_equal(result.loads_kw, [500.0, 500.0])


def test_simulation_result_savings_fraction_property():
    steps = [_make_result(t) for t in [0.0, 1.0]]
    result = SimulationResult(steps=steps)
    assert len(result.savings_fraction) == 2


def test_simulation_result_cop_arrays_property():
    steps = [_make_result(t) for t in [0.0, 1.0]]
    result = SimulationResult(steps=steps)
    assert result.cop_arrays.shape == (2, 4)


def test_initial_state_stores_fields():
    state = InitialState(
        active_mask=np.array([True, False, True]),
        time_since_start_hours=np.array([2.0, 0.0, 0.5]),
    )
    assert state.active_mask[0] is np.bool_(True)
    assert state.time_since_start_hours[2] == 0.5


from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions


def test_chiller_grid_from_regular_grid():
    grid = ChillerLayout.create_grid(
        rows=2, cols=3, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0, alpha=0.7
    )
    assert grid.positions_m.shape == (6, 2)
    assert grid.base_cop == 5.0
    assert grid.alpha == 0.7
    assert len(grid.ages_years) == 6


def test_chiller_grid_seed_reproducible():
    g1 = ChillerLayout.create_grid(
        rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0, seed=42
    )
    g2 = ChillerLayout.create_grid(
        rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0, seed=42
    )
    np.testing.assert_array_equal(g1.ages_years, g2.ages_years)


def test_chiller_grid_explicit_ages():
    ages = np.array([1.0, 2.0, 3.0, 4.0])
    grid = ChillerLayout.create_grid(
        rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0, ages_years=ages
    )
    np.testing.assert_array_equal(grid.ages_years, ages)


def test_chiller_grid_num_chillers():
    grid = ChillerLayout.create_grid(
        rows=3, cols=4, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0
    )
    assert grid.num_chillers == 12


def test_wind_conditions_stores_fields():
    wind = WindConditions(speed_m_per_s=3.0, angle_deg=45.0)
    assert wind.speed_m_per_s == 3.0
    assert wind.angle_deg == 45.0


def test_wind_conditions_to_unit_vector():
    # Due east (angle=0): unit vector = (1, 0)
    wind = WindConditions(speed_m_per_s=5.0, angle_deg=0.0)
    uv = wind.unit_vector
    assert abs(uv[0] - 1.0) < 1e-9
    assert abs(uv[1]) < 1e-9

    # Due north (angle=90): unit vector = (0, 1)
    wind_n = WindConditions(speed_m_per_s=5.0, angle_deg=90.0)
    uv_n = wind_n.unit_vector
    assert abs(uv_n[0]) < 1e-9
    assert abs(uv_n[1] - 1.0) < 1e-9


def test_chiller_layout_from_positions():
    positions = np.array([[0.0, 0.0], [10.0, 5.0], [25.0, 15.0]])
    ages = np.array([1.0, 5.0, 10.0])
    layout = ChillerLayout.from_positions(
        positions_m=positions,
        ages_years=ages,
        base_cop=5.0,
        max_cooling_kw=500.0,
    )
    assert layout.positions_m.shape == (3, 2)
    assert layout.num_chillers == 3
    assert layout.base_cop == 5.0
    assert layout.alpha == 0.7  # default
    assert layout.max_cooling_kw == 500.0
    np.testing.assert_array_equal(layout.ages_years, ages)


def test_from_positions_rejects_wrong_shape_1d():
    with pytest.raises(ValueError, match="positions_m"):
        ChillerLayout.from_positions(
            positions_m=np.array([1.0, 2.0, 3.0]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_wrong_shape_3col():
    with pytest.raises(ValueError, match="positions_m"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0, 0.0]]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_mismatched_ages():
    with pytest.raises(ValueError, match="ages_years"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0], [10.0, 5.0]]),
            ages_years=np.array([1.0, 2.0, 3.0]),  # 3 ages for 2 positions
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_zero_max_cooling():
    with pytest.raises(ValueError, match="max_cooling_kw"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0]]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=0.0,
        )
