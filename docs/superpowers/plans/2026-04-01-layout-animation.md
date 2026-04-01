# Layout Animation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `chiller_sim.visualization.animate_simulation()` to render completed simulations as animated GIF/MP4 with configurable chiller coloring and info overlays.

**Architecture:** Single public function in a new `chiller_sim/visualization/` module. matplotlib is an optional dependency imported at call time. Each animation frame draws chiller squares colored by a user-selected property (COP, capacity, load, intake), plus wind vane and info text overlays.

**Tech Stack:** Python, matplotlib (optional), NumPy, Pillow (for GIF via PillowWriter)

**Key facts discovered during exploration:**
- `WindFn.__call__` returns `tuple[float, float]` (speed, angle_deg) — NOT a `WindConditions` object. The animation must construct `WindConditions` from the tuple when given a `WindFn`.
- `AmbientTempFn` returns temperature in **Kelvin**. Display must convert to °C (subtract 273.15).
- `DegradationFn` signature: `(age_years: float) -> float` returns multiplier in (0, 1].
- Existing tests live in `tests/test_behavior.py` and use a `_base_sim()` helper.

---

### Task 1: Add `viz` optional dependency to pyproject.toml

**Files:**
- Modify: `pyproject.toml:32-43`

- [ ] **Step 1: Add the viz extra**

In `pyproject.toml`, add the `viz` extra after the existing `docs` section:

```toml
viz = [
    "matplotlib>=3.7.0",
]
```

- [ ] **Step 2: Install with viz extra**

Run: `pip install -e ".[dev,viz]"`
Expected: matplotlib installs successfully.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: add optional viz extra for matplotlib"
```

---

### Task 2: Create visualization module skeleton with import guard

**Files:**
- Create: `src/chiller_sim/visualization/__init__.py`
- Create: `src/chiller_sim/visualization/animation.py`
- Modify: `src/chiller_sim/__init__.py`

- [ ] **Step 1: Write the test for import guard**

Create `tests/test_visualization.py`:

```python
from unittest.mock import patch

import pytest


