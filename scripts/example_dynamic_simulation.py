"""
Example: Dynamic Simulation with Varying Load, Wind, and Chiller Startup
======================================================================

Demonstrates:
- Time-varying heat load from data center
- Constant or varying wind (direction)
- Chiller startup delay: COP ramps linearly from 0 to full over startup time

Usage
-----
    cd /workspace
    PYTHONPATH=src python scripts/example_dynamic_simulation.py

Constants (edit core/constants.py)
----------------------------------
- CHILLER_STARTUP_TIME_HOURS: Time for COP to ramp 0→1 (default 0.25h)
"""

from __future__ import annotations

import numpy as np

from components import ChillerArray, WindVector, sinusoidal_direction_profile
from components.data_center import DataCenter
from core.constants import (
    CHILLER_STARTUP_TIME_HOURS,
    compute_cop_startup_factor_linear,
)
from models import GaussianPlumeModel
from simulation import DynamicSimulation, SimulationEnvironment


def demo_constant_load() -> None:
    """Demonstrate dynamic simulation with constant load."""
    print("\n" + "=" * 60)
    print("1. CONSTANT LOAD (startup ramp visible)")
    print("=" * 60)

    array = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=15.0,
        base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    env = SimulationEnvironment(array, wind, model)
    dc = DataCenter(base_load_kw=500.0)

    sim = DynamicSimulation(
        environment=env,
        data_center=dc,
        time_step_hours=0.1,
        startup_time_hours=0.25,
    )

    print(f"Load: 500 kW constant | Startup: {CHILLER_STARTUP_TIME_HOURS}h")
    print("Time(h) | Load(kW) | Work(kW) | Active")
    print("-" * 50)

    for step in sim.run(duration_hours=0.6):
        n_active = int(np.sum(step.active_mask))
        print(
            f"  {step.time_hours:.1f}   |   {step.load_kw:.0f}   | "
            f" {step.total_work_kw:7.1f} | {n_active}"
        )


def demo_varying_load() -> None:
    """Demonstrate dynamic simulation with sinusoidal load."""
    print("\n" + "=" * 60)
    print("2. VARYING LOAD (sinusoidal daily profile)")
    print("=" * 60)

    array = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=15.0,
        base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    wind = WindVector(velocity_m_per_s=(3.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    env = SimulationEnvironment(array, wind, model)

    dc = DataCenter.with_sinusoidal_profile(
        base_load_kw=300.0,
        peak_load_kw=800.0,
        period_hours=24.0,
    )

    sim = DynamicSimulation(
        environment=env,
        data_center=dc,
        time_step_hours=2.0,
        startup_time_hours=0.25,
    )

    print("Time(h) | Load(kW) | Work(kW) | Active")
    print("-" * 45)

    for step in sim.run(duration_hours=12.0):
        n_active = int(np.sum(step.active_mask))
        print(
            f"  {step.time_hours:5.1f} | {step.load_kw:7.0f} | "
            f"{step.total_work_kw:7.1f} | {n_active}"
        )


def demo_varying_wind() -> None:
    """Demonstrate dynamic simulation with varying wind direction."""
    print("\n" + "=" * 60)
    print("3. VARYING WIND DIRECTION (sinusoidal)")
    print("=" * 60)

    array = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=15.0,
        base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    # Initial wind (used when wind_profile not provided at t=0)
    wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    env = SimulationEnvironment(array, wind, model)
    dc = DataCenter(base_load_kw=500.0)

    wind_profile = sinusoidal_direction_profile(
        speed_m_per_s=5.0,
        angle_center_deg=90.0,  # North
        angle_amplitude_deg=60.0,
        period_hours=24.0,
        ambient_temp_k=298.15,
    )

    sim = DynamicSimulation(
        environment=env,
        data_center=dc,
        time_step_hours=2.0,
        wind_profile=wind_profile,
    )

    print("Time(h) | Load(kW) | Work(kW) | Wind(deg) | Active")
    print("-" * 55)
    for step in sim.run(duration_hours=8.0):
        angle_deg = np.degrees(np.arctan2(
            step.wind.velocity_m_per_s[1],
            step.wind.velocity_m_per_s[0],
        ))
        n_active = int(np.sum(step.active_mask))
        print(
            f"  {step.time_hours:5.1f} | {step.load_kw:7.0f} | "
            f"{step.total_work_kw:7.1f} | {angle_deg:8.1f} | {n_active}"
        )


def demo_startup_ramp() -> None:
    """Show COP startup ramp (linear function)."""
    print("\n" + "=" * 60)
    print("4. COP STARTUP RAMP (linear 0→1)")
    print("=" * 60)

    print("Time since start | COP factor")
    print("-" * 35)
    for t in [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.5]:
        factor = compute_cop_startup_factor_linear(t)
        print(f"  {t:5.2f} h         | {factor:.2f} ({factor*100:.0f}%)")


def main() -> None:
    """Run all dynamic simulation demos."""
    print("\nDYNAMIC SIMULATION: Varying Load, Wind, and Chiller Startup")
    print("Startup: linear COP ramp")
    demo_constant_load()
    demo_varying_load()
    demo_varying_wind()
    demo_startup_ramp()
    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
