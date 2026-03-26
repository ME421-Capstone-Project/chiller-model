#!/usr/bin/env python
"""Example 1: Your First Optimization -- horizontal bar chart of COP per chiller."""

import numpy as np
import matplotlib.pyplot as plt

from chiller_sim import Simulator

# -- Style constants --
PRIMARY = "#1a5f7a"
MUTED = "#c8dde4"
SPINE_COLOR = "#cccccc"

# -- Build and optimize --
sim = (
    Simulator()
    .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
    .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
    .with_ambient_temp(temp_k=298.15)
    .with_load_fn(lambda t: 800.0)
    .build()
)

result = sim.optimize(time_hours=0.0)

# -- Plot --
n = len(result.cop_array)
labels = [f"Chiller {i}" for i in range(n)]
colors = [PRIMARY if result.active_mask[i] else MUTED for i in range(n)]

fig, ax = plt.subplots(figsize=(7, 3.5))
y_pos = np.arange(n)
ax.barh(y_pos, result.cop_array, color=colors, edgecolor="white", height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel("Effective COP")
ax.set_title("COP per Chiller (active = dark teal)")

# Style
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(SPINE_COLOR)
ax.spines["bottom"].set_color(SPINE_COLOR)
ax.tick_params(colors="#333333")

plt.tight_layout()
fig.savefig("docs/_static/images/example1_cop_bar.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved example1_cop_bar.png")
