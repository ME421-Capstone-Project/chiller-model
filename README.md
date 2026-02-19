# Chiller Array Simulation Package

Simulate how data center chillers affect each other when packed together—and find the most efficient way to run them.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://chiller-model.readthedocs.io)

## What This Does

When chillers sit close together, hot exhaust from one can blow into another’s intake. That heats up the air and makes the second chiller work harder—using more electricity for the same cooling.

This package models that effect and helps you choose which chillers to run so you use less energy.

**What we’ve seen in simulations:**
- Thermal interference can cut a chiller’s efficiency by **30%** or more
- Picking the right chillers (and sometimes running fewer) can save **10–15%** energy
- Older chillers lose efficiency over time; the model accounts for that too

## Features

- **Thermal interference**: Physics-based model of how exhaust affects neighbors
- **Optimization**: Finds which chillers to run for best efficiency
- **Aging**: Models COP loss as chillers get older
- **Dynamic simulation**: Time-varying load, wind, and chiller startup
- **Modular design**: Swap models and components easily
- **SI units**: All calculations in standard units (K, Pa, kg/s, J)

## Installation

### From Source

```bash
git clone https://github.com/example/chiller-model.git
cd chiller-model
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/example/chiller-model.git
cd chiller-model
pip install -e ".[dev,docs]"
```

### Requirements

- Python 3.10 or higher
- NumPy >= 1.24.0
- Pydantic >= 2.0.0

## Quick Start

```python
import numpy as np
from src.components import WindVector, ChillerArray
from src.models import GaussianPlumeModel
from src.simulation import SimulationEnvironment, Optimizer

# Create wind conditions (5 m/s from the east)
wind = WindVector(
    velocity_m_per_s=(5.0, 0.0),
    ambient_temp_k=298.15  # 25°C
)

# Create a 5x5 chiller array with 3m spacing
array = ChillerArray.create_grid(
    rows=5, cols=5, spacing_m=3.0,
    base_cop=4.0, alpha=0.7
)

# Set up simulation with Gaussian plume model
model = GaussianPlumeModel(dispersion_coeff=1.2)
env = SimulationEnvironment(array, wind, model)

# Compare standard vs. optimized activation for 100 kW load
# Standard: first 15 chillers
state_std = np.zeros(25, dtype=bool)
state_std[:15] = True
result_std = env.compute_performance(state_std, total_load_kw=100.0)

# Optimized: greedy selection of best 15 chillers
optimizer = Optimizer(env, total_load_kw=100.0)
opt_result = optimizer.optimize_greedy(min_active=15)
result_opt = env.compute_performance(opt_result.optimal_mask, 100.0)

print(f"Standard: {result_std.total_work_kw:.2f} kW")
print(f"Optimized: {result_opt.total_work_kw:.2f} kW")
print(f"Savings: {(1 - result_opt.total_work_kw/result_std.total_work_kw)*100:.1f}%")
```

## Project Structure

```
chiller-model/
├── src/
│   ├── core/           # Constants and Pydantic configurations
│   │   ├── configs.py
│   │   └── constants.py
│   ├── components/     # Physical component models
│   │   ├── wind.py
│   │   ├── chiller.py
│   │   ├── chiller_array.py
│   │   └── data_center.py
│   ├── models/         # Thermal interaction models
│   │   ├── base_interaction.py
│   │   └── gaussian_plume.py
│   └── simulation/     # Simulation and optimization
│       ├── environment.py
│       └── optimizer.py
├── tests/              # Unit and integration tests
├── verification/       # AHRI 550/590 compliance tests
├── docs/               # Sphinx documentation
├── demo.ipynb          # Interactive demonstration notebook
└── pyproject.toml
```

## Architecture

The package uses a modular, composition-based architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Simulation Layer                              │
│  ┌──────────────────────┐    ┌───────────────────────┐         │
│  │ SimulationEnvironment│◄───│     Optimizer         │         │
│  │ (orchestrates)       │    │  (optimization)       │         │
│  └─────────┬────────────┘    └───────────────────────┘         │
└────────────┼─────────────────────────────────────────────────────┘
             │ composes ▼
┌────────────┴─────────────────────────────────────────────────────┐
│                   Component Layer                                │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐          │
│  │ChillerArray│  │ WindVector  │  │ InteractionModel │          │
│  │(positions) │  │(atmosphere) │  │  (pluggable)     │          │
│  └────────────┘  └─────────────┘  └────────┬─────────┘          │
└────────────────────────────────────────────┼────────────────────┘
                                              │ implements ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Model Layer                                    │
│  ┌──────────────────────┐    ┌───────────────────────┐          │
│  │BaseInteractionModel  │◄───┤ GaussianPlumeModel   │          │
│  │  (abstract)          │    │  (physics)           │          │
│  └──────────────────────┘    └───────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Composition over Inheritance**: Build systems by composing component instances
- **Immutability**: Thermodynamic states use frozen dataclasses and NamedTuples
- **Vectorization**: All array operations use NumPy (no explicit for-loops)
- **Type Safety**: Comprehensive type hints with Pydantic validation

For detailed architecture diagrams and data flow, see [Architecture Documentation](docs/architecture.rst).

## Documentation

Full documentation is available at [chiller-model.readthedocs.io](https://chiller-model.readthedocs.io).

- [Getting Started](https://chiller-model.readthedocs.io/getting-started.html)
- [Architecture & Module Flow](https://chiller-model.readthedocs.io/architecture.html) - Visual system architecture
- [User Guide](https://chiller-model.readthedocs.io/user-guide.html)
- [Examples](https://chiller-model.readthedocs.io/examples.html)
- [API Reference](https://chiller-model.readthedocs.io/api/index.html)

## Example Scripts

Run these from the project root (with `PYTHONPATH=src`):

- **Aging**: `python scripts/example_chiller_age.py` — how chiller age affects COP
- **Dynamic simulation**: `python scripts/example_dynamic_simulation.py` — varying load, wind, and startup
- **Doc figures**: `python scripts/generate_doc_figures.py` — generates plots for the docs

## Interactive Demo

The `demo.ipynb` notebook provides an interactive walkthrough with visualizations:

```bash
jupyter notebook demo.ipynb
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run verification tests against AHRI standards
pytest verification/
```

## Physics (Simplified)

**Thermal interference**: The model treats hot exhaust like a plume that spreads downwind. Chillers downwind get warmer air and lose efficiency.

**COP formula**: Each chiller’s COP drops when it receives hot air from others:

$$COP_m = \frac{COP_{base}}{1 + \alpha \sum_k A_{km}}$$

- $A_{km}$ = how much chiller $k$ heats chiller $m$ (based on distance and wind)
- $\alpha$ = sensitivity (typically 0.5–1.0)

**Aging**: Older chillers get a COP multiplier below 1 (e.g. 80% at 1 year). See `src/core/constants.py` to adjust.

## Contributing

Contributions are welcome! Please see our contributing guidelines for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- ASHRAE Handbook - Fundamentals, 2021
- ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
- AHRI Standard 550/590-2015

## Acknowledgments

This project was developed to address thermal management challenges in high-density data center cooling systems.
