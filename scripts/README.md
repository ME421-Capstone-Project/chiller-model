# Scripts Directory

Executable examples and utilities. Run from project root with ``PYTHONPATH=src``.

## Available Scripts

### `example_chiller_age.py`
Shows how chiller age affects COP. Covers manual ages, random ages, and new vs aged comparison.

### `example_dynamic_simulation.py`
Dynamic simulation with varying load, wind, and chiller startup. Four demos: constant load, sinusoidal load, varying wind, and COP startup ramp.

### `generate_doc_figures.py`
Generates figures for the documentation (aging, dynamic simulation). Output: ``docs/_static/images/*.png``.

### `examples_visualization.py`
Publication-quality figures: thermal plume, optimization comparison, wind sensitivity, etc.

### `QUICK_START.py`
Basic chiller model usage and quick demo.

## Usage

```bash
PYTHONPATH=src python scripts/example_chiller_age.py
PYTHONPATH=src python scripts/example_dynamic_simulation.py
PYTHONPATH=src python scripts/generate_doc_figures.py
```

## Adding New Scripts

When adding utility scripts, examples, or tools:
1. Place them in this `scripts/` directory
2. Use descriptive names (e.g., `benchmark_performance.py`, `validate_against_ahri.py`)
3. Include a docstring at the top explaining what the script does
4. Update this README with a brief description
