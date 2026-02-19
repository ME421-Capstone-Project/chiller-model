"""
Example: Chiller Age and COP Degradation
========================================

Demonstrates the age parameter for chillers:
- Age assigned randomly (uniform 0-20 years) or manually
- COP decays exponentially with age: 100% at age=0 to 80% at age=1 year
- All constants configurable in src/core/constants.py

Usage
-----
    cd /workspace
    PYTHONPATH=src python scripts/example_chiller_age.py

    Or, if package installed: python scripts/example_chiller_age.py

Constants (edit core/constants.py or src/core/constants.py)
--------------------------------------
- AGE_MIN_YEARS, AGE_MAX_YEARS: Random age range
- COP_AGE_FRACTION_AT_1_YEAR: COP fraction after 1 year (default 0.8)
- COP_AGE_DECAY_TIMESCALE_YEARS: Timescale for decay curve
"""

from __future__ import annotations

import numpy as np

from components import ChillerArray, WindVector
from core.constants import (
    AGE_MAX_YEARS,
    AGE_MIN_YEARS,
    COP_AGE_FRACTION_AT_1_YEAR,
    compute_cop_age_factor,
)
from models import GaussianPlumeModel
from simulation import SimulationEnvironment


def demo_manual_ages() -> None:
    """Demonstrate manually assigned chiller ages."""
    print("\n" + "=" * 60)
    print("1. MANUAL AGE ASSIGNMENT")
    print("=" * 60)

    # Create 4 chillers with explicit ages: 0, 1, 5, 10 years
    ages = np.array([0.0, 1.0, 5.0, 10.0], dtype=np.float64)
    array = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=15.0,
        base_cop=5.0,
        ages_years=ages,
    )

    print(f"Chiller ages (years): {array.ages_years}")
    print(f"COP age factors:      {array.cop_age_factors}")
    print(f"  Age 0 yr  -> factor {compute_cop_age_factor(0):.3f} (100%)")
    print(f"  Age 1 yr  -> factor {compute_cop_age_factor(1):.3f} ({COP_AGE_FRACTION_AT_1_YEAR*100:.0f}%)")
    print(f"  Age 5 yr  -> factor {compute_cop_age_factor(5):.3f}")
    print(f"  Age 10 yr -> factor {compute_cop_age_factor(10):.3f}")


def demo_random_ages() -> None:
    """Demonstrate random age assignment at simulation start."""
    print("\n" + "=" * 60)
    print("2. RANDOM AGE ASSIGNMENT (uniform 0-20 years)")
    print("=" * 60)

    # Create grid without ages -> random uniform [AGE_MIN, AGE_MAX]
    array = ChillerArray.create_grid(
        rows=3,
        cols=3,
        spacing_m=10.0,
        base_cop=5.0,
        seed=42,  # Reproducible
    )

    print(f"Random ages (seed=42): {array.ages_years.round(2)}")
    print(f"Age range: [{AGE_MIN_YEARS}, {AGE_MAX_YEARS}] years")
    print(f"COP factors:          {array.cop_age_factors.round(3)}")


def demo_simulation_with_age() -> None:
    """Compare simulation results: new vs aged chillers."""
    print("\n" + "=" * 60)
    print("3. SIMULATION: NEW vs AGED CHILLERS")
    print("=" * 60)

    wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
    model = GaussianPlumeModel()
    total_load_kw = 500.0

    # All new chillers (age=0)
    array_new = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=10.0,
        base_cop=5.0,
        ages_years=np.zeros(4, dtype=np.float64),
    )
    env_new = SimulationEnvironment(array_new, wind, model)
    result_new = env_new.compute_performance(
        active_mask=np.ones(4, dtype=bool),
        total_load_kw=total_load_kw,
    )

    # Mixed ages: 0, 5, 10, 15 years
    array_mixed = ChillerArray.create_grid(
        rows=2,
        cols=2,
        spacing_m=10.0,
        base_cop=5.0,
        ages_years=np.array([0.0, 5.0, 10.0, 15.0], dtype=np.float64),
    )
    env_mixed = SimulationEnvironment(array_mixed, wind, model)
    result_mixed = env_mixed.compute_performance(
        active_mask=np.ones(4, dtype=bool),
        total_load_kw=total_load_kw,
    )

    print(f"Load: {total_load_kw} kW, 4 chillers active")
    print()
    print("All new (age=0):")
    print(f"  Total work:    {result_new.total_work_kw:.1f} kW")
    print(f"  Effective COP: {result_new.effective_cop:.2f}")
    print()
    print("Mixed ages (0, 5, 10, 15 yr):")
    print(f"  Total work:    {result_mixed.total_work_kw:.1f} kW")
    print(f"  Effective COP: {result_mixed.effective_cop:.2f}")
    print()
    print(f"Age increases work by: {(result_mixed.total_work_kw/result_new.total_work_kw - 1)*100:.1f}%")


def demo_cop_decay_curve() -> None:
    """Show COP decay curve over age."""
    print("\n" + "=" * 60)
    print("4. COP DECAY CURVE (exponential)")
    print("=" * 60)

    print("Age (yr) | COP factor | % of new")
    print("-" * 35)
    for age in [0, 0.5, 1, 2, 5, 10, 15, 20]:
        factor = compute_cop_age_factor(float(age))
        pct = factor * 100
        print(f"  {age:5.1f}  |    {factor:.3f}   |  {pct:5.1f}%")


def main() -> None:
    """Run all age demos."""
    print("\nCHILLER AGE AND COP DEGRADATION EXAMPLES")
    print("Constants: src/core/constants.py")
    demo_manual_ages()
    demo_random_ages()
    demo_simulation_with_age()
    demo_cop_decay_curve()
    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
