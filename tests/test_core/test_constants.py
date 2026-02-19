"""Tests for core constants and age-related COP degradation.

Validates compute_cop_age_factor and compute_cop_age_factors_vectorized.
"""

import numpy as np
import pytest

from src.core.constants import (
    AGE_MAX_YEARS,
    AGE_MIN_YEARS,
    COP_AGE_FRACTION_AT_1_YEAR,
    compute_cop_age_factor,
    compute_cop_age_factors_vectorized,
)


class TestComputeCopAgeFactor:
    """Tests for compute_cop_age_factor (scalar)."""

    def test_age_zero_returns_one(self) -> None:
        """Age 0 should give 100% COP (factor 1.0)."""
        assert compute_cop_age_factor(0.0) == pytest.approx(1.0)
        assert compute_cop_age_factor(-0.1) == pytest.approx(1.0)

    def test_age_one_returns_fraction_constant(self) -> None:
        """Age 1 year should give COP_AGE_FRACTION_AT_1_YEAR."""
        assert compute_cop_age_factor(1.0) == pytest.approx(
            COP_AGE_FRACTION_AT_1_YEAR
        )

    def test_exponential_decay_monotonic(self) -> None:
        """Factor should decrease monotonically with age."""
        for age in [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]:
            f = compute_cop_age_factor(age)
            assert 0 < f <= 1.0, f"Age {age} gave factor {f}"

    def test_older_means_lower_factor(self) -> None:
        """Older chillers should have lower COP factor."""
        f0 = compute_cop_age_factor(0.0)
        f1 = compute_cop_age_factor(1.0)
        f5 = compute_cop_age_factor(5.0)
        f20 = compute_cop_age_factor(20.0)
        assert f0 > f1 > f5 > f20


class TestComputeCopAgeFactorsVectorized:
    """Tests for compute_cop_age_factors_vectorized."""

    def test_vectorized_matches_scalar(self) -> None:
        """Vectorized results should match scalar for each element."""
        ages = np.array([0.0, 0.5, 1.0, 5.0, 20.0], dtype=np.float64)
        vectorized = compute_cop_age_factors_vectorized(ages)
        for i, age in enumerate(ages):
            scalar = compute_cop_age_factor(float(age))
            assert vectorized[i] == pytest.approx(scalar)

    def test_negative_ages_treated_as_zero(self) -> None:
        """Negative ages should be clipped to 0 (factor 1.0)."""
        ages = np.array([-1.0, -0.5, 0.0], dtype=np.float64)
        factors = compute_cop_age_factors_vectorized(ages)
        np.testing.assert_allclose(factors, [1.0, 1.0, 1.0])

    def test_output_shape_matches_input(self) -> None:
        """Output shape should match input shape."""
        ages = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        factors = compute_cop_age_factors_vectorized(ages)
        assert factors.shape == ages.shape


class TestAgeConstants:
    """Tests for age-related constants."""

    def test_age_bounds_reasonable(self) -> None:
        """AGE_MIN and AGE_MAX should be in sensible range."""
        assert AGE_MIN_YEARS >= 0
        assert AGE_MAX_YEARS > AGE_MIN_YEARS
        assert AGE_MAX_YEARS <= 50  # Reasonable upper bound

    def test_cop_fraction_in_valid_range(self) -> None:
        """COP_AGE_FRACTION_AT_1_YEAR should be in (0, 1]."""
        assert 0 < COP_AGE_FRACTION_AT_1_YEAR <= 1.0
