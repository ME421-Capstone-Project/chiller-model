# Documentation Rewrite for chiller_sim

**Date:** 2026-03-26
**Status:** Approved

## Context

The old `src.*` package (components, core, models, simulation) was removed in the chiller_sim refactor. All existing documentation references deleted class names (`ChillerArray`, `WindVector`, `SimulationEnvironment`, `Optimizer`, `DataCenter`, `DynamicSimulation`) and the old 4-module structure. Every doc file must be rewritten from scratch for the new API.

---

## Scope — Files changed

| File | Action | Notes |
|---|---|---|
| `docs/getting-started.rst` | Rewrite | New package structure, minimal example |
| `docs/user-guide.rst` | Rewrite | Architecture overview + full API narrative |
| `docs/architecture.rst` | Delete | Folded into user-guide |
| `docs/examples.rst` | Rewrite | 5 new examples with generated images |
| `docs/api/index.rst` | Rewrite | Toctree pointing to 3 new pages |
| `docs/api/components.rst` | Rename → `layout.rst` | `automodule:: chiller_sim.layout` |
| `docs/api/core.rst` | Delete | No equivalent module |
| `docs/api/models.rst` | Rename → `physics.rst` | `automodule:: chiller_sim.physics` |
| `docs/api/simulation.rst` | Rewrite | `automodule:: chiller_sim.simulation` |
| `scripts/example_1_first_optimization.py` | New | Generates `example1_cop_bar.png` |
| `scripts/example_2_thermal_interference.py` | New | Generates `example2_interaction_matrix.png` |
| `scripts/example_3_aging_capacity.py` | New | Generates `example3_aging_capacity.png` |
| `scripts/example_4_streaming.py` | New | Generates `example4_stream_timeline.png` |
| `scripts/example_5_wind_fn.py` | New | Generates `example5_wind_fn.png` |

No new `.rst` files. Two `.rst` files deleted. Five new scripts added.

---

## Section 1 — `getting-started.rst`

### Content structure

1. **Installation** — `pip install -e .` from source
2. **Basic concepts** — four short definitions:
   - COP: cooling output ÷ electrical input
   - Thermal interference: exhaust from one chiller heats a neighbour's intake
   - Max cooling capacity: nameplate limit per chiller; aging reduces it
   - Startup ramp: fresh chillers come online at reduced capacity
3. **Package structure** — three bullet points:
   - `chiller_sim.layout`: grid geometry and wind conditions
   - `chiller_sim.physics`: COP, degradation, ramp, and plume models
   - `chiller_sim.simulation`: builder, simulator, and result types
4. **Minimal working example** — `SimulatorBuilder` chain → `.build()` → `.optimize()` → print `active_mask`, `cop_array`, `total_work_kw`
5. **Understanding results** — one-line description of each `OptimizeResult` field

---

## Section 2 — `user-guide.rst`

### Content structure

**Architecture** (replaces `architecture.rst`)

ASCII diagram showing three layers:

```
layout (ChillerGrid, WindConditions)
    ↓
physics (CopFn, DegradationFn, RampFn, GaussianPlumeModel)
    ↓
simulation (SimulatorBuilder → Simulator)
```

One sentence per layer describing its role.

**SimulatorBuilder reference**

One subsection per method group:

- Grid: `with_grid(rows, cols, spacing_m, base_cop, max_cooling_kw, alpha, ages_years, seed)`
- Wind: `with_wind(speed_m_per_s, angle_deg)` / `with_wind_fn(fn)`
- Temperature: `with_ambient_temp(temp_k)` / `with_ambient_temp_fn(fn)`
- Load: `with_load_fn(fn)`
- Physics plugins: `with_cop_fn(fn)`, `with_degradation_fn(fn)`, `with_ramp_fn(fn)`
- Dispersion: `with_dispersion(coeff)`
- Switching: `with_switching_threshold(min_savings_kw)`
- Build: `build()` — validation rules (grid, wind/wind_fn, ambient_temp/fn, load_fn all required)

**Running simulations**

Three methods with when-to-use guidance:

- `optimize(time_hours, load_kw)` — single step, state-aware
- `stream(duration_hours, time_step_hours)` — yields `OptimizeResult` per step; advances clocks automatically
- `simulate(duration_hours, time_step_hours, initial_state)` — returns `SimulationResult`

**Results reference**

`OptimizeResult` fields: `time_hours`, `load_kw`, `active_mask`, `cop_array`, `temp_rise_array`, `total_work_kw`, `baseline_work_kw`, `savings_fraction`

`SimulationResult` properties: `total_work_kw` (array), `loads_kw` (array), `savings_fraction` (array), `schedule` (2D bool array), `cop_arrays` (2D array)

