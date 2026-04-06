#!/usr/bin/env python
"""Generate animated GIFs for Examples 4 and 5 in the documentation."""

import math

import numpy as np

from chiller_sim import Simulator
from chiller_sim.visualization import animate_simulation

# ---------------------------------------------------------------------------
# Example 4: 24-Hour Sinusoidal Load Profile
# ---------------------------------------------------------------------------
sim4 = (
    Simulator()
    .with_grid(rows=2, cols=4, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 550.0 + 250.0 * math.sin(2 * math.pi * t / 24))
    .build()
)

result4 = sim4.simulate(duration_hours=24.0, time_step_hours=1.0)

animate_simulation(
    result4,
    sim4._layout,
    color_by="cop",
    output_path="docs/_static/images/example4_animation.gif",
    fps=4,
    figsize=(10, 6),
)
print("Saved example4_animation.gif")

# ---------------------------------------------------------------------------
# Example 5: Time-Varying Wind
# ---------------------------------------------------------------------------
def rotating_wind(time_hours: float) -> tuple[float, float]:
    """Wind that rotates +-60 deg around 90 deg with 12 h period."""
    angle = 90.0 + 60.0 * math.sin(2 * math.pi * time_hours / 12)
    return (5.0, angle)


sim5 = (
    Simulator()
    .with_grid(rows=2, cols=4, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind_fn(rotating_wind)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 1000.0)
    .build()
)

result5 = sim5.simulate(duration_hours=24.0, time_step_hours=1.0)

animate_simulation(
    result5,
    sim5._layout,
    wind=rotating_wind,
    color_by="intake",
    output_path="docs/_static/images/example5_animation.gif",
    fps=4,
    figsize=(10, 6),
)
print("Saved example5_animation.gif")
