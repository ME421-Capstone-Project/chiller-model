# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development
pip install -e ".[dev,docs]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_simulation/test_environment.py

# Run tests with coverage
pytest --cov=src

# Run AHRI compliance verification tests
pytest verification/

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy

# Build docs
cd docs && make html
```

## Architecture

This is a scientific Python package for simulating thermal interference between data center chillers and optimizing which chillers to run.

**Layered composition:**
1. **`src/core/`** — Physical constants, COP functions, Pydantic configs
2. **`src/components/`** — Immutable physical models: `ChillerSpec`/`ChillerState`, `ChillerArray` (grid positioning), `WindVector`, `DataCenter` (load profiles)
3. **`src/models/`** — Pluggable thermal interaction models (abstract `BaseInteractionModel`, physics implementation `GaussianPlumeModel`)
4. **`src/simulation/`** — Orchestration: `SimulationEnvironment` (precomputes N×N interaction matrix), `Optimizer` (greedy chiller selection), `dynamic.py` (time-varying runs)

**Key design patterns:**
- `SimulationEnvironment` is the main entry point — it owns the interaction matrix and wires together array, wind, and model
- Thermal states use frozen dataclasses/NamedTuples (`PerformanceResult`) for immutability
- All array math is vectorized via NumPy (no explicit Python loops over chillers)
- Pydantic validates all configuration inputs

**Data flow:** `ChillerArray` positions → `WindVector` conditions → `GaussianPlumeModel` computes pairwise thermal influence → `SimulationEnvironment` aggregates into effective inlet temperatures → `Optimizer` selects subset of chillers minimizing total power

## Code Style

- Line length: 88 characters
- Docstrings: NumPy convention
- Imports ordered: stdlib → third-party → local
- Matplotlib: use object-oriented API (`fig, ax = plt.subplots()`)
