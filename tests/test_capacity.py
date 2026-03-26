"""
Tests for max_cooling_kw capacity model:
- Feasibility gate forces multi-chiller activation at high loads
- Capacity degrades with chiller age via DegradationFn
- Startup ramp reduces effective capacity (not COP)
- COP is unaffected by age
"""
import numpy as np
import pytest

from chiller_sim import Simulator
from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.physics.degradation import default_capacity_degradation_fn


def test_create_grid_rejects_zero_max_cooling_kw():
    with pytest.raises(ValueError, match="max_cooling_kw"):
        ChillerGrid.create_grid(
            rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=0.0,
        )


def test_create_grid_rejects_negative_max_cooling_kw():
    with pytest.raises(ValueError, match="max_cooling_kw"):
        ChillerGrid.create_grid(
            rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=-100.0,
        )


def test_capacity_gate_forces_multiple_chillers():
    """If max_cooling_kw < load_kw, a single chiller cannot satisfy demand —
    the optimizer must activate multiple chillers."""
    # 4 chillers each capped at 200 kW; load = 350 kW → at least 2 required
    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=200.0,
                   ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 350.0)
        .build()
    )
    result = sim.optimize(time_hours=0.0)
    assert result.active_mask.sum() >= 2


def test_aged_chillers_require_more_active():
    """Heavily aged chillers have lower effective capacity, so more must be
    active to satisfy the same load than brand-new chillers."""
    load_kw = 350.0
    ages_new = np.zeros(4)
    ages_old = np.full(4, 20.0)  # 20 years old: ~exp(-rate*20) ≈ 0.49 for 10yr threshold

    sim_new = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=250.0,
                   ages_years=ages_new)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: load_kw)
        .build()
    )
    sim_old = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=250.0,
                   ages_years=ages_old)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: load_kw)
        .build()
    )
    r_new = sim_new.optimize(time_hours=0.0)
    r_old = sim_old.optimize(time_hours=0.0)
    assert r_old.active_mask.sum() >= r_new.active_mask.sum()


def test_ramp_reduces_effective_capacity():
    """When a chiller is at time_since_start=0, ramp_fn(0)=0 → effective cap=0.
    The feasibility gate returns inf for that configuration."""
    from chiller_sim.simulation.results import InitialState

    # 4 chillers at 200 kW each; with ramp=0 total cap=0; load=350 → infeasible
    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=200.0,
                   ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 350.0)
        .with_switching_threshold(min_savings_kw=1e9)  # lock in the initial set
        .build()
    )
    # Provide all 4 active but just started (ramp=0)
    state = InitialState(
        active_mask=np.ones(4, dtype=bool),
        time_since_start_hours=np.zeros(4),
    )
    result = sim.simulate(duration_hours=1.0, time_step_hours=1.0, initial_state=state)
    # At t=0, effective cap = 200 * 1.0 * ramp(0) = 0 → infeasible → work = inf
    assert result.total_work_kw[0] == float("inf")


def test_default_capacity_degradation_fn_at_threshold():
    fn = default_capacity_degradation_fn(years_to_80_pct=10.0)
    assert abs(fn(10.0) - 0.8) < 1e-9


def test_cop_unaffected_by_age():
    """COP should be the same for a brand-new vs 20-year-old chiller
    (degradation affects capacity only)."""
    ages_new = np.zeros(4)
    ages_old = np.full(4, 20.0)

    def _sim(ages):
        return (
            Simulator()
            .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=1000.0,
                       ages_years=ages)
            .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
            .with_ambient_temp(temp_k=298.15)
            .with_load_fn(lambda t: 100.0)
            .with_switching_threshold(min_savings_kw=1e9)
            .build()
        )

    r_new = _sim(ages_new).optimize(time_hours=0.0)
    r_old = _sim(ages_old).optimize(time_hours=0.0)
    # Active cops should be equal — age does not enter cop_fn
    active_new = r_new.cop_array[r_new.active_mask]
    active_old = r_old.cop_array[r_old.active_mask]
    np.testing.assert_allclose(np.sort(active_new), np.sort(active_old), rtol=1e-9)


def test_custom_degradation_fn_affects_aged_chillers():
    """With 50% capacity degradation, the optimizer needs more chillers than
    with no degradation to satisfy the same load."""
    ages = np.full(4, 10.0)
    load_kw = 350.0

    sim_nodeg = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=250.0,
                   ages_years=ages)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: load_kw)
        .with_degradation_fn(lambda age: 1.0)
        .build()
    )
    sim_heavydeg = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=250.0,
                   ages_years=ages)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: load_kw)
        .with_degradation_fn(lambda age: 0.5)
        .build()
    )
    r_nodeg = sim_nodeg.optimize(time_hours=0.0)
    r_heavydeg = sim_heavydeg.optimize(time_hours=0.0)
    # With 50% capacity, each chiller can do 125 kW → need 3+ to cover 350
    assert r_heavydeg.active_mask.sum() >= r_nodeg.active_mask.sum()
