"""Chiller Simulation Package.

A modular simulation package for chiller array thermal interactions
with wind effects. Designed for flexibility in modifying performance
degradation models and comprehensive documentation.

Modules
-------
core : Thermodynamic property engines and configuration models
components : Physical component models (wind, chiller, data center)
models : Pluggable interaction models for thermal interference
simulation : Simulation orchestration and optimization

Example
-------
>>> from src.components import WindVector, ChillerArray
>>> from src.models import GaussianPlumeModel
>>> from src.simulation import SimulationEnvironment
>>>
>>> wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
>>> array = ChillerArray.create_grid(rows=3, cols=4, spacing_m=10.0)
>>> model = GaussianPlumeModel(dispersion_coeff=1.2)
>>> env = SimulationEnvironment(array, wind, model)
"""

__version__ = "0.1.0"
