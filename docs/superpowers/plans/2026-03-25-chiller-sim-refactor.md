# chiller-sim Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing multi-layer `src/` package with a flat, builder-friendly `src/chiller_sim/` package featuring pluggable physics functions, decoupled wind/ambient-temp inputs, and a state-aware time-varying optimizer.

**Architecture:** `Simulator()` returns a `SimulatorBuilder` that chains `.with_*()` configuration methods and produces an immutable `Simulator` on `.build()`. The `Simulator` precomputes the N×N Gaussian plume interaction matrix once and reuses it. Internal state (active chiller set, per-chiller startup clocks) persists across `optimize()` calls; `stream()`/`simulate()` reset state at the start of each run. All physics (COP, degradation, ramp, load, wind, ambient temp) are injectable callables conforming to typed Protocols.

**Tech Stack:** Python 3.10+, NumPy (vectorized matrix math), pytest (TDD), ruff (linting/formatting). Pydantic is removed — validation moves into `SimulatorBuilder.__build()`.

**Spec:** `docs/superpowers/specs/2026-03-25-chiller-sim-refactor-design.md`

---

## File Map

### Created

```
src/chiller_sim/__init__.py                   # public re-exports
src/chiller_sim/layout/__init__.py
src/chiller_sim/layout/grid.py                # ChillerGrid frozen dataclass
src/chiller_sim/layout/wind.py                # WindConditions frozen dataclass + WindFn Protocol
src/chiller_sim/physics/__init__.py
src/chiller_sim/physics/gaussian_plume.py     # GaussianPlumeModel
src/chiller_sim/physics/cop.py                # CopFn Protocol + default_cop_fn factory
src/chiller_sim/physics/degradation.py        # DegradationFn Protocol + default_degradation_fn
src/chiller_sim/physics/ramp.py               # RampFn Protocol + default_ramp_fn
src/chiller_sim/physics/load.py               # LoadFn Protocol
src/chiller_sim/physics/ambient_temp.py       # AmbientTempFn Protocol
src/chiller_sim/simulation/__init__.py
src/chiller_sim/simulation/results.py         # OptimizeResult, SimulationResult, InitialState
src/chiller_sim/simulation/builder.py         # SimulatorBuilder
src/chiller_sim/simulation/simulator.py       # Simulator
tests/test_types.py                           # result types and layout types
tests/test_physics.py                         # default physics function behaviors
tests/test_builder.py                         # builder validation errors
tests/test_behavior.py                        # all behavior tests through Simulator API
```

### Modified

```
pyproject.toml                                # update package name/description
```

### Deleted (Task 10)

```
src/__init__.py
src/core/
src/components/
src/models/
src/simulation/
tests/test_core/
tests/test_components/
tests/test_models/
tests/test_simulation/
verification/
scripts/  (outdated examples)
```

---

## Task 1: Package Scaffold

**Files:**
- Create: `src/chiller_sim/__init__.py` and all sub-package `__init__.py` files
- Modify: `pyproject.toml`

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p src/chiller_sim/layout
mkdir -p src/chiller_sim/physics
mkdir -p src/chiller_sim/simulation
touch src/chiller_sim/__init__.py
touch src/chiller_sim/layout/__init__.py
touch src/chiller_sim/physics/__init__.py
touch src/chiller_sim/simulation/__init__.py
```

- [ ] **Step 2: Update `pyproject.toml` description**

In `pyproject.toml`, change `description` to:
```toml
description = "Builder-friendly simulation package for chiller array thermal optimization"
```

Leave `name = "chiller-sim"` and `where = ["src"]` unchanged — setuptools will discover both the old and new packages during transition.

- [ ] **Step 3: Verify the new package is importable**

```bash
pip install -e ".[dev]"
python -c "import chiller_sim; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/chiller_sim/ pyproject.toml
git commit -m "feat: scaffold chiller_sim package structure"
```

---

## Task 2: Result Types

**Files:**
- Create: `src/chiller_sim/simulation/results.py`
- Create: `tests/test_types.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_types.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_types.py -v
```

Expected: `ImportError` — `results.py` doesn't exist yet.

- [ ] **Step 3: Implement `results.py`**

Create `src/chiller_sim/simulation/results.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class OptimizeResult:
    time_hours: float
    load_kw: float
    active_mask: NDArray[np.bool_]
    total_work_kw: float
    baseline_work_kw: float
    savings_fraction: float
    cop_array: NDArray[np.float64]
    temp_rise_array: NDArray[np.float64]


