"""Simulation orchestration and optimization.

This module contains:
- SimulationEnvironment: Central composed simulation system
- Optimizer: Strategies for optimizing chiller array operation
- PerformanceResult: Immutable result container
"""

from .environment import SimulationEnvironment, PerformanceResult
from .optimizer import Optimizer, OptimizationResult

__all__ = [
    "SimulationEnvironment",
    "PerformanceResult",
    "Optimizer",
    "OptimizationResult",
]
