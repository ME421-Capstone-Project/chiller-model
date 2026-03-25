import numpy as np
from chiller_sim.simulation.results import OptimizeResult, SimulationResult, InitialState


def _make_result(time_hours: float = 0.0, n: int = 4) -> OptimizeResult:
    return OptimizeResult(
        time_hours=time_hours,
        load_kw=500.0,
        active_mask=np.array([True, True, False, False]),
        total_work_kw=100.0,
        baseline_work_kw=120.0,
        savings_fraction=1/6,
        cop_array=np.array([4.0, 3.5, 0.0, 0.0]),
        temp_rise_array=np.array([0.0, 0.5, 0.0, 0.0]),
    )


def test_optimize_result_stores_fields():
    r = _make_result()
    assert r.time_hours == 0.0
    assert r.load_kw == 500.0
    assert r.total_work_kw == 100.0
    assert r.baseline_work_kw == 120.0
    assert abs(r.savings_fraction - 1/6) < 1e-9
    assert r.active_mask.dtype == bool
    assert len(r.cop_array) == 4


def test_simulation_result_schedule_property():
    steps = [_make_result(t) for t in [0.0, 1.0, 2.0]]
    result = SimulationResult(steps=steps)
    schedule = result.schedule
    assert schedule.shape == (3, 4)
    assert schedule.dtype == bool
    assert np.all(schedule[:, 0])   # chiller 0 always on
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