@dataclass
class SimulationResult:
    steps: list[OptimizeResult]

    @property
    def schedule(self) -> NDArray[np.bool_]:
        return np.array([s.active_mask for s in self.steps])

    @property
    def total_work_kw(self) -> NDArray[np.float64]:
        return np.array([s.total_work_kw for s in self.steps])

    @property
    def loads_kw(self) -> NDArray[np.float64]:
        return np.array([s.load_kw for s in self.steps])

    @property
    def savings_fraction(self) -> NDArray[np.float64]:
        return np.array([s.savings_fraction for s in self.steps])

    @property
    def cop_arrays(self) -> NDArray[np.float64]:
        return np.array([s.cop_array for s in self.steps])


@dataclass(frozen=True)
class InitialState:
    active_mask: NDArray[np.bool_]
    time_since_start_hours: NDArray[np.float64]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_types.py -v
```

Expected: all 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/simulation/results.py tests/test_types.py
git commit -m "feat: add OptimizeResult, SimulationResult, InitialState types"
```

---

## Task 3: Layout Types

**Files:**
- Create: `src/chiller_sim/layout/grid.py`
- Create: `src/chiller_sim/layout/wind.py`
- Extend: `tests/test_types.py`

- [ ] **Step 1: Write failing tests — append to `tests/test_types.py`**

```python
from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.layout.wind import WindConditions


def test_chiller_grid_from_regular_grid():
    grid = ChillerGrid.create_grid(rows=2, cols=3, spacing_m=10.0, base_cop=5.0, alpha=0.7)
    assert grid.positions_m.shape == (6, 2)
    assert grid.base_cop == 5.0
    assert grid.alpha == 0.7
    assert len(grid.ages_years) == 6


def test_chiller_grid_seed_reproducible():
    g1 = ChillerGrid.create_grid(rows=2, cols=2, spacing_m=5.0, base_cop=4.0, seed=42)
    g2 = ChillerGrid.create_grid(rows=2, cols=2, spacing_m=5.0, base_cop=4.0, seed=42)
    np.testing.assert_array_equal(g1.ages_years, g2.ages_years)


def test_chiller_grid_explicit_ages():
    ages = np.array([1.0, 2.0, 3.0, 4.0])
    grid = ChillerGrid.create_grid(rows=2, cols=2, spacing_m=5.0, base_cop=4.0, ages_years=ages)
    np.testing.assert_array_equal(grid.ages_years, ages)


def test_chiller_grid_num_chillers():
    grid = ChillerGrid.create_grid(rows=3, cols=4, spacing_m=10.0, base_cop=4.0)
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_types.py -v -k "grid or wind"
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `grid.py`**

Create `src/chiller_sim/layout/grid.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChillerGrid:
    positions_m: NDArray[np.float64]   # shape (n_chillers, 2)
    base_cop: float
    alpha: float
    ages_years: NDArray[np.float64]    # shape (n_chillers,)

    @property
    def num_chillers(self) -> int:
        return len(self.positions_m)

    @classmethod
    def create_grid(
        cls,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float,
        alpha: float = 0.7,
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
    ) -> ChillerGrid:
        xs = np.arange(cols) * spacing_m
        ys = np.arange(rows) * spacing_m
        xx, yy = np.meshgrid(xs, ys)
        positions = np.column_stack([xx.ravel(), yy.ravel()])

        n = rows * cols
        if ages_years is not None:
            resolved_ages = np.asarray(ages_years, dtype=np.float64)
        else:
            rng = np.random.default_rng(seed)
            resolved_ages = rng.uniform(0.0, 20.0, size=n)

        return cls(
            positions_m=positions,
            base_cop=base_cop,
            alpha=alpha,
            ages_years=resolved_ages,
        )
```

- [ ] **Step 4: Implement `wind.py`**

Create `src/chiller_sim/layout/wind.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class WindConditions:
    speed_m_per_s: float
    angle_deg: float  # CCW from east

    @property
    def unit_vector(self) -> NDArray[np.float64]:
        rad = np.deg2rad(self.angle_deg)
        return np.array([np.cos(rad), np.sin(rad)])

    @property
    def velocity_vector(self) -> NDArray[np.float64]:
        return self.speed_m_per_s * self.unit_vector


@runtime_checkable
class WindFn(Protocol):
    def __call__(self, time_hours: float) -> tuple[float, float]:
        """Return (speed_m_per_s, angle_deg) at the given time."""
        ...
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_types.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/chiller_sim/layout/ tests/test_types.py
git commit -m "feat: add ChillerGrid and WindConditions layout types"
```

---

## Task 4: Physics Protocols and Defaults

**Files:**
- Create: `src/chiller_sim/physics/cop.py`
- Create: `src/chiller_sim/physics/degradation.py`
- Create: `src/chiller_sim/physics/ramp.py`
- Create: `src/chiller_sim/physics/load.py`
- Create: `src/chiller_sim/physics/ambient_temp.py`
- Create: `tests/test_physics.py`

The default `cop_fn` is a factory (closure over `alpha`) because `alpha` comes from `ChillerGrid` but is not a parameter in the `CopFn` signature.

- [ ] **Step 1: Write failing tests**

Create `tests/test_physics.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_physics.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `cop.py`**

