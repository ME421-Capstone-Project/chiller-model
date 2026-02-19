import numpy as np
import pytest

from src.components import ChillerArray, WindVector
from src.models import GaussianPlumeModel
from src.simulation import SimulationEnvironment


@pytest.fixture
def sample_positions() -> np.ndarray:
    x = np.arange(4) * 10.0
    y = np.arange(4) * 10.0
    xx, yy = np.meshgrid(x, y)
    positions = np.column_stack([xx.ravel(), yy.ravel()])
    return positions.astype(np.float64)


@pytest.fixture
def sample_wind() -> WindVector:
    return WindVector(
        velocity_m_per_s=(5.0, 0.0),
        ambient_temp_k=298.15,
    )


@pytest.fixture
def sample_chiller_array(sample_positions: np.ndarray) -> ChillerArray:
    return ChillerArray(
        positions_m=sample_positions,
        base_cop=4.0,
        alpha=0.7,
    )


@pytest.fixture
def gaussian_model() -> GaussianPlumeModel:
    return GaussianPlumeModel(dispersion_coeff=1.2)


@pytest.fixture
def simulation_env(
    sample_chiller_array: ChillerArray,
    sample_wind: WindVector,
    gaussian_model: GaussianPlumeModel,
) -> SimulationEnvironment:
    return SimulationEnvironment(
        chiller_array=sample_chiller_array,
        wind=sample_wind,
        interaction_model=gaussian_model,
    )
