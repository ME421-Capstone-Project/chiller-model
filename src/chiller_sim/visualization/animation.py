from __future__ import annotations

from pathlib import Path

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
        return np.array([layout.max_cooling_kw * deg_fn(age) for age in layout.ages_years])
    elif color_by == "load":
        n_active = step.active_mask.sum()
        per_chiller = step.load_kw / max(n_active, 1)
        values = np.zeros(layout.num_chillers)
        values[step.active_mask] = per_chiller
        return values
    raise ValueError(f"Unknown color_by: {color_by!r}")


def _resolve_wind(
    wind: WindConditions | WindFn | None,
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
    ambient_temp: AmbientTempFn | ArrayLike | None,
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


_COLORMAP_MAP = {
    "cop": "RdYlGn",
    "capacity": "Blues",
    "load": "OrRd",
    "intake": "YlOrRd",
}

_LABEL_MAP = {
    "cop": "COP",
    "capacity": "Capacity (kW)",
    "load": "Load (kW)",
    "intake": "Intake Rise (°C)",
}


def _draw_frame(
    ax: object,
    fig: object,
    step: OptimizeResult,
    layout: ChillerLayout,
    color_by: str,
    square_size: float,
    vmin: float,
    vmax: float,
    wind_conditions: WindConditions | None,
    ambient_temp_c: float | None,
) -> None:
    """Draw a single animation frame onto *ax*."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize
        from matplotlib.patches import Rectangle
    except ImportError as err:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install chiller-sim[viz]"
        ) from err

    ax.clear()

    cmap = plt.colormaps[_COLORMAP_MAP[color_by]]
    norm = Normalize(vmin=vmin, vmax=vmax)
    color_values = _get_color_values(step, layout, color_by)
    half = square_size / 2.0

    for i in range(layout.num_chillers):
        x, y = layout.positions_m[i]
        if step.active_mask[i]:
            color = cmap(norm(color_values[i]))
            alpha = 1.0
        else:
            color = "0.75"
            alpha = 0.3

        rect = Rectangle(
            (x - half, y - half),
            square_size,
            square_size,
            facecolor=color,
            edgecolor="black",
            linewidth=0.8,
            alpha=alpha,
        )
        ax.add_patch(rect)

    # Axis limits with padding
    xs = layout.positions_m[:, 0]
    ys = layout.positions_m[:, 1]
    pad = square_size * 2
    ax.set_xlim(xs.min() - pad, xs.max() + pad)
    ax.set_ylim(ys.min() - pad, ys.max() + pad)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"t = {step.time_hours:.1f} h")

    # Wind vane in top-left
    if wind_conditions is not None:
        uv = wind_conditions.unit_vector
        ax_x = xs.min() - pad * 0.5
        ax_y = ys.max() + pad * 0.5
        arrow_len = square_size * 1.5
        ax.annotate(
            "",
            xy=(ax_x + uv[0] * arrow_len, ax_y + uv[1] * arrow_len),
            xytext=(ax_x, ax_y),
            arrowprops={"arrowstyle": "->", "lw": 2, "color": "steelblue"},
        )
        ax.text(
            ax_x,
            ax_y + arrow_len * 1.2,
            f"{wind_conditions.speed_m_per_s:.1f} m/s",
            fontsize=9,
            ha="center",
            color="steelblue",
            fontweight="bold",
        )

    # Info text on the right
    info_lines = [f"Load: {step.load_kw:.0f} kW"]
    if ambient_temp_c is not None:
        info_lines.append(f"Ambient: {ambient_temp_c:.1f} °C")
    info_lines.append(f"Savings: {step.savings_fraction * 100:.1f}%")

    info_text = "\n".join(info_lines)
    ax.text(
        1.02,
        0.5,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="center",
        fontfamily="monospace",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "wheat", "alpha": 0.8},
    )


def animate_simulation(
    result: SimulationResult,
    layout: ChillerLayout,
    wind: WindConditions | WindFn | None = None,
    color_by: str = "cop",
    output_path: str = "simulation.gif",
    fps: int = 4,
    figsize: tuple[float, float] = (10, 6),
    ambient_temp: AmbientTempFn | ArrayLike | None = None,
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
        raise ValueError(f"color_by must be one of {_VALID_COLOR_BY}, got {color_by!r}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import Normalize
    except ImportError as err:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install chiller-sim[viz]"
        ) from err

    # Compute global color range for consistent colorbar across frames
    all_values = np.array([_get_color_values(step, layout, color_by) for step in result.steps])
    vmin = float(np.nanmin(all_values))
    vmax = float(np.nanmax(all_values))
    if vmin == vmax:
        vmax = vmin + 1.0

    # Compute square size from minimum inter-chiller distance (pure NumPy, no scipy)
    if layout.num_chillers > 1:
        diff = layout.positions_m[:, np.newaxis, :] - layout.positions_m[np.newaxis, :, :]
        dist_matrix = np.sqrt((diff**2).sum(axis=-1))
        np.fill_diagonal(dist_matrix, np.inf)
        square_size = float(dist_matrix.min()) * 0.7
    else:
        square_size = 5.0

    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(right=0.78)

    # Add colorbar
    cmap = plt.colormaps[_COLORMAP_MAP[color_by]]
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.15)
    cbar.set_label(_LABEL_MAP[color_by])

    def update(frame_idx: int) -> None:
        step = result.steps[frame_idx]
        wc = _resolve_wind(wind, step.time_hours)
        temp_c = _resolve_ambient_temp(ambient_temp, step.time_hours, frame_idx)
        _draw_frame(
            ax=ax,
            fig=fig,
            step=step,
            layout=layout,
            color_by=color_by,
            square_size=square_size,
            vmin=vmin,
            vmax=vmax,
            wind_conditions=wc,
            ambient_temp_c=temp_c,
        )

    anim = FuncAnimation(fig, update, frames=len(result.steps), interval=1000 // fps)

    out = Path(output_path)
    if out.suffix == ".mp4":
        from matplotlib.animation import FFMpegWriter

        anim.save(str(out), writer=FFMpegWriter(fps=fps))
    else:
        anim.save(str(out), writer=PillowWriter(fps=fps))

    plt.close(fig)
    return out.resolve()
