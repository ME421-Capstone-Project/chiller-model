"""Tests for ChillerSpec and ChillerState components."""

import pytest

from src.components.chiller import ChillerSpec, ChillerState
from src.core.configs import ChillerConfig


class TestChillerSpec:

    def test_create_chiller_spec(self) -> None:
        spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.7)
        assert spec.base_cop == 5.0
        assert spec.rated_capacity_kw == 500.0
        assert spec.alpha == 0.7

    def test_default_alpha(self) -> None:
        spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0)
        assert spec.alpha == 0.7

    def test_is_immutable(self) -> None:
        spec = ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0)
        with pytest.raises(Exception):
            spec.base_cop = 6.0  # type: ignore

    def test_cop_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="base_cop must be > 0"):
            ChillerSpec(base_cop=0.0, rated_capacity_kw=500.0)
        with pytest.raises(ValueError, match="base_cop must be > 0"):
            ChillerSpec(base_cop=-1.0, rated_capacity_kw=500.0)

    def test_cop_cannot_exceed_physical_limit(self) -> None:
        with pytest.raises(ValueError, match="non-physical"):
            ChillerSpec(base_cop=11.0, rated_capacity_kw=500.0)

    def test_capacity_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="rated_capacity_kw must be > 0"):
            ChillerSpec(base_cop=5.0, rated_capacity_kw=0.0)

    def test_alpha_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="alpha must be > 0"):
            ChillerSpec(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.0)

    def test_from_config_factory(self) -> None:
        config = ChillerConfig(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.8)
        spec = ChillerSpec.from_config(config)
        assert spec.base_cop == 5.0
        assert spec.rated_capacity_kw == 500.0
        assert spec.alpha == 0.8


class TestChillerState:

    def test_create_chiller_state(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0, is_active=True)
        assert state.inlet_temp_k == 305.0
        assert state.cop == 4.5
        assert state.load_kw == 100.0
        assert state.is_active is True

    def test_default_is_active(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
        assert state.is_active is True

    def test_is_immutable(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
        with pytest.raises(AttributeError):
            state.cop = 5.0  # type: ignore

    def test_compute_power(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=5.0, load_kw=100.0)
        assert state.compute_power_kw() == pytest.approx(20.0)

    def test_power_zero_when_inactive(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=5.0, load_kw=100.0, is_active=False)
        assert state.compute_power_kw() == 0.0

    def test_power_zero_when_cop_zero(self) -> None:
        state = ChillerState(inlet_temp_k=305.0, cop=0.0, load_kw=100.0)
        assert state.compute_power_kw() == 0.0

    def test_replace_creates_new_state(self) -> None:
        state1 = ChillerState(inlet_temp_k=305.0, cop=4.5, load_kw=100.0)
        state2 = state1._replace(load_kw=150.0)
        assert state1.load_kw == 100.0
        assert state2.load_kw == 150.0
        assert state2.cop == 4.5