Create `src/chiller_sim/physics/cop.py`:

```python
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CopFn(Protocol):
    def __call__(self, base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        ...


def default_cop_fn(alpha: float) -> CopFn:
    """Factory returning the default COP function closed over alpha."""
    def _cop(base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
        return base_cop / (1.0 + alpha * temp_rise_k)
    return _cop
```

- [ ] **Step 4: Implement `degradation.py`**

Create `src/chiller_sim/physics/degradation.py`:

```python
from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

# Rate chosen so degradation_fn(1.0) == 0.8
_DECAY_RATE = -math.log(0.8)  # ≈ 0.2231


@runtime_checkable
class DegradationFn(Protocol):
    def __call__(self, age_years: float) -> float:
        ...


def default_degradation_fn(age_years: float) -> float:
    return math.exp(-_DECAY_RATE * age_years)
```

- [ ] **Step 5: Implement `ramp.py`**

Create `src/chiller_sim/physics/ramp.py`:

```python
from __future__ import annotations

from typing import Protocol, runtime_checkable

_STARTUP_TIME_HOURS = 0.25


@runtime_checkable
class RampFn(Protocol):
    def __call__(self, time_since_start_hours: float) -> float:
        ...


def default_ramp_fn(time_since_start_hours: float) -> float:
    return min(1.0, time_since_start_hours / _STARTUP_TIME_HOURS)
```

- [ ] **Step 6: Implement `load.py` and `ambient_temp.py`**

Create `src/chiller_sim/physics/load.py`:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class LoadFn(Protocol):
    def __call__(self, time_hours: float) -> float:
        ...
```

Create `src/chiller_sim/physics/ambient_temp.py`:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class AmbientTempFn(Protocol):
    def __call__(self, time_hours: float) -> float:
        ...
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/test_physics.py -v
```

Expected: all 12 tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/chiller_sim/physics/ tests/test_physics.py
git commit -m "feat: add physics protocols and default cop/degradation/ramp functions"
```

---

## Task 5: GaussianPlumeModel

**Files:**
- Create: `src/chiller_sim/physics/gaussian_plume.py`
- Extend: `tests/test_physics.py`

This ports the existing interaction matrix logic from `src/models/gaussian_plume.py`, adapting it to use `WindConditions` (no `ambient_temp_k`).

- [ ] **Step 1: Write failing tests — append to `tests/test_physics.py`**

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_physics.py -v -k "interaction or upwind or lateral or distance or nan"
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `gaussian_plume.py`**

Create `src/chiller_sim/physics/gaussian_plume.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.wind import WindConditions


@dataclass(frozen=True)
class GaussianPlumeModel:
    dispersion_coeff: float = 1.2

    def compute_interaction_matrix(
        self,
        positions_m: NDArray[np.float64],
        wind: WindConditions,
    ) -> NDArray[np.float64]:
        """Return N×N matrix A where A[k, m] = thermal influence of chiller k on chiller m."""
        n = len(positions_m)
        uv = wind.unit_vector                        # (2,) unit vector in wind direction
        perp = np.array([-uv[1], uv[0]])             # perpendicular unit vector

        # Pairwise displacement vectors: diff[k, m] = positions[m] - positions[k]
        diff = positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]  # (n, n, 2)

        longitudinal = diff @ uv    # (n, n): along-wind distance from k to m
        lateral = diff @ perp       # (n, n): cross-wind distance from k to m

        sigma = self.dispersion_coeff
        denom = longitudinal + 1.0
        with np.errstate(divide='ignore', invalid='ignore'):
            A = np.where(
                longitudinal > 0,
                np.exp(-lateral**2 / (sigma * denom)) / denom,
                0.0,
            )

        np.fill_diagonal(A, 0.0)
        # Safety net: suppress any NaN/Inf from edge cases with coincident positions
        return np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)
```

Note: `lateral = diff @ perp` gives a signed scalar projection. Because it is squared in the exponent, the sign cancels and the result equals the squared lateral distance in 2-D. This is correct for 2-D grids; positions are asserted to be 2-D in `_evaluate_work` callers via the typed `NDArray[float64]` shape `(n, 2)` from `ChillerGrid`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_physics.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/physics/gaussian_plume.py tests/test_physics.py
git commit -m "feat: add GaussianPlumeModel for thermal interaction matrix"
```

---

## Task 6: SimulatorBuilder

**Files:**
- Create: `src/chiller_sim/simulation/builder.py`
- Create: `src/chiller_sim/simulation/simulator.py` (stub — `Simulator.__init__` only)
- Create: `tests/test_builder.py`

The builder stores all configuration and runs validation at `.build()`. The `Simulator` stores a reference to its builder so users can chain `.with_wind().build()` on a live instance.

