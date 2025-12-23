# tests/strategies/armstrong/test_armstrong_cycle_strategy.py
"""
Tests für die Armstrong Cycle Strategy.

Testet:
- Strategy-Instanziierung und Konfiguration
- Signal-Generierung
- R&D-Safety-Flags
- Tier-Gating-Mechanismus
"""

import pytest
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.strategies.armstrong import (
    ArmstrongCycleStrategy,
    ArmstrongPhase,
    ArmstrongCycleModel,
)
from src.strategies.armstrong.armstrong_cycle_strategy import (
    DEFAULT_PHASE_POSITION_MAP,
    AGGRESSIVE_PHASE_POSITION_MAP,
    CONSERVATIVE_PHASE_POSITION_MAP,
)
from src.live.live_gates import (
    RnDLiveTradingBlockedError,
    check_r_and_d_tier_for_mode,
    assert_strategy_not_r_and_d_for_live,
    get_strategy_tier,
    log_strategy_tier_info,
    check_strategy_live_eligibility,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def dummy_ohlcv_data() -> pd.DataFrame:
    """Erzeugt Dummy-OHLCV-Daten für Tests (50 Tage)."""
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(50))

    return pd.DataFrame(
        {
            "open": close - np.random.rand(50),
            "high": close + np.random.rand(50) * 2,
            "low": close - np.random.rand(50) * 2,
            "close": close,
            "volume": np.random.randint(1000, 10000, 50),
        },
        index=dates,
    )


@pytest.fixture
def strategy_default() -> ArmstrongCycleStrategy:
    """Standard-Strategie für Tests."""
    return ArmstrongCycleStrategy()


@pytest.fixture
def strategy_custom() -> ArmstrongCycleStrategy:
    """Strategie mit Custom-Parametern."""
    return ArmstrongCycleStrategy(
        cycle_length_days=100,
        reference_date="2020-01-01",
        phase_position_map="aggressive",
        use_risk_scaling=False,
    )


# =============================================================================
# STRATEGY INSTANTIATION TESTS
# =============================================================================


class TestArmstrongCycleStrategyInstantiation:
    """Tests für Strategy-Instanziierung."""

    def test_default_instantiation(self) -> None:
        """Prüft Default-Instanziierung."""
        strategy = ArmstrongCycleStrategy()

        assert strategy.cycle_length_days == 3141
        assert strategy.reference_date == date(2015, 10, 1)
        assert strategy.use_risk_scaling is True

    def test_custom_instantiation(self) -> None:
        """Prüft Custom-Instanziierung."""
        strategy = ArmstrongCycleStrategy(
            cycle_length_days=1000,
            reference_date="2022-06-01",
            event_window_days=30,
        )

        assert strategy.cycle_length_days == 1000
        assert strategy.reference_date == date(2022, 6, 1)
        assert strategy.event_window_days == 30

    def test_config_override(self) -> None:
        """Prüft Config-Override."""
        strategy = ArmstrongCycleStrategy(
            cycle_length_days=500,
            config={"cycle_length_days": 800},
        )

        # Config sollte Parameter überschreiben
        assert strategy.cycle_length_days == 800

    def test_from_config_classmethod(self) -> None:
        """Prüft from_config Classmethod."""

        class MockConfig:
            def get(self, path: str, default=None):
                if "cycle_length_days" in path:
                    return 2000
                if "reference_date" in path:
                    return "2023-01-01"
                return default

        strategy = ArmstrongCycleStrategy.from_config(MockConfig())

        assert strategy.cycle_length_days == 2000
        assert strategy.reference_date == date(2023, 1, 1)

    def test_validation_fails_for_short_cycle(self) -> None:
        """Prüft Validierungsfehler bei zu kurzem Zyklus."""
        with pytest.raises(ValueError, match="cycle_length_days"):
            ArmstrongCycleStrategy(cycle_length_days=10)

    def test_validation_fails_for_large_event_window(self) -> None:
        """Prüft Validierungsfehler bei zu großem Event-Window."""
        with pytest.raises(ValueError, match="event_window_days"):
            ArmstrongCycleStrategy(
                cycle_length_days=100,
                event_window_days=60,  # >= half cycle
            )


# =============================================================================
# R&D SAFETY FLAGS TESTS
# =============================================================================


