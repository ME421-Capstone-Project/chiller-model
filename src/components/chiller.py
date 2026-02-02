"""Chiller specification and state models.

This module defines immutable data structures for chiller
specifications (manufacturer data) and thermodynamic states.

Design Pattern
--------------
Per project rules, thermodynamic states are immutable. A new state
object is returned after each thermodynamic process rather than
modifying the existing state.

Reference
---------
AHRI Standard 550/590-2015 (Performance Rating of Water-Chilling Packages)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from src.core.configs import ChillerConfig


@dataclass(frozen=True)
class ChillerSpec:
    """Manufacturer specifications for a chiller unit (immutable).

    Contains the rated performance characteristics of a chiller as
    specified by the manufacturer. These values are fixed for a given
    chiller model.

    Attributes
    ----------
    base_cop : float
        Coefficient of Performance at rated conditions.
        Defined as cooling capacity / input power.
    rated_capacity_kw : float
        Rated cooling capacity in kilowatts at standard conditions.
    alpha : float
        Sensitivity coefficient to inlet temperature rise.
        Higher values mean greater COP degradation per degree of
        temperature rise at the condenser inlet.

    Notes
    -----
    The COP degradation model follows:

    .. math::

        COP = \\frac{COP_{base}}{1 + \\alpha \\cdot \\Delta T}

    where :math:`\\Delta T` is the temperature rise at the inlet
    due to thermal interference from other units.

    Reference
    ---------
    AHRI Standard 550/590-2015

    Examples
    --------
    >>> spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.7)
    >>> spec.base_cop
    5.0
    """

    base_cop: float
    rated_capacity_kw: float
    alpha: float = 0.7

    def __post_init__(self) -> None:
        """Validate chiller specifications."""
        if self.base_cop <= 0:
            raise ValueError(f"base_cop must be > 0, got {self.base_cop}")
        if self.base_cop > 10:
            raise ValueError(
                f"base_cop > 10 is non-physical for vapor compression, "
                f"got {self.base_cop}"
            )
        if self.rated_capacity_kw <= 0:
            raise ValueError(
                f"rated_capacity_kw must be > 0, got {self.rated_capacity_kw}"
            )
        if self.alpha <= 0:
            raise ValueError(f"alpha must be > 0, got {self.alpha}")

    @classmethod
    def from_config(cls, config: ChillerConfig) -> ChillerSpec:
        """Create ChillerSpec from validated Pydantic config.

        Parameters
        ----------
        config : ChillerConfig
            Validated chiller configuration.

        Returns
        -------
        ChillerSpec
            Immutable chiller specification.
        """
        return cls(
            base_cop=config.base_cop,
            rated_capacity_kw=config.rated_capacity_kw,
            alpha=config.alpha,
        )


class ChillerState(NamedTuple):
    """Thermodynamic state of a chiller (immutable namedtuple).

    Returns a NEW state after each thermodynamic process rather
    than modifying the existing state, per project rules on immutability.

    Attributes
    ----------
    inlet_temp_k : float
        Inlet air temperature in Kelvin.
    cop : float
        Current coefficient of performance (degraded by thermal interference).
    load_kw : float
        Current cooling load assigned to this chiller in kW.
    is_active : bool
        Whether the chiller is currently running.

    Notes
    -----
    This uses NamedTuple for immutability and memory efficiency.
    States should never be modified in place.

    Examples
    --------
    >>> state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
    >>> state.is_active
    True
    >>> # Create new state with different load
    >>> new_state = state._replace(load_kw=150.0)
    """

    inlet_temp_k: float
    cop: float
    load_kw: float
    is_active: bool = True

    def compute_power_kw(self) -> float:
        """Compute electrical power consumption.

        Returns
        -------
        float
            Electrical power input in kW.

        Notes
        -----
        Power is computed as:

        .. math::

            P = \\frac{Q}{COP}

        where Q is the cooling load.
        """
        if not self.is_active or self.cop <= 0:
            return 0.0
        return self.load_kw / self.cop
