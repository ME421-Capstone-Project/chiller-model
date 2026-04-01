# Non-Grid Layouts for Chiller Positioning

**Date:** 2026-04-01
**Status:** Approved

## Summary

Rename `ChillerGrid` to `ChillerLayout` and add support for arbitrary (x, y) chiller
positions via a `from_positions()` class method and a new `SimulatorBuilder.with_layout()`
method. The existing `create_grid()` factory and `with_grid()` builder method remain as
convenience entry points for regular rectangular grids. No backward-compatibility alias
for `ChillerGrid` -- all references are renamed directly.

## Motivation

Real data center chiller installations are not always arranged in regular grids. Users
need to model arbitrary placements where pairwise distances between chillers are derived
from explicit (x, y) coordinates. The existing physics layer
(`GaussianPlumeModel.compute_interaction_matrix`) already operates on a raw `(n, 2)`
positions array, so the only coupling to grid geometry lives in `ChillerGrid.create_grid()`
and `SimulatorBuilder.with_grid()`.

## Design

### 1. Core Type Rename

`ChillerGrid` in `layout/grid.py` is renamed to `ChillerLayout`. Same frozen dataclass,
same fields:

- `positions_m: NDArray[np.float64]` -- shape `(n, 2)`
- `base_cop: float`
- `alpha: float`
- `ages_years: NDArray[np.float64]` -- shape `(n,)`
- `max_cooling_kw: float`

The `num_chillers` property remains unchanged.

All imports and references across the codebase are updated: no `ChillerGrid` alias is
provided.

### 2. New `from_positions()` Class Method

`ChillerLayout.from_positions()` accepts:

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `positions_m` | `NDArray[np.float64]` (n, 2) | yes | -- |
| `ages_years` | `NDArray[np.float64]` (n,) | yes | -- |
| `base_cop` | `float` | yes | -- |
| `alpha` | `float` | no | 0.7 |
| `max_cooling_kw` | `float` | yes | -- |

Validations:

- `positions_m.ndim == 2` and `positions_m.shape[1] == 2`
- `ages_years.shape[0] == positions_m.shape[0]`
- `max_cooling_kw > 0`

Returns a frozen `ChillerLayout` instance.

`create_grid()` is refactored to internally call `from_positions()` after generating
the meshgrid positions.

### 3. Builder API

`SimulatorBuilder` gains a new method:

```python
def with_layout(
    self,
    positions_m: NDArray[np.float64],
    ages_years: NDArray[np.float64],
    base_cop: float = ...,
    alpha: float = ...,
    max_cooling_kw: float = ...,
) -> "SimulatorBuilder":
```

This calls `ChillerLayout.from_positions()` and stores the result.

`with_grid()` remains unchanged in signature and behavior -- it still calls
`create_grid()`, which now returns a `ChillerLayout`.

Both methods write to the same internal field (renamed from `_grid` to `_layout`).
Calling either satisfies the builder requirement. Last call wins if both are used.

### 4. Internal Rename

All internal references in `Simulator`, `SimulatorBuilder`, and supporting code:

- `self._grid` -> `self._layout`
- Parameter names `grid` -> `layout`
- Type annotations `ChillerGrid` -> `ChillerLayout`

The physics layer (`GaussianPlumeModel`) takes `positions_m` as a raw array and
requires no changes.

### 5. Tests

- Rename all `ChillerGrid` references to `ChillerLayout` in existing tests.
- Add tests for `ChillerLayout.from_positions()`:
  - Valid construction with arbitrary positions
  - Validation errors for wrong `positions_m` shape
  - Validation error for mismatched `ages_years` length
  - Validation error for `max_cooling_kw <= 0`
- Add test for `SimulatorBuilder.with_layout()`:
  - End-to-end optimize with a non-grid layout (e.g. triangle of 3 chillers)
- Verify existing tests pass with the rename (no behavior change).

### 6. Documentation

- Update all markdown docs referencing `ChillerGrid` to `ChillerLayout`.
- Update `CLAUDE.md` architecture section.
- Update examples to mention `with_layout()` as an alternative to `with_grid()`.

## Scope Boundary

Out of scope for this change:

- Per-chiller heterogeneous properties (`base_cop`, `alpha`, `max_cooling_kw`)
- Named/labeled chiller nodes
- 3D positioning
- Any changes to the physics or optimization layers
