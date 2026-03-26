#!/usr/bin/env python
"""Example 5: Time-Varying Wind -- two-panel plot of angle and work over time."""

import math

import numpy as np
import matplotlib.pyplot as plt

from chiller_sim import Simulator

# -- Style constants --
PRIMARY = "#1a5f7a"
ACCENT = "#2d9db0"
SPINE_COLOR = "#cccccc"


def rotating_wind(time_hours: float) -> tuple[float, float]:
    """Wind that rotates +-60 deg around 90 deg with 12 h period."""
    angle = 90.0 + 60.0 * math.sin(2 * math.pi * time_hours / 12)
    return (5.0, angle)


# -- Build simulator --
sim = (
    Simulator()
    .with_grid(rows=2, cols=4, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind_fn(rotating_wind)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 1000.0)
    .build()
)

# -- Collect results --
times, angles, works = [], [], []
for result in sim.stream(duration_hours=24.0, time_step_hours=0.5):
    t = result.time_hours
    times.append(t)
    angles.append(90.0 + 60.0 * math.sin(2 * math.pi * t / 12))
    works.append(result.total_work_kw)

times = np.array(times)
angles = np.array(angles)
works = np.array(works)

# -- Two-panel plot --
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True)

# Top: wind angle
ax1.plot(times, angles, color=ACCENT, linewidth=2)
ax1.set_ylabel("Wind angle (deg)")
ax1.set_title("Time-Varying Wind Effect on Total Work")
ax1.axhline(90, color="#cccccc", linestyle="--", linewidth=0.8)

# Bottom: total work
ax2.plot(times, works, color=PRIMARY, linewidth=2)
ax2.set_ylabel("Total work (kW)")
ax2.set_xlabel("Time (hours)")

# Style both axes
for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.tick_params(colors="#333333")
    ax.grid(axis="y", color="#eeeeee", linewidth=0.5)

plt.tight_layout()
fig.savefig("docs/_static/images/example5_wind_fn.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved example5_wind_fn.png")
