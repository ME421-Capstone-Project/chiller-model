#!/usr/bin/env python
"""Example 2: Thermal Interference -- heatmap of the 4x4 interaction matrix."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from chiller_sim.layout.grid import ChillerLayout
from chiller_sim.layout.wind import WindConditions
from chiller_sim.physics.gaussian_plume import GaussianPlumeModel

# -- Style constants --
PRIMARY = "#1a5f7a"
SPINE_COLOR = "#cccccc"

# -- Build a 1x4 row and compute the interaction matrix --
grid = ChillerLayout.create_grid(
    rows=1,
    cols=4,
    spacing_m=10.0,
    base_cop=4.0,
    max_cooling_kw=500.0,
)
wind = WindConditions(speed_m_per_s=5.0, angle_deg=0.0)
model = GaussianPlumeModel(dispersion_coeff=1.2)
matrix = model.compute_interaction_matrix(grid.positions_m, wind)

# -- Plot heatmap --
fig, ax = plt.subplots(figsize=(5, 4))
cmap = mcolors.LinearSegmentedColormap.from_list("teal", ["#ffffff", PRIMARY])
im = ax.imshow(matrix, cmap=cmap, aspect="equal")

# Annotate cells
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        val = matrix[i, j]
        text_color = "white" if val > matrix.max() * 0.6 else "#333333"
        ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=10, color=text_color)

ax.set_xticks(range(4))
ax.set_yticks(range(4))
ax.set_xticklabels([f"Ch {i}" for i in range(4)])
ax.set_yticklabels([f"Ch {i}" for i in range(4)])
ax.set_xlabel("Affected chiller (m)")
ax.set_ylabel("Source chiller (k)")
ax.set_title("Thermal Interaction Matrix  (wind \u2192)")

# Style
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(SPINE_COLOR)
ax.spines["bottom"].set_color(SPINE_COLOR)

cbar = fig.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("Interaction strength")

plt.tight_layout()
fig.savefig("docs/_static/images/example2_interaction_matrix.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved example2_interaction_matrix.png")
