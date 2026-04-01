# Non-Grid Layouts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `ChillerGrid` to `ChillerLayout`, add `from_positions()` for arbitrary chiller placement, add `SimulatorBuilder.with_layout()`, update all tests and docs.

**Architecture:** Straight rename of the core type + one new class method + one new builder method. The physics layer already works on raw position arrays and needs no changes. Internal `_grid` references become `_layout`.

**Tech Stack:** Python, NumPy, pytest, ruff

---

This plan is structured as a Ralph Loop: each task is one loop iteration that ends with a commit once tests pass and code is validated. Each task also includes a simplification pass to minimize nesting.

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `src/chiller_sim/layout/grid.py` | Rename class, add `from_positions()` |
| Modify | `src/chiller_sim/simulation/builder.py` | Rename refs, add `with_layout()` |
| Modify | `src/chiller_sim/simulation/simulator.py` | Rename `_grid` → `_layout` |
| Modify | `tests/test_types.py` | Rename `ChillerGrid` → `ChillerLayout` |
| Modify | `tests/test_capacity.py` | Rename `ChillerGrid` → `ChillerLayout` |
| Modify | `tests/test_bugs.py` | Rename `ChillerGrid` → `ChillerLayout` |
| Modify | `tests/test_builder.py` | Add `with_layout()` tests |
| Modify | `scripts/example_2_thermal_interference.py` | Rename `ChillerGrid` → `ChillerLayout` |
| Modify | `docs/user-guide.rst` | Rename references |
| Modify | `README.md` | Rename references |
| Modify | `CLAUDE.md` | Rename references, mention `with_layout()` |
| Modify | `report/report.tex` | Rename references |

---

### Task 1: Rename `ChillerGrid` → `ChillerLayout` in core + fix all imports

This loop renames the class and all references. No new functionality yet.

**Files:**
- Modify: `src/chiller_sim/layout/grid.py:10-63`
- Modify: `src/chiller_sim/simulation/builder.py:8,26,39-62,122-123,133,150`
- Modify: `src/chiller_sim/simulation/simulator.py:9,29,43`
- Modify: `tests/test_types.py` (import + all `ChillerGrid` refs)
- Modify: `tests/test_capacity.py` (import + all `ChillerGrid` refs)
- Modify: `tests/test_bugs.py` (import + all `ChillerGrid` refs)
- Modify: `tests/test_builder.py` (`sim._grid` → `sim._layout` in assertions)
- Modify: `scripts/example_2_thermal_interference.py` (import + usage)

- [ ] **Step 1: Rename the class in `grid.py`**

In `src/chiller_sim/layout/grid.py`, rename `ChillerGrid` to `ChillerLayout` everywhere:
- Line 10: `class ChillerGrid:` → `class ChillerLayout:`
- Line 12 docstring: "chiller array layout" (no change needed)
- Line 35: return type `-> ChillerGrid:` → `-> ChillerLayout:`

- [ ] **Step 2: Update `builder.py` imports and references**