- [ ] **Step 1: Write failing tests**

Create `tests/test_builder.py`:

```python
import numpy as np
import pytest
from chiller_sim.simulation.builder import SimulatorBuilder


def _base_builder() -> SimulatorBuilder:
    return (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0)
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
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
    )
    with pytest.raises(ValueError, match="load_fn"):
        builder.build()


def test_build_raises_without_ambient_temp():
    builder = (
        SimulatorBuilder()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0)
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
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0)
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_builder.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `builder.py`**

Create `src/chiller_sim/simulation/builder.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.physics.cop import CopFn, default_cop_fn
from chiller_sim.physics.degradation import DegradationFn, default_degradation_fn
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel
from chiller_sim.physics.load import LoadFn
from chiller_sim.physics.ramp import RampFn, default_ramp_fn

if TYPE_CHECKING:
    from chiller_sim.simulation.simulator import Simulator


class SimulatorBuilder:
    def __init__(self) -> None:
        self._grid: ChillerGrid | None = None
        self._grid_seed: int | None = None
        self._wind: WindConditions | None = None
        self._wind_fn: WindFn | None = None
        self._ambient_temp_k: float | None = None
        self._ambient_temp_fn: AmbientTempFn | None = None
        self._dispersion_coeff: float = 1.2
        self._load_fn: LoadFn | None = None
        self._cop_fn: CopFn | None = None
        self._degradation_fn: DegradationFn | None = None
        self._ramp_fn: RampFn | None = None
        self._min_savings_kw: float = 0.0

    def with_grid(
        self,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float,
        alpha: float = 0.7,
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
    ) -> SimulatorBuilder:
        self._grid_seed = seed
        self._grid = ChillerGrid.create_grid(
            rows=rows, cols=cols, spacing_m=spacing_m,
            base_cop=base_cop, alpha=alpha,
            ages_years=ages_years, seed=seed,
        )
        return self

    def with_wind(self, speed_m_per_s: float, angle_deg: float) -> SimulatorBuilder:
        self._wind = WindConditions(speed_m_per_s=speed_m_per_s, angle_deg=angle_deg)
        return self

    def with_wind_fn(self, fn: WindFn) -> SimulatorBuilder:
        self._wind_fn = fn
        return self

    def with_ambient_temp(self, temp_k: float) -> SimulatorBuilder:
        self._ambient_temp_k = temp_k
        return self

    def with_ambient_temp_fn(self, fn: AmbientTempFn) -> SimulatorBuilder:
        self._ambient_temp_fn = fn
        return self

    def with_dispersion(self, coeff: float) -> SimulatorBuilder:
        self._dispersion_coeff = coeff
        return self

    def with_load_fn(self, fn: LoadFn) -> SimulatorBuilder:
        self._load_fn = fn
        return self

    def with_cop_fn(self, fn: CopFn) -> SimulatorBuilder:
        self._cop_fn = fn
        return self

    def with_degradation_fn(self, fn: DegradationFn) -> SimulatorBuilder:
        self._degradation_fn = fn
        return self

    def with_ramp_fn(self, fn: RampFn) -> SimulatorBuilder:
        self._ramp_fn = fn
        return self

    def with_switching_threshold(self, min_savings_kw: float) -> SimulatorBuilder:
        self._min_savings_kw = min_savings_kw
        return self

    def build(self) -> Simulator:
        from chiller_sim.simulation.simulator import Simulator

        if self._grid is None:
            raise ValueError("grid is required — call .with_grid() before .build()")
        if self._load_fn is None:
            raise ValueError("load_fn is required — call .with_load_fn() before .build()")
        if self._ambient_temp_k is None and self._ambient_temp_fn is None:
            raise ValueError(
                "ambient_temp is required — call .with_ambient_temp() or "
                ".with_ambient_temp_fn() before .build()"
            )

        # Resolve defaults
        cop_fn = self._cop_fn if self._cop_fn is not None else default_cop_fn(self._grid.alpha)
        deg_fn = self._degradation_fn if self._degradation_fn is not None else default_degradation_fn
        ramp_fn = self._ramp_fn if self._ramp_fn is not None else default_ramp_fn

        # Build initial wind conditions (required for matrix precomputation)
        if self._wind is None and self._wind_fn is None:
            raise ValueError("wind is required — call .with_wind() or .with_wind_fn() before .build()")
        initial_wind = self._wind or WindConditions(*self._wind_fn(0.0))

        model = GaussianPlumeModel(dispersion_coeff=self._dispersion_coeff)

        return Simulator(
            builder=self,
            grid=self._grid,
            initial_wind=initial_wind,
            model=model,
            load_fn=self._load_fn,
            cop_fn=cop_fn,
            degradation_fn=deg_fn,
            ramp_fn=ramp_fn,
            wind_fn=self._wind_fn,
            ambient_temp_k=self._ambient_temp_k,
            ambient_temp_fn=self._ambient_temp_fn,
            min_savings_kw=self._min_savings_kw,
        )
