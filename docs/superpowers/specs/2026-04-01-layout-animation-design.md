# Chiller Layout Animation — Design Spec

## Goal

Add a `chiller_sim.visualization` module with a single public function,
`animate_simulation()`, that renders a completed `SimulationResult` as a
GIF or MP4.  Each frame shows chiller positions as colored squares on a 2-D
plan view, with overlays for wind, load, ambient temperature, and savings.

## Module structure

```
src/chiller_sim/visualization/
    __init__.py        # re-exports animate_simulation
    animation.py       # implementation
```

`animate_simulation` is also re-exported from `chiller_sim.__init__`.

matplotlib is an **optional** dependency — imported at call time inside the
function, not at package level.  A clear `ImportError` message tells users
to `pip install matplotlib` if it is missing.

## Public API

```python
from pathlib import Path
from chiller_sim.simulation.results import SimulationResult
from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions, WindFn
from chiller_sim.physics.ambient_temp import AmbientTempFn
from numpy.typing import ArrayLike

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
        Static wind or callable (time_hours -> WindConditions).
        None hides the wind vane.
    color_by : str
        Property used to color chiller squares.
        One of "cop", "capacity", "load", "intake".
    output_path : str
        Destination file.  Format inferred from extension (.gif or .mp4).
    fps : int
        Frames per second.
    figsize : tuple[float, float]
        Figure size in inches.
    ambient_temp : AmbientTempFn, ArrayLike, or None
        Callable (time_hours -> float) or pre-computed array of temps (C).
        None omits ambient temperature from the overlay text.

    Returns
    -------
    Path
        Absolute path to the saved animation file.
    """
```

## Frame layout

Each frame corresponds to one `OptimizeResult` timestep.

### Chiller squares

- Plotted at `layout.positions_m` using `matplotlib.patches.Rectangle`.
- Square size derived from the minimum distance between any two chillers,
  scaled down so squares don't overlap.
- Colored by the selected property via a colormap (see table below).
- Inactive chillers (where `active_mask` is False) rendered in gray with
  reduced opacity (alpha ~0.3).

### Color-by options

| `color_by`   | Data source                                           | Units          | Colormap |
|-------------- |------------------------------------------------------|----------------|----------|
| `"cop"`      | `OptimizeResult.cop_array`                             | dimensionless  | RdYlGn   |
| `"capacity"` | `layout.max_cooling_kw` degraded by chiller age        | kW             | Blues    |
| `"load"`     | per-chiller share of `load_kw` among active chillers   | kW             | OrRd     |
| `"intake"`   | `OptimizeResult.temp_rise_array`                       | deg C          | YlOrRd   |

A colorbar is shown on the right edge of the figure, labeled with the
property name and units.  The colorbar range is fixed across all frames
(global min/max) so colors are comparable.

### Wind vane (top-left corner)

- Arrow whose direction matches the wind vector.
- Text label beside it: speed in m/s (e.g. "3.2 m/s").
- Drawn in an inset axes so it doesn't interfere with the main plot.
- Hidden when `wind` is None.

### Info text (right center)

Displayed as a text block outside the main axes:

- **Load**: current `load_kw` in kW
- **Ambient**: current ambient temperature in deg C (omitted if `ambient_temp` is None)
- **Savings**: `savings_fraction` as a percentage
- **Time**: `time_hours` in hours

### Title

Shows the current time step, e.g. "t = 2.5 h".

## Wind and ambient temp resolution

- If `wind` is a `WindConditions` instance, the same wind is used for every
  frame.
- If `wind` is a `WindFn` callable, it is called with
  `step.time_hours` for each frame.
- If `ambient_temp` is a callable, it is called with `step.time_hours`.
- If `ambient_temp` is an array-like, it must have length equal to the
  number of steps.

## Output format

- Extension `.gif` uses `PillowWriter`.
- Extension `.mp4` uses `FFMpegWriter` (requires ffmpeg installed).
- The function returns `Path(output_path).resolve()`.

## Dependencies

- matplotlib is optional; imported inside `animate_simulation()`.
- Pillow required for GIF output (transitive via matplotlib's PillowWriter).
- ffmpeg required for MP4 output (system binary, not a Python package).
- No new required dependencies are added to the package.

matplotlib is added to `pyproject.toml` under an optional `[viz]` extra:
```toml
[project.optional-dependencies]
viz = ["matplotlib>=3.7"]
```

## Testing

- Unit test that `animate_simulation` produces a GIF file with correct
  number of frames for a small (2x2) grid simulation.
- Test each `color_by` option runs without error.
- Test with `wind=None` and `ambient_temp=None` (overlays hidden).
- Test with `WindFn` callable and `AmbientTempFn` callable.
- Test that invalid `color_by` raises `ValueError`.
- Test that missing matplotlib raises `ImportError` with a helpful message
  (can be tested by mocking the import).
