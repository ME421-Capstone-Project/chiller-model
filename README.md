# Chiller Array Simulation Package

Simulate how data center chillers affect each other when packed together -- and find the most efficient way to run them.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What This Does

When chillers sit close together, hot exhaust from one can blow into another's intake. That heats up the air and makes the second chiller work harder -- using more electricity for the same cooling.

This package models that effect and helps you choose which chillers to run so you use less energy.

## Features

- **Thermal interference**: Physics-based Gaussian plume model of exhaust affecting neighbors
- **Optimization**: Greedy selection of the best subset of chillers to run
- **Aging**: Models capacity loss as chillers get older
- **Startup ramp**: Freshly started chillers come online at reduced capacity
- **Dynamic simulation**: Time-varying load, wind, and ambient temperature
- **Pluggable physics**: Swap COP, degradation, and ramp functions via the builder API

## Installation

```bash
git clone https://github.com/example/chiller-model.git
cd chiller-model
pip install -e .
```

For development (tests, linting, docs):

```bash
pip install -e ".[dev,docs]"
```

### Requirements

- Python 3.10+
- NumPy >= 1.24.0
- Pydantic >= 2.0.0

## Quick Start

```python
from chiller_sim import Simulator

sim = (
    Simulator()
    .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 800.0)
    .build()
)

result = sim.optimize(time_hours=0.0)
print(f"Active: {result.active_mask}")
print(f"Work:   {result.total_work_kw:.2f} kW")
print(f"Saved:  {result.savings_fraction:.1%}")
```

## Project Structure

```
chiller-model/
├── src/chiller_sim/
│   ├── layout/          # Grid geometry and wind conditions
│   │   ├── grid.py      # ChillerLayout (frozen dataclass)
│   │   └── wind.py      # WindConditions, WindFn protocol
│   ├── physics/         # Pluggable physics models
│   │   ├── cop.py       # CopFn protocol + default
│   │   ├── degradation.py  # DegradationFn protocol + default
│   │   ├── ramp.py      # RampFn protocol + default
│   │   ├── gaussian_plume.py  # Thermal plume dispersion
│   │   ├── load.py      # LoadFn protocol
│   │   └── ambient_temp.py  # AmbientTempFn protocol
│   └── simulation/      # Builder, simulator, results
│       ├── builder.py   # SimulatorBuilder (fluent API)
│       ├── simulator.py # Simulator (optimize, stream, simulate)
│       └── results.py   # OptimizeResult, SimulationResult, InitialState
├── tests/               # Behavior-oriented tests
├── scripts/             # Example scripts with generated images
├── docs/                # Sphinx documentation
├── report/              # LaTeX technical report
├── demo.ipynb           # Interactive notebook
└── pyproject.toml
```

## Architecture

Three layers, each depending only on the one above:

```
layout (ChillerLayout, WindConditions)
    |
physics (CopFn, DegradationFn, RampFn, GaussianPlumeModel)
    |
simulation (SimulatorBuilder -> Simulator)
```

**layout** -- Where chillers sit (on a grid via `with_grid()` or in arbitrary positions via `with_layout()`) and what the wind looks like.

**physics** -- Pluggable functions for COP degradation, capacity aging, startup ramp, and thermal plume dispersion.

**simulation** -- Fluent builder assembles the pieces, runs the optimizer, and returns typed results.

## Running Tests

```bash
pytest              # all tests
pytest --cov=src    # with coverage
```

## Example Scripts

Run from the project root:

```bash
python scripts/example_1_first_optimization.py
python scripts/example_2_thermal_interference.py
python scripts/example_3_aging_capacity.py
python scripts/example_4_streaming.py
python scripts/example_5_wind_fn.py
```

## Documentation

Build the Sphinx docs:

```bash
cd docs && make html
```

## Physics

**Thermal interference**: Hot exhaust is modeled as a Gaussian plume that spreads downwind. Chillers downwind get warmer intake air and lose efficiency.

**COP formula**: Each chiller's COP drops with inlet temperature rise:

$$COP = \frac{COP_{base}}{1 + \alpha \cdot \Delta T}$$

**Aging**: Older chillers lose cooling capacity via an exponential decay function. The optimizer accounts for reduced capacity when selecting which chillers to run.

**Startup ramp**: Freshly started chillers produce reduced cooling output, ramping linearly to full capacity over 15 minutes by default.

## License

MIT License -- see [LICENSE](LICENSE).

## References

- ASHRAE Handbook -- Fundamentals, 2021
- ASHRAE Handbook -- HVAC Systems and Equipment, Chapter 40
- AHRI Standard 550/590-2015
