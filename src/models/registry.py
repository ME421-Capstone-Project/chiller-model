"""Model registration system for extensibility.

This module provides a registry for interaction models, allowing
users to register custom models and retrieve them by name.

Design Pattern
--------------
Uses the Registry pattern to decouple model creation from usage.
Models can be registered at import time and instantiated later.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from src.models.base_interaction import BaseInteractionModel

T = TypeVar("T", bound=BaseInteractionModel)

# Global registry mapping names to model factories
_MODEL_REGISTRY: dict[str, type[BaseInteractionModel]] = {}


def register_model(name: str) -> Callable[[type[T]], type[T]]:
    """Decorator to register an interaction model class.

    Parameters
    ----------
    name : str
        Unique name for the model in the registry.

    Returns
    -------
    Callable
        Decorator function.

    Examples
    --------
    >>> @register_model("my_custom_model")
    ... class MyCustomModel(BaseInteractionModel):
    ...     def compute_interaction_matrix(self, positions_m, wind):
    ...         pass
    """

    def decorator(cls: type[T]) -> type[T]:
        if name in _MODEL_REGISTRY:
            raise ValueError(f"Model '{name}' is already registered")
        _MODEL_REGISTRY[name] = cls
        return cls

    return decorator


def get_model(name: str, **kwargs: object) -> BaseInteractionModel:
    """Get a registered model instance by name.

    Parameters
    ----------
    name : str
        Registered name of the model.
    **kwargs
        Keyword arguments passed to the model constructor.

    Returns
    -------
    BaseInteractionModel
        Instantiated model.

    Raises
    ------
    KeyError
        If no model is registered with the given name.

    Examples
    --------
    >>> model = get_model("gaussian_plume", dispersion_coeff=1.5)
    """
    if name not in _MODEL_REGISTRY:
        available = list(_MODEL_REGISTRY.keys())
        raise KeyError(
            f"Model '{name}' not found. Available models: {available}"
        )
    return _MODEL_REGISTRY[name](**kwargs)


def list_models() -> list[str]:
    """List all registered model names.

    Returns
    -------
    list[str]
        Names of all registered models.
    """
    return list(_MODEL_REGISTRY.keys())


def clear_registry() -> None:
    """Clear all registered models (useful for testing)."""
    _MODEL_REGISTRY.clear()


# Register built-in models
# Import here to avoid circular imports
def _register_builtin_models() -> None:
    """Register the built-in models."""
    from src.models.gaussian_plume import GaussianPlumeModel

    if "gaussian_plume" not in _MODEL_REGISTRY:
        _MODEL_REGISTRY["gaussian_plume"] = GaussianPlumeModel


# Auto-register when module is imported
_register_builtin_models()