```

- [ ] **Step 4: Implement `simulator.py` stub**

Create `src/chiller_sim/simulation/simulator.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.grid import ChillerGrid
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.physics.cop import CopFn
from chiller_sim.physics.degradation import DegradationFn
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel
from chiller_sim.physics.load import LoadFn
from chiller_sim.physics.ramp import RampFn

if TYPE_CHECKING:
    from chiller_sim.simulation.builder import SimulatorBuilder


class Simulator:
    def __init__(
        self,
        builder: SimulatorBuilder,
        grid: ChillerGrid,
        initial_wind: WindConditions,
        model: GaussianPlumeModel,
        load_fn: LoadFn,
        cop_fn: CopFn,
        degradation_fn: DegradationFn,
        ramp_fn: RampFn,
        wind_fn: WindFn | None,
        ambient_temp_k: float | None,
        ambient_temp_fn: AmbientTempFn | None,
        min_savings_kw: float,
    ) -> None:
        self._builder = builder
        self._grid = grid
        self._model = model
        self._load_fn = load_fn
        self._cop_fn = cop_fn
        self._degradation_fn = degradation_fn
        self._ramp_fn = ramp_fn
        self._wind_fn = wind_fn
        self._ambient_temp_k = ambient_temp_k
        self._ambient_temp_fn = ambient_temp_fn
        self._min_savings_kw = min_savings_kw

        # Precompute interaction matrix for initial wind
        self._current_wind = initial_wind
        self._interaction_matrix = model.compute_interaction_matrix(grid.positions_m, initial_wind)

        # Optimizer state — reset at start of each stream()/simulate() call
        self._is_first_call = True
        self._active_mask: NDArray[np.bool_] = np.zeros(grid.num_chillers, dtype=bool)
        self._time_since_start: NDArray[np.float64] = np.zeros(grid.num_chillers)

    # Builder re-entry: allow sim.with_wind(...).build()
    def with_wind(self, speed_m_per_s: float, angle_deg: float) -> SimulatorBuilder:
        return self._builder.with_wind(speed_m_per_s=speed_m_per_s, angle_deg=angle_deg)

    def with_wind_fn(self, fn: WindFn) -> SimulatorBuilder:
        return self._builder.with_wind_fn(fn)

    def with_ambient_temp(self, temp_k: float) -> SimulatorBuilder:
        return self._builder.with_ambient_temp(temp_k=temp_k)

    def with_ambient_temp_fn(self, fn: AmbientTempFn) -> SimulatorBuilder:
        return self._builder.with_ambient_temp_fn(fn)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_builder.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/chiller_sim/simulation/builder.py src/chiller_sim/simulation/simulator.py tests/test_builder.py
git commit -m "feat: add SimulatorBuilder with validation and Simulator stub"
```

---

## Task 7: Simulator.optimize()

**Files:**
- Extend: `src/chiller_sim/simulation/simulator.py`
- Create: `tests/test_behavior.py` (optimization tests)

This implements the core greedy algorithm with state tracking. Key design notes:
- `_evaluate_work()` returns `(total_work_kw, cop_array, temp_rise_array)` — shared by optimize and stream
- Baseline uses `use_steady_state_ramp=True` (all ramp factors = 1.0)
- First call initializes from all-on at steady state

- [ ] **Step 1: Write failing tests**

Create `tests/test_behavior.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_behavior.py -v -k "optimize"
```

Expected: `ImportError` (Simulator not yet importable from `chiller_sim`).

- [ ] **Step 3: Wire up top-level `__init__.py`**

Create `src/chiller_sim/__init__.py`:

```python
from chiller_sim.simulation.builder import SimulatorBuilder as Simulator
from chiller_sim.simulation.results import InitialState, OptimizeResult, SimulationResult

