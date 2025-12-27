# tests/strategies/armstrong/test_cycle_model.py
"""
Tests für das Armstrong Cycle Model.

Testet:
- ArmstrongPhase Enum
- ArmstrongCycleConfig Dataclass
- ArmstrongCycleModel (phase_for_date, risk_multiplier_for_date)
"""

import pytest
from datetime import date, timedelta

import pandas as pd

from src.strategies.armstrong.cycle_model import (
    ArmstrongPhase,
    ArmstrongCycleConfig,
    ArmstrongCycleModel,
    get_phase_for_date,
    get_risk_multiplier_for_date,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def default_config() -> ArmstrongCycleConfig:
    """Standard-Konfiguration für Tests."""
    return ArmstrongCycleConfig.default()


@pytest.fixture
def test_config() -> ArmstrongCycleConfig:
    """Test-Konfiguration mit bekanntem Referenzdatum und kurzer Zykluslänge."""
    return ArmstrongCycleConfig(
        reference_peak_date=date(2020, 1, 1),
        cycle_length_days=100,  # Kurzer Zyklus für einfache Tests
    )


@pytest.fixture
def model_default(default_config: ArmstrongCycleConfig) -> ArmstrongCycleModel:
    """Modell mit Standard-Config."""
    return ArmstrongCycleModel(default_config)


@pytest.fixture
def model_test(test_config: ArmstrongCycleConfig) -> ArmstrongCycleModel:
    """Modell mit Test-Config."""
    return ArmstrongCycleModel(test_config)


# =============================================================================
# ARMSTRONG PHASE ENUM TESTS
# =============================================================================


class TestArmstrongPhase:
    """Tests für ArmstrongPhase Enum."""

    def test_phase_values(self) -> None:
        """Prüft, dass alle erwarteten Phasen existieren."""
        assert ArmstrongPhase.CRISIS.value == "crisis"
        assert ArmstrongPhase.EXPANSION.value == "expansion"
        assert ArmstrongPhase.CONTRACTION.value == "contraction"
        assert ArmstrongPhase.PRE_CRISIS.value == "pre_crisis"
        assert ArmstrongPhase.POST_CRISIS.value == "post_crisis"

    def test_phase_count(self) -> None:
        """Prüft die Anzahl der Phasen."""
        assert len(ArmstrongPhase) == 5

    def test_phase_str(self) -> None:
        """Prüft String-Repräsentation."""
        assert str(ArmstrongPhase.EXPANSION) == "expansion"
        assert str(ArmstrongPhase.CRISIS) == "crisis"


# =============================================================================
# ARMSTRONG CYCLE CONFIG TESTS
# =============================================================================


class TestArmstrongCycleConfig:
    """Tests für ArmstrongCycleConfig Dataclass."""

    def test_default_config(self) -> None:
        """Prüft Default-Konfiguration."""
        config = ArmstrongCycleConfig.default()

        assert config.reference_peak_date == date(2015, 10, 1)
        assert config.cycle_length_days == 3141
        assert "expansion" in config.phase_distribution
        assert "crisis" in config.phase_distribution

    def test_custom_config(self) -> None:
        """Prüft benutzerdefinierte Konfiguration."""
        config = ArmstrongCycleConfig(
            reference_peak_date=date(2024, 1, 1),
            cycle_length_days=1000,
        )

        assert config.reference_peak_date == date(2024, 1, 1)
        assert config.cycle_length_days == 1000

    def test_config_validation(self) -> None:
        """Prüft Parameter-Validierung."""
        # Zu kurze Zykluslänge sollte ValueError werfen
        with pytest.raises(ValueError, match="cycle_length_days"):
            ArmstrongCycleConfig(
                reference_peak_date=date(2020, 1, 1),
                cycle_length_days=10,  # Zu kurz
            )

    def test_risk_multipliers_exist(self) -> None:
        """Prüft, dass Risk-Multiplier definiert sind."""
        config = ArmstrongCycleConfig.default()

        assert "crisis" in config.risk_multipliers
        assert "expansion" in config.risk_multipliers
        assert config.risk_multipliers["expansion"] == 1.0
        assert config.risk_multipliers["crisis"] == 0.3

    def test_to_dict(self) -> None:
        """Prüft Dictionary-Export."""
        config = ArmstrongCycleConfig.default()
        d = config.to_dict()

        assert "reference_peak_date" in d
        assert "cycle_length_days" in d
        assert "phase_distribution" in d
        assert "risk_multipliers" in d


# =============================================================================
# ARMSTRONG CYCLE MODEL TESTS
# =============================================================================


class TestArmstrongCycleModel:
    """Tests für ArmstrongCycleModel."""

    def test_model_creation_default(self) -> None:
        """Prüft Modell-Erstellung mit Default-Config."""
        model = ArmstrongCycleModel.from_default()

        assert model.config.cycle_length_days == 3141
        assert model.config.reference_peak_date == date(2015, 10, 1)

    def test_model_creation_custom(self) -> None:
        """Prüft Modell-Erstellung mit Custom-Config."""
        config = ArmstrongCycleConfig(
            reference_peak_date=date(2020, 6, 15),
            cycle_length_days=2000,
        )
        model = ArmstrongCycleModel(config)

        assert model.config.cycle_length_days == 2000

    def test_from_config_dict(self) -> None:
        """Prüft Erstellung aus Dictionary."""
        config_dict = {
            "reference_peak_date": "2022-03-01",
            "cycle_length_days": 500,
        }
        model = ArmstrongCycleModel.from_config_dict(config_dict)

        assert model.config.reference_peak_date == date(2022, 3, 1)
        assert model.config.cycle_length_days == 500


class TestArmstrongPhaseForDate:
    """Tests für phase_for_date Methode."""

    def test_phase_at_reference_date(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft Phase am Referenzdatum (sollte Post-Crisis sein da 0% im Zyklus)."""
        # Am Referenzdatum sind wir bei Position 0.0 (Post-Crisis)
        phase = model_test.phase_for_date(date(2020, 1, 1))
        assert phase == ArmstrongPhase.POST_CRISIS

    def test_different_dates_different_phases(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass verschiedene Daten verschiedene Phasen ergeben können."""
        ref = date(2020, 1, 1)
        phases = []

        # 100 Tage durchgehen (ein voller Zyklus)
        for i in range(0, 100, 10):
            test_date = ref + timedelta(days=i)
            phase = model_test.phase_for_date(test_date)
            phases.append(phase)

        # Es sollten mehrere verschiedene Phasen vorkommen
        unique_phases = set(phases)
        assert len(unique_phases) >= 3, "Sollte mindestens 3 verschiedene Phasen geben"

    def test_phase_deterministic(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass Phase-Bestimmung deterministisch ist."""
        test_date = date(2020, 3, 15)

        phase1 = model_test.phase_for_date(test_date)
        phase2 = model_test.phase_for_date(test_date)
        phase3 = model_test.phase_for_date(test_date)

        assert phase1 == phase2 == phase3

    def test_phase_with_timestamp(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft Phase-Bestimmung mit pd.Timestamp."""
        ts = pd.Timestamp("2020-04-15")
        phase = model_test.phase_for_date(ts)

        assert isinstance(phase, ArmstrongPhase)

    def test_phase_cyclic(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass der Zyklus sich wiederholt."""
        ref = date(2020, 1, 1)
        cycle_length = model_test.config.cycle_length_days

        # Phase am Tag 50
        phase_50 = model_test.phase_for_date(ref + timedelta(days=50))

        # Phase am Tag 50 + ein voller Zyklus sollte gleich sein
        phase_50_plus_cycle = model_test.phase_for_date(ref + timedelta(days=50 + cycle_length))

        assert phase_50 == phase_50_plus_cycle


class TestArmstrongRiskMultiplier:
    """Tests für risk_multiplier_for_date Methode."""

    def test_risk_multiplier_range(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass Risk-Multiplier im Bereich 0-1 liegt."""
        ref = date(2020, 1, 1)

        for i in range(100):
            test_date = ref + timedelta(days=i)
            mult = model_test.risk_multiplier_for_date(test_date)

            assert 0.0 <= mult <= 1.0, f"Multiplier {mult} außerhalb Bereich für Tag {i}"

    def test_risk_multiplier_deterministic(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass Risk-Multiplier deterministisch ist."""
        test_date = date(2020, 5, 10)

        mult1 = model_test.risk_multiplier_for_date(test_date)
        mult2 = model_test.risk_multiplier_for_date(test_date)

        assert mult1 == mult2

    def test_risk_multiplier_consistent_with_phase(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft Konsistenz zwischen Phase und Risk-Multiplier."""
        ref = date(2020, 1, 1)

        for i in range(100):
            test_date = ref + timedelta(days=i)
            phase = model_test.phase_for_date(test_date)
            mult = model_test.risk_multiplier_for_date(test_date)

            # Expansion sollte höheren Multiplier haben als Crisis
            if phase == ArmstrongPhase.EXPANSION:
                assert mult >= 0.8, f"Expansion sollte hohen Multiplier haben, got {mult}"


class TestArmstrongCycleInfo:
    """Tests für get_cycle_info Methode."""

    def test_cycle_info_contains_expected_keys(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass get_cycle_info alle erwarteten Keys enthält."""
        info = model_test.get_cycle_info(date(2020, 6, 15))

        expected_keys = [
            "phase",
            "phase_name",
            "cycle_position",
            "days_since_reference",
            "risk_multiplier",
            "next_turning_point",
            "cycle_length_days",
        ]

        for key in expected_keys:
            assert key in info, f"Key '{key}' fehlt in cycle_info"

    def test_cycle_position_range(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass cycle_position im Bereich 0-1 liegt."""
        ref = date(2020, 1, 1)

        for i in range(100):
            test_date = ref + timedelta(days=i)
            info = model_test.get_cycle_info(test_date)

            assert 0.0 <= info["cycle_position"] < 1.0

    def test_next_turning_point_in_future(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass next_turning_point in der Zukunft liegt."""
        test_date = date(2020, 6, 15)
        info = model_test.get_cycle_info(test_date)

        # Konvertiere zu date falls pd.Timestamp
        next_tp = info["next_turning_point"]
        if hasattr(next_tp, "date"):
            next_tp = next_tp.date()

        assert next_tp > test_date


# =============================================================================
# CONVENIENCE FUNCTIONS TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests für Convenience-Funktionen."""

    def test_get_phase_for_date(self) -> None:
        """Prüft get_phase_for_date Funktion."""
        phase = get_phase_for_date(date(2024, 6, 15))

        assert isinstance(phase, ArmstrongPhase)

    def test_get_phase_for_date_custom(self) -> None:
        """Prüft get_phase_for_date mit Custom-Parametern."""
        phase = get_phase_for_date(
            date(2020, 1, 1),
            reference_date=date(2020, 1, 1),
            cycle_length=100,
        )

        assert phase == ArmstrongPhase.POST_CRISIS

    def test_get_risk_multiplier_for_date(self) -> None:
        """Prüft get_risk_multiplier_for_date Funktion."""
        mult = get_risk_multiplier_for_date(date(2024, 6, 15))

        assert isinstance(mult, float)
        assert 0.0 <= mult <= 1.0

    def test_get_risk_multiplier_for_date_custom(self) -> None:
        """Prüft get_risk_multiplier_for_date mit Custom-Parametern."""
        mult = get_risk_multiplier_for_date(
            date(2020, 1, 1),
            reference_date=date(2020, 1, 1),
            cycle_length=100,
        )

        assert isinstance(mult, float)


# =============================================================================
# MODEL REPR TESTS
# =============================================================================


class TestModelRepr:
    """Tests für __repr__ Methode."""

    def test_model_repr_contains_key_info(self, model_test: ArmstrongCycleModel) -> None:
        """Prüft, dass __repr__ wichtige Infos enthält."""
        repr_str = repr(model_test)

        assert "ArmstrongCycleModel" in repr_str
        assert "RESEARCH-ONLY" in repr_str
        assert "100" in repr_str  # cycle_length