In `src/chiller_sim/simulation/builder.py`:
- Line 8: `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- Line 26: `self._grid: ChillerGrid | None = None` → `self._layout: ChillerLayout | None = None`
- Line 51: `self._grid_seed = seed` stays (grid seed is still relevant for grid factory)
- Line 52: `self._grid = ChillerGrid.create_grid(` → `self._layout = ChillerLayout.create_grid(`
- Line 122: `if self._grid is None:` → `if self._layout is None:`
- Line 123: error message update to mention `.with_grid()` or `.with_layout()`
- Line 133: `self._grid.alpha` → `self._layout.alpha`
- Line 150: `grid=self._grid,` → `layout=self._layout,`

- [ ] **Step 3: Update `simulator.py` imports and references**

In `src/chiller_sim/simulation/simulator.py`:
- Line 9: `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- Line 29: parameter `grid: ChillerGrid` → `layout: ChillerLayout`
- Line 43: `self._grid = grid` → `self._layout = layout`
- All `self._grid` → `self._layout` (lines 56, 60, 61, 97, 121, 122, 137, 152, 235, 281)

- [ ] **Step 4: Update all test files**

In `tests/test_types.py`:
- `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- All `ChillerGrid.create_grid` → `ChillerLayout.create_grid`

In `tests/test_capacity.py`:
- `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- All `ChillerGrid.create_grid` → `ChillerLayout.create_grid`

In `tests/test_bugs.py`:
- `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- All `ChillerGrid.create_grid` → `ChillerLayout.create_grid`

In `tests/test_builder.py`:
- `sim._grid` → `sim._layout` in assertions (lines referencing `sim._grid.ages_years`, `sim._grid.num_chillers`)

In `tests/test_behavior.py`:
- `sim._grid.num_chillers` → `sim._layout.num_chillers`

- [ ] **Step 5: Update example script**

In `scripts/example_2_thermal_interference.py`:
- `from chiller_sim.layout.grid import ChillerGrid` → `from chiller_sim.layout.grid import ChillerLayout`
- `grid = ChillerGrid.create_grid(` → `grid = ChillerLayout.create_grid(`

- [ ] **Step 6: Run tests, lint, type check**

```bash
pytest
ruff check .
ruff format .
mypy
```

Expected: all pass with zero failures.

- [ ] **Step 7: Simplify — scan changed files for unnecessary nesting**

Review all modified files for deeply nested code. Flatten any `if`/`else` blocks that can use early returns or guard clauses.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: rename ChillerGrid to ChillerLayout"
```

---

### Task 2: Add `ChillerLayout.from_positions()` class method

**Files:**
- Modify: `src/chiller_sim/layout/grid.py`
- Modify: `tests/test_types.py`

- [ ] **Step 1: Write failing tests for `from_positions()`**

Add to `tests/test_types.py`:

```python
def test_chiller_layout_from_positions():
    positions = np.array([[0.0, 0.0], [10.0, 5.0], [25.0, 15.0]])
    ages = np.array([1.0, 5.0, 10.0])
    layout = ChillerLayout.from_positions(
        positions_m=positions,
        ages_years=ages,
        base_cop=5.0,
        max_cooling_kw=500.0,
    )
    assert layout.positions_m.shape == (3, 2)
    assert layout.num_chillers == 3
    assert layout.base_cop == 5.0
    assert layout.alpha == 0.7  # default
    assert layout.max_cooling_kw == 500.0
    np.testing.assert_array_equal(layout.ages_years, ages)


def test_from_positions_rejects_wrong_shape_1d():
    with pytest.raises(ValueError, match="positions_m"):
        ChillerLayout.from_positions(
            positions_m=np.array([1.0, 2.0, 3.0]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_wrong_shape_3col():
    with pytest.raises(ValueError, match="positions_m"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0, 0.0]]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_mismatched_ages():
    with pytest.raises(ValueError, match="ages_years"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0], [10.0, 5.0]]),
            ages_years=np.array([1.0, 2.0, 3.0]),  # 3 ages for 2 positions
            base_cop=5.0,
            max_cooling_kw=500.0,
        )


def test_from_positions_rejects_zero_max_cooling():
    with pytest.raises(ValueError, match="max_cooling_kw"):
        ChillerLayout.from_positions(
            positions_m=np.array([[0.0, 0.0]]),
            ages_years=np.array([1.0]),
            base_cop=5.0,
            max_cooling_kw=0.0,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_types.py -k "from_positions" -v
```

Expected: FAIL — `from_positions` not defined.

- [ ] **Step 3: Implement `from_positions()`**

Add to `ChillerLayout` in `src/chiller_sim/layout/grid.py`:

```python
@classmethod
def from_positions(
    cls,
    positions_m: NDArray[np.float64],
    ages_years: NDArray[np.float64],
    base_cop: float,
    max_cooling_kw: float,
    alpha: float = 0.7,
) -> ChillerLayout:
    """Build a layout from explicit (x, y) positions."""
    positions_m = np.asarray(positions_m, dtype=np.float64)
    ages_years = np.asarray(ages_years, dtype=np.float64)

    if positions_m.ndim != 2 or positions_m.shape[1] != 2:
        raise ValueError(
            f"positions_m must have shape (n, 2), got {positions_m.shape}"
        )
    if ages_years.shape[0] != positions_m.shape[0]:
        raise ValueError(
            f"ages_years length {len(ages_years)} does not match "
            f"{positions_m.shape[0]} positions"
        )
    if max_cooling_kw <= 0:
        raise ValueError(f"max_cooling_kw must be > 0, got {max_cooling_kw}")

    return cls(
        positions_m=positions_m,
        base_cop=base_cop,
        alpha=alpha,
        ages_years=ages_years,
        max_cooling_kw=max_cooling_kw,
    )
```

- [ ] **Step 4: Refactor `create_grid()` to call `from_positions()`**

Replace the tail of `create_grid()` so it delegates to `from_positions()`:

```python
return cls.from_positions(
    positions_m=positions,
    ages_years=resolved_ages,
    base_cop=base_cop,
    max_cooling_kw=max_cooling_kw,
    alpha=alpha,
)
```

The `max_cooling_kw` validation in `create_grid()` can be removed since `from_positions()` handles it.

- [ ] **Step 5: Run tests, lint, type check**

```bash
pytest
ruff check .
ruff format .
mypy
```

Expected: all pass.

- [ ] **Step 6: Simplify — review `grid.py` for nesting**

Check that `create_grid()` and `from_positions()` use early returns / guard clauses. Remove any redundant validation from `create_grid()` now that `from_positions()` validates.

- [ ] **Step 7: Commit**

```bash
git add src/chiller_sim/layout/grid.py tests/test_types.py
git commit -m "feat: add ChillerLayout.from_positions() for arbitrary placement"
```

---

### Task 3: Add `SimulatorBuilder.with_layout()` and end-to-end test

**Files:**
- Modify: `src/chiller_sim/simulation/builder.py`
- Modify: `tests/test_builder.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_builder.py`:

```python
def test_with_layout_builds_successfully():
    positions = np.array([[0.0, 0.0], [15.0, 0.0], [7.5, 13.0]])
    ages = np.array([2.0, 5.0, 8.0])
    sim = (
        SimulatorBuilder()
        .with_layout(
            positions_m=positions,
            ages_years=ages,
            base_cop=5.0,
            max_cooling_kw=500.0,
        )
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
        .build()
    )
    assert sim is not None
    assert sim._layout.num_chillers == 3


def test_with_layout_optimize_triangle():
    """End-to-end: optimize with 3 chillers in a triangle (non-grid layout)."""
    positions = np.array([[0.0, 0.0], [20.0, 0.0], [10.0, 17.3]])
    ages = np.array([0.0, 0.0, 0.0])
    sim = (
        SimulatorBuilder()
        .with_layout(
            positions_m=positions,
            ages_years=ages,
            base_cop=5.0,
            max_cooling_kw=500.0,
        )
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 300.0)
        .build()
    )
    result = sim.optimize(time_hours=0.0)
    assert result.active_mask.sum() >= 1
    assert result.total_work_kw < float("inf")


def test_build_raises_without_layout_or_grid():
    builder = (
        SimulatorBuilder()
        .with_wind(speed_m_per_s=3.0, angle_deg=0.0)
        .with_ambient_temp(temp_k=298.15)
        .with_load_fn(lambda t: 400.0)
    )
    with pytest.raises(ValueError, match="layout"):
        builder.build()
```

Add `import numpy as np` to the top of `tests/test_builder.py` if not already present.

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_builder.py -k "layout" -v
```

Expected: FAIL — `with_layout` not defined.

- [ ] **Step 3: Implement `with_layout()`**

Add to `SimulatorBuilder` in `src/chiller_sim/simulation/builder.py`:

```python
def with_layout(
    self,
    positions_m: NDArray[np.float64],
    ages_years: NDArray[np.float64],
    base_cop: float,
    max_cooling_kw: float,
    alpha: float = 0.7,
) -> SimulatorBuilder:
    """Set the chiller layout from explicit (x, y) positions."""
    self._layout = ChillerLayout.from_positions(
        positions_m=positions_m,
        ages_years=ages_years,
        base_cop=base_cop,
        max_cooling_kw=max_cooling_kw,
        alpha=alpha,
    )
    return self
```

Update the `build()` error message (from Task 1) to say:
`"layout is required — call .with_grid() or .with_layout() before .build()"`

- [ ] **Step 4: Update existing `test_build_raises_without_grid` test**

The existing test checks for `match="grid"` in the error message. Update it to `match="layout"` since the error message now says "layout".

- [ ] **Step 5: Run tests, lint, type check**

```bash
pytest
ruff check .
ruff format .
mypy
```

Expected: all pass.

- [ ] **Step 6: Simplify — review builder for nesting**

Check `with_layout()` and `build()` for unnecessary nesting. Ensure guard clauses are used.

- [ ] **Step 7: Commit**

```bash
git add src/chiller_sim/simulation/builder.py tests/test_builder.py
git commit -m "feat: add SimulatorBuilder.with_layout() for arbitrary positions"
```

---

### Task 4: Update documentation

**Files:**
- Modify: `docs/user-guide.rst`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `report/report.tex`

- [ ] **Step 1: Update all docs**

In every file listed above, replace:
- `ChillerGrid` → `ChillerLayout`
- Add mention of `with_layout()` alongside `with_grid()` where the builder API is described

In `CLAUDE.md` specifically:
- Architecture section: `ChillerGrid` → `ChillerLayout`
- Key design patterns: mention `with_layout()` as alternative to `with_grid()`
- Data flow: update `ChillerGrid` references

- [ ] **Step 2: Run docs build (if applicable)**

```bash
cd docs && make html 2>&1 | tail -5; cd ..
```

- [ ] **Step 3: Run full test suite to ensure nothing broke**

```bash
pytest
ruff check .
ruff format .
```

- [ ] **Step 4: Commit**

```bash
git add docs/ README.md CLAUDE.md report/
git commit -m "docs: update all references from ChillerGrid to ChillerLayout"
```

- [ ] **Step 5: Push**

```bash
git push origin main
```
