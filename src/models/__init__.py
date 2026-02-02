"""Chiller interaction models for thermal interference calculations.

This module contains pluggable interaction models that compute
the thermal coupling between chillers based on position, wind,
and other environmental factors.

Design Pattern
--------------
Uses Abstract Base Class (ABC) to define the interface. Users can
implement custom models by subclassing BaseInteractionModel.
"""

from .base_interaction import BaseInteractionModel
from .gaussian_plume import GaussianPlumeModel

__all__ = [
    "BaseInteractionModel",
    "GaussianPlumeModel",
]