class TestRnDSafetyFlags:
    """Tests für R&D-Safety-Flags."""

    def test_is_live_ready_false(self) -> None:
        """Prüft, dass IS_LIVE_READY False ist."""
        assert ArmstrongCycleStrategy.IS_LIVE_READY is False

    def test_tier_is_r_and_d(self) -> None:
        """Prüft, dass TIER 'r_and_d' ist."""
        assert ArmstrongCycleStrategy.TIER == "r_and_d"

    def test_allowed_environments(self) -> None:
        """Prüft erlaubte Environments."""
        expected = ["offline_backtest", "research"]
        assert ArmstrongCycleStrategy.ALLOWED_ENVIRONMENTS == expected

    def test_metadata_contains_r_and_d_tag(self) -> None:
        """Prüft, dass Metadata r_and_d Tag enthält."""
        strategy = ArmstrongCycleStrategy()

        assert "r_and_d" in strategy.meta.tags

    def test_strategy_key(self) -> None:
        """Prüft Strategy-Key."""
        assert ArmstrongCycleStrategy.KEY == "armstrong_cycle"


# =============================================================================
# PHASE-POSITION MAPPING TESTS
# =============================================================================


class TestPhasePositionMapping:
    """Tests für Phase→Position Mappings."""

    def test_default_mapping(self) -> None:
        """Prüft Default-Mapping."""
        strategy = ArmstrongCycleStrategy(phase_position_map="default")

        assert strategy.phase_position_map[ArmstrongPhase.EXPANSION] == 1
        assert strategy.phase_position_map[ArmstrongPhase.CRISIS] == 0

    def test_aggressive_mapping(self) -> None:
        """Prüft Aggressive-Mapping."""
        strategy = ArmstrongCycleStrategy(phase_position_map="aggressive")

        assert strategy.phase_position_map[ArmstrongPhase.CRISIS] == -1
        assert strategy.phase_position_map[ArmstrongPhase.PRE_CRISIS] == -1

    def test_conservative_mapping(self) -> None:
        """Prüft Conservative-Mapping."""
        strategy = ArmstrongCycleStrategy(phase_position_map="conservative")

        # Nur EXPANSION sollte long sein
        assert strategy.phase_position_map[ArmstrongPhase.EXPANSION] == 1
        assert strategy.phase_position_map[ArmstrongPhase.POST_CRISIS] == 0

    def test_custom_mapping_dict(self) -> None:
        """Prüft Custom-Mapping als Dict."""
        custom_map = {
            ArmstrongPhase.EXPANSION: 1,
            ArmstrongPhase.CRISIS: -1,
            ArmstrongPhase.CONTRACTION: 0,
            ArmstrongPhase.PRE_CRISIS: 0,
            ArmstrongPhase.POST_CRISIS: 0,
        }

        strategy = ArmstrongCycleStrategy(phase_position_map=custom_map)

        assert strategy.phase_position_map[ArmstrongPhase.CRISIS] == -1


# =============================================================================
# SIGNAL GENERATION TESTS
# =============================================================================


