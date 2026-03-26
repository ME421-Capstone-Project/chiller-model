import numpy as np
import pytest
from chiller_sim.simulation.builder import SimulatorBuilder


def _base_builder() -> SimulatorBuilder:
    return (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
    )


def test_build_succeeds_with_required_fields():
    sim = _base_builder().build()
    assert sim is not None


def test_build_raises_without_load_fn():
    builder = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
    )
    with pytest.raises(ValueError, match="load_fn"):
        builder.build()


def test_build_raises_without_ambient_temp():
    builder = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_load_fn(lambda t: 400.0)
    )
    with pytest.raises(ValueError, match="ambient_temp"):
        builder.build()


def test_build_raises_without_grid():
    builder = (
        SimulatorBuilder()
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
    )
    with pytest.raises(ValueError, match="grid"):
        builder.build()


def test_ambient_temp_fn_satisfies_ambient_requirement():
    # ambient_temp_fn counts as satisfying the ambient_temp requirement
    sim = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, max_cooling_kw=500.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp_fn(lambda t: 298.15)
        .with_load_fn(lambda t: 400.0)
        .build()
    )
    assert sim is not None


def test_seed_preserved_on_rebuild():
    sim1 = _base_builder().build()
    sim2 = sim1.with_wind(speed_m_per_s=5.0, angle_deg=45.0).build()
    # Ages should be the same across rebuilds
    np.testing.assert_array_equal(sim1._grid.ages_years, sim2._grid.ages_years)


def test_switching_threshold_defaults_to_zero():
    sim = _base_builder().build()
    assert sim._min_savings_kw == 0.0


def test_dispersion_defaults_to_1_2():
    sim = _base_builder().build()
    assert sim._model.dispersion_coeff == 1.2
