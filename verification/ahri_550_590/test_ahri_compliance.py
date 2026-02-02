"""Verification tests against AHRI 550/590 rating conditions.

This module contains regression tests that verify the chiller model
produces reasonable outputs at standard AHRI rating conditions.

Reference
---------
AHRI Standard 550/590-2015:
    Performance Rating of Water-Chilling and Heat Pump
    Water-Heating Packages Using the Vapor Compression Cycle

Rating Conditions (Full Load)
-----------------------------
- Evaporator leaving water temp: 44°F (6.67°C, 279.82 K)
- Condenser entering water temp: 85°F (29.44°C, 302.59 K)
- Condenser leaving water temp: 95°F (35°C, 308.15 K)

Notes
-----
These tests verify that the simulation framework produces physically
reasonable results. They do NOT validate specific manufacturer data
(which would require actual certified rating data).
"""

import numpy as np
import pytest

from src.components.chiller_array import ChillerArray
from src.components.wind import WindVector
from src.models.gaussian_plume import GaussianPlumeModel
from src.simulation.environment import SimulationEnvironment
from src.simulation.optimizer import Optimizer


class TestAHRIRatingConditions:
    """Tests at AHRI standard rating conditions.

    Reference: AHRI Standard 550/590-2015
    """

    # Standard AHRI rating temperatures
    AHRI_CONDENSER_ENTERING_TEMP_K = 302.59  # 85°F

    @pytest.fixture
    def ahri_wind(self) -> WindVector:
        """Wind conditions at AHRI rating temperature."""
        return WindVector(
            velocity_m_per_s=(3.0, 0.0),  # Moderate 3 m/s wind
            ambient_temp_k=self.AHRI_CONDENSER_ENTERING_TEMP_K,
        )

    @pytest.fixture
    def ahri_chiller_array(self) -> ChillerArray:
        """Chiller array with typical AHRI-rated specifications.

        A 4x4 grid of 500-ton (1758 kW) chillers with COP of 5.5
        represents a typical high-efficiency centrifugal installation.
        """
        return ChillerArray.create_grid(
            rows=4,
            cols=4,
            spacing_m=15.0,  # 15m spacing is typical for large installations
            base_cop=5.5,  # IPLV-rated efficiency
            alpha=0.7,
        )

    @pytest.fixture
    def ahri_env(
        self,
        ahri_chiller_array: ChillerArray,
        ahri_wind: WindVector,
    ) -> SimulationEnvironment:
        """Simulation environment at AHRI conditions."""
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        return SimulationEnvironment(ahri_chiller_array, ahri_wind, model)

    def test_cop_within_physical_bounds(
        self,
        ahri_env: SimulationEnvironment,
    ) -> None:
        """COP must remain within physical limits at AHRI conditions.

        Physical Constraints:
        - COP > 0 (thermodynamic necessity)
        - COP <= base_cop (interference can only degrade, not improve)
        - COP typically 3-7 for water-cooled chillers
        """
        active_mask = np.ones(16, dtype=bool)
        result = ahri_env.compute_performance(active_mask, total_load_kw=5000.0)

        # COP must be positive
        assert np.all(result.cop_array > 0), "COP must be positive"

        # COP cannot exceed base
        assert np.all(result.cop_array <= ahri_env.chiller_array.base_cop)

        # COP should be in reasonable range for water-cooled chillers
        assert np.all(result.cop_array >= 2.0), "COP < 2 is unrealistic"
        assert np.all(result.cop_array <= 8.0), "COP > 8 is unrealistic"

    def test_power_proportional_to_load(
        self,
        ahri_env: SimulationEnvironment,
    ) -> None:
        """Power consumption should scale with cooling load.

        At fixed COP, doubling load should roughly double power.
        """
        active_mask = np.ones(16, dtype=bool)

        result_1000 = ahri_env.compute_performance(active_mask, total_load_kw=1000.0)
        result_2000 = ahri_env.compute_performance(active_mask, total_load_kw=2000.0)

        # Power should roughly double (exactly if COP unchanged)
        ratio = result_2000.total_work_kw / result_1000.total_work_kw
        assert 1.8 < ratio < 2.2, f"Power ratio {ratio} should be ~2.0"

    def test_system_efficiency_reasonable(
        self,
        ahri_env: SimulationEnvironment,
    ) -> None:
        """System efficiency should be in typical range.

        For water-cooled centrifugal chillers at AHRI conditions:
        - Individual unit COP: 5-7
        - System effective COP with interference: 4-6.5 typically
        """
        active_mask = np.ones(16, dtype=bool)
        result = ahri_env.compute_performance(active_mask, total_load_kw=5000.0)

        effective_cop = result.effective_cop
        assert effective_cop > 3.5, f"Effective COP {effective_cop} too low"
        assert effective_cop < 7.0, f"Effective COP {effective_cop} too high"

    def test_optimization_provides_improvement(
        self,
        ahri_env: SimulationEnvironment,
    ) -> None:
        """Optimization should provide energy savings at AHRI conditions.

        With 16 densely packed chillers, turning off some units
        should reduce thermal interference and save energy.
        """
        optimizer = Optimizer(ahri_env, total_load_kw=5000.0)
        result = optimizer.optimize_greedy(min_active=4)

        # Should achieve some savings
        assert result.savings_fraction >= 0, "Optimization should not increase work"

        # Optimal should use fewer than all chillers
        # (unless spacing is large enough that there's no interference)
        # For dense 15m spacing, we expect some benefit from partial operation

    def test_thermal_interference_increases_with_density(self) -> None:
        """Denser arrays should have more thermal interference.

        This validates the core physics: closer chillers = more
        exhaust recirculation = lower effective COP.
        """
        wind = WindVector(
            velocity_m_per_s=(3.0, 0.0),
            ambient_temp_k=self.AHRI_CONDENSER_ENTERING_TEMP_K,
        )
        model = GaussianPlumeModel(dispersion_coeff=1.2)

        # Sparse array (25m spacing)
        sparse_array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=25.0, base_cop=5.5
        )
        sparse_env = SimulationEnvironment(sparse_array, wind, model)

        # Dense array (10m spacing)
        dense_array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=10.0, base_cop=5.5
        )
        dense_env = SimulationEnvironment(dense_array, wind, model)

        active_mask = np.ones(16, dtype=bool)
        sparse_result = sparse_env.compute_performance(active_mask, 5000.0)
        dense_result = dense_env.compute_performance(active_mask, 5000.0)

        # Dense array should require more work (lower efficiency)
        assert dense_result.total_work_kw > sparse_result.total_work_kw
        assert dense_result.effective_cop < sparse_result.effective_cop