def test_animate_simulation_import_error_without_matplotlib():
    with patch.dict("sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}):
        # Force reimport to trigger the guard
        import importlib
        import chiller_sim.visualization.animation as mod

        importlib.reload(mod)
        with pytest.raises(ImportError, match="pip install"):
            mod.animate_simulation.__wrapped__()
```

Actually — this is tricky to test via mock. A simpler approach: test that a `ValueError` is raised for invalid `color_by`, which exercises the function entry point.

Create `tests/test_visualization.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_visualization.py::test_invalid_color_by_raises -v`
Expected: FAIL — module does not exist yet.

- [ ] **Step 3: Create the module skeleton**

Create `src/chiller_sim/visualization/__init__.py`:

```python
from chiller_sim.visualization.animation import animate_simulation

__all__ = ["animate_simulation"]
```

Create `src/chiller_sim/visualization/animation.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.simulation.results import SimulationResult

_VALID_COLOR_BY = ("cop", "capacity", "load", "intake")


def animate_simulation(
    result: SimulationResult,
    layout: ChillerLayout,
    wind: Union[WindConditions, WindFn, None] = None,
    color_by: str = "cop",
    output_path: str = "simulation.gif",
    fps: int = 4,
    figsize: tuple[float, float] = (10, 6),
    ambient_temp: Union[AmbientTempFn, ArrayLike, None] = None,
) -> Path:
    """Render a simulation as an animated GIF or MP4.

    Parameters
    ----------
    result : SimulationResult
        Completed simulation (must contain at least one step).
    layout : ChillerLayout
        Chiller positions and metadata.
    wind : WindConditions, WindFn, or None
        Static wind or callable ``(time_hours) -> (speed, angle_deg)``.
        None hides the wind vane.
    color_by : str
        Property used to color chiller squares.
        One of ``"cop"``, ``"capacity"``, ``"load"``, ``"intake"``.
    output_path : str
        Destination file. Format inferred from extension (``.gif`` or ``.mp4``).
    fps : int
        Frames per second.
    figsize : tuple of float
        Figure size in inches.
    ambient_temp : AmbientTempFn, array-like, or None
        Callable ``(time_hours) -> float`` (Kelvin) or pre-computed array.
        None omits ambient temperature from the overlay text.

    Returns
    -------
    Path
        Absolute path to the saved animation file.
    """
    if color_by not in _VALID_COLOR_BY:
        raise ValueError(
            f"color_by must be one of {_VALID_COLOR_BY}, got {color_by!r}"
        )

    raise NotImplementedError("Animation rendering not yet implemented")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_visualization.py::test_invalid_color_by_raises -v`
Expected: PASS

- [ ] **Step 5: Add re-export from top-level `__init__.py`**

Modify `src/chiller_sim/__init__.py` to add the import:

```python
from chiller_sim.simulation.builder import SimulatorBuilder as Simulator
from chiller_sim.simulation.results import InitialState, OptimizeResult, SimulationResult
from chiller_sim.visualization import animate_simulation

__all__ = ["Simulator", "OptimizeResult", "SimulationResult", "InitialState", "animate_simulation"]
```

- [ ] **Step 6: Commit**

```bash
git add src/chiller_sim/visualization/ src/chiller_sim/__init__.py tests/test_visualization.py pyproject.toml
git commit -m "feat: add visualization module skeleton with animate_simulation stub"
```

---

### Task 3: Implement per-frame data extraction helpers

**Files:**
- Modify: `src/chiller_sim/visualization/animation.py`
- Modify: `tests/test_visualization.py`

These helper functions compute the color values and overlay data for each frame, keeping the main animation function clean.

- [ ] **Step 1: Write tests for data extraction**

Add to `tests/test_visualization.py`:

```python
from chiller_sim.visualization.animation import (
    _get_color_values,
    _resolve_wind,
    _resolve_ambient_temp,
)
from chiller_sim.layout.wind import WindConditions


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_visualization.py -k "get_color or resolve" -v`
Expected: FAIL — functions don't exist yet.

- [ ] **Step 3: Implement the helpers**

Add to `src/chiller_sim/visualization/animation.py`, above the `animate_simulation` function:

```python
from chiller_sim.physics.degradation import default_capacity_degradation_fn
from chiller_sim.simulation.results import OptimizeResult


def _get_color_values(
    step: OptimizeResult,
    layout: ChillerLayout,
    color_by: str,
) -> NDArray[np.float64]:
    """Extract per-chiller values for the selected color-by property."""
    if color_by == "cop":
        return step.cop_array
    elif color_by == "intake":
        return step.temp_rise_array
    elif color_by == "capacity":
        deg_fn = default_capacity_degradation_fn(years_to_80_pct=15.0)
        return np.array([
            layout.max_cooling_kw * deg_fn(age)
            for age in layout.ages_years
        ])
    elif color_by == "load":
        n_active = step.active_mask.sum()
        per_chiller = step.load_kw / max(n_active, 1)
        values = np.zeros(layout.num_chillers)
        values[step.active_mask] = per_chiller
        return values
    raise ValueError(f"Unknown color_by: {color_by!r}")


def _resolve_wind(
    wind: Union[WindConditions, WindFn, None],
    time_hours: float,
) -> WindConditions | None:
    """Resolve wind to a WindConditions snapshot or None."""
    if wind is None:
        return None
    if isinstance(wind, WindConditions):
        return wind
    speed, angle = wind(time_hours)
    return WindConditions(speed_m_per_s=speed, angle_deg=angle)


def _resolve_ambient_temp(
    ambient_temp: Union[AmbientTempFn, ArrayLike, None],
    time_hours: float,
    step_index: int,
) -> float | None:
    """Resolve ambient temperature to Celsius or None."""
    if ambient_temp is None:
        return None
    if callable(ambient_temp):
        return ambient_temp(time_hours) - 273.15
    arr = np.asarray(ambient_temp)
    return float(arr[step_index]) - 273.15
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_visualization.py -k "get_color or resolve" -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/visualization/animation.py tests/test_visualization.py
git commit -m "feat: add data extraction helpers for animation frames"
```

---

### Task 4: Implement the frame-drawing function

**Files:**
- Modify: `src/chiller_sim/visualization/animation.py`
- Modify: `tests/test_visualization.py`

This function draws a single frame onto a matplotlib figure. It is called by
`FuncAnimation` for each timestep.

- [ ] **Step 1: Write the test**

Add to `tests/test_visualization.py`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from chiller_sim.visualization.animation import _draw_frame


def test_draw_frame_creates_patches():
    fig, ax = plt.subplots()
    result = _make_result(n_chillers=4, n_steps=1)
    layout = _make_layout()
    step = result.steps[0]

    _draw_frame(
        ax=ax,
        fig=fig,
        step=step,
        layout=layout,
        color_by="cop",
        square_size=3.0,
        vmin=2.0,
        vmax=6.0,
        wind_conditions=None,
        ambient_temp_c=None,
    )

    # Should have 4 Rectangle patches (one per chiller)
    from matplotlib.patches import Rectangle
    rects = [p for p in ax.patches if isinstance(p, Rectangle)]
    assert len(rects) == 4
    plt.close(fig)


def test_draw_frame_with_overlays():
    fig, ax = plt.subplots()
    result = _make_result(n_chillers=4, n_steps=1)
    layout = _make_layout()
    step = result.steps[0]
    wc = WindConditions(speed_m_per_s=3.0, angle_deg=45.0)

    _draw_frame(
        ax=ax,
        fig=fig,
        step=step,
        layout=layout,
        color_by="cop",
        square_size=3.0,
        vmin=2.0,
        vmax=6.0,
        wind_conditions=wc,
        ambient_temp_c=25.0,
    )

    from matplotlib.patches import Rectangle
    rects = [p for p in ax.patches if isinstance(p, Rectangle)]
    assert len(rects) == 4
    plt.close(fig)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_visualization.py -k "draw_frame" -v`
Expected: FAIL — `_draw_frame` does not exist.

- [ ] **Step 3: Implement `_draw_frame`**

Add to `src/chiller_sim/visualization/animation.py`:

```python
_COLORMAP_MAP = {
    "cop": "RdYlGn",
    "capacity": "Blues",
    "load": "OrRd",
    "intake": "YlOrRd",
}

_LABEL_MAP = {
    "cop": "COP",
    "capacity": "Capacity (kW)",
    "load": "Load (kW)",
    "intake": "Intake Rise (°C)",
}


def _draw_frame(
    ax: object,
    fig: object,
    step: OptimizeResult,
    layout: ChillerLayout,
    color_by: str,
    square_size: float,
    vmin: float,
    vmax: float,
    wind_conditions: WindConditions | None,
    ambient_temp_c: float | None,
) -> None:
    """Draw a single animation frame onto *ax*."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from matplotlib.colors import Normalize
        import matplotlib.cm as cm
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install chiller-sim[viz]"
        )

    ax.clear()

    cmap = cm.get_cmap(_COLORMAP_MAP[color_by])
    norm = Normalize(vmin=vmin, vmax=vmax)
    color_values = _get_color_values(step, layout, color_by)
    half = square_size / 2.0

    for i in range(layout.num_chillers):
        x, y = layout.positions_m[i]
        if step.active_mask[i]:
            color = cmap(norm(color_values[i]))
            alpha = 1.0
        else:
            color = "0.75"
            alpha = 0.3

        rect = Rectangle(
            (x - half, y - half), square_size, square_size,
            facecolor=color, edgecolor="black", linewidth=0.8, alpha=alpha,
        )
        ax.add_patch(rect)

    # Axis limits with padding
    xs = layout.positions_m[:, 0]
    ys = layout.positions_m[:, 1]
    pad = square_size * 2
    ax.set_xlim(xs.min() - pad, xs.max() + pad)
    ax.set_ylim(ys.min() - pad, ys.max() + pad)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"t = {step.time_hours:.1f} h")

    # Wind vane in top-left
    if wind_conditions is not None:
        uv = wind_conditions.unit_vector
        # Place arrow in axes coords via a small inset
        ax_x = xs.min() - pad * 0.5
        ax_y = ys.max() + pad * 0.5
        arrow_len = square_size * 1.5
        ax.annotate(
            "",
            xy=(ax_x + uv[0] * arrow_len, ax_y + uv[1] * arrow_len),
            xytext=(ax_x, ax_y),
            arrowprops=dict(arrowstyle="->", lw=2, color="steelblue"),
        )
        ax.text(
            ax_x, ax_y + arrow_len * 1.2,
            f"{wind_conditions.speed_m_per_s:.1f} m/s",
            fontsize=9, ha="center", color="steelblue", fontweight="bold",
        )

    # Info text on the right
    info_lines = [f"Load: {step.load_kw:.0f} kW"]
    if ambient_temp_c is not None:
        info_lines.append(f"Ambient: {ambient_temp_c:.1f} °C")
    info_lines.append(f"Savings: {step.savings_fraction * 100:.1f}%")

    info_text = "\n".join(info_lines)
    ax.text(
        1.02, 0.5, info_text,
        transform=ax.transAxes, fontsize=10,
        verticalalignment="center", fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.8),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_visualization.py -k "draw_frame" -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/visualization/animation.py tests/test_visualization.py
git commit -m "feat: implement _draw_frame for single animation frames"
```

---

### Task 5: Implement `animate_simulation` main function

**Files:**
- Modify: `src/chiller_sim/visualization/animation.py`
- Modify: `tests/test_visualization.py`

Wire the helpers and `_draw_frame` into a `FuncAnimation` that saves to GIF or MP4.

- [ ] **Step 1: Write integration test**

Add to `tests/test_visualization.py`:

```python
import tempfile
from pathlib import Path
from chiller_sim.visualization import animate_simulation


def test_animate_simulation_creates_gif():
    result = _make_result(n_chillers=4, n_steps=3)
    layout = _make_layout()

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.gif"
        returned = animate_simulation(
            result, layout, output_path=str(out), fps=2,
        )
        assert out.exists()
        assert out.stat().st_size > 0
        assert returned == out.resolve()


def test_animate_simulation_each_color_by():
    result = _make_result(n_chillers=4, n_steps=2)
    layout = _make_layout()

    for cb in ("cop", "capacity", "load", "intake"):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / f"test_{cb}.gif"
            animate_simulation(result, layout, color_by=cb, output_path=str(out))
            assert out.exists()


def test_animate_simulation_with_wind_and_ambient():
    result = _make_result(n_chillers=4, n_steps=3)
    layout = _make_layout()
    wc = WindConditions(speed_m_per_s=3.0, angle_deg=45.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.gif"
        animate_simulation(
            result, layout, wind=wc,
            ambient_temp=np.array([298.0, 299.0, 300.0]),
            output_path=str(out),
        )
        assert out.exists()


def test_animate_simulation_with_wind_fn():
    result = _make_result(n_chillers=4, n_steps=2)
    layout = _make_layout()

    def wind_fn(t: float) -> tuple[float, float]:
        return (3.0, t * 45.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.gif"
        animate_simulation(
            result, layout, wind=wind_fn, output_path=str(out),
        )
        assert out.exists()


def test_animate_simulation_with_ambient_fn():
    result = _make_result(n_chillers=4, n_steps=2)
    layout = _make_layout()

    def temp_fn(t: float) -> float:
        return 298.0 + t

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.gif"
        animate_simulation(
            result, layout, ambient_temp=temp_fn, output_path=str(out),
        )
        assert out.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_visualization.py -k "animate_simulation" -v`
Expected: FAIL — function raises `NotImplementedError`.

- [ ] **Step 3: Implement `animate_simulation`**

Replace the body of `animate_simulation` in `src/chiller_sim/visualization/animation.py` (keep signature and docstring, replace from the `if color_by` check onward):

```python
    if color_by not in _VALID_COLOR_BY:
        raise ValueError(
            f"color_by must be one of {_VALID_COLOR_BY}, got {color_by!r}"
        )

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install chiller-sim[viz]"
        )

    # Compute global color range for consistent colorbar across frames
    all_values = np.array([
        _get_color_values(step, layout, color_by) for step in result.steps
    ])
    vmin = float(np.nanmin(all_values))
    vmax = float(np.nanmax(all_values))
    if vmin == vmax:
        vmax = vmin + 1.0

    # Compute square size from minimum inter-chiller distance
    from scipy.spatial.distance import pdist
    dists = pdist(layout.positions_m)
    square_size = float(dists.min()) * 0.7 if len(dists) > 0 else 5.0

    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(right=0.78)

    # Add colorbar
    cmap = cm.get_cmap(_COLORMAP_MAP[color_by])
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.15)
    cbar.set_label(_LABEL_MAP[color_by])

    def update(frame_idx: int) -> None:
        step = result.steps[frame_idx]
        wc = _resolve_wind(wind, step.time_hours)
        temp_c = _resolve_ambient_temp(ambient_temp, step.time_hours, frame_idx)
        _draw_frame(
            ax=ax, fig=fig, step=step, layout=layout,
            color_by=color_by, square_size=square_size,
            vmin=vmin, vmax=vmax,
            wind_conditions=wc, ambient_temp_c=temp_c,
        )

    anim = FuncAnimation(fig, update, frames=len(result.steps), interval=1000 // fps)

    out = Path(output_path)
    if out.suffix == ".mp4":
        from matplotlib.animation import FFMpegWriter
        anim.save(str(out), writer=FFMpegWriter(fps=fps))
    else:
        anim.save(str(out), writer=PillowWriter(fps=fps))

    plt.close(fig)
    return out.resolve()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_visualization.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/visualization/animation.py tests/test_visualization.py
git commit -m "feat: implement animate_simulation with GIF/MP4 output"
```

---

### Task 6: Remove scipy dependency — use NumPy for pairwise distance

The implementation above uses `scipy.spatial.distance.pdist`, which adds
an unnecessary dependency. Replace it with a pure NumPy calculation.

**Files:**
- Modify: `src/chiller_sim/visualization/animation.py`

- [ ] **Step 1: Replace pdist with NumPy**

In `animate_simulation`, replace:

```python
    from scipy.spatial.distance import pdist
    dists = pdist(layout.positions_m)
    square_size = float(dists.min()) * 0.7 if len(dists) > 0 else 5.0
```

With:

```python
    if layout.num_chillers > 1:
        diff = layout.positions_m[:, np.newaxis, :] - layout.positions_m[np.newaxis, :, :]
        dist_matrix = np.sqrt((diff ** 2).sum(axis=-1))
        np.fill_diagonal(dist_matrix, np.inf)
        square_size = float(dist_matrix.min()) * 0.7
    else:
        square_size = 5.0
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/test_visualization.py -v`
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add src/chiller_sim/visualization/animation.py
git commit -m "refactor: replace scipy pdist with NumPy pairwise distance"
```

---

### Task 7: Lint, type-check, and final validation

**Files:**
- Possibly modify any files with lint issues

- [ ] **Step 1: Run ruff check**

Run: `ruff check src/chiller_sim/visualization/ tests/test_visualization.py`
Expected: No errors. Fix any that appear.

- [ ] **Step 2: Run ruff format**

Run: `ruff format src/chiller_sim/visualization/ tests/test_visualization.py`

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: All tests pass, including existing tests.

- [ ] **Step 4: Commit any fixes**

```bash
git add -u
git commit -m "style: fix lint and formatting in visualization module"
```