__all__ = ["Simulator", "OptimizeResult", "SimulationResult", "InitialState"]
```

Note: `Simulator()` is the entry point — it returns a `SimulatorBuilder`. The actual `Simulator` class is an implementation detail.

- [ ] **Step 4: Run to verify tests fail with correct error**

```bash
pytest tests/test_behavior.py -v -k "optimize"
```

Expected: `AttributeError` — `optimize` not yet implemented.

- [ ] **Step 5: Implement `_evaluate_work()` and `optimize()` in `simulator.py`**

Add these methods to `Simulator` in `src/chiller_sim/simulation/simulator.py`:

```python
    def _get_ambient_temp(self, time_hours: float) -> float:
        if self._ambient_temp_fn is not None:
            return self._ambient_temp_fn(time_hours)
        return self._ambient_temp_k  # type: ignore[return-value]

    def _get_wind(self, time_hours: float) -> WindConditions:
        if self._wind_fn is not None:
            speed, angle = self._wind_fn(time_hours)
            return WindConditions(speed_m_per_s=speed, angle_deg=angle)
        return self._current_wind

    def _update_wind_if_changed(self, time_hours: float) -> None:
        new_wind = self._get_wind(time_hours)
        if new_wind != self._current_wind:
            self._current_wind = new_wind
            self._interaction_matrix = self._model.compute_interaction_matrix(
                self._grid.positions_m, new_wind
            )

    def _evaluate_work(
        self,
        active_mask: NDArray[np.bool_],
        time_since_start: NDArray[np.float64],
        load_kw: float,
        ambient_temp_k: float,
        use_steady_state_ramp: bool = False,
    ) -> tuple[float, NDArray[np.float64], NDArray[np.float64]]:
        """Return (total_work_kw, cop_array, temp_rise_array)."""
        n = len(active_mask)
        n_active = int(active_mask.sum())

        if n_active == 0:
            return float("inf"), np.zeros(n), np.zeros(n)

        load_per_unit = load_kw / n_active
        temp_rise = active_mask.astype(np.float64) @ self._interaction_matrix

        ramp_factors = (
            np.ones(n)
            if use_steady_state_ramp
            else np.array([self._ramp_fn(t) for t in time_since_start])
        )
        deg_factors = np.array([self._degradation_fn(a) for a in self._grid.ages_years])

        cop_array = np.array([
            self._cop_fn(self._grid.base_cop, temp_rise[i], ambient_temp_k)
            * deg_factors[i]
            * ramp_factors[i]
            for i in range(n)
        ])
        cop_array = np.maximum(cop_array, 1e-6)

        total_work = float(np.sum(load_per_unit / cop_array[active_mask]))
        return total_work, cop_array, temp_rise

    def _greedy_optimize(
        self,
        load_kw: float,
        ambient_temp_k: float,
    ) -> tuple[NDArray[np.bool_], NDArray[np.float64]]:
        n = self._grid.num_chillers

        # On the first call, start all-on at steady-state ramp throughout the
        # entire greedy loop — this ensures custom ramp_fn values do not affect
        # the first-call behavior, matching the spec guarantee.
        is_first = self._is_first_call
        if is_first:
            active_mask = np.ones(n, dtype=bool)
            time_since_start = np.full(n, np.inf)
            self._is_first_call = False
        else:
            active_mask = self._active_mask.copy()
            time_since_start = self._time_since_start.copy()

        current_work, _, _ = self._evaluate_work(
            active_mask, time_since_start, load_kw, ambient_temp_k,
            use_steady_state_ramp=is_first,
        )

        improved = True
        while improved:
            improved = False
            best_work = current_work
            best_mask: NDArray[np.bool_] | None = None
            best_times: NDArray[np.float64] | None = None

            for i in range(n):
                candidate_mask = active_mask.copy()
                candidate_times = time_since_start.copy()
                candidate_mask[i] = not candidate_mask[i]

                if candidate_mask[i]:  # activating
                    candidate_times[i] = 0.0
                # deactivating: time value irrelevant for inactive chillers

                candidate_work, _, _ = self._evaluate_work(
                    candidate_mask, candidate_times, load_kw, ambient_temp_k,
                    use_steady_state_ramp=is_first,
                )
                savings = current_work - candidate_work

                if savings >= self._min_savings_kw and candidate_work < best_work:
                    best_work = candidate_work
                    best_mask = candidate_mask
                    best_times = candidate_times

            if best_mask is not None:
                active_mask = best_mask
                time_since_start = best_times  # type: ignore[assignment]
                current_work = best_work
                improved = True

        return active_mask, time_since_start

    def optimize(
        self,
        time_hours: float,
        load_kw: float | None = None,
    ) -> OptimizeResult:
        from chiller_sim.simulation.results import OptimizeResult

        self._update_wind_if_changed(time_hours)
        ambient_temp_k = self._get_ambient_temp(time_hours)
        resolved_load = load_kw if load_kw is not None else self._load_fn(time_hours)

        # Baseline: all chillers on at steady-state ramp
        n = self._grid.num_chillers
        all_on = np.ones(n, dtype=bool)
        steady_times = np.full(n, np.inf)
        baseline_work, _, _ = self._evaluate_work(
            all_on, steady_times, resolved_load, ambient_temp_k, use_steady_state_ramp=True
        )

        active_mask, time_since_start = self._greedy_optimize(resolved_load, ambient_temp_k)
        total_work, cop_array, temp_rise = self._evaluate_work(
            active_mask, time_since_start, resolved_load, ambient_temp_k
        )

        savings_fraction = (
            (baseline_work - total_work) / baseline_work if baseline_work > 0 else 0.0
        )

        # Persist state for next optimize() call
        self._active_mask = active_mask
        self._time_since_start = time_since_start

        return OptimizeResult(
            time_hours=time_hours,
            load_kw=resolved_load,
            active_mask=active_mask,
            total_work_kw=total_work,
            baseline_work_kw=baseline_work,
            savings_fraction=savings_fraction,
            cop_array=cop_array,
            temp_rise_array=temp_rise,
        )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_behavior.py -v -k "optimize"
