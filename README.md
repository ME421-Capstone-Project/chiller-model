# Chiller Array Simulation Package

A modular Python package for simulating thermal interference effects in data center chiller arrays, with wind-aware optimization for improved energy efficiency.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://chiller-model.readthedocs.io)

## Overview

When chillers are densely packed in data center cooling arrays, thermal recirculation can significantly degrade performance. Hot exhaust from one unit gets drawn into the intake of neighboring units, reducing their Coefficient of Performance (COP) and increasing energy consumption.

This package models these thermal interference effects using physics-based Gaussian plume dispersion and provides optimization tools to select the most efficient subset of chillers to operate.

**Key findings from our simulations:**
- Thermal interference can reduce individual chiller COP by **30%** or more
- Wind-aware optimization can improve array efficiency by **10-15%**
- Sometimes running **fewer** chillers is more efficient than running all of them

## Features

- **Physics-Based Modeling**: Gaussian plume dispersion model for thermal wake effects
- **Modular Architecture**: Pluggable interaction models, composable components
- **Wind-Aware Optimization**: Greedy optimization accounting for wind direction
- **Validated Inputs**: Pydantic models ensure physical plausibility
- **SI Units**: All internal calculations use SI units (K, Pa, kg/s, J)
- **Vectorized Computations**: NumPy-based for efficient large-scale simulations

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

## Documentation

Full documentation is available at [chiller-model.readthedocs.io](https://chiller-model.readthedocs.io).

- [Getting Started](https://chiller-model.readthedocs.io/getting-started.html)
- [User Guide](https://chiller-model.readthedocs.io/user-guide.html)
- [Examples](https://chiller-model.readthedocs.io/examples.html)
- [API Reference](https://chiller-model.readthedocs.io/api/index.html)

## Interactive Demo

The `demo.ipynb` notebook provides an interactive walkthrough of the package features with visualizations:

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

## Physics Background

### Thermal Interference Model

The Gaussian plume model calculates thermal impact between chillers:

$$A_{km} = \frac{\exp(-d_{lat}^2 / (\sigma (d_{long} + 1)))}{d_{long} + 1}$$

Where:
- $A_{km}$: Thermal impact of chiller $k$ on chiller $m$
- $d_{long}$: Longitudinal distance along wind direction (m)
- $d_{lat}$: Lateral distance perpendicular to wind (m)
- $\sigma$: Dispersion coefficient

### COP Degradation

COP degrades based on cumulative thermal interference:

$$COP_m = \frac{COP_{base}}{1 + \alpha \sum_k A_{km}}$$

Where $\alpha$ is the sensitivity coefficient (typically 0.5-1.0).

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
