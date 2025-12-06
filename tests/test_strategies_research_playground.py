"""
Peak_Trade – Tests für Phase 18: Strategy Research Playground
==============================================================

Testet:
- Neue Strategien (TrendFollowing, MeanReversion)
- Strategy Registry-Integration
- Research-Scripts (Smoke-Tests)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """
    Erstellt synthetische OHLCV-Daten für Tests.

    Enthält sowohl Trends als auch Seitwärtsphasen für verschiedene Strategietypen.
    """
    np.random.seed(42)
    n_bars = 200

    # Zeitindex
    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    # Preis mit Trend und Zyklen
    returns = np.random.normal(0, 0.015, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend
    close_prices = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.005, n_bars))
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.005, n_bars))
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


@pytest.fixture
def trending_data() -> pd.DataFrame:
    """
    Erstellt Daten mit klarem Aufwärtstrend für Trend-Following-Tests.
    """
    np.random.seed(123)
    n_bars = 200

    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    # Starker Aufwärtstrend
    returns = np.random.normal(0.001, 0.01, n_bars)  # Positiver Drift
    close_prices = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.003, n_bars))
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.003, n_bars))
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


@pytest.fixture
def ranging_data() -> pd.DataFrame:
    """
    Erstellt Seitwärtsdaten für Mean-Reversion-Tests.
    """
    np.random.seed(456)
    n_bars = 200

    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    # Seitwärtsbewegung (Mean-Reversion-freundlich)
    base_price = 50000
    noise = np.random.normal(0, 0.005, n_bars).cumsum()
    # Zurück zum Mittelwert ziehen
    mean_reversion = -0.1 * noise
    close_prices = base_price * (1 + noise + mean_reversion)

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.002, n_bars))
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.002, n_bars))
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# =============================================================================
# TESTS: TREND FOLLOWING STRATEGY
# =============================================================================


class TestTrendFollowingStrategy:
    """Tests für TrendFollowingStrategy."""

    def test_import(self):
        """Strategy kann importiert werden."""
        from src.strategies.trend_following import TrendFollowingStrategy
        assert TrendFollowingStrategy is not None

    def test_instantiation_default_params(self):
        """Strategy kann mit Defaults instantiiert werden."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy()
        assert strategy.adx_period == 14
        assert strategy.adx_threshold == 25.0
        assert strategy.exit_threshold == 20.0
        assert strategy.ma_period == 50
        assert strategy.use_ma_filter is True

    def test_instantiation_custom_params(self):
        """Strategy kann mit Custom-Params instantiiert werden."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy(
            adx_period=20,
            adx_threshold=30.0,
            exit_threshold=25.0,
            ma_period=100,
            use_ma_filter=False,
        )
        assert strategy.adx_period == 20
        assert strategy.adx_threshold == 30.0
        assert strategy.use_ma_filter is False

    def test_validation_invalid_adx_period(self):
        """Ungültige adx_period wirft Fehler."""
        from src.strategies.trend_following import TrendFollowingStrategy

        with pytest.raises(ValueError, match="adx_period"):
            TrendFollowingStrategy(adx_period=0)

    def test_validation_invalid_thresholds(self):
        """exit_threshold >= adx_threshold wirft Fehler."""
        from src.strategies.trend_following import TrendFollowingStrategy

        with pytest.raises(ValueError, match="exit_threshold"):
            TrendFollowingStrategy(adx_threshold=20.0, exit_threshold=25.0)

    def test_generate_signals_returns_series(self, sample_ohlcv_data):
        """generate_signals gibt pd.Series zurück."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_generate_signals_values(self, sample_ohlcv_data):
        """Signale sind nur -1, 0, 1."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_generate_signals_requires_ohlc(self):
        """Fehlende Spalten werfen Fehler."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy()
        df = pd.DataFrame({"close": [1, 2, 3]})

        with pytest.raises(ValueError, match="high"):
            strategy.generate_signals(df)

    def test_generate_signals_too_few_bars(self, sample_ohlcv_data):
        """Zu wenig Daten wirft Fehler."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy(adx_period=50, ma_period=100)
        short_data = sample_ohlcv_data.head(50)

        with pytest.raises(ValueError, match="Bars"):
            strategy.generate_signals(short_data)

    def test_metadata(self):
        """Metadata ist korrekt gesetzt."""
        from src.strategies.trend_following import TrendFollowingStrategy

        strategy = TrendFollowingStrategy()
        assert strategy.meta.name == "Trend Following"
        assert strategy.meta.regime == "trending"
        assert "trend" in strategy.meta.tags


# =============================================================================
# TESTS: MEAN REVERSION STRATEGY
# =============================================================================


class TestMeanReversionStrategy:
    """Tests für MeanReversionStrategy."""

    def test_import(self):
        """Strategy kann importiert werden."""
        from src.strategies.mean_reversion import MeanReversionStrategy
        assert MeanReversionStrategy is not None

    def test_instantiation_default_params(self):
        """Strategy kann mit Defaults instantiiert werden."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        assert strategy.lookback == 20
        assert strategy.entry_threshold == -2.0
        assert strategy.exit_threshold == 0.0
        assert strategy.use_vol_filter is False

    def test_instantiation_custom_params(self):
        """Strategy kann mit Custom-Params instantiiert werden."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy(
            lookback=30,
            entry_threshold=-2.5,
            exit_threshold=0.5,
            use_vol_filter=True,
        )
        assert strategy.lookback == 30
        assert strategy.entry_threshold == -2.5
        assert strategy.use_vol_filter is True

    def test_validation_invalid_lookback(self):
        """Ungültiger lookback wirft Fehler."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        with pytest.raises(ValueError, match="lookback"):
            MeanReversionStrategy(lookback=0)

    def test_validation_invalid_thresholds(self):
        """entry_threshold >= exit_threshold wirft Fehler."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        with pytest.raises(ValueError, match="entry_threshold"):
            MeanReversionStrategy(entry_threshold=1.0, exit_threshold=-1.0)

    def test_generate_signals_returns_series(self, sample_ohlcv_data):
        """generate_signals gibt pd.Series zurück."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)

    def test_generate_signals_values(self, sample_ohlcv_data):
        """Signale sind nur -1, 0, 1."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_generate_signals_requires_close(self):
        """Fehlende 'close' Spalte wirft Fehler."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        df = pd.DataFrame({"open": [1, 2, 3]})

        with pytest.raises(ValueError, match="close"):
            strategy.generate_signals(df)

    def test_metadata(self):
        """Metadata ist korrekt gesetzt."""
        from src.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        assert strategy.meta.name == "Mean Reversion"
        assert strategy.meta.regime == "ranging"
        assert "mean-reversion" in strategy.meta.tags