```

Expected: all 9 optimization tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/chiller_sim/simulation/simulator.py src/chiller_sim/__init__.py tests/test_behavior.py
git commit -m "feat: implement Simulator.optimize() with state-aware greedy algorithm"
```

---

## Task 8: Simulator.stream() and Simulator.simulate()

**Files:**
- Extend: `src/chiller_sim/simulation/simulator.py`
- Extend: `tests/test_behavior.py`

- [ ] **Step 1: Write failing tests — append to `tests/test_behavior.py`**

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_behavior.py -v -k "simulate or stream or startup or initial or load_fn"
```

Expected: `AttributeError` — `simulate`/`stream` not yet implemented.

- [ ] **Step 3: Implement `stream()` and `simulate()` in `simulator.py`**

Add to `Simulator`:

```python
    from __future__ import annotations  # already at top of file
    from typing import Generator
    from chiller_sim.simulation.results import InitialState, SimulationResult  # add to imports

    def _reset_state(self, initial_state: InitialState | None) -> None:
        """Reset internal optimizer state at start of stream()/simulate()."""
        n = self._grid.num_chillers
        if initial_state is not None:
            self._active_mask = initial_state.active_mask.copy()
            self._time_since_start = initial_state.time_since_start_hours.copy()
            self._is_first_call = False
        else:
            self._active_mask = np.zeros(n, dtype=bool)
            self._time_since_start = np.zeros(n)
            self._is_first_call = True

    def stream(
        self,
        duration_hours: float,
        time_step_hours: float = 1.0,
        initial_time_hours: float = 0.0,
        initial_state: InitialState | None = None,
    ) -> Generator[OptimizeResult, None, None]:
        self._reset_state(initial_state)
        t = initial_time_hours
        while t < initial_time_hours + duration_hours - 1e-9:
            result = self.optimize(time_hours=t)
            # Advance startup clocks for active chillers
            self._time_since_start[self._active_mask] += time_step_hours
            self._time_since_start[~self._active_mask] = 0.0
            yield result
            t += time_step_hours

    def simulate(
        self,
        duration_hours: float,
        time_step_hours: float = 1.0,
        initial_time_hours: float = 0.0,
        initial_state: InitialState | None = None,
    ) -> SimulationResult:
        from chiller_sim.simulation.results import SimulationResult
        steps = list(self.stream(
            duration_hours=duration_hours,
            time_step_hours=time_step_hours,
            initial_time_hours=initial_time_hours,
            initial_state=initial_state,
        ))
        return SimulationResult(steps=steps)
```

Also add `OptimizeResult` and `InitialState` to the imports at top of `simulator.py`:
```python
from chiller_sim.simulation.results import InitialState, OptimizeResult, SimulationResult
```

And add the `Generator` import:
```python
from collections.abc import Generator
```

- [ ] **Step 4: Run all behavior tests**

```bash
pytest tests/test_behavior.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/chiller_sim/simulation/simulator.py tests/test_behavior.py
git commit -m "feat: implement Simulator.stream() and Simulator.simulate() with InitialState support"
```

---

## Task 9: Plugin Behavior Tests

**Files:**
- Extend: `tests/test_behavior.py`

These tests verify that custom physics functions are actually called and change results.

- [ ] **Step 1: Write plugin tests — append to `tests/test_behavior.py`**

```python
# --- Physics plugins ---

def test_custom_cop_fn_changes_work():
    sim_default = _base_sim()
    r_default = sim_default.optimize(time_hours=0.0)

    # A worse cop_fn (returns half the COP) should result in more work
    sim_custom = (
        Simulator()
        .with_grid(rows=4, cols=4, spacing_m=10.0, base_cop=5.5, alpha=0.7, seed=0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 500.0)
        .with_cop_fn(lambda base, rise, ambient: base / 2.0)
        .build()
    )
    r_custom = sim_custom.optimize(time_hours=0.0)
    assert r_custom.total_work_kw > r_default.total_work_kw


def test_custom_degradation_fn_affects_aged_chillers():
    # No degradation vs heavy degradation on a grid with known ages
    ages = np.full(4, 10.0)  # all 10 years old

    sim_nodeg = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, ages_years=ages)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .with_degradation_fn(lambda age: 1.0)   # no degradation
        .build()
    )
    sim_heavydeg = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, ages_years=ages)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .with_degradation_fn(lambda age: 0.5)   # 50% degradation always
        .build()
    )
    r_nodeg = sim_nodeg.optimize(time_hours=0.0)
    r_heavydeg = sim_heavydeg.optimize(time_hours=0.0)
    assert r_heavydeg.total_work_kw > r_nodeg.total_work_kw


