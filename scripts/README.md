# Scripts Directory

This directory contains executable scripts, examples, and utility programs for the chiller model project.

## Available Scripts

### `examples_visualization.py`
Generates visualization figures demonstrating various aspects of the chiller model:
- Thermal plume propagation
- COP degradation with ambient temperature
- Optimization comparison between different array configurations
- Wind direction sensitivity analysis
- Optimal array size determination

### `QUICK_START.py`
Quick start guide and demonstration script for basic chiller model usage.
Provides simple examples to get started with the package.

## Usage

All scripts can be run directly from the project root:

```bash
python scripts/examples_visualization.py
python scripts/QUICK_START.py
```

## Adding New Scripts

When adding utility scripts, examples, or tools:
1. Place them in this `scripts/` directory
2. Use descriptive names (e.g., `benchmark_performance.py`, `validate_against_ahri.py`)
3. Include a docstring at the top explaining what the script does
4. Update this README with a brief description
