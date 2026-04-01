from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from chiller_sim.simulation.results import SimulationResult

_VALID_COLOR_BY = ("cop", "capacity", "load", "intake")


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
