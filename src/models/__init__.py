"""Pluggable interaction models for thermal interference between chillers."""

from .gaussian_plume import GaussianPlumeModel

__all__ = [
    "GaussianPlumeModel",
]
