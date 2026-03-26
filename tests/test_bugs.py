"""
Regression tests for bugs identified during code review.
Each test is paired with a description of the bug it catches.
"""
from __future__ import annotations

import numpy as np
import pytest

from chiller_sim import Simulator
from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.simulation.builder import SimulatorBuilder
from chiller_sim.simulation.results import InitialState


def _base_builder() -> SimulatorBuilder:
    return (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0, ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
    )


# ---------------------------------------------------------------------------
# Bug 1: ChillerGrid.create_grid does not validate ages_years length
#
# If ages_years has the wrong length, _evaluate_work loops over
# self._grid.ages_years (wrong length) to build deg_factors, then indexes
# deg_factors[i] for i in range(n_chillers), causing an IndexError deep
# inside the simulation rather than a clear ValueError at construction time.
# ---------------------------------------------------------------------------

def test_create_grid_rejects_ages_too_short():
    """Wrong-length ages_years should raise ValueError at grid creation, not IndexError later."""
    with pytest.raises(ValueError, match="ages_years"):
        ChillerGrid.create_grid(
            rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0,
            ages_years=np.zeros(2),  # needs 4
        )


def test_create_grid_rejects_ages_too_long():
    with pytest.raises(ValueError, match="ages_years"):
        ChillerGrid.create_grid(
            rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0,
            ages_years=np.zeros(6),  # needs 4
        )


def test_create_grid_accepts_correct_ages_length():
    """Sanity check: correct length should not raise."""
    grid = ChillerGrid.create_grid(
        rows=2, cols=2, spacing_m=5.0, base_cop=4.0, max_cooling_kw=500.0,
        ages_years=np.array([1.0, 2.0, 3.0, 4.0]),
    )
    assert len(grid.ages_years) == 4


# ---------------------------------------------------------------------------
# Bug 2: cop_array in OptimizeResult has misleading values for inactive
#         chillers
#
# _evaluate_work computes the ramp factor for ALL chillers including inactive
# ones. For inactive chillers with time_since_start=0, ramp_fn(0)=0 gives
# cop ≈ 1e-6 (after clipping). Callers reading result.cop_array[~active_mask]
# get near-zero nonsense values instead of 0.0, which distorts any downstream
# efficiency analysis (e.g. mean COP across the array).
# ---------------------------------------------------------------------------

def test_cop_array_is_zero_for_inactive_chillers_on_first_call():
    """Inactive chillers must have cop_array == 0.0, not a ramp-penalised value."""
    sim = _base_builder().build()
    result = sim.optimize(time_hours=0.0)
    inactive = ~result.active_mask
    assert inactive.any(), "test requires at least one inactive chiller"
    np.testing.assert_array_equal(result.cop_array[inactive], 0.0)


def test_cop_array_is_zero_for_inactive_chillers_after_stream():
    """Same invariant must hold for every step produced by stream()."""
    sim = _base_builder().build()
    for step in sim.stream(duration_hours=4.0, time_step_hours=1.0):
        inactive = ~step.active_mask
        if inactive.any():
            np.testing.assert_array_equal(
                step.cop_array[inactive], 0.0,
                err_msg=f"Non-zero COP for inactive chillers at t={step.time_hours}",
            )


def test_cop_array_is_zero_for_inactive_chillers_with_initial_state():
    """Inactive-chiller COP must be zero even when using a warm-start initial state."""
    sim = _base_builder().build()
    state = InitialState(
        active_mask=np.array([True, False, True, False]),
        time_since_start_hours=np.array([2.0, 0.0, 2.0, 0.0]),
    )
    result = sim.optimize(time_hours=5.0)
    # Force fixed state via stream with initial_state
    steps = list(
        sim.stream(duration_hours=1.0, time_step_hours=1.0, initial_state=state)
    )
    for step in steps:
        inactive = ~step.active_mask
        if inactive.any():
            np.testing.assert_array_equal(step.cop_array[inactive], 0.0)


# ---------------------------------------------------------------------------
# Bug 3: with_wind_fn does not clear the previously set static _wind
#
# The PR 7 fix correctly made with_wind() clear _wind_fn. The symmetric case
# was missed: with_wind_fn() does NOT clear _wind. When both are set,
# build() uses `self._wind or WindConditions(*self._wind_fn(0.0))`, so the
# static wind wins for the initial interaction matrix even though the caller
# intended the fn to be the sole source of wind.
# ---------------------------------------------------------------------------

def test_with_wind_fn_clears_prior_static_wind_from_builder():
    """After with_wind_fn(), the builder should have _wind = None."""
    builder = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_wind_fn(lambda t: (5.0, 90.0))
    )
    assert builder._wind is None


def test_wind_fn_determines_initial_interaction_matrix_not_prior_static():
    """
    When with_wind_fn overrides a prior with_wind, the initial interaction matrix
    must be computed from fn(0), not from the stale static WindConditions.
    """
    north_wind_fn = lambda t: (3.0, 90.0)  # always north (90°)

    sim = (
        Simulator()
        .with_grid(rows=1, cols=2, spacing_m=20.0, base_cop=5.0, max_cooling_kw=500.0, ages_years=np.zeros(2))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)   # east — set first
        .with_wind_fn(north_wind_fn)                    # north — should win
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 200.0)
        .build()
    )
    # The simulator's initial wind must reflect fn(0) = north, not static east.
    assert sim._current_wind.angle_deg == pytest.approx(90.0)


def test_with_ambient_temp_fn_clears_prior_static_ambient():
    """Symmetric check: with_ambient_temp_fn() should clear _ambient_temp_k."""
    builder = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_ambient_temp_fn(lambda t: 300.0)
    )
    assert builder._ambient_temp_k is None
