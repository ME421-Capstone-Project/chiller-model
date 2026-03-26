#!/usr/bin/env python
"""Example 3: Capacity, Aging, and the Feasibility Gate -- grouped bar chart."""

import numpy as np
import matplotlib.pyplot as plt

from chiller_sim import Simulator

# -- Style constants --
PRIMARY = "#1a5f7a"
ACCENT = "#2d9db0"
SPINE_COLOR = "#cccccc"

load_kw = 800.0

# -- New fleet --
sim_new = (
    Simulator()
    .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=4.0,
               max_cooling_kw=500.0, ages_years=np.zeros(4))
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: load_kw)
    .build()
)

# -- Aged fleet (20 years) --
sim_aged = (
    Simulator()
    .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=4.0,
               max_cooling_kw=500.0, ages_years=np.full(4, 20.0))
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: load_kw)
    .build()
)

r_new = sim_new.optimize(time_hours=0.0)
r_aged = sim_aged.optimize(time_hours=0.0)

n_active_new = int(r_new.active_mask.sum())
n_active_aged = int(r_aged.active_mask.sum())

# -- Plot grouped bar chart --
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

groups = ["New fleet", "Aged fleet"]
x = np.arange(len(groups))

# Left: active count
ax1.bar(x, [n_active_new, n_active_aged], color=[PRIMARY, ACCENT],
        width=0.5, edgecolor="white")
ax1.set_xticks(x)
ax1.set_xticklabels(groups)
ax1.set_ylabel("Active chillers")
ax1.set_title("Active Chillers")
ax1.set_ylim(0, 5)

# Right: total work
ax2.bar(x, [r_new.total_work_kw, r_aged.total_work_kw], color=[PRIMARY, ACCENT],
        width=0.5, edgecolor="white")
ax2.set_xticks(x)
ax2.set_xticklabels(groups)
ax2.set_ylabel("Total work (kW)")
ax2.set_title("Total Electrical Work")

# Style both axes
for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.tick_params(colors="#333333")

plt.tight_layout()
fig.savefig("docs/_static/images/example3_aging_capacity.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved example3_aging_capacity.png")
print(f"New fleet:  {n_active_new} active, {r_new.total_work_kw:.1f} kW")
print(f"Aged fleet: {n_active_aged} active, {r_aged.total_work_kw:.1f} kW")
