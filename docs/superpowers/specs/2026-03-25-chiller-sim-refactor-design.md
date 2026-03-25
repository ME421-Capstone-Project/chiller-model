# chiller-sim Refactor Design

**Date:** 2026-03-25
**Status:** Approved

## Overview

Refactor the `chiller-sim` package for simplicity, readability, and real-time usability. The goal is a flat, builder-friendly API that serves both researchers (quick notebook usage) and developers (embedding in larger systems), with pluggable physics functions and a state-aware optimizer.

No backward compatibility required. All existing call sites (scripts, docs) will be updated.

---

## Module Structure

One package with three sub-folders for internal organization. All public symbols re-exported from the top-level `__init__.py` so users never import from submodules.

```
src/chiller_sim/
    __init__.py              # public API: Simulator, OptimizeResult, SimulationResult, InitialState
    layout/
        __init__.py
        grid.py              # ChillerGrid
        wind.py              # WindConditions, WindFn Protocol
    physics/
        __init__.py
        gaussian_plume.py    # GaussianPlumeModel
        cop.py               # CopFn Protocol + default implementation
        degradation.py       # DegradationFn Protocol + default implementation
        ramp.py              # RampFn Protocol + default implementation
        load.py              # LoadFn Protocol (no default — user must supply)
        ambient_temp.py      # AmbientTempFn Protocol (no default — user must supply if time-varying)
    simulation/
        __init__.py
        builder.py           # SimulatorBuilder (returned by Simulator())
        simulator.py         # Simulator
        results.py           # OptimizeResult, SimulationResult, InitialState
```

**Import convention:**
```python
from chiller_sim import Simulator
from chiller_sim import OptimizeResult, SimulationResult, InitialState  # for type hints
```

---

## Interfaces

### Construction (Builder Pattern)

`Simulator()` returns a `SimulatorBuilder`. Calling `.build()` precomputes the N×N thermal interaction matrix and freezes all configuration.

```python
sim = (Simulator()
    .with_grid(rows=4, cols=4, spacing_m=10.0, base_cop=5.5, alpha=0.7,
               ages_years=None, seed=42)
    .with_wind(speed_m_per_s=3.0, angle_deg=0.0)          # fixed wind
    .with_wind_fn(my_wind_fn)                               # time-varying, overrides fixed wind
    .with_ambient_temp(temp_k=298.15)                       # fixed ambient temp (required if no fn)
    .with_ambient_temp_fn(my_temp_fn)                       # time-varying, overrides fixed
    .with_dispersion(coeff=1.2)                             # optional, default 1.2
    .with_load_fn(my_load_fn)                               # required — no default
    .with_cop_fn(my_cop_fn)                                 # optional, uses default if omitted
    .with_degradation_fn(my_deg_fn)                         # optional, uses default if omitted
    .with_ramp_fn(my_ramp_fn)                               # optional, uses default if omitted
    .with_switching_threshold(min_savings_kw=10.0)          # optional, default 0.0
    .build())
```

**Seed persistence:** The `seed` passed to `.with_grid()` is stored on the builder. When `.build()` is called (including rebuilds after `.with_wind()` etc.), the same seed is reused so ages are not re-randomized on rebuild. If `ages_years` is supplied explicitly, `seed` is ignored.

To update a live simulator (e.g. new wind conditions), chain from the existing instance and rebuild:

```python
sim = sim.with_wind(speed_m_per_s=5.0, angle_deg=45.0).build()
```

### Plugin Function Signatures

All physics functions are plain callables — no inheritance required. Protocols define the expected signatures for type checking.

```python
# COP: given base COP, thermal temp rise, and ambient temp, return effective COP
CopFn:            (base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float

# Degradation: given age in years, return multiplier in [0.0, 1.0]
DegradationFn:    (age_years: float) -> float

# Ramp: given time since startup in hours, return multiplier in [0.0, 1.0]
RampFn:           (time_since_start_hours: float) -> float

# Load: given simulation time, return cooling load in kW
LoadFn:           (time_hours: float) -> float

# Wind: given simulation time, return (speed_m_per_s, angle_deg)
WindFn:           (time_hours: float) -> tuple[float, float]

# Ambient temperature: given simulation time, return temperature in Kelvin
AmbientTempFn:    (time_hours: float) -> float
```

**Required at `.build()`:** `load_fn` and either `ambient_temp` or `ambient_temp_fn`. `.build()` raises `ValueError` if either is missing.

**Wind:** if `wind_fn` is provided it is called at each step; otherwise the fixed wind from `.with_wind()` is used. A wind change triggers recomputation of the interaction matrix for that step.

**Ambient temp:** if `ambient_temp_fn` is provided it is called at each step; otherwise the fixed value from `.with_ambient_temp()` is used. Ambient temp is passed to `cop_fn` at each step — the default `cop_fn` ignores it, but custom implementations can use it.

