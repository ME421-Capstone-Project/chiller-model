"""Immutable chiller specification and thermodynamic state.

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
    """Manufacturer specification for a single chiller unit (immutable).

    COP degrades with inlet temperature rise:
        COP = base_cop / (1 + alpha * delta_T)
    """

    base_cop: float
    rated_capacity_kw: float
    alpha: float = 0.7

    def __post_init__(self) -> None:
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
        """Create from a validated Pydantic ChillerConfig."""
        return cls(
            base_cop=config.base_cop,
            rated_capacity_kw=config.rated_capacity_kw,
            alpha=config.alpha,
        )


class ChillerState(NamedTuple):
    """Immutable thermodynamic snapshot of a single chiller.

    A new state is returned after each process rather than mutating.
    """

    inlet_temp_k: float
    cop: float
    load_kw: float
    is_active: bool = True

    def compute_power_kw(self) -> float:
        """Electrical power = load / COP. Zero when inactive or COP <= 0."""
        if not self.is_active or self.cop <= 0:
            return 0.0
        return self.load_kw / self.cop
