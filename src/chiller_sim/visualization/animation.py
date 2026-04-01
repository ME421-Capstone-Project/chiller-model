from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.physics.degradation import default_capacity_degradation_fn
from chiller_sim.simulation.results import OptimizeResult, SimulationResult

_VALID_COLOR_BY = ("cop", "capacity", "load", "intake")


def _get_color_values(
    step: OptimizeResult,
    layout: ChillerLayout,
    color_by: str,
) -> NDArray[np.float64]:
    """Extract per-chiller values for the selected color-by property."""
    if color_by == "cop":
        return step.cop_array
    elif color_by == "intake":
        return step.temp_rise_array
    elif color_by == "capacity":
        deg_fn = default_capacity_degradation_fn(years_to_80_pct=15.0)
        return np.array([
            layout.max_cooling_kw * deg_fn(age)
            for age in layout.ages_years
        ])
    elif color_by == "load":
        n_active = step.active_mask.sum()
        per_chiller = step.load_kw / max(n_active, 1)
        values = np.zeros(layout.num_chillers)
        values[step.active_mask] = per_chiller
        return values
    raise ValueError(f"Unknown color_by: {color_by!r}")


def _resolve_wind(
    wind: Union[WindConditions, WindFn, None],
    time_hours: float,
) -> WindConditions | None:
    """Resolve wind to a WindConditions snapshot or None."""
    if wind is None:
        return None
    if isinstance(wind, WindConditions):
        return wind
    speed, angle = wind(time_hours)
    return WindConditions(speed_m_per_s=speed, angle_deg=angle)


def _resolve_ambient_temp(
    ambient_temp: Union[AmbientTempFn, ArrayLike, None],
    time_hours: float,
    step_index: int,
) -> float | None:
    """Resolve ambient temperature to Celsius or None."""
    if ambient_temp is None:
        return None
    if callable(ambient_temp):
        return ambient_temp(time_hours) - 273.15
    arr = np.asarray(ambient_temp)
    return float(arr[step_index]) - 273.15


def animate_simulation(
    result: SimulationResult,
    layout: ChillerLayout,
    wind: Union[WindConditions, WindFn, None] = None,
    color_by: str = "cop",
    output_path: str = "simulation.gif",
    fps: int = 4,
    figsize: tuple[float, float] = (10, 6),
    ambient_temp: Union[AmbientTempFn, ArrayLike, None] = None,
) -> Path:
    """Render a simulation as an animated GIF or MP4.

    Parameters
    ----------
    result : SimulationResult
        Completed simulation (must contain at least one step).
    layout : ChillerLayout
        Chiller positions and metadata.
    wind : WindConditions, WindFn, or None
        Static wind or callable ``(time_hours) -> (speed, angle_deg)``.
        None hides the wind vane.
    color_by : str
        Property used to color chiller squares.
        One of ``"cop"``, ``"capacity"``, ``"load"``, ``"intake"``.
    output_path : str
        Destination file. Format inferred from extension (``.gif`` or ``.mp4``).
    fps : int
        Frames per second.
    figsize : tuple of float
        Figure size in inches.
    ambient_temp : AmbientTempFn, array-like, or None
        Callable ``(time_hours) -> float`` (Kelvin) or pre-computed array.
        None omits ambient temperature from the overlay text.

    Returns
    -------
    Path
        Absolute path to the saved animation file.
    """
    if color_by not in _VALID_COLOR_BY:
        raise ValueError(
            f"color_by must be one of {_VALID_COLOR_BY}, got {color_by!r}"
        )

    raise NotImplementedError("Animation rendering not yet implemented")
