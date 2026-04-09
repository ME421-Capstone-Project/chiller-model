# Gaussian Plume Wind-Speed Dependence

**Issue:** anthropics/chiller-model#10 — `GaussianPlumeModel.compute_interaction_matrix` ignores `wind.speed_m_per_s`, so a 0.1 m/s breeze produces the same thermal interference as a 10 m/s gale.

## Goal

Make the Gaussian plume interaction scale with wind speed, and document the equations for both the plume model and the default COP function in the user guide.

## Non-goals

- No full Pasquill–Gifford stability-class rewrite. σ_y stays constant (controlled by `dispersion_coeff`).
- No changes to `WindConditions`, `SimulatorBuilder`, or any caller's public API.

## Design

### Physics change

Standard ground-level Gaussian plume concentration scales as `1/u`. With σ_y held constant, the simplified per-pair influence becomes:

```
I[k, m] = 0                                            if u < u_min
        = exp(-y² / (σ · (x + 1))) / (u · (x + 1))     if x > 0 and u ≥ u_min
        = 0                                            otherwise
```

where
- `x` is the along-wind (longitudinal) distance from chiller `k` to chiller `m`
- `y` is the cross-wind (lateral) distance
- `u` is `wind.speed_m_per_s`
- `σ` is `dispersion_coeff`
- `u_min` is the new `u_min_m_per_s` field

**Calm-wind behaviour:** `u < u_min` is treated as a cutoff — the interaction matrix is identically zero. `u_min` is not a floor on `u`; it is a hard threshold below which the plume model is assumed not to propagate thermal interference at any distance.

### Code change surface

Only `src/chiller_sim/physics/gaussian_plume.py`:

1. Add `u_min_m_per_s: float = 0.1` to `GaussianPlumeModel`.
2. In `compute_interaction_matrix`:
   - Read `u = wind.speed_m_per_s`.
   - If `u < u_min_m_per_s`, return `np.zeros((n, n))` immediately.
   - Otherwise, divide the existing influence by `u` in addition to `denom`.
3. Update the class docstring to state the equation and the `u_min` cutoff semantics.

No changes elsewhere in `src/`.

### Docs change surface

`docs/user-guide.rst` gains rendered equations (Sphinx `.. math::`) for both physics defaults:

- **Default COP** near the `CopFn` section:

  ```
  COP(ΔT) = COP_base / (1 + α · ΔT_rise)
  ```

  With a sentence explaining why COP falls as the effective inlet temperature rises.

- **Gaussian plume** near the `with_plume_model` section: the piecewise equation above, plus a note that this is a simplified constant-σ form of the standard ground-level Gaussian plume and that the `1/u` factor is the physical rationale for the new wind-speed dependence.

### Tests

Add to `tests/test_physics.py`:

1. **Scales as 1/u** — for two `GaussianPlumeModel` runs with identical geometry but wind speeds `u` and `2u` (both ≥ `u_min`), every nonzero entry of the second matrix equals half the corresponding entry of the first.
2. **Cutoff below u_min** — with `u = u_min / 2`, the interaction matrix is all zeros.
3. **At u_min boundary** — with `u = u_min`, nonzero interactions still exist for downwind pairs (the cutoff is strict `<`, not `≤`).
4. **Existing tests still pass** — all current tests in `tests/test_physics.py` use `u = 3.0 m/s` which is well above the default `u_min = 0.1`, and they compare entries relatively (not absolutely), so they continue to hold.

## Acceptance

- `pytest` green.
- `ruff check . && ruff format --check .` clean.
- `mypy` clean.
- `docs/user-guide.rst` renders both new equation blocks in `make html`.
- Issue #10 can be closed: `with_wind(speed_m_per_s=X)` now meaningfully affects the interaction matrix.
