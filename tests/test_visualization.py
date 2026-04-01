import numpy as np
import pytest

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.simulation.results import OptimizeResult, SimulationResult


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
