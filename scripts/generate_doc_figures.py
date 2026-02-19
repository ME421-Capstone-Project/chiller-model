"""Generate figures for documentation (all examples).

Run from project root with: PYTHONPATH=src python scripts/generate_doc_figures.py

Output: docs/_static/images/*.png
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Add project root and src for imports
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))
sys.path.insert(0, os.path.join(_root, "scripts"))

from components import ChillerArray, WindVector
from components.data_center import DataCenter
from core.constants import compute_cop_age_factor, CHILLER_STARTUP_TIME_HOURS
from models import GaussianPlumeModel
from simulation import DynamicSimulation, SimulationEnvironment, Optimizer


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "_static", "images")


def _ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save(fig: plt.Figure, name: str) -> None:
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def plot_aging_cop_decay() -> None:
    """Plot COP decay curve vs chiller age."""
    ages = np.linspace(0, 20, 201)
    factors = np.array([compute_cop_age_factor(a) for a in ages])

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ages, factors * 100, "b-", linewidth=2)
    ax.fill_between(ages, factors * 100, alpha=0.2)
    ax.set_xlabel("Chiller age (years)")
    ax.set_ylabel("COP (% of new)")
    ax.set_title("How Chiller Age Affects Efficiency")
    ax.set_ylim(0, 105)
    ax.set_xlim(0, 20)
    ax.grid(True, alpha=0.3)
    ax.axhline(80, color="gray", linestyle="--", alpha=0.7, label="80% at 1 year")
    ax.legend()
    fig.tight_layout()
    _save(fig, "aging_cop_decay.png")


def plot_aging_new_vs_aged() -> None:
    """Compare total work: all-new vs mixed-age array."""
    wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    load = 500.0

    # New array
    array_new = ChillerArray.create_grid(
        rows=2, cols=2, spacing_m=10.0, base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    env_new = SimulationEnvironment(array_new, wind, model)
    r_new = env_new.compute_performance(np.ones(4, dtype=bool), load)

    # Mixed ages
    array_mixed = ChillerArray.create_grid(
        rows=2, cols=2, spacing_m=10.0, base_cop=5.0,
        ages_years=np.array([0.0, 5.0, 10.0, 15.0], dtype=np.float64),
    )
    env_mixed = SimulationEnvironment(array_mixed, wind, model)
    r_mixed = env_mixed.compute_performance(np.ones(4, dtype=bool), load)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        ["All new\n(age 0)", "Mixed ages\n(0, 5, 10, 15 yr)"],
        [r_new.total_work_kw, r_mixed.total_work_kw],
        color=["#2ecc71", "#e74c3c"],
        edgecolor="black",
        linewidth=1,
    )
    ax.set_ylabel("Electrical work (kW)")
    ax.set_title("Aged Chillers Use More Energy (500 kW load)")
    max_h = max(b.get_height() for b in bars)
    pad = max(5, max_h * 0.06)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + pad, f"{b.get_height():.0f} kW",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, max(r_new.total_work_kw, r_mixed.total_work_kw) * 1.2)
    fig.tight_layout()
    _save(fig, "aging_new_vs_aged.png")


def plot_dynamic_load_profile() -> None:
    """Plot varying load over time (sinusoidal)."""
    dc = DataCenter.with_sinusoidal_profile(
        base_load_kw=300.0, peak_load_kw=800.0, period_hours=24.0
    )
    times = np.linspace(0, 24, 241)
    loads = dc.get_load_series_kw(times)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(times, loads, "b-", linewidth=2)
    ax.fill_between(times, loads, alpha=0.2)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Cooling load (kW)")
    ax.set_title("Daily Load Profile (Sinusoidal)")
    ax.set_xlim(0, 24)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "dynamic_load_profile.png")


def plot_dynamic_startup_ramp() -> None:
    """Plot COP startup ramp (0 to 1 over startup time)."""
    times = np.linspace(0, 0.5, 101)
    factors = np.where(
        times <= 0, 0.0, np.minimum(1.0, times / CHILLER_STARTUP_TIME_HOURS)
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(times * 60, factors * 100, "g-", linewidth=2)  # minutes on x
    ax.axvline(CHILLER_STARTUP_TIME_HOURS * 60, color="gray", linestyle="--", alpha=0.7)
    ax.set_xlabel("Time since start (minutes)")
    ax.set_ylabel("COP (% of full)")
    ax.set_title("Chiller Startup: COP Ramps Up Over Time")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "dynamic_startup_ramp.png")


def plot_dynamic_simulation_timeline() -> None:
    """Plot load, work, and active chillers over a short run."""
    array = ChillerArray.create_grid(
        rows=2, cols=2, spacing_m=15.0, base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    wind = WindVector(velocity_m_per_s=(3.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    env = SimulationEnvironment(array, wind, model)
    dc = DataCenter.with_sinusoidal_profile(
        base_load_kw=300.0, peak_load_kw=800.0, period_hours=24.0
    )
    sim = DynamicSimulation(
        environment=env, data_center=dc,
        time_step_hours=2.0, startup_time_hours=0.25,
    )

    times, loads, works, n_active = [], [], [], []
    for step in sim.run(duration_hours=12.0):
        times.append(step.time_hours)
        loads.append(step.load_kw)
        works.append(step.total_work_kw)
        n_active.append(int(np.sum(step.active_mask)))

    fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    axes[0].plot(times, loads, "b-o", markersize=6)
    axes[0].set_ylabel("Load (kW)")
    axes[0].set_title("Dynamic Simulation Over Time")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(times, works, "r-o", markersize=6)
    axes[1].set_ylabel("Work (kW)")
    axes[1].grid(True, alpha=0.3)

    axes[2].bar(times, n_active, width=1.5, color="green", alpha=0.7)
    axes[2].set_ylabel("Active chillers")
    axes[2].set_xlabel("Time (hours)")
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    _save(fig, "dynamic_simulation_timeline.png")


def plot_example1_thermal_plume() -> None:
    """Example 1: Thermal plume from center chiller."""
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    env = SimulationEnvironment(array, wind, model)
    source_idx = 12
    thermal_impact = env.interaction_matrix[source_idx, :]
    positions = array.positions_m

    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(
        positions[:, 0], positions[:, 1],
        c=thermal_impact, cmap="YlOrBr", s=200, edgecolor="k",
    )
    ax.scatter(
        positions[source_idx, 0], positions[source_idx, 1],
        c="blue", s=350, marker="*", label="Source",
    )
    plt.colorbar(sc, ax=ax, label="Thermal Impact Factor")
    ax.set_title("Thermal Wake of a Single Chiller (5×5 Array)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.legend()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "example1_thermal_plume.png")


def plot_example2_density_penalty() -> None:
    """Example 2: Isolated vs crowded COP comparison."""
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0, base_cop=4.0)
    env = SimulationEnvironment(array, wind, GaussianPlumeModel(1.2))
    center_idx = 12

    state_solo = np.zeros(array.num_chillers, dtype=bool)
    state_solo[center_idx] = True
    r_solo = env.compute_performance(state_solo, 10.0)
    state_full = np.ones(array.num_chillers, dtype=bool)
    r_full = env.compute_performance(state_full, 250.0)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        ["Isolated\n(1 chiller)", "Dense array\n(25 chillers)"],
        [r_solo.cop_array[center_idx], r_full.cop_array[center_idx]],
        color=["#2ecc71", "#e74c3c"],
        edgecolor="black",
        linewidth=1,
    )
    ax.set_ylabel("COP")
    ax.set_title("Density Penalty: Same Chiller, Different Neighbors")
    max_h = max(b.get_height() for b in bars)
    pad = max(0.15, max_h * 0.06)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + pad, f"{b.get_height():.2f}",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, 4.8)
    ax.axhline(4.0, color="gray", linestyle="--", alpha=0.5)
    fig.tight_layout()
    _save(fig, "example2_density_penalty.png")


def plot_example3_less_is_more() -> None:
    """Example 3: Standard vs optimized activation."""
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    env = SimulationEnvironment(array, wind, GaussianPlumeModel(1.2))
    total_load = 100.0
    target = 15

    state_std = np.zeros(array.num_chillers, dtype=bool)
    state_std[:target] = True
    r_std = env.compute_performance(state_std, total_load)
    opt = Optimizer(env, total_load)
    opt_result = opt.optimize_greedy(min_active=target)
    r_opt = env.compute_performance(opt_result.optimal_mask, total_load)
    savings = (1 - r_opt.total_work_kw / r_std.total_work_kw) * 100

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        [f"Standard\n(first {target})", "Optimized\n(wind-aware)"],
        [r_std.total_work_kw, r_opt.total_work_kw],
        color=["#e74c3c", "#2ecc71"],
        edgecolor="black",
        linewidth=1,
    )
    ax.set_ylabel("Total work (kW)")
    ax.set_title(f'"Less is More": {savings:.1f}% Energy Savings')
    max_h = max(b.get_height() for b in bars)
    pad = max(1.0, max_h * 0.06)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + pad, f"{b.get_height():.1f} kW",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, max(r_std.total_work_kw, r_opt.total_work_kw) * 1.2)
    fig.tight_layout()
    _save(fig, "example3_less_is_more.png")


def plot_example4_wind_sensitivity() -> None:
    """Example 4: Work vs wind direction."""
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    model = GaussianPlumeModel(1.2)
    active = np.ones(array.num_chillers, dtype=bool)
    load = 100.0

    angles = np.linspace(0, 360, 37)
    results = []
    for angle in angles:
        wind = WindVector.from_speed_and_angle(
            speed_m_per_s=2.0, angle_deg=angle, ambient_temp_k=298.15
        )
        env = SimulationEnvironment(array, wind, model)
        r = env.compute_performance(active, load)
        results.append(r.total_work_kw)
    results = np.array(results)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(angles, results, "b-", linewidth=2)
    ax.fill_between(angles, results, alpha=0.2)
    best_idx = np.argmin(results)
    worst_idx = np.argmax(results)
    ax.scatter(angles[best_idx], results[best_idx], c="green", s=150, marker="*", zorder=5, label=f"Best: {angles[best_idx]:.0f}°")
    ax.scatter(angles[worst_idx], results[worst_idx], c="red", s=150, marker="X", zorder=5, label=f"Worst: {angles[worst_idx]:.0f}°")
    ax.set_xlabel("Wind direction (degrees)")
    ax.set_ylabel("Total work (kW)")
    ax.set_title("Wind Direction Sensitivity")
    ax.set_xlim(0, 360)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "example4_wind_sensitivity.png")


def plot_example5_interaction_models() -> None:
    """Example 5: Compare Gaussian vs simple distance model."""

    class SimpleDistanceModel:
        def __init__(self, decay: float = 0.5):
            self.decay = decay

        def compute_interaction_matrix(self, positions, wind):
            n = len(positions)
            A = np.zeros((n, n), dtype=np.float64)
            wind_vec = wind.direction
            for k in range(n):
                for m in range(n):
                    if k != m:
                        d = positions[m] - positions[k]
                        if np.dot(d, wind_vec) > 0:
                            A[k, m] = self.decay / (np.linalg.norm(d) + 1)
            return A

    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    active = np.ones(array.num_chillers, dtype=bool)
    load = 100.0

    models_data = [
        ("Gaussian σ=1.2", GaussianPlumeModel(1.2)),
        ("Gaussian σ=2.0", GaussianPlumeModel(2.0)),
        ("Simple Distance", SimpleDistanceModel(0.5)),
    ]
    names, works, cops = [], [], []
    for name, model in models_data:
        env = SimulationEnvironment(array, wind, model)
        r = env.compute_performance(active, load)
        names.append(name)
        works.append(r.total_work_kw)
        cops.append(np.mean(r.cop_array))

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(names))
    bars = ax.bar(x - 0.2, works, 0.4, label="Work (kW)", color="steelblue")
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, cops, 0.4, label="Mean COP", color="forestgreen", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("Total work (kW)")
    ax2.set_ylabel("Mean COP")
    ax.set_title("Comparing Interaction Models")
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")
    fig.tight_layout()
    _save(fig, "example5_interaction_models.png")


def plot_example6_large_scale() -> None:
    """Example 6: Work vs number of active chillers (100-chiller array)."""
    array = ChillerArray.create_grid(rows=10, cols=10, spacing_m=5.0)
    wind = WindVector(velocity_m_per_s=(3.0, 1.0), ambient_temp_k=303.15)
    model = GaussianPlumeModel(1.5)
    env = SimulationEnvironment(array, wind, model)
    total_load = 500.0

    n_active_range = list(range(20, 101, 10))
    works = []
    for n in n_active_range:
        opt = Optimizer(env, total_load)
        res = opt.optimize_greedy(min_active=n)
        perf = env.compute_performance(res.optimal_mask, total_load)
        works.append(perf.total_work_kw)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(n_active_range, works, "b-o", linewidth=2, markersize=8)
    best_idx = np.argmin(works)
    ax.scatter(n_active_range[best_idx], works[best_idx], c="red", s=200, marker="*", zorder=5, label=f"Optimal: {n_active_range[best_idx]} chillers")
    ax.set_xlabel("Number of active chillers")
    ax.set_ylabel("Total work (kW)")
    ax.set_title("Large-Scale Array (100 chillers): Less is More")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "example6_large_scale.png")


def main() -> None:
    _ensure_output_dir()
    # Examples 1–6
    plot_example1_thermal_plume()
    plot_example2_density_penalty()
    plot_example3_less_is_more()
    plot_example4_wind_sensitivity()
    plot_example5_interaction_models()
    plot_example6_large_scale()
    # Aging and dynamic (7–8)
    plot_aging_cop_decay()
    plot_aging_new_vs_aged()
    plot_dynamic_load_profile()
    plot_dynamic_startup_ramp()
    plot_dynamic_simulation_timeline()
    print("Done. Figures saved to docs/_static/images/")


if __name__ == "__main__":
    main()