**Physics plugins**

Protocol signatures and default implementations for each:

- `CopFn(base_cop, temp_rise_k, ambient_temp_k) → float`
- `DegradationFn(age_years) → float` — default: `default_capacity_degradation_fn(years_to_80_pct=10.0)`
- `RampFn(time_since_start_hours) → float` — default: linear ramp, 0.1 at t=0, 1.0 at t=0.25h
- `WindFn(time_hours) → WindConditions`
- `AmbientTempFn(time_hours) → float`

**Warm start with `InitialState`**

Show how to pass `InitialState(active_mask, time_since_start_hours)` to `simulate()`.

---

## Section 3 — `examples.rst`

Five examples in order of increasing complexity. Each has: one-sentence intro, code block, expected output snippet, `.. image::` referencing the generated PNG.

### Example 1 — Your First Optimization

Builds a 2×2 grid with `SimulatorBuilder`, calls `optimize(time_hours=0.0)`, prints active mask, COP per chiller, and total work.

Image: horizontal bar chart of COP for each chiller, active bars in dark teal, inactive bars in light grey.

### Example 2 — Thermal Interference

1×4 row of chillers, wind blowing along the row (angle=0°). Prints inlet temperature rise at each position. Shows that downwind chillers run hotter.

Image: heatmap of the 4×4 interaction matrix — dark teal for high interaction, white for zero.

### Example 3 — Capacity, Aging, and the Feasibility Gate

Two simulations at the same load: brand-new fleet (`ages_years=np.zeros(4)`) vs. aged fleet (`ages_years=np.full(4, 20.0)`). Aged chillers have lower effective capacity so more must activate.

Image: grouped bar chart — two groups (new / aged), bars showing `n_active` and `total_work_kw` side by side.

### Example 4 — Streaming a 24-Hour Load Profile

Sinusoidal load function (300–800 kW, 24h period) fed to `stream()` with 1h time step. Prints load, work, active count per step.

Image: three-panel line plot sharing x-axis (time): top = load kW, middle = total work kW, bottom = active chiller count.

### Example 5 — Time-Varying Wind

Custom `wind_fn` that rotates wind direction sinusoidally (±60° around 90°, 12h period). Feed into `stream()` over 24h. Shows total work varying as wind alignment changes.

Image: two-panel line plot — top = wind angle over time, bottom = total work kW over time.

---

## Section 4 — `api/` pages

Three thin files, each a heading plus `automodule::`:

**`layout.rst`**
```
Layout
======
.. automodule:: chiller_sim.layout
   :members:
```
Documents `ChillerGrid`, `WindConditions`.

**`physics.rst`**
```
Physics
=======
.. automodule:: chiller_sim.physics
   :members:
```
Documents all protocol classes and default function factories.

**`simulation.rst`**
```
Simulation
==========
.. automodule:: chiller_sim.simulation
   :members:
```
Documents `SimulatorBuilder`, `Simulator`, `OptimizeResult`, `SimulationResult`, `InitialState`.

**`index.rst`** updated toctree:
```
.. toctree::
   layout
   physics
   simulation
```

---

## Section 5 — Image scripts

### Style rules (applied in every script)

- Figure background: white (`#ffffff`)
- Primary color: `#1a5f7a` (dark teal)
- Secondary/accent: `#2d9db0`
- Inactive/muted: `#c8dde4`
- Font: default sans-serif, normal weight
- Spines: top and right removed; left and bottom in `#cccccc`
- Grid lines: none (or very light `#eeeeee` horizontal-only where helpful)
- No legend box border
- `plt.tight_layout()` called before save
- Saved with `dpi=150`, `bbox_inches='tight'`
- `plt.show()` never called (headless-safe)
- Each script is runnable standalone: `python scripts/example_N_*.py`

### Verification

After each script generates its image, the PNG is read with the Read tool to visually check for:
- Text overlap (axis labels, tick labels, title)
- Adequate padding around chart elements
- Color legibility

Scripts are adjusted and re-run until each image is clean.

### Output paths

All images saved to `docs/_static/images/`:

| Script | Output |
|---|---|
| `scripts/example_1_first_optimization.py` | `docs/_static/images/example1_cop_bar.png` |
| `scripts/example_2_thermal_interference.py` | `docs/_static/images/example2_interaction_matrix.png` |
| `scripts/example_3_aging_capacity.py` | `docs/_static/images/example3_aging_capacity.png` |
| `scripts/example_4_streaming.py` | `docs/_static/images/example4_stream_timeline.png` |
| `scripts/example_5_wind_fn.py` | `docs/_static/images/example5_wind_fn.png` |