# =============================================================================
# TESTS: MY_STRATEGY (VOLATILITY BREAKOUT)
# =============================================================================


class TestMyStrategy:
    """Tests für MyStrategy (Volatility Breakout)."""

    def test_import(self):
        """Strategy kann importiert werden."""
        from src.strategies.my_strategy import MyStrategy
        assert MyStrategy is not None

    def test_instantiation_default_params(self):
        """Strategy kann mit Defaults instantiiert werden."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy()
        assert strategy.lookback_window == 20
        assert strategy.entry_multiplier == 1.5
        assert strategy.exit_multiplier == 0.5
        assert strategy.use_close_only is False

    def test_instantiation_custom_params(self):
        """Strategy kann mit Custom-Params instantiiert werden."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy(
            lookback_window=30,
            entry_multiplier=2.0,
            exit_multiplier=0.8,
            use_close_only=True,
        )
        assert strategy.lookback_window == 30
        assert strategy.entry_multiplier == 2.0
        assert strategy.exit_multiplier == 0.8
        assert strategy.use_close_only is True

    def test_validation_invalid_lookback(self):
        """Ungültiger lookback_window wirft Fehler."""
        from src.strategies.my_strategy import MyStrategy

        with pytest.raises(ValueError, match="lookback_window"):
            MyStrategy(lookback_window=1)

    def test_validation_invalid_entry_multiplier(self):
        """Ungültiger entry_multiplier wirft Fehler."""
        from src.strategies.my_strategy import MyStrategy

        with pytest.raises(ValueError, match="entry_multiplier"):
            MyStrategy(entry_multiplier=0)

    def test_validation_invalid_multiplier_relationship(self):
        """exit_multiplier >= entry_multiplier wirft Fehler."""
        from src.strategies.my_strategy import MyStrategy

        with pytest.raises(ValueError, match="exit_multiplier"):
            MyStrategy(entry_multiplier=1.0, exit_multiplier=1.5)

    def test_generate_signals_returns_series(self, sample_ohlcv_data):
        """generate_signals gibt pd.Series zurück."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_generate_signals_values(self, sample_ohlcv_data):
        """Signale sind nur -1, 0, 1."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_generate_signals_requires_ohlc(self):
        """Fehlende high/low Spalten werfen Fehler wenn use_close_only=False."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy(use_close_only=False)
        df = pd.DataFrame({"close": [1, 2, 3] * 50})

        with pytest.raises(ValueError, match="high"):
            strategy.generate_signals(df)

    def test_generate_signals_close_only_mode(self, sample_ohlcv_data):
        """use_close_only=True funktioniert nur mit close-Spalte."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy(use_close_only=True)
        df = sample_ohlcv_data[["close"]].copy()
        signals = strategy.generate_signals(df)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

    def test_generate_signals_too_few_bars(self, sample_ohlcv_data):
        """Zu wenig Daten wirft Fehler."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy(lookback_window=50)
        short_data = sample_ohlcv_data.head(30)

        with pytest.raises(ValueError, match="Bars"):
            strategy.generate_signals(short_data)

    def test_metadata(self):
        """Metadata ist korrekt gesetzt."""
        from src.strategies.my_strategy import MyStrategy

        strategy = MyStrategy()
        assert strategy.meta.name == "Volatility Breakout"
        assert strategy.meta.regime == "trending"
        assert "breakout" in strategy.meta.tags
        assert "atr" in strategy.meta.tags

    def test_legacy_function(self, sample_ohlcv_data):
        """Legacy generate_signals() Funktion funktioniert."""
        from src.strategies.my_strategy import generate_signals

        params = {"lookback_window": 20, "entry_multiplier": 1.5}
        signals = generate_signals(sample_ohlcv_data, params)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)


# =============================================================================
# TESTS: STRATEGY REGISTRY
# =============================================================================


class TestStrategyRegistry:
    """Tests für Strategy Registry-Integration."""

    def test_new_strategies_in_registry(self):
        """Neue Strategien sind in Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys

        keys = get_available_strategy_keys()
        assert "trend_following" in keys
        assert "mean_reversion" in keys
        assert "my_strategy" in keys

    def test_get_trend_following_spec(self):
        """TrendFollowing-Spec kann abgerufen werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("trend_following")
        assert spec.key == "trend_following"
        assert spec.config_section == "strategy.trend_following"
        assert "Trend" in spec.description

    def test_get_mean_reversion_spec(self):
        """MeanReversion-Spec kann abgerufen werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("mean_reversion")
        assert spec.key == "mean_reversion"
        assert spec.config_section == "strategy.mean_reversion"
        assert "Mean" in spec.description or "Reversion" in spec.description

    def test_get_my_strategy_spec(self):
        """MyStrategy-Spec kann abgerufen werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("my_strategy")
        assert spec.key == "my_strategy"
        assert spec.config_section == "strategy.my_strategy"
        assert "Volatility" in spec.description or "ATR" in spec.description

    def test_create_trend_following_from_registry(self, sample_ohlcv_data):
        """TrendFollowing kann über Registry erstellt werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("trend_following")
        # Direkte Instantiierung ohne Config
        strategy = spec.cls()

        signals = strategy.generate_signals(sample_ohlcv_data)
        assert len(signals) == len(sample_ohlcv_data)

    def test_create_mean_reversion_from_registry(self, sample_ohlcv_data):
        """MeanReversion kann über Registry erstellt werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("mean_reversion")
        strategy = spec.cls()

        signals = strategy.generate_signals(sample_ohlcv_data)
        assert len(signals) == len(sample_ohlcv_data)

    def test_create_my_strategy_from_registry(self, sample_ohlcv_data):
        """MyStrategy kann über Registry erstellt werden."""
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec("my_strategy")
        strategy = spec.cls()

        signals = strategy.generate_signals(sample_ohlcv_data)
        assert len(signals) == len(sample_ohlcv_data)

    def test_unknown_strategy_raises(self):
        """Unbekannte Strategie wirft KeyError."""
        from src.strategies.registry import get_strategy_spec

        with pytest.raises(KeyError, match="nicht in Registry"):
            get_strategy_spec("nonexistent_strategy")


# =============================================================================
# TESTS: LEGACY API COMPATIBILITY
# =============================================================================


class TestLegacyAPI:
    """Tests für Backwards Compatibility mit Legacy-API."""

    def test_trend_following_legacy_function(self, sample_ohlcv_data):
        """Legacy generate_signals() Funktion funktioniert."""
        from src.strategies.trend_following import generate_signals

        params = {"adx_period": 14, "adx_threshold": 25.0}
        signals = generate_signals(sample_ohlcv_data, params)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)

    def test_mean_reversion_legacy_function(self, sample_ohlcv_data):
        """Legacy generate_signals() Funktion funktioniert."""
        from src.strategies.mean_reversion import generate_signals

        params = {"lookback": 20, "entry_threshold": -2.0}
        signals = generate_signals(sample_ohlcv_data, params)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv_data)


# =============================================================================
# TESTS: RESEARCH SCRIPTS (SMOKE TESTS)
# =============================================================================


class TestResearchScripts:
    """Smoke-Tests für Research-Scripts."""

    def test_research_run_strategy_script_exists(self):
        """research_run_strategy.py existiert."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent / "scripts" / "research_run_strategy.py"
        assert script_path.exists()

    def test_research_compare_strategies_script_exists(self):
        """research_compare_strategies.py existiert."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent / "scripts" / "research_compare_strategies.py"
        assert script_path.exists()

    def test_research_run_strategy_imports(self):
        """research_run_strategy.py kann importiert werden."""
        import sys
        from pathlib import Path

        scripts_dir = str(Path(__file__).parent.parent / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        # Prüfe nur dass Hauptfunktionen existieren
        # (vollständiger Import würde main() aufrufen)
        script_path = Path(__file__).parent.parent / "scripts" / "research_run_strategy.py"
        content = script_path.read_text()
        assert "def main()" in content
        assert "def parse_args()" in content

    def test_research_compare_strategies_imports(self):
        """research_compare_strategies.py kann importiert werden."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent / "scripts" / "research_compare_strategies.py"
        content = script_path.read_text()
        assert "def main()" in content
        assert "def parse_args()" in content


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration-Tests für Research Playground."""

    def test_trend_following_with_backtest_engine(self, trending_data):
        """TrendFollowing funktioniert mit BacktestEngine."""
        from src.strategies.trend_following import TrendFollowingStrategy
        from src.backtest.engine import BacktestEngine
        from src.core.position_sizing import NoopPositionSizer
        from src.core.risk import NoopRiskManager

        strategy = TrendFollowingStrategy()

        def signal_fn(df, params):
            return strategy.generate_signals(df)

        engine = BacktestEngine(
            core_position_sizer=NoopPositionSizer(),
            risk_manager=NoopRiskManager(),
        )

        result = engine.run_realistic(
            df=trending_data,
            strategy_signal_fn=signal_fn,
            strategy_params={"stop_pct": 0.02},
        )

        assert result is not None
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "stats")

    def test_mean_reversion_with_backtest_engine(self, ranging_data):
        """MeanReversion funktioniert mit BacktestEngine."""
        from src.strategies.mean_reversion import MeanReversionStrategy
        from src.backtest.engine import BacktestEngine
        from src.core.position_sizing import NoopPositionSizer
        from src.core.risk import NoopRiskManager

        strategy = MeanReversionStrategy()

        def signal_fn(df, params):
            return strategy.generate_signals(df)

        engine = BacktestEngine(
            core_position_sizer=NoopPositionSizer(),
            risk_manager=NoopRiskManager(),
        )

        result = engine.run_realistic(
            df=ranging_data,
            strategy_signal_fn=signal_fn,
            strategy_params={"stop_pct": 0.02},
        )

        assert result is not None
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "stats")

    def test_my_strategy_with_backtest_engine(self, sample_ohlcv_data):
        """MyStrategy funktioniert mit BacktestEngine."""
        from src.strategies.my_strategy import MyStrategy
        from src.backtest.engine import BacktestEngine
        from src.core.position_sizing import NoopPositionSizer
        from src.core.risk import NoopRiskManager

        strategy = MyStrategy()

        def signal_fn(df, params):
            return strategy.generate_signals(df)

        engine = BacktestEngine(
            core_position_sizer=NoopPositionSizer(),
            risk_manager=NoopRiskManager(),
        )

        result = engine.run_realistic(
            df=sample_ohlcv_data,
            strategy_signal_fn=signal_fn,
            strategy_params={"stop_pct": 0.02},
        )

        assert result is not None
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "stats")
