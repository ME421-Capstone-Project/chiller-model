"""Tests for ChillerSpec and ChillerState components.

Validates immutability and physical constraints on chiller models.
"""

import pytest

from src.components.chiller import ChillerSpec, ChillerState
from src.core.configs import ChillerConfig


class TestChillerSpec:
    """Tests for ChillerSpec class."""

    def test_create_chiller_spec(self) -> None:
        """Basic chiller spec creation should work."""
        spec = ChillerSpec(
            base_cop=5.0,
            rated_capacity_kw=500.0,
            alpha=0.7,
        )
        assert spec.base_cop == 5.0
        assert spec.rated_capacity_kw == 500.0
        assert spec.alpha == 0.7

    def test_default_alpha(self) -> None:
        """Default alpha should be 0.7."""
        spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0)
        assert spec.alpha == 0.7

    def test_is_immutable(self) -> None:
        """ChillerSpec should be immutable (frozen dataclass)."""
        spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0)

        with pytest.raises(Exception):  # FrozenInstanceError
            spec.base_cop = 6.0  # type: ignore

    def test_cop_must_be_positive(self) -> None:
        """COP <= 0 should raise ValueError."""
        with pytest.raises(ValueError, match="base_cop must be > 0"):
            ChillerSpec(base_cop=0.0, rated_capacity_kw=500.0)

        with pytest.raises(ValueError, match="base_cop must be > 0"):
            ChillerSpec(base_cop=-1.0, rated_capacity_kw=500.0)

    def test_cop_cannot_exceed_physical_limit(self) -> None:
        """COP > 10 should raise ValueError."""
        with pytest.raises(ValueError, match="non-physical"):
            ChillerSpec(base_cop=11.0, rated_capacity_kw=500.0)

    def test_capacity_must_be_positive(self) -> None:
        """Rated capacity <= 0 should raise ValueError."""
        with pytest.raises(ValueError, match="rated_capacity_kw must be > 0"):
            ChillerSpec(base_cop=5.0, rated_capacity_kw=0.0)

    def test_alpha_must_be_positive(self) -> None:
        """Alpha <= 0 should raise ValueError."""
        with pytest.raises(ValueError, match="alpha must be > 0"):
            ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.0)

    def test_from_config_factory(self) -> None:
        """Factory method from_config should work correctly."""
        config = ChillerConfig(
            base_cop=5.0,
            rated_capacity_kw=500.0,
            alpha=0.8,
        )
        spec = ChillerSpec.from_config(config)

        assert spec.base_cop == 5.0
        assert spec.rated_capacity_kw == 500.0
        assert spec.alpha == 0.8


class TestChillerState:
    """Tests for ChillerState class."""

    def test_create_chiller_state(self) -> None:
        """Basic chiller state creation should work."""
        state = ChillerState(
            inlet_temp_k=305.0,
            cop=4.5,
            load_kw=100.0,
            is_active=True,
        )
        assert state.inlet_temp_k == 305.0
        assert state.cop == 4.5
        assert state.load_kw == 100.0
        assert state.is_active is True

    def test_default_is_active(self) -> None:
        """Default is_active should be True."""
        state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
        assert state.is_active is True

    def test_is_immutable(self) -> None:
        """ChillerState should be immutable (NamedTuple)."""
        state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)

        with pytest.raises(AttributeError):
            state.cop = 5.0  # type: ignore

    def test_compute_power(self) -> None:
        """Power should be computed as load / COP."""
        state = ChillerState(inlet_temp_k=305.0, cop=5.0, load_kw=100.0)
        power = state.compute_power_kw()

        assert power == pytest.approx(20.0)  # 100 / 5 = 20

    def test_power_zero_when_inactive(self) -> None:
        """Power should be zero when chiller is inactive."""
        state = ChillerState(
            inlet_temp_k=305.0,
            cop=5.0,
            load_kw=100.0,
            is_active=False,
        )
        assert state.compute_power_kw() == 0.0

    def test_power_zero_when_cop_zero(self) -> None:
        """Power should be zero when COP is zero (edge case)."""
        state = ChillerState(inlet_temp_k=305.0, cop=0.0, load_kw=100.0)
        assert state.compute_power_kw() == 0.0

    def test_replace_creates_new_state(self) -> None:
        """_replace should create new state (immutability)."""
        state1 = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
        state2 = state1._replace(load_kw=150.0)

        assert state1.load_kw == 100.0  # Original unchanged
        assert state2.load_kw == 150.0  # New state has new value
        assert state2.cop == 4.5  # Other fields preserved
