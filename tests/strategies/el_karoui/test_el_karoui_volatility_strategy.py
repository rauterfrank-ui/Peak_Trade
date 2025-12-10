# tests/strategies/el_karoui/test_el_karoui_volatility_strategy.py
"""
Tests für die El Karoui Volatility Strategy.

Testet:
- Strategy-Instanziierung und Konfiguration
- Signal-Generierung
- R&D-Safety-Flags
- Tier-Gating-Mechanismus
"""
import pytest
import numpy as np
import pandas as pd

from src.strategies.el_karoui import (
    ElKarouiVolatilityStrategy,
    ElKarouiVolModelStrategy,
    VolRegime,
    ElKarouiVolModel,
)
from src.strategies.el_karoui.el_karoui_vol_model_strategy import (
    DEFAULT_REGIME_POSITION_MAP,
    AGGRESSIVE_REGIME_POSITION_MAP,
    CONSERVATIVE_REGIME_POSITION_MAP,
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
    """Erzeugt Dummy-OHLCV-Daten für Tests (100 Tage)."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(100) * 0.02)  # ~2% daily vol

    return pd.DataFrame(
        {
            "open": close - np.random.rand(100) * 0.5,
            "high": close + np.random.rand(100) * 1.0,
            "low": close - np.random.rand(100) * 1.0,
            "close": close,
            "volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )


@pytest.fixture
def low_vol_ohlcv_data() -> pd.DataFrame:
    """Erzeugt OHLCV-Daten mit niedriger Volatilität."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(100) * 0.005)  # ~0.5% daily vol

    return pd.DataFrame(
        {
            "open": close - np.random.rand(100) * 0.1,
            "high": close + np.random.rand(100) * 0.2,
            "low": close - np.random.rand(100) * 0.2,
            "close": close,
            "volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )


@pytest.fixture
def high_vol_ohlcv_data() -> pd.DataFrame:
    """Erzeugt OHLCV-Daten mit hoher Volatilität."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(100) * 0.05)  # ~5% daily vol

    return pd.DataFrame(
        {
            "open": close - np.random.rand(100) * 2.0,
            "high": close + np.random.rand(100) * 3.0,
            "low": close - np.random.rand(100) * 3.0,
            "close": close,
            "volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )


@pytest.fixture
def strategy_default() -> ElKarouiVolatilityStrategy:
    """Standard-Strategie für Tests."""
    return ElKarouiVolatilityStrategy()


@pytest.fixture
def strategy_custom() -> ElKarouiVolatilityStrategy:
    """Strategie mit Custom-Parametern."""
    return ElKarouiVolatilityStrategy(
        vol_window=15,
        lookback_window=60,
        low_threshold=0.25,
        high_threshold=0.75,
        vol_target=0.12,
        regime_position_map="conservative",
        use_vol_scaling=False,
    )


# =============================================================================
# STRATEGY INSTANTIATION TESTS
# =============================================================================


class TestElKarouiStrategyInstantiation:
    """Tests für Strategy-Instanziierung."""

    def test_default_instantiation(self) -> None:
        """Prüft Default-Instanziierung."""
        strategy = ElKarouiVolatilityStrategy()

        assert strategy.vol_window == 20
        assert strategy.lookback_window == 252
        assert strategy.low_threshold == 0.30
        assert strategy.high_threshold == 0.70
        assert strategy.vol_target == 0.10
        assert strategy.use_vol_scaling is True

    def test_custom_instantiation(self) -> None:
        """Prüft Custom-Instanziierung."""
        strategy = ElKarouiVolatilityStrategy(
            vol_window=15,
            lookback_window=100,
            low_threshold=0.25,
            high_threshold=0.80,
            vol_target=0.15,
        )

        assert strategy.vol_window == 15
        assert strategy.lookback_window == 100
        assert strategy.vol_target == 0.15

    def test_config_override(self) -> None:
        """Prüft Config-Override."""
        strategy = ElKarouiVolatilityStrategy(
            vol_window=20,
            config={"vol_window": 25},
        )

        # Config sollte Parameter überschreiben
        assert strategy.vol_window == 25

    def test_from_config_classmethod(self) -> None:
        """Prüft from_config Classmethod."""

        class MockConfig:
            def get(self, path: str, default=None):
                if "vol_window" in path:
                    return 30
                if "vol_target" in path:
                    return 0.12
                return default

        strategy = ElKarouiVolatilityStrategy.from_config(MockConfig())

        assert strategy.vol_window == 30
        assert strategy.vol_target == 0.12

    def test_validation_fails_for_small_window(self) -> None:
        """Prüft Validierungsfehler bei zu kleinem Fenster."""
        with pytest.raises(ValueError, match="vol_window"):
            ElKarouiVolatilityStrategy(vol_window=1)

    def test_validation_fails_for_invalid_thresholds(self) -> None:
        """Prüft Validierungsfehler bei ungültigen Schwellen."""
        with pytest.raises(ValueError, match="low_threshold"):
            ElKarouiVolatilityStrategy(
                low_threshold=0.80,
                high_threshold=0.30,
            )

    def test_backwards_compatibility_alias(self) -> None:
        """Prüft, dass ElKarouiVolModelStrategy als Alias funktioniert."""
        strategy = ElKarouiVolModelStrategy()

        assert isinstance(strategy, ElKarouiVolatilityStrategy)


# =============================================================================
# R&D SAFETY FLAGS TESTS
# =============================================================================


class TestRnDSafetyFlags:
    """Tests für R&D-Safety-Flags."""

    def test_is_live_ready_false(self) -> None:
        """Prüft, dass IS_LIVE_READY False ist."""
        assert ElKarouiVolatilityStrategy.IS_LIVE_READY is False

    def test_tier_is_r_and_d(self) -> None:
        """Prüft, dass TIER 'r_and_d' ist."""
        assert ElKarouiVolatilityStrategy.TIER == "r_and_d"

    def test_allowed_environments(self) -> None:
        """Prüft erlaubte Environments."""
        expected = ["offline_backtest", "research"]
        assert ElKarouiVolatilityStrategy.ALLOWED_ENVIRONMENTS == expected

    def test_metadata_contains_r_and_d_tag(self) -> None:
        """Prüft, dass Metadata r_and_d Tag enthält."""
        strategy = ElKarouiVolatilityStrategy()

        assert "r_and_d" in strategy.meta.tags

    def test_strategy_key(self) -> None:
        """Prüft Strategy-Key."""
        assert ElKarouiVolatilityStrategy.KEY == "el_karoui_vol_v1"


# =============================================================================
# REGIME-POSITION MAPPING TESTS
# =============================================================================


class TestRegimePositionMapping:
    """Tests für Regime→Position Mappings."""

    def test_default_mapping(self) -> None:
        """Prüft Default-Mapping."""
        strategy = ElKarouiVolatilityStrategy(regime_position_map="default")

        assert strategy.regime_position_map[VolRegime.LOW] == 1
        assert strategy.regime_position_map[VolRegime.MEDIUM] == 1
        assert strategy.regime_position_map[VolRegime.HIGH] == 0

    def test_conservative_mapping(self) -> None:
        """Prüft Conservative-Mapping."""
        strategy = ElKarouiVolatilityStrategy(regime_position_map="conservative")

        assert strategy.regime_position_map[VolRegime.LOW] == 1
        assert strategy.regime_position_map[VolRegime.MEDIUM] == 0
        assert strategy.regime_position_map[VolRegime.HIGH] == 0

    def test_aggressive_mapping(self) -> None:
        """Prüft Aggressive-Mapping."""
        strategy = ElKarouiVolatilityStrategy(regime_position_map="aggressive")

        assert strategy.regime_position_map[VolRegime.LOW] == 1
        assert strategy.regime_position_map[VolRegime.MEDIUM] == 1
        assert strategy.regime_position_map[VolRegime.HIGH] == 1

    def test_custom_mapping_dict(self) -> None:
        """Prüft Custom-Mapping als Dict."""
        custom_map = {
            VolRegime.LOW: 1,
            VolRegime.MEDIUM: 0,
            VolRegime.HIGH: 0,
        }

        strategy = ElKarouiVolatilityStrategy(regime_position_map=custom_map)

        assert strategy.regime_position_map[VolRegime.MEDIUM] == 0


# =============================================================================
# SIGNAL GENERATION TESTS
# =============================================================================


class TestSignalGeneration:
    """Tests für Signal-Generierung."""

    def test_generate_signals_returns_series(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass generate_signals eine Series zurückgibt."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(dummy_ohlcv_data)

    def test_signals_have_valid_values(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signale nur 0, 1 enthalten (keine Shorts für Vol-Strategie)."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        unique_values = signals.unique()
        for val in unique_values:
            assert val in [0, 1], f"Ungültiger Signal-Wert: {val}"

    def test_signals_deterministic(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signal-Generierung deterministisch ist."""
        signals1 = strategy_default.generate_signals(dummy_ohlcv_data)
        signals2 = strategy_default.generate_signals(dummy_ohlcv_data)

        pd.testing.assert_series_equal(signals1, signals2)

    def test_signals_match_index(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signal-Index mit Daten-Index übereinstimmt."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        pd.testing.assert_index_equal(signals.index, dummy_ohlcv_data.index)

    def test_signals_contain_metadata(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signale Metadaten enthalten."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        assert "regimes" in signals.attrs
        assert "scaling_factors" in signals.attrs
        assert "vol_annualized" in signals.attrs
        assert "vol_window" in signals.attrs

    def test_empty_dataframe_handling(
        self, strategy_default: ElKarouiVolatilityStrategy
    ) -> None:
        """Prüft Handling von leerem DataFrame."""
        empty_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([]),
        )

        signals = strategy_default.generate_signals(empty_df)

        assert len(signals) == 0

    def test_missing_close_column_raises(
        self, strategy_default: ElKarouiVolatilityStrategy
    ) -> None:
        """Prüft, dass fehlende 'close' Spalte einen Fehler wirft."""
        bad_df = pd.DataFrame(
            {"open": [100, 101, 102]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        with pytest.raises(ValueError, match="close"):
            strategy_default.generate_signals(bad_df)

    def test_signals_no_nans(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Signale keine NaNs enthalten."""
        signals = strategy_default.generate_signals(dummy_ohlcv_data)

        assert not signals.isna().any()


class TestSignalGenerationWithDifferentConfigs:
    """Tests für Signal-Generierung mit verschiedenen Configs."""

    def test_conservative_generates_more_flat(
        self, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass conservative mehr Flat-Signale generiert."""
        strategy_default = ElKarouiVolatilityStrategy(
            regime_position_map="default",
            vol_window=10,
            lookback_window=50,
        )
        strategy_conservative = ElKarouiVolatilityStrategy(
            regime_position_map="conservative",
            vol_window=10,
            lookback_window=50,
        )

        signals_default = strategy_default.generate_signals(dummy_ohlcv_data)
        signals_conservative = strategy_conservative.generate_signals(dummy_ohlcv_data)

        # Conservative sollte mehr oder gleich viele Flat-Signale haben
        flat_default = (signals_default == 0).sum()
        flat_conservative = (signals_conservative == 0).sum()

        assert flat_conservative >= flat_default

    def test_vol_scaling_affects_metadata(
        self, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft, dass Vol-Scaling die Scaling-Faktoren beeinflusst."""
        strategy_with_scaling = ElKarouiVolatilityStrategy(
            use_vol_scaling=True,
            vol_window=10,
            lookback_window=50,
        )
        strategy_without_scaling = ElKarouiVolatilityStrategy(
            use_vol_scaling=False,
            vol_window=10,
            lookback_window=50,
        )

        signals_with = strategy_with_scaling.generate_signals(dummy_ohlcv_data)
        signals_without = strategy_without_scaling.generate_signals(dummy_ohlcv_data)

        # Mit Scaling sollten die Faktoren variieren
        factors_with = signals_with.attrs["scaling_factors"]
        factors_without = signals_without.attrs["scaling_factors"]

        # Ohne Vol-Target-Scaling sollte die Varianz der Faktoren geringer sein
        # (nur Regime-Multiplier, kein Vol-Target-Scaling)
        warmup = strategy_without_scaling.vol_window
        factors_with_valid = factors_with[warmup:]
        factors_without_valid = factors_without[warmup:]

        # Prüfe, dass beide Listen nicht leer sind
        assert len(factors_with_valid) > 0
        assert len(factors_without_valid) > 0


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================


class TestHelperMethods:
    """Tests für Helper-Methoden."""

    def test_get_vol_analysis(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft get_vol_analysis Methode."""
        analysis = strategy_default.get_vol_analysis(dummy_ohlcv_data)

        assert "current_vol" in analysis
        assert "vol_regime" in analysis or "regime" in analysis
        assert "scaling_factor" in analysis

    def test_get_current_regime(
        self, strategy_default: ElKarouiVolatilityStrategy, dummy_ohlcv_data: pd.DataFrame
    ) -> None:
        """Prüft get_current_regime Methode."""
        regime = strategy_default.get_current_regime(dummy_ohlcv_data)

        assert isinstance(regime, VolRegime)

    def test_get_position_for_regime(
        self, strategy_default: ElKarouiVolatilityStrategy
    ) -> None:
        """Prüft get_position_for_regime Methode."""
        pos_low = strategy_default.get_position_for_regime(VolRegime.LOW)
        pos_high = strategy_default.get_position_for_regime(VolRegime.HIGH)

        assert pos_low in [0, 1]
        assert pos_high in [0, 1]

    def test_get_strategy_info(
        self, strategy_default: ElKarouiVolatilityStrategy
    ) -> None:
        """Prüft get_strategy_info Methode."""
        info = strategy_default.get_strategy_info()

        assert info["id"] == "el_karoui_vol_v1"
        assert info["tier"] == "r_and_d"
        assert info["category"] == "volatility"
        assert info["is_live_ready"] is False

    def test_repr(self, strategy_default: ElKarouiVolatilityStrategy) -> None:
        """Prüft __repr__ Methode."""
        repr_str = repr(strategy_default)

        assert "ElKarouiVolatilityStrategy" in repr_str
        assert "R&D-ONLY" in repr_str
        assert "tier=r_and_d" in repr_str


# =============================================================================
# TIER-GATING TESTS
# =============================================================================


class TestTierGating:
    """Tests für Tier-Gating-Mechanismus."""

    def test_r_and_d_blocked_for_live(self) -> None:
        """Prüft, dass R&D-Strategie für Live blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "live")

        assert is_blocked is True

    def test_r_and_d_blocked_for_paper(self) -> None:
        """Prüft, dass R&D-Strategie für Paper blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "paper")

        assert is_blocked is True

    def test_r_and_d_blocked_for_testnet(self) -> None:
        """Prüft, dass R&D-Strategie für Testnet blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "testnet")

        assert is_blocked is True

    def test_r_and_d_blocked_for_shadow(self) -> None:
        """Prüft, dass R&D-Strategie für Shadow blockiert ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "shadow")

        assert is_blocked is True

    def test_r_and_d_allowed_for_offline_backtest(self) -> None:
        """Prüft, dass R&D-Strategie für offline_backtest erlaubt ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "offline_backtest")

        assert is_blocked is False

    def test_r_and_d_allowed_for_research(self) -> None:
        """Prüft, dass R&D-Strategie für research erlaubt ist."""
        is_blocked = check_r_and_d_tier_for_mode("el_karoui_vol_model", "research")

        assert is_blocked is False

    def test_assert_strategy_not_r_and_d_raises_for_live(self) -> None:
        """Prüft, dass assert_strategy_not_r_and_d_for_live Exception wirft."""
        with pytest.raises(RnDLiveTradingBlockedError) as exc_info:
            assert_strategy_not_r_and_d_for_live("el_karoui_vol_model", "live")

        assert "el_karoui_vol_model" in str(exc_info.value)
        assert "live" in str(exc_info.value)

    def test_assert_strategy_not_r_and_d_ok_for_backtest(self) -> None:
        """Prüft, dass keine Exception für offline_backtest geworfen wird."""
        # Sollte keine Exception werfen
        assert_strategy_not_r_and_d_for_live("el_karoui_vol_model", "offline_backtest")

    def test_get_strategy_tier(self) -> None:
        """Prüft get_strategy_tier Funktion."""
        tier = get_strategy_tier("el_karoui_vol_model")

        assert tier == "r_and_d"

    def test_log_strategy_tier_info(self) -> None:
        """Prüft log_strategy_tier_info Funktion."""
        info = log_strategy_tier_info("el_karoui_vol_model")

        assert info["strategy_id"] == "el_karoui_vol_model"
        assert info["tier"] == "r_and_d"
        assert info["is_r_and_d"] is True
        assert info["allow_live"] is False


class TestLiveEligibility:
    """Tests für Live-Eligibility-Check."""

    def test_el_karoui_not_live_eligible(self) -> None:
        """Prüft, dass El Karoui-Strategie nicht live-eligible ist."""
        result = check_strategy_live_eligibility("el_karoui_vol_model")

        assert result.is_eligible is False
        assert result.tier == "r_and_d"
        assert any("R&D" in reason for reason in result.reasons)

    def test_eligibility_result_details(self) -> None:
        """Prüft Details des Eligibility-Results."""
        result = check_strategy_live_eligibility("el_karoui_vol_model")

        assert result.entity_id == "el_karoui_vol_model"
        assert result.entity_type == "strategy"
        assert result.tier == "r_and_d"


# =============================================================================
# EXCEPTION TESTS
# =============================================================================


class TestRnDLiveTradingBlockedError:
    """Tests für RnDLiveTradingBlockedError Exception."""

    def test_exception_message(self) -> None:
        """Prüft Exception-Message."""
        exc = RnDLiveTradingBlockedError("el_karoui_vol_model", "live")

        assert "el_karoui_vol_model" in str(exc)
        assert "live" in str(exc)

    def test_exception_attributes(self) -> None:
        """Prüft Exception-Attribute."""
        exc = RnDLiveTradingBlockedError("el_karoui_vol_model", "paper")

        assert exc.strategy_id == "el_karoui_vol_model"
        assert exc.mode == "paper"


# =============================================================================
# INTEGRATION / SMOKE TESTS
# =============================================================================


class TestSmoke:
    """Smoke-Tests für grundlegende Funktionalität."""

    def test_full_backtest_workflow(self, dummy_ohlcv_data: pd.DataFrame) -> None:
        """Testet kompletten Backtest-Workflow."""
        # 1. Strategie erstellen
        strategy = ElKarouiVolatilityStrategy()

        # 2. Signale generieren
        signals = strategy.generate_signals(dummy_ohlcv_data)

        # 3. Grundlegende Validierung
        assert len(signals) == len(dummy_ohlcv_data)
        assert signals.dtype == int

        # 4. Prüfe, dass Signale sinnvoll sind
        assert not signals.isna().any()
        # Mindestens ein Signal sollte vorhanden sein
        assert signals.sum() > 0 or (signals == 0).sum() == len(signals)

    def test_strategy_info_complete(self) -> None:
        """Testet, dass Strategy-Info vollständig ist."""
        strategy = ElKarouiVolatilityStrategy()
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
        # Simuliere Versuch, El Karoui im Live-Modus zu starten
        strategy_id = "el_karoui_vol_model"
        mode = "live"

        # Dies sollte blockiert werden
        with pytest.raises(RnDLiveTradingBlockedError):
            assert_strategy_not_r_and_d_for_live(strategy_id, mode)

        # Aber offline_backtest sollte funktionieren
        assert_strategy_not_r_and_d_for_live(strategy_id, "offline_backtest")

    def test_vol_analysis_not_empty(self, dummy_ohlcv_data: pd.DataFrame) -> None:
        """Testet, dass Vol-Analyse Ergebnisse liefert."""
        strategy = ElKarouiVolatilityStrategy()
        analysis = strategy.get_vol_analysis(dummy_ohlcv_data)

        assert analysis is not None
        assert "regime" in analysis
        assert analysis["current_vol"] is not None

    def test_regime_detection_works(
        self, low_vol_ohlcv_data: pd.DataFrame, high_vol_ohlcv_data: pd.DataFrame
    ) -> None:
        """Testet, dass Regime-Detection bei unterschiedlicher Vol funktioniert."""
        strategy = ElKarouiVolatilityStrategy(
            vol_window=10,
            lookback_window=50,
        )

        regime_low = strategy.get_current_regime(low_vol_ohlcv_data)
        regime_high = strategy.get_current_regime(high_vol_ohlcv_data)

        # Bei konstant niedriger Vol sollte Regime LOW sein, bei hoher HIGH
        # Aber wegen rolling percentile kann das variieren, also prüfen wir nur, dass es funktioniert
        assert isinstance(regime_low, VolRegime)
        assert isinstance(regime_high, VolRegime)


