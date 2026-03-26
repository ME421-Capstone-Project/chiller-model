# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development
pip install -e ".[dev,docs]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_behavior.py

# Run tests with coverage
pytest --cov=src

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

This is a scientific Python package (`chiller_sim`) for simulating thermal interference between data center chillers and optimizing which chillers to run. It uses a fluent builder API.

**Three-layer structure:**
1. **`chiller_sim/layout/`** -- Grid geometry (`ChillerGrid` frozen dataclass) and wind conditions (`WindConditions`, `WindFn` protocol)
2. **`chiller_sim/physics/`** -- Pluggable physics: `CopFn`, `DegradationFn`, `RampFn` protocols with defaults; `GaussianPlumeModel` for thermal plume dispersion; `LoadFn` and `AmbientTempFn` protocols
3. **`chiller_sim/simulation/`** -- `SimulatorBuilder` (fluent construction), `Simulator` (optimize/stream/simulate), result types (`OptimizeResult`, `SimulationResult`, `InitialState`)

**Key design patterns:**
- `SimulatorBuilder` is the main entry point -- chain `.with_*()` methods, call `.build()` to get a `Simulator`
- `Simulator` is state-aware: `optimize()` calls carry chiller state (startup clocks) across calls
- Physics plugins are plain callables matching Protocol signatures -- no inheritance required
- All array math is vectorized via NumPy
- Result types are immutable (frozen dataclasses / NamedTuples)

**Data flow:** `ChillerGrid` positions -> `WindConditions` -> `GaussianPlumeModel` computes N*N interaction matrix -> `Simulator` aggregates into effective inlet temperatures -> greedy optimizer selects best chiller subset

## Code Style

- Line length: 88 characters
- Docstrings: NumPy convention
- Imports ordered: stdlib -> third-party -> local
- Matplotlib: use object-oriented API (`fig, ax = plt.subplots()`)