### Plugin Composition Order

The `Simulator` applies the three physics plugins in this fixed sequence for each chiller at each time step:

```
effective_cop[i] = cop_fn(base_cop[i], temp_rise_k[i], ambient_temp_k)
                   × degradation_fn(age_years[i])
                   × ramp_fn(time_since_start_hours[i])
```

`cop_fn` handles the thermal interaction penalty. `degradation_fn` handles age-related COP loss. `ramp_fn` handles startup ramp-up. Each is applied independently and multiplicatively. Custom implementations replace only the function they override; the others use their defaults.

### Real-Time Optimization

Single time-point query. Uses `load_fn(time_hours)` unless `load_kw` is passed explicitly.

```python
result = sim.optimize(time_hours=8.0)
result = sim.optimize(time_hours=8.0, load_kw=500.0)  # explicit override
```

The `Simulator` maintains internal chiller state between `optimize()` calls — which chillers are running and for how long — so ramp factors and switching thresholds apply correctly across sequential calls.

### Initial State

Both `stream()` and `simulate()` accept an optional `InitialState` describing which chillers are already running and how long they have been running. If omitted, all chillers start off with zero elapsed time.

```python
InitialState:
    active_mask: NDArray[bool]               # which chillers are currently on
    time_since_start_hours: NDArray[float]   # runtime for each chiller (ignored if not active)
```

Chiller ages are part of `ChillerGrid` (set at build time via `.with_grid(ages_years=...)`), not `InitialState`.

### Dynamic Simulation

**Streaming** (real-time control loop, generator):
```python
for step in sim.stream(duration_hours=24.0, time_step_hours=1.0):
    send_to_controller(step.active_mask, step.time_hours)

# with non-zero initial state
state = InitialState(active_mask=np.array([True, True, False, False]),
                     time_since_start_hours=np.array([2.0, 0.1, 0.0, 0.0]))
for step in sim.stream(duration_hours=24.0, time_step_hours=1.0, initial_state=state):
    ...
```

**Batch** (full simulation, returns aggregated result):
```python
result = sim.simulate(duration_hours=24.0, time_step_hours=1.0)
result = sim.simulate(duration_hours=24.0, time_step_hours=1.0, initial_state=state)
result.schedule           # NDArray[bool], shape (n_steps, n_chillers)
result.schedule[:, 3]     # chiller 3's on/off history
```

**State at start of run:** Both `stream()` and `simulate()` initialize from `InitialState` if provided, otherwise from all-off. Prior `optimize()` call state does not carry over into `stream()`/`simulate()`.

`stream()` and `simulate()` produce identical schedules for the same inputs and initial state.

### Result Types

`sim.optimize()` and `sim.stream()` both return `OptimizeResult`. `SimulationResult` is defined in terms of `OptimizeResult` — no data duplication.

```python
OptimizeResult:
    time_hours: float
    load_kw: float                   # load used for this optimization
    active_mask: NDArray[bool]       # which chillers are on
    total_work_kw: float             # total electrical work
    baseline_work_kw: float          # work if all chillers were on (steady-state ramp)
    savings_fraction: float          # (baseline - total_work) / baseline
    cop_array: NDArray[float]        # per-chiller effective COP
    temp_rise_array: NDArray[float]  # per-chiller inlet temp rise (K)

SimulationResult:
    steps: list[OptimizeResult]      # one per time step, in order

    # convenience properties (derived from steps, no data duplication)
    @property schedule        -> NDArray[bool]   # shape (n_steps, n_chillers)
    @property total_work_kw   -> NDArray[float]  # shape (n_steps,)
    @property loads_kw        -> NDArray[float]  # shape (n_steps,)
    @property savings_fraction -> NDArray[float] # shape (n_steps,)
    @property cop_arrays      -> NDArray[float]  # shape (n_steps, n_chillers)
```

---

## Data Types

### ChillerGrid

Frozen dataclass holding the physical layout of chillers:

```python
ChillerGrid:
    positions_m: NDArray[float]   # shape (n_chillers, 2), (x, y) in metres
    base_cop: float               # rated COP for all chillers
    alpha: float                  # temperature sensitivity coefficient (default 0.7)
    ages_years: NDArray[float]    # shape (n_chillers,), per-chiller age
```

Created via the builder (`.with_grid()`), not directly by users.

### WindConditions

Frozen dataclass. Ambient temperature is independent and not stored here.

```python
WindConditions:
    speed_m_per_s: float
    angle_deg: float              # direction in degrees, CCW from east
```

---

## State-Aware Optimizer (Level 3)

The optimizer is time-aware and maintains state across `optimize()` calls within a session. `stream()` and `simulate()` reset this state at the start of each call.

