from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.physics.cop import CopFn, default_cop_fn
from chiller_sim.physics.degradation import DegradationFn, default_capacity_degradation_fn
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel
from chiller_sim.physics.load import LoadFn
from chiller_sim.physics.ramp import RampFn, default_ramp_fn

if TYPE_CHECKING:
    from chiller_sim.simulation.simulator import Simulator


class SimulatorBuilder:
    """Fluent builder that assembles a Simulator from its constituent plugins."""

    def __init__(self) -> None:
        """Initialise builder with all fields unset and sensible numeric defaults."""
        self._layout: ChillerLayout | None = None
        self._grid_seed: int | None = None
        self._wind: WindConditions | None = None
        self._wind_fn: WindFn | None = None
        self._ambient_temp_k: float | None = None
        self._ambient_temp_fn: AmbientTempFn | None = None
        self._dispersion_coeff: float = 1.2
        self._load_fn: LoadFn | None = None
        self._cop_fn: CopFn | None = None
        self._degradation_fn: DegradationFn | None = None
        self._ramp_fn: RampFn | None = None
        self._min_savings_kw: float = 0.0

    def with_grid(
        self,
        rows: int,
        cols: int,
        spacing_m: float,
        base_cop: float,
        max_cooling_kw: float,
        alpha: float = 0.7,
        ages_years: NDArray[np.float64] | None = None,
        seed: int | None = None,
    ) -> SimulatorBuilder:
        """Set the chiller grid layout."""
        self._grid_seed = seed
        self._layout = ChillerLayout.create_grid(
            rows=rows,
            cols=cols,
            spacing_m=spacing_m,
            base_cop=base_cop,
            max_cooling_kw=max_cooling_kw,
            alpha=alpha,
            ages_years=ages_years,
            seed=seed,
        )
        return self

    def with_layout(
        self,
        positions_m: NDArray[np.float64],
        ages_years: NDArray[np.float64],
        base_cop: float,
        max_cooling_kw: float,
        alpha: float = 0.7,
    ) -> SimulatorBuilder:
        """Set the chiller layout from explicit (x, y) positions."""
        self._layout = ChillerLayout.from_positions(
            positions_m=positions_m,
            ages_years=ages_years,
            base_cop=base_cop,
            max_cooling_kw=max_cooling_kw,
            alpha=alpha,
        )
        return self

    def with_wind(self, speed_m_per_s: float, angle_deg: float) -> SimulatorBuilder:
        """Set static wind conditions (speed and direction)."""
        self._wind = WindConditions(speed_m_per_s=speed_m_per_s, angle_deg=angle_deg)
        self._wind_fn = None
        return self

    def with_wind_fn(self, fn: WindFn) -> SimulatorBuilder:
        """Set a time-varying wind plugin; overrides any static wind."""
        self._wind_fn = fn
        self._wind = None
        return self

    def with_ambient_temp(self, temp_k: float) -> SimulatorBuilder:
        """Set a constant ambient temperature in Kelvin."""
        self._ambient_temp_k = temp_k
        self._ambient_temp_fn = None
        return self

    def with_ambient_temp_fn(self, fn: AmbientTempFn) -> SimulatorBuilder:
        """Set a time-varying ambient temperature plugin."""
        self._ambient_temp_fn = fn
        self._ambient_temp_k = None
        return self

    def with_dispersion(self, coeff: float) -> SimulatorBuilder:
        """Override the Gaussian plume dispersion coefficient."""
        self._dispersion_coeff = coeff
        return self

    def with_load_fn(self, fn: LoadFn) -> SimulatorBuilder:
        """Set the facility load profile plugin."""
        self._load_fn = fn
        return self

    def with_cop_fn(self, fn: CopFn) -> SimulatorBuilder:
        """Override the default COP computation plugin."""
        self._cop_fn = fn
        return self

    def with_degradation_fn(self, fn: DegradationFn) -> SimulatorBuilder:
        """Override the default age-based capacity degradation plugin."""
        self._degradation_fn = fn
        return self

    def with_ramp_fn(self, fn: RampFn) -> SimulatorBuilder:
        """Override the default startup ramp plugin."""
        self._ramp_fn = fn
        return self

    def with_switching_threshold(self, min_savings_kw: float) -> SimulatorBuilder:
        """Set the minimum savings (kW) required to switch chiller on/off."""
        self._min_savings_kw = min_savings_kw
        return self

    def build(self) -> Simulator:
        """Validate configuration and construct the Simulator."""
        from chiller_sim.simulation.simulator import Simulator

        if self._layout is None:
            raise ValueError(
                "layout is required — call .with_grid() or .with_layout() before .build()"
            )
        if self._load_fn is None:
            raise ValueError("load_fn is required — call .with_load_fn() before .build()")
        if self._ambient_temp_k is None and self._ambient_temp_fn is None:
            raise ValueError(
                "ambient_temp is required — call .with_ambient_temp() or "
                ".with_ambient_temp_fn() before .build()"
            )

        # Resolve defaults
        cop_fn = self._cop_fn if self._cop_fn is not None else default_cop_fn(self._layout.alpha)
        deg_fn = (
            self._degradation_fn
            if self._degradation_fn is not None
            else default_capacity_degradation_fn(years_to_80_pct=10.0)
        )
        ramp_fn = self._ramp_fn if self._ramp_fn is not None else default_ramp_fn()

        # Build initial wind conditions (required for matrix precomputation)
        if self._wind is None and self._wind_fn is None:
            raise ValueError(
                "wind is required — call .with_wind() or .with_wind_fn() before .build()"
            )
        initial_wind = self._wind or WindConditions(*self._wind_fn(0.0))

        model = GaussianPlumeModel(dispersion_coeff=self._dispersion_coeff)

        return Simulator(
            builder=self,
            layout=self._layout,
            initial_wind=initial_wind,
            model=model,
            load_fn=self._load_fn,
            cop_fn=cop_fn,
            degradation_fn=deg_fn,
            ramp_fn=ramp_fn,
            wind_fn=self._wind_fn,
            ambient_temp_k=self._ambient_temp_k,
            ambient_temp_fn=self._ambient_temp_fn,
            min_savings_kw=self._min_savings_kw,
        )
