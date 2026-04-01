import numpy as np
import pytest

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions
from chiller_sim.simulation.results import OptimizeResult, SimulationResult
from chiller_sim.visualization.animation import (
    _get_color_values,
    _resolve_ambient_temp,
    _resolve_wind,
)


def _make_result(n_chillers: int = 4, n_steps: int = 3) -> SimulationResult:
    """Create a minimal SimulationResult for testing."""
    steps = []
    for i in range(n_steps):
        steps.append(
            OptimizeResult(
                time_hours=float(i),
                load_kw=100.0,
                active_mask=np.ones(n_chillers, dtype=bool),
                total_work_kw=80.0,
                baseline_work_kw=100.0,
                savings_fraction=0.2,
                cop_array=np.full(n_chillers, 4.0),
                temp_rise_array=np.full(n_chillers, 1.5),
            )
        )
    return SimulationResult(steps=steps)


def _make_layout(n_chillers: int = 4) -> ChillerLayout:
    """Create a 2x2 layout for testing."""
    return ChillerLayout.create_grid(
        rows=2, cols=2, spacing_m=10.0,
        base_cop=5.5, max_cooling_kw=500.0, seed=0,
    )


def test_invalid_color_by_raises():
    result = _make_result()
    layout = _make_layout()
    from chiller_sim.visualization import animate_simulation

    with pytest.raises(ValueError, match="color_by"):
        animate_simulation(result, layout, color_by="invalid")


def test_get_color_values_cop():
    step = _make_result(n_chillers=4, n_steps=1).steps[0]
    layout = _make_layout()
    values = _get_color_values(step, layout, "cop")
    np.testing.assert_array_equal(values, step.cop_array)


def test_get_color_values_intake():
    step = _make_result(n_chillers=4, n_steps=1).steps[0]
    layout = _make_layout()
    values = _get_color_values(step, layout, "intake")
    np.testing.assert_array_equal(values, step.temp_rise_array)


def test_get_color_values_capacity():
    step = _make_result(n_chillers=4, n_steps=1).steps[0]
    layout = _make_layout()
    values = _get_color_values(step, layout, "capacity")
    assert values.shape == (4,)
    assert all(v > 0 for v in values)


def test_get_color_values_load():
    step = _make_result(n_chillers=4, n_steps=1).steps[0]
    layout = _make_layout()
    values = _get_color_values(step, layout, "load")
    assert values.shape == (4,)


def test_resolve_wind_static():
    wc = WindConditions(speed_m_per_s=3.0, angle_deg=45.0)
    resolved = _resolve_wind(wc, time_hours=1.0)
    assert resolved.speed_m_per_s == 3.0
    assert resolved.angle_deg == 45.0


def test_resolve_wind_callable():
    def wind_fn(t: float) -> tuple[float, float]:
        return (t * 2.0, 90.0)

    resolved = _resolve_wind(wind_fn, time_hours=5.0)
    assert resolved.speed_m_per_s == 10.0
    assert resolved.angle_deg == 90.0


def test_resolve_wind_none():
    assert _resolve_wind(None, time_hours=0.0) is None


def test_resolve_ambient_temp_callable():
    def temp_fn(t: float) -> float:
        return 300.0  # Kelvin

    temp_c = _resolve_ambient_temp(temp_fn, time_hours=0.0, step_index=0)
    assert pytest.approx(temp_c) == 26.85


def test_resolve_ambient_temp_array():
    temps_k = np.array([295.0, 300.0, 305.0])
    temp_c = _resolve_ambient_temp(temps_k, time_hours=0.0, step_index=1)
    assert pytest.approx(temp_c) == 26.85


def test_resolve_ambient_temp_none():
    assert _resolve_ambient_temp(None, time_hours=0.0, step_index=0) is None