**Baseline computation:** Before the greedy loop, the baseline is computed by evaluating all N chillers as active with steady-state ramp (all `ramp_fn` values saturated at 1.0, regardless of current startup clocks). This gives a consistent, comparable reference across calls. This baseline is stored in `baseline_work_kw` on the result.

**Algorithm:**

1. Initialize the prior active set. On the first `optimize()` call, start from all-on (steady-state ramp). On subsequent calls, start from the active set left by the previous call with their current startup clocks.
2. Evaluate all single-chiller toggles (activate an off chiller, or deactivate an on chiller).
3. Apply the `min_savings_kw` threshold symmetrically: a toggle is only eligible if it reduces total work by at least `min_savings_kw`. This prevents switching in either direction for marginal gains.
4. For activation candidates: evaluate using `ramp_fn(0.0)` (as if the chiller just started). Once committed, the chiller's startup clock begins and advances each subsequent call.
5. Commit the best eligible toggle if it reduces total work.
6. Repeat from step 2 until no eligible improving toggle remains.

**Ramp state on first call:** On the first `optimize()` call, all chillers in the initial all-on set are assumed to be at steady state (startup clock = infinity, `ramp_fn` = 1.0). This ensures the baseline is meaningful and avoids a degenerate first result.

---

## Physics

The thermal interaction model is unchanged from the original. The N×N interaction matrix `A` is precomputed once at `.build()` time:

```
A[k, m] = exp(-lateral² / (σ · (longitudinal + 1))) / (longitudinal + 1)   if longitudinal > 0
         = 0                                                                  otherwise
```

Where `longitudinal` is the along-wind distance (metres) and `lateral` is the cross-wind distance (metres) from chiller k to chiller m. Diagonal entries are zero (a chiller does not interfere with itself).

Default COP function:
```
cop_fn(base_cop, temp_rise_k, ambient_temp_k) = base_cop / (1 + alpha × temp_rise_k)
```

The default implementation ignores `ambient_temp_k` — it uses only the rise above ambient. Custom implementations may use absolute inlet temperature (`ambient_temp_k + temp_rise_k`) for more detailed models.

`alpha` is the temperature sensitivity coefficient, configurable via `.with_grid(alpha=0.7)`. Default value: `0.7`.

Default degradation function (exponential decay):
```
degradation_fn(age_years) = exp(-rate × age_years)
```
Where `rate` is chosen so that a 1-year-old chiller retains 80% of its rated COP.

Default ramp function (linear ramp):
```
ramp_fn(time_since_start_hours) = min(1.0, time_since_start_hours / startup_time_hours)
```
Default `startup_time_hours = 0.25`.

---

## Testing Strategy

Tests are behavior-oriented — they validate outcomes, not internal structure. Organized into three groups:

### 1. Optimization Correctness
- Optimizing a crowded grid uses fewer chillers and less energy than all-on
- `min_savings_kw` threshold suppresses switching for marginal gains
- Downwind chillers have higher inlet temperatures than upwind chillers
- Chiller state (startup clock) persists across sequential `optimize()` calls
- Savings fraction is in [0, 1]
- A new `simulate()` call produces the same schedule regardless of prior `optimize()` calls (state reset)

### 2. Physics Plugins
- Custom `cop_fn` produces different work output than the default
- Custom `degradation_fn` changes effective COP for aged chillers
- Custom `ramp_fn` increases work during the startup window
- Custom `load_fn` drives the correct load at each time step

### 3. Dynamic Simulation
- `simulate()` returns correct number of steps for given duration and time step
- `result.schedule` has shape `(n_steps, n_chillers)`
- A chiller activated at step N carries startup state into step N+1 within the same run
- `stream()` and `simulate()` produce identical schedules for the same inputs
- Switching threshold prevents cycling near load boundary

**Out of scope:** Internal class construction, field validation, NumPy matrix math — these are implementation details.

---

## Key Simplifications vs. Current Code

| Current | Refactored |
|---|---|
| 5 objects to wire before running | 1 builder chain + `.build()` |
| `BaseInteractionModel` referenced but missing | Protocols defined and present |
| `ChillerArray` claims immutability but isn't | `ChillerGrid` is a frozen dataclass |
| Optimizer restarts from all-on each step | Optimizer starts from prior active set |
| No switching threshold | Configurable `min_savings_kw` |
| `DataCenter` untested | Load is a plain `LoadFn` callable — tested via plugin tests |
| Doc references `result.load_array` (wrong) | `load_kw: float` in all result types |
| `alpha` buried in `ChillerArray` | Explicit in `.with_grid(alpha=0.7)` |
| Random ages non-reproducible at direct construction | `seed` stored on builder, reused on rebuild |
