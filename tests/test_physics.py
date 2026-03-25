import math
from chiller_sim.physics.cop import default_cop_fn
from chiller_sim.physics.degradation import default_degradation_fn
from chiller_sim.physics.ramp import default_ramp_fn


def test_default_cop_no_thermal_impact():
    cop_fn = default_cop_fn(alpha=0.7)
    # No thermal rise: returns base_cop unchanged
    assert cop_fn(5.0, 0.0, 298.15) == 5.0


def test_default_cop_with_thermal_rise():
    cop_fn = default_cop_fn(alpha=0.7)
    # temp_rise = 1.0: COP = 5.0 / (1 + 0.7 * 1.0) = 5.0 / 1.7
    result = cop_fn(5.0, 1.0, 298.15)
    assert abs(result - 5.0 / 1.7) < 1e-9


def test_default_cop_ignores_ambient_temp():
    cop_fn = default_cop_fn(alpha=0.7)
    # Different ambient temps, same result
    r1 = cop_fn(5.0, 0.5, 280.0)
    r2 = cop_fn(5.0, 0.5, 320.0)
    assert r1 == r2


def test_default_cop_decreases_with_thermal_rise():
    cop_fn = default_cop_fn(alpha=0.7)
    r_low = cop_fn(5.0, 0.5, 298.15)
    r_high = cop_fn(5.0, 2.0, 298.15)
    assert r_low > r_high


def test_default_degradation_new_chiller():
    # Age 0: factor = 1.0
    assert default_degradation_fn(0.0) == 1.0


def test_default_degradation_one_year():
    # Age 1: factor = 0.8 (by design)
    assert abs(default_degradation_fn(1.0) - 0.8) < 1e-9


def test_default_degradation_monotone():
    factors = [default_degradation_fn(a) for a in [0.0, 1.0, 5.0, 10.0]]
    assert all(factors[i] > factors[i + 1] for i in range(len(factors) - 1))


def test_default_ramp_at_zero():
    # Just started: factor = 0.0
    assert default_ramp_fn(0.0) == 0.0


def test_default_ramp_at_startup_time():
    # At startup_time_hours (0.25): factor = 1.0
    assert default_ramp_fn(0.25) == 1.0


def test_default_ramp_midpoint():
    # At half startup time: factor = 0.5
    assert abs(default_ramp_fn(0.125) - 0.5) < 1e-9


def test_default_ramp_saturates_above_startup_time():
    # Beyond startup time: stays at 1.0
    assert default_ramp_fn(1.0) == 1.0
    assert default_ramp_fn(100.0) == 1.0


def test_default_ramp_steady_state_at_inf():
    assert default_ramp_fn(float('inf')) == 1.0


import numpy as np
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel
from chiller_sim.layout.wind import WindConditions


def _east_wind() -> WindConditions:
    return WindConditions(speed_m_per_s=3.0, angle_deg=0.0)


def test_interaction_matrix_shape():
    positions = np.array([[0.0, 0.0], [10.0, 0.0], [20.0, 0.0]])
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    assert A.shape == (3, 3)


def test_interaction_matrix_zero_diagonal():
    positions = np.array([[0.0, 0.0], [10.0, 0.0], [20.0, 0.0]])
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    np.testing.assert_array_equal(np.diag(A), 0.0)


def test_upwind_chiller_has_no_effect_on_downwind():
    # With east wind: chiller at x=20 is downwind of x=0
    # A[k,m] = influence of k on m; chiller 2 (x=20) cannot influence chiller 0 (x=0)
    positions = np.array([[0.0, 0.0], [20.0, 0.0]])
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    assert A[1, 0] == 0.0   # downwind chiller (1) does not affect upwind (0)
    assert A[0, 1] > 0.0    # upwind chiller (0) affects downwind (1)


def test_thermal_influence_decreases_with_distance():
    positions = np.array([[0.0, 0.0], [10.0, 0.0], [30.0, 0.0]])
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    # Chiller 0 should affect chiller 1 (10m away) more than chiller 2 (30m away)
    assert A[0, 1] > A[0, 2]


def test_lateral_offset_reduces_influence():
    # Chiller directly downwind vs. chiller offset laterally
    positions = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 5.0]])
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    # Chiller 1 (directly downwind) should receive more heat than chiller 2 (offset)
    assert A[0, 1] > A[0, 2]


def test_no_nan_or_inf_in_matrix():
    rng = np.random.default_rng(0)
    positions = rng.uniform(0, 50, size=(10, 2))
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    A = model.compute_interaction_matrix(positions, _east_wind())
    assert not np.any(np.isnan(A))
    assert not np.any(np.isinf(A))