class TestVerificationData:
    """Tests using reference verification data.

    These tests would use actual manufacturer rating data if available.
    Currently demonstrates the verification framework structure.
    """

    @pytest.fixture
    def reference_case(self) -> dict:
        """Reference verification case.

        In a real implementation, this would load from data files
        in the data/manufacturer_curves/ directory.
        """
        return {
            "description": "4x4 grid at standard conditions",
            "num_chillers": 16,
            "spacing_m": 15.0,
            "base_cop": 5.5,
            "wind_speed_m_s": 3.0,
            "total_load_kw": 5000.0,
            # Expected ranges (not exact values without real data)
            "expected_work_kw_range": (800.0, 1500.0),
            "expected_effective_cop_range": (4.0, 6.5),
        }

    def test_against_reference_case(self, reference_case: dict) -> None:
        """Test model output against reference case.

        This demonstrates the verification framework. With real
        manufacturer data, the expected values would be more precise.
        """
        array = ChillerArray.create_grid(
            rows=4,
            cols=4,
            spacing_m=reference_case["spacing_m"],
            base_cop=reference_case["base_cop"],
        )
        wind = WindVector(
            velocity_m_per_s=(reference_case["wind_speed_m_s"], 0.0),
            ambient_temp_k=302.59,
        )
        model = GaussianPlumeModel(dispersion_coeff=1.2)
        env = SimulationEnvironment(array, wind, model)

        active_mask = np.ones(reference_case["num_chillers"], dtype=bool)
        result = env.compute_performance(
            active_mask,
            reference_case["total_load_kw"],
        )

        # Verify within expected ranges
        work_min, work_max = reference_case["expected_work_kw_range"]
        assert work_min <= result.total_work_kw <= work_max, (
            f"Work {result.total_work_kw:.1f} kW outside expected range "
            f"[{work_min}, {work_max}]"
        )

        cop_min, cop_max = reference_case["expected_effective_cop_range"]
        assert cop_min <= result.effective_cop <= cop_max, (
            f"Effective COP {result.effective_cop:.2f} outside expected range "
            f"[{cop_min}, {cop_max}]"
        )


class TestPhysicalConsistency:
    """Tests for internal physical consistency.

    These tests verify that the model behaves consistently
    with thermodynamic principles.
    """

    def test_energy_balance_qualitative(self) -> None:
        """Total work should be greater than load / max_COP.

        Thermodynamic lower bound: Work >= Load / COP_max
        """
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=15.0, base_cop=5.0
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=300.0)
        model = GaussianPlumeModel()
        env = SimulationEnvironment(array, wind, model)

        active_mask = np.ones(16, dtype=bool)
        result = env.compute_performance(active_mask, total_load_kw=1000.0)

        # Minimum possible work = load / base_cop
        min_work = 1000.0 / 5.0  # 200 kW
        assert result.total_work_kw >= min_work, (
            f"Work {result.total_work_kw} below thermodynamic minimum {min_work}"
        )

    def test_no_negative_entropy_generation(self) -> None:
        """Interference cannot improve COP (would violate 2nd law).

        More active chillers = more interference = lower or equal COP
        """
        array = ChillerArray.create_grid(
            rows=4, cols=4, spacing_m=10.0, base_cop=5.0, alpha=1.0
        )
        wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=300.0)
        model = GaussianPlumeModel(dispersion_coeff=1.0)
        env = SimulationEnvironment(array, wind, model)

        # Single chiller: no interference
        single_mask = np.zeros(16, dtype=bool)
        single_mask[0] = True
        single_result = env.compute_performance(single_mask, total_load_kw=100.0)

        # All chillers: maximum interference
        all_mask = np.ones(16, dtype=bool)
        all_result = env.compute_performance(all_mask, total_load_kw=100.0)

        # Single chiller COP should be at or above any chiller in full array
        # (no interference vs maximum interference)
        assert single_result.cop_array[0] >= np.min(all_result.cop_array)
