import numpy as np
import pytest
from chiller_sim import Simulator


def _base_sim(load_kw: float = 500.0, min_savings_kw: float = 0.0) -> object:
    return (
        Simulator()
        .with_grid(rows=4, cols=4, spacing_m=10.0, base_cop=5.5, alpha=0.7, seed=0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: load_kw)
        .with_switching_threshold(min_savings_kw=min_savings_kw)
        .build()
    )


# --- Optimization correctness ---

def test_optimize_uses_fewer_chillers_than_all_on():
    sim = _base_sim()
    result = sim.optimize(time_hours=0.0)
    assert result.active_mask.sum() < sim._grid.num_chillers


def test_optimize_total_work_less_than_baseline():
    sim = _base_sim()
    result = sim.optimize(time_hours=0.0)
    assert result.total_work_kw <= result.baseline_work_kw


def test_optimize_savings_fraction_in_range():
    sim = _base_sim()
    result = sim.optimize(time_hours=0.0)
    assert 0.0 <= result.savings_fraction <= 1.0


def test_optimize_load_kw_matches_load_fn():
    sim = _base_sim(load_kw=750.0)
    result = sim.optimize(time_hours=0.0)
    assert result.load_kw == 750.0


def test_optimize_explicit_load_overrides_load_fn():
    sim = _base_sim(load_kw=500.0)
    result = sim.optimize(time_hours=0.0, load_kw=999.0)
    assert result.load_kw == 999.0


def test_downwind_chillers_have_higher_inlet_temp():
    # Two chillers on east-west axis; east wind means chiller at x=0 is upwind,
    # chiller at x=20 is downwind. Force both on with huge switching threshold.
    sim = (
        Simulator()
        .with_grid(rows=1, cols=2, spacing_m=20.0, base_cop=5.0, ages_years=np.zeros(2))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 200.0)
        .with_switching_threshold(min_savings_kw=1e9)  # keep both on
        .build()
    )
    result = sim.optimize(time_hours=0.0)
    # chiller 0 at x=0 (upwind), chiller 1 at x=20 (downwind)
    assert result.temp_rise_array[1] > result.temp_rise_array[0]


def test_switching_threshold_suppresses_marginal_switching():
    # With a high threshold, optimizer should leave all chillers on
    sim = _base_sim(min_savings_kw=1e9)
    result = sim.optimize(time_hours=0.0)
    assert result.active_mask.sum() == sim._grid.num_chillers


def test_startup_clock_persists_across_optimize_calls():
    sim = _base_sim()
    r1 = sim.optimize(time_hours=0.0)
    # Which chillers were active after first call
    active_after_first = r1.active_mask.copy()
    r2 = sim.optimize(time_hours=1.0)
    # Active chillers from call 1 should show non-zero time_since_start in internal state
    for i in np.where(active_after_first)[0]:
        assert sim._time_since_start[i] > 0.0


from chiller_sim import InitialState

# --- Dynamic simulation ---

def test_simulate_returns_correct_step_count():
    sim = _base_sim()
    result = sim.simulate(duration_hours=12.0, time_step_hours=1.0)
    assert len(result.steps) == 12


def test_simulate_schedule_shape():
    sim = _base_sim()
    result = sim.simulate(duration_hours=6.0, time_step_hours=1.0)
    assert result.schedule.shape == (6, sim._grid.num_chillers)


def test_stream_and_simulate_identical_schedules():
    sim = _base_sim()
    sim_result = sim.simulate(duration_hours=6.0, time_step_hours=1.0)

    # Reset: simulate resets state, stream should too
    stream_steps = list(sim.stream(duration_hours=6.0, time_step_hours=1.0))
    stream_schedule = np.array([s.active_mask for s in stream_steps])

    np.testing.assert_array_equal(sim_result.schedule, stream_schedule)


def test_simulate_resets_state_regardless_of_prior_optimize():
    sim = _base_sim()
    # Run optimize several times to build up state
    for t in range(5):
        sim.optimize(time_hours=float(t))

    # Two independent simulate() calls should give same result
    r1 = sim.simulate(duration_hours=4.0, time_step_hours=1.0)
    r2 = sim.simulate(duration_hours=4.0, time_step_hours=1.0)
    np.testing.assert_array_equal(r1.schedule, r2.schedule)


def test_ramp_state_advances_within_run():
    # Start with all chillers just turned on (time=0 → ramp_fn(0)=0 → COP penalized).
    # After one 1-hour step (past the 0.25h startup window), COP should be unpenalized.
    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .with_switching_threshold(min_savings_kw=1e9)  # keep all on, no toggling
        .build()
    )
    state = InitialState(
        active_mask=np.ones(4, dtype=bool),
        time_since_start_hours=np.zeros(4),  # just started
    )
    steps = list(sim.stream(duration_hours=2.0, time_step_hours=1.0, initial_state=state))
    # Step 0: ramp_fn(0.0) = 0.0 → COP clipped to ~1e-6
    assert steps[0].cop_array[0] < 0.01
    # Step 1: ramp_fn(1.0) = 1.0 (past startup window) → full COP
    assert steps[1].cop_array[0] > steps[0].cop_array[0]


def test_initial_state_chillers_start_ramped():
    # Chillers given time_since_start=0 start at ramp penalty (ramp_fn(0)=0 → COP ≈ 0).
    # Use a huge switching threshold to prevent the optimizer deactivating penalized chillers,
    # so the ramp effect is visible in the work output.
    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .with_switching_threshold(min_savings_kw=1e9)  # keep all on
        .build()
    )
    state = InitialState(
        active_mask=np.ones(4, dtype=bool),
        time_since_start_hours=np.zeros(4),
    )
    result_with_state = sim.simulate(duration_hours=1.0, time_step_hours=1.0, initial_state=state)
    result_default = sim.simulate(duration_hours=1.0, time_step_hours=1.0)
    # With ramp_fn(0)=0, step 0 work should be much higher than steady-state default
    assert result_with_state.total_work_kw[0] > result_default.total_work_kw[0]


def test_custom_load_fn_drives_load_at_each_step():
    loads_seen = []
    def tracking_load(t: float) -> float:
        loads_seen.append(t)
        return 300.0 + t * 10.0

    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, seed=0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(tracking_load)
        .build()
    )
    result = sim.simulate(duration_hours=3.0, time_step_hours=1.0)
    assert len(loads_seen) >= 3
    for i, step in enumerate(result.steps):
        assert step.load_kw == 300.0 + step.time_hours * 10.0
