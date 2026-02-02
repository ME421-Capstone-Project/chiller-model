"""Pytest fixtures for chiller simulation tests.

Provides common test fixtures including sample positions, wind
configurations, and simulation environments.
"""

import numpy as np
import pytest

from src.components import ChillerArray, WindVector
from src.models import GaussianPlumeModel
from src.simulation import SimulationEnvironment


@pytest.fixture
def sample_positions() -> np.ndarray:
    """Create sample chiller positions for testing.

    Returns a 4x4 grid of chillers spaced 10m apart.
    """
    x = np.arange(4) * 10.0
    y = np.arange(4) * 10.0
    xx, yy = np.meshgrid(x, y)
    positions = np.column_stack([xx.ravel(), yy.ravel()])
    return positions.astype(np.float64)


@pytest.fixture
def sample_wind() -> WindVector:
    """Create sample wind conditions for testing.

    Wind blowing in positive x-direction at 5 m/s.
    """
    return WindVector(
        velocity_m_per_s=(5.0, 0.0),
        ambient_temp_k=298.15,
    )


@pytest.fixture
def sample_chiller_array(sample_positions: np.ndarray) -> ChillerArray:
    """Create sample chiller array for testing."""
    return ChillerArray(
        positions_m=sample_positions,
        base_cop=4.0,
        alpha=0.7,
    )


@pytest.fixture
def gaussian_model() -> GaussianPlumeModel:
    """Create Gaussian plume model with default parameters."""
    return GaussianPlumeModel(dispersion_coeff=1.2)


@pytest.fixture
def simulation_env(
    sample_chiller_array: ChillerArray,
    sample_wind: WindVector,
    gaussian_model: GaussianPlumeModel,
) -> SimulationEnvironment:
    """Create complete simulation environment for testing."""
    return SimulationEnvironment(
        chiller_array=sample_chiller_array,
        wind=sample_wind,
        interaction_model=gaussian_model,
    )
