"""Generate figures for documentation (aging and dynamic simulation examples).

Run from project root with: PYTHONPATH=src python scripts/generate_doc_figures.py

Output: docs/_static/images/*.png
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np

# Add project root so 'src' package is importable
import sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)
# Also add src for direct module imports (components, models, etc.)
sys.path.insert(0, os.path.join(_root, "src"))

from components import ChillerArray, WindVector
from components.data_center import DataCenter
from core.constants import compute_cop_age_factor, CHILLER_STARTUP_TIME_HOURS
from models import GaussianPlumeModel
from simulation import DynamicSimulation, SimulationEnvironment


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
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2, f"{b.get_height():.0f} kW", ha="center")
    ax.set_ylim(0, max(r_new.total_work_kw, r_mixed.total_work_kw) * 1.15)
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


def main() -> None:
    _ensure_output_dir()
    plot_aging_cop_decay()
    plot_aging_new_vs_aged()
    plot_dynamic_load_profile()
    plot_dynamic_startup_ramp()
    plot_dynamic_simulation_timeline()
    print("Done. Figures saved to docs/_static/images/")


if __name__ == "__main__":
    main()
