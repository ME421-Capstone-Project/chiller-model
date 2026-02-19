import pytest
from pydantic import ValidationError

from src.core.configs import ChillerConfig, SimulationConfig, WindConfig
from src.core.constants import MAX_REALISTIC_COP


class TestChillerConfig:

    def test_valid_config(self) -> None:
        config = ChillerConfig(
            base_cop=5.0,
            rated_capacity_kw=500.0,
            alpha=0.7,
        )
        assert config.base_cop == 5.0
        assert config.rated_capacity_kw == 500.0
        assert config.alpha == 0.7

    def test_default_values(self) -> None:
        config = ChillerConfig(rated_capacity_kw=500.0)
        assert config.base_cop == pytest.approx(4.0)
        assert config.alpha == pytest.approx(0.7)

    def test_cop_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=0.0, rated_capacity_kw=500.0)

        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=-1.0, rated_capacity_kw=500.0)

    def test_cop_cannot_exceed_thermodynamic_limit(self) -> None:
        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=MAX_REALISTIC_COP + 0.1, rated_capacity_kw=500.0)

    def test_capacity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=5.0, rated_capacity_kw=0.0)

        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=5.0, rated_capacity_kw=-100.0)

    def test_alpha_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=5.0, rated_capacity_kw=500.0, alpha=0.0)

    def test_alpha_cannot_exceed_limit(self) -> None:
        with pytest.raises(ValidationError):
            ChillerConfig(base_cop=5.0, rated_capacity_kw=500.0, alpha=2.1)


class TestWindConfig:

    def test_valid_config(self) -> None:
        config = WindConfig(
            velocity_x_m_per_s=5.0,
            velocity_y_m_per_s=0.0,
            ambient_temp_k=298.15,
        )
        assert config.velocity_x_m_per_s == 5.0
        assert config.velocity_y_m_per_s == 0.0
        assert config.ambient_temp_k == 298.15

    def test_temperature_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            WindConfig(
                velocity_x_m_per_s=5.0,
                velocity_y_m_per_s=0.0,
                ambient_temp_k=0.0,
            )

        with pytest.raises(ValidationError):
            WindConfig(
                velocity_x_m_per_s=5.0,
                velocity_y_m_per_s=0.0,
                ambient_temp_k=-10.0,
            )

    def test_temperature_below_realistic_minimum(self) -> None:
        with pytest.raises(ValidationError):
            WindConfig(
                velocity_x_m_per_s=5.0,
                velocity_y_m_per_s=0.0,
                ambient_temp_k=100.0,
            )

    def test_temperature_above_realistic_maximum(self) -> None:
        with pytest.raises(ValidationError):
            WindConfig(
                velocity_x_m_per_s=5.0,
                velocity_y_m_per_s=0.0,
                ambient_temp_k=400.0,
            )


class TestSimulationConfig:

    def test_valid_config(self) -> None:
        config = SimulationConfig(
            dispersion_coeff=1.2,
            total_load_kw=500.0,
        )
        assert config.dispersion_coeff == 1.2
        assert config.total_load_kw == 500.0

    def test_dispersion_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            SimulationConfig(dispersion_coeff=0.0, total_load_kw=500.0)

    def test_load_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            SimulationConfig(total_load_kw=0.0)