def test_custom_ramp_fn_increases_work_when_starting_from_initial_state():
    # A chiller starting from time=0 with a zero ramp function should have very high work.
    # Use initial_state so the first call is NOT the first-call steady-state path.
    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, ages_years=np.zeros(4))
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .with_ramp_fn(lambda t: 0.0)   # always zero (clipped to 1e-6 in _evaluate_work)
        .with_switching_threshold(min_savings_kw=1e9)
        .build()
    )
    state = InitialState(
        active_mask=np.ones(4, dtype=bool),
        time_since_start_hours=np.zeros(4),
    )
    result = sim.simulate(duration_hours=1.0, time_step_hours=1.0, initial_state=state)
    # ramp_fn always returns 0 → COP clipped to 1e-6 → work per chiller = load/4 / 1e-6 ≈ huge
    assert result.total_work_kw[0] > 1e6


def test_custom_ambient_temp_fn_is_called():
    temps_seen = []
    def tracking_temp(t: float) -> float:
        temps_seen.append(t)
        return 298.15

    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, seed=0)
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp_fn(tracking_temp)
        .with_load_fn(lambda t: 400.0)
        .build()
    )
    sim.simulate(duration_hours=3.0, time_step_hours=1.0)
    assert len(temps_seen) >= 3


def test_wind_fn_is_called_at_each_step():
    wind_times: list[float] = []
    def tracking_wind(t: float) -> tuple[float, float]:
        wind_times.append(t)
        return (3.0, 0.0)

    sim = (
        Simulator()
        .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=5.0, seed=0)
        .with_wind_fn(tracking_wind)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .build()
    )
    sim.simulate(duration_hours=3.0, time_step_hours=1.0)
    assert len(wind_times) >= 3


def test_switching_threshold_prevents_cycling():
    # Near a load boundary where one chiller toggling is marginal
    # With a high threshold, the optimizer should not change the active set
    sim_no_thresh = _base_sim(load_kw=500.0, min_savings_kw=0.0)
    sim_with_thresh = _base_sim(load_kw=500.0, min_savings_kw=1e9)

    r_no = sim_no_thresh.simulate(duration_hours=3.0, time_step_hours=1.0)
    r_with = sim_with_thresh.simulate(duration_hours=3.0, time_step_hours=1.0)

    # With high threshold, all chillers stay on (no toggle eligible)
    assert np.all(r_with.schedule)
    # Without threshold, some are turned off
    assert not np.all(r_no.schedule)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_behavior.py -v -k "custom or plugin or cycling or switching"
```

Expected: some pass, some fail (switching threshold test may need adjustment).

- [ ] **Step 3: Run all tests and fix any failures**

```bash
pytest tests/test_behavior.py -v
```

Fix any failing tests by adjusting test parameters if needed (e.g., the ramp test threshold).

- [ ] **Step 4: Commit**

```bash
git add tests/test_behavior.py
git commit -m "test: add plugin behavior tests and switching threshold tests"
```

---

## Task 10: Cleanup and Final Wiring

**Files:**
- Modify: `src/chiller_sim/__init__.py` (ensure all exports correct)
- Delete: all old `src/` package files
- Delete: old test directories
- Modify: `pyproject.toml` (remove verification testpath)

- [ ] **Step 1: Run the full new test suite first**

```bash
pytest tests/ -v
```

Expected: all tests in `tests/test_types.py`, `tests/test_physics.py`, `tests/test_builder.py`, `tests/test_behavior.py` pass.

- [ ] **Step 2: Delete old source package**

```bash
rm -rf src/__init__.py src/core src/components src/models src/simulation
```

- [ ] **Step 3: Delete old tests and verification**

```bash
rm -rf tests/test_core tests/test_components tests/test_models tests/test_simulation
rm -rf tests/conftest.py
rm -rf verification/
```

- [ ] **Step 4: Delete outdated scripts**

```bash
rm -rf scripts/
```

- [ ] **Step 5: Update `pyproject.toml`**

Remove `"verification"` from `testpaths`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 6: Verify package still installs and tests pass**

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Expected: all tests pass, no import errors from old package.

- [ ] **Step 7: Run linter**

```bash
ruff check src/chiller_sim/
```

Fix any issues, then:

```bash
ruff format src/chiller_sim/
```

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "refactor: remove old src package, complete chiller_sim refactor"
```

---

## Quick Reference: Running Tests

```bash
# All tests
pytest tests/ -v

# Single file
pytest tests/test_behavior.py -v

# Specific test
pytest tests/test_behavior.py::test_optimize_total_work_less_than_baseline -v

# With coverage
pytest tests/ --cov=src/chiller_sim --cov-report=term-missing
```
