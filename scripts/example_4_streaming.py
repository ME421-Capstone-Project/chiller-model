#!/usr/bin/env python
"""Example 4: Streaming a 24-Hour Load Profile -- three-panel timeline."""

import math

import numpy as np
import matplotlib.pyplot as plt

from chiller_sim import Simulator

# -- Style constants --
PRIMARY = "#1a5f7a"
ACCENT = "#2d9db0"
SPINE_COLOR = "#cccccc"

# -- Build simulator with sinusoidal load --
sim = (
    Simulator()
    .with_grid(rows=2, cols=4, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 550.0 + 250.0 * math.sin(2 * math.pi * t / 24))
    .build()
)

# -- Collect streaming results --
times, loads, works, actives = [], [], [], []
for result in sim.stream(duration_hours=24.0, time_step_hours=1.0):
    times.append(result.time_hours)
    loads.append(result.load_kw)
    works.append(result.total_work_kw)
    actives.append(int(result.active_mask.sum()))

times = np.array(times)
loads = np.array(loads)
works = np.array(works)
actives = np.array(actives)

# -- Three-panel plot --
fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)

# Top: Load
axes[0].plot(times, loads, color=PRIMARY, linewidth=2)
axes[0].set_ylabel("Load (kW)")
axes[0].set_title("24-Hour Streaming Simulation")

# Middle: Total work
axes[1].plot(times, works, color=ACCENT, linewidth=2)
axes[1].set_ylabel("Total work (kW)")

# Bottom: Active count
axes[2].step(times, actives, color=PRIMARY, linewidth=2, where="post")
axes[2].set_ylabel("Active chillers")
axes[2].set_xlabel("Time (hours)")
axes[2].set_ylim(0, 9)

# Style all axes
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.tick_params(colors="#333333")
    ax.grid(axis="y", color="#eeeeee", linewidth=0.5)

plt.tight_layout()
fig.savefig("docs/_static/images/example4_stream_timeline.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved example4_stream_timeline.png")