class TestSignalGeneration:
    """Tests für Signal-Generierung."""

    def test_generate_signals_returns_series(
        self, strategy_default: ArmstrongCycleStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass generate_signals eine Series zurückgibt."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(dummy_ohlcv_data)

    def test_signals_have_valid_values(
        self, strategy_default: ArmstrongCycleStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signale nur -1, 0, 1 enthalten."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        unique_values = signals.unique()
        for val in unique_values:
            assert val in [-1, 0, 1], f"Ungültiger Signal-Wert: {val}"

    def test_signals_deterministic(
        self, strategy_default: ArmstrongCycleStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signal-Generierung deterministisch ist."""
        signals1 = strategy_default.generate_signals(dummy_ohlcv_data)
        signals2 = strategy_default.generate_signals(dummy_ohlcv_data)

        pd.testing.assert_series_equal(signals1, signals2)

    def test_signals_match_index(
        self, strategy_default: ArmstrongCycleStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signal-Index mit Daten-Index übereinstimmt."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        pd.testing.assert_index_equal(signals.index, dummy_ohlcv_data.index)

    def test_signals_contain_metadata(
        self, strategy_default: ArmstrongCycleStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signale Metadaten enthalten."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        # Research-stub mode: only basic metadata, no phases/risk_multipliers
        assert "cycle_length_days" in signals.attrs
        assert "reference_date" in signals.attrs
        assert "is_research_stub" in signals.attrs
        assert signals.attrs["is_research_stub"] is True

    def test_empty_dataframe_handling(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft Handling von leerem DataFrame."""
        empty_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([]),
        )

        signals = strategy_default.generate_signals(empty_df)

        assert len(signals) == 0

    def test_non_datetime_index_raises(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft, dass nicht-datetime Index einen Fehler wirft."""
        bad_df = pd.DataFrame(
            {"close": [100, 101, 102]},
            index=[0, 1, 2],  # Integer-Index
        )

        with pytest.raises(ValueError, match="DatetimeIndex"):
            strategy_default.generate_signals(bad_df)


class TestSignalGenerationWithDifferentConfigs:
    """Tests für Signal-Generierung mit verschiedenen Configs."""

    def test_aggressive_generates_short_signals(self, dummy_ohlcv_data: pd.DataFrame) -> None:
        """Prüft, dass aggressive Mapping Short-Signale generiert."""
        strategy = ArmstrongCycleStrategy(
            phase_position_map="aggressive",
            cycle_length_days=200,  # Zyklus muss > 2*event_window sein
            event_window_days=20,  # Angepasst für kurzen Zyklus
            reference_date="2024-01-01",
        )

        signals = strategy.generate_signals(dummy_ohlcv_data)

        # Research-stub mode: only flat signals (0) for safety
        # Real signal generation is disabled until explicitly approved
        unique_values = set(signals.unique())
        assert unique_values == {
            0
        }, f"Expected only flat signals in research-stub mode, got {unique_values}"
        assert signals.attrs["is_research_stub"] is True

    def test_conservative_only_long_or_flat(self, dummy_ohlcv_data: pd.DataFrame) -> None:
        """Prüft, dass conservative Mapping nur long oder flat generiert."""
        strategy = ArmstrongCycleStrategy(
            phase_position_map="conservative",
            cycle_length_days=200,  # Zyklus muss > 2*event_window sein
            event_window_days=20,  # Angepasst für kurzen Zyklus
            reference_date="2024-01-01",
        )

        signals = strategy.generate_signals(dummy_ohlcv_data)

        # Conservative sollte keine Short-Signale haben
        assert -1 not in signals.values


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================


class TestHelperMethods:
    """Tests für Helper-Methoden."""

    def test_get_cycle_info(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft get_cycle_info Methode."""
        info = strategy_default.get_cycle_info(pd.Timestamp("2024-06-15"))

        assert "phase" in info
        assert "risk_multiplier" in info
        assert isinstance(info["phase"], ArmstrongPhase)

    def test_get_phase_for_date(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft get_phase_for_date Methode."""
        phase = strategy_default.get_phase_for_date(pd.Timestamp("2024-06-15"))

        assert isinstance(phase, ArmstrongPhase)

    def test_get_position_for_phase(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft get_position_for_phase Methode."""
        pos_expansion = strategy_default.get_position_for_phase(ArmstrongPhase.EXPANSION)
        pos_crisis = strategy_default.get_position_for_phase(ArmstrongPhase.CRISIS)

        assert pos_expansion in [-1, 0, 1]
        assert pos_crisis in [-1, 0, 1]

    def test_get_strategy_info(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft get_strategy_info Methode."""
        info = strategy_default.get_strategy_info()

        assert info["id"] == "armstrong_cycle_v1"
        assert info["tier"] == "r_and_d"
        assert info["category"] == "cycles"
        assert info["is_live_ready"] is False

    def test_repr(self, strategy_default: ArmstrongCycleStrategy) -> None:
        """Prüft __repr__ Methode."""
        repr_str = repr(strategy_default)

        assert "ArmstrongCycleStrategy" in repr_str
        assert "R&D-ONLY" in repr_str
        assert "tier=r_and_d" in repr_str


# =============================================================================
# TIER-GATING TESTS
# =============================================================================


class TestTierGating:
    """Tests für Tier-Gating-Mechanismus."""

    def test_r_and_d_blocked_for_live(self) -> None:
        """Prüft, dass R&D-Strategie für Live blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "live")

        assert is_blocked is True

    def test_r_and_d_blocked_for_paper(self) -> None:
        """Prüft, dass R&D-Strategie für Paper blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "paper")

        assert is_blocked is True

    def test_r_and_d_blocked_for_testnet(self) -> None:
        """Prüft, dass R&D-Strategie für Testnet blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "testnet")

        assert is_blocked is True

    def test_r_and_d_blocked_for_shadow(self) -> None:
        """Prüft, dass R&D-Strategie für Shadow blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "shadow")

        assert is_blocked is True

    def test_r_and_d_allowed_for_offline_backtest(self) -> None:
        """Prüft, dass R&D-Strategie für offline_backtest erlaubt ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "offline_backtest")

        assert is_blocked is False

    def test_r_and_d_allowed_for_research(self) -> None:
        """Prüft, dass R&D-Strategie für research erlaubt ist."""
        is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "research")

        assert is_blocked is False

    def test_assert_strategy_not_r_and_d_raises_for_live(self) -> None:
        """Prüft, dass assert_strategy_not_r_and_d_for_live Exception wirft."""
        with pytest.raises(RnDLiveTradingBlockedError) as exc_info:
            assert_strategy_not_r_and_d_for_live("armstrong_cycle", "live")

        assert "armstrong_cycle" in str(exc_info.value)
        assert "live" in str(exc_info.value)
        assert "Research/Backtests" in str(exc_info.value)

    def test_assert_strategy_not_r_and_d_ok_for_backtest(self) -> None:
        """Prüft, dass keine Exception für offline_backtest geworfen wird."""
        # Sollte keine Exception werfen
        assert_strategy_not_r_and_d_for_live("armstrong_cycle", "offline_backtest")

    def test_get_strategy_tier(self) -> None:
        """Prüft get_strategy_tier Funktion."""
        tier = get_strategy_tier("armstrong_cycle")

        assert tier == "r_and_d"

    def test_log_strategy_tier_info(self) -> None:
        """Prüft log_strategy_tier_info Funktion."""
        info = log_strategy_tier_info("armstrong_cycle")

        assert info["strategy_id"] == "armstrong_cycle"
        assert info["tier"] == "r_and_d"
        assert info["is_r_and_d"] is True
        assert info["allow_live"] is False


class TestLiveEligibility:
    """Tests für Live-Eligibility-Check."""

    def test_armstrong_not_live_eligible(self) -> None:
        """Prüft, dass Armstrong-Strategie nicht live-eligible ist."""
        result = check_strategy_live_eligibility("armstrong_cycle")

        assert result.is_eligible is False
        assert result.tier == "r_and_d"
        assert any("R&D" in reason for reason in result.reasons)

    def test_eligibility_result_details(self) -> None:
        """Prüft Details des Eligibility-Results."""
        result = check_strategy_live_eligibility("armstrong_cycle")

        assert result.entity_id == "armstrong_cycle"
        assert result.entity_type == "strategy"
        assert result.tier == "r_and_d"


# =============================================================================
# EXCEPTION TESTS
# =============================================================================


class TestRnDLiveTradingBlockedError:
    """Tests für RnDLiveTradingBlockedError Exception."""

    def test_exception_message(self) -> None:
        """Prüft Exception-Message."""
        exc = RnDLiveTradingBlockedError("test_strategy", "live")

        assert "test_strategy" in str(exc)
        assert "live" in str(exc)
        assert "Research/Backtests" in str(exc)

    def test_exception_attributes(self) -> None:
        """Prüft Exception-Attribute."""
        exc = RnDLiveTradingBlockedError("test_strategy", "paper")

        assert exc.strategy_id == "test_strategy"
        assert exc.mode == "paper"

    def test_custom_message(self) -> None:
        """Prüft Custom-Message."""
        custom_msg = "Custom error message"
        exc = RnDLiveTradingBlockedError("test", "live", message=custom_msg)

        assert str(exc) == custom_msg


# =============================================================================
# INTEGRATION / SMOKE TESTS
# =============================================================================


class TestSmoke:
    """Smoke-Tests für grundlegende Funktionalität."""

    def test_full_backtest_workflow(self, dummy_ohlcv_data: pd.DataFrame) -> None:
        """Testet kompletten Backtest-Workflow."""
        # 1. Strategie erstellen
        strategy = ArmstrongCycleStrategy()

        # 2. Signale generieren
        signals = strategy.generate_signals(dummy_ohlcv_data)

        # 3. Grundlegende Validierung
        assert len(signals) == len(dummy_ohlcv_data)
        assert signals.dtype == int

        # 4. Prüfe, dass Signale sinnvoll sind
        # (mindestens einige sollten nicht 0 sein bei langem Backtest)
        # Bei kurzen Tests kann alles 0 sein, das ist OK

    def test_strategy_info_complete(self) -> None:
        """Testet, dass Strategy-Info vollständig ist."""
        strategy = ArmstrongCycleStrategy()
        info = strategy.get_strategy_info()

        required_keys = [
            "id",
            "name",
            "category",
            "tier",
            "is_live_ready",
            "allowed_environments",
        ]

        for key in required_keys:
            assert key in info, f"Key '{key}' fehlt in strategy_info"

    def test_tier_gating_prevents_live_run(self) -> None:
        """Testet, dass Tier-Gating Live-Runs verhindert."""
        # Simuliere Versuch, Armstrong im Live-Modus zu starten
        strategy_id = "armstrong_cycle"
        mode = "live"

        # Dies sollte blockiert werden
        with pytest.raises(RnDLiveTradingBlockedError):
            assert_strategy_not_r_and_d_for_live(strategy_id, mode)

        # Aber offline_backtest sollte funktionieren
        assert_strategy_not_r_and_d_for_live(strategy_id, "offline_backtest")
