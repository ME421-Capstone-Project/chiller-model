# Max Cooling Capacity with Age Degradation

**Date:** 2026-03-26
**Status:** Approved

## Context

The current simulator models chiller aging as a COP penalty (`DegradationFn` multiplied into `cop_array` inside `_evaluate_work`). This produces a single best chiller running all day regardless of load, because splitting load across chillers with equal or lower COP never reduces total electrical work.

The more physically realistic model is: aging reduces a chiller's **maximum cooling output** (nameplate capacity), not its efficiency. As chillers age, more units must be activated to collectively cover the facility load. Startup ramp-up is also remodelled: a cold chiller comes online at reduced *capacity*, not reduced *efficiency*.

## Scope

Four files change. No new files. No new protocols.

---

## Section 1 — Data model (`ChillerGrid`)

`ChillerGrid` gains one new required field:

```python
max_cooling_kw: float   # nameplate capacity of a brand-new chiller (same for all)
```

`create_grid` gains the matching required parameter `max_cooling_kw: float`.

Validation in `create_grid`: `max_cooling_kw` must be `> 0`, otherwise raise `ValueError`.

The effective capacity of chiller `i` at any point in time is:

```
effective_cap[i] = max_cooling_kw * degradation_fn(ages_years[i]) * ramp_fn(time_since_start[i])
```

---

## Section 2 — Physics (`degradation.py`)

`default_degradation_fn` (hardcoded 80% at 1 year, not parameterised) is **replaced** by:

```python
def default_capacity_degradation_fn(years_to_80_pct: float) -> DegradationFn:
    rate = -math.log(0.8) / years_to_80_pct
    def _fn(age_years: float) -> float:
        return math.exp(-rate * age_years)
    return _fn
```

`DegradationFn` protocol is unchanged — same `(age_years: float) → float` signature.

The hardcoded `_DECAY_RATE` constant is removed.

---

## Section 3 — Simulation (`simulator._evaluate_work`)

**Remove** the degradation factor from COP:

```python
# BEFORE
cop_array[i] = cop_fn(...) * deg_factors[i] * ramp_factors[i]

# AFTER
cop_array[i] = cop_fn(...)
```

**Move ramp to capacity** and add feasibility gate (inserted after the `n_active == 0` check):

```python
ramp_factors = (
    np.ones(n)
    if use_steady_state_ramp
    else np.array([self._ramp_fn(t) for t in time_since_start])
)
effective_caps = np.array([
    self._grid.max_cooling_kw
    * self._degradation_fn(self._grid.ages_years[i])
    * ramp_factors[i]
    for i in range(n)
])
if load_kw > effective_caps[active_mask].sum():
    return float("inf"), np.zeros(n), np.zeros(n)
```

The equal load split (`load_kw / n_active`) is unchanged.

`use_steady_state_ramp=True` sets all ramp factors to 1.0, giving full capacity for greedy evaluation and first-call steady-state calculations.

---

## Section 4 — Builder (`builder.py` / `simulator.py`)

`with_grid()` gains `max_cooling_kw: float` as a **required** positional-ish parameter (no default — omitting it is a clear call-site error):

```python
def with_grid(
    self,
    rows: int,
    cols: int,
    spacing_m: float,
    base_cop: float,
    max_cooling_kw: float,       # new
    alpha: float = 0.7,
    ages_years: NDArray | None = None,
    seed: int | None = None,
) -> SimulatorBuilder:
```

`with_degradation_fn()`, `_degradation_fn`, and `degradation_fn` in `Simulator.__init__` keep their existing names — there is only one degradation concept.

Default resolved at `build()` time (if `with_degradation_fn` not called):

```python
default_capacity_degradation_fn(years_to_80_pct=10.0)
```

`Simulator.__init__` signature: `degradation_fn` parameter unchanged in name, updated in meaning.

---

## Section 5 — Tests

| Test | What it checks |
|---|---|
| `test_create_grid_rejects_zero_max_cooling_kw` | `ValueError` on non-positive capacity |
| `test_capacity_gate_forces_multiple_chillers` | Low `max_cooling_kw` → optimizer activates >1 chiller |
| `test_aged_chillers_require_more_active` | Older `ages_years` → more chillers needed for same load |
| `test_ramp_reduces_effective_capacity` | Fresh chiller contributes ~0 capacity; optimizer adds extras |
| `test_default_capacity_degradation_fn_at_threshold` | `fn(years_to_80_pct) ≈ 0.8` |
| `test_cop_unaffected_by_age` | COP is identical for new and old chillers under same thermal conditions |
| Update existing `test_custom_degradation_fn_affects_aged_chillers` | Now tests capacity, not work |

---

## Files changed

| File | Change |
|---|---|
| `src/chiller_sim/layout/grid.py` | Add `max_cooling_kw` field + validation |
| `src/chiller_sim/physics/degradation.py` | Replace `default_degradation_fn` with `default_capacity_degradation_fn(years_to_80_pct)` |
| `src/chiller_sim/simulation/simulator.py` | Move ramp+degradation from COP to capacity; add feasibility gate |
| `src/chiller_sim/simulation/builder.py` | Add `max_cooling_kw` to `with_grid()`; update default degradation fn |
