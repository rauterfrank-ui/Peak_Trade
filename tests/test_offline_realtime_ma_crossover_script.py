"""
Tests für scripts/run_offline_realtime_ma_crossover.py
========================================================

Testet die Offline-Realtime MA-Crossover Pipeline.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Python-Path anpassen für src-Import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import der Script-Module
from scripts.run_offline_realtime_ma_crossover import (
    OfflineRealtimeFeed,
    OfflineRealtimeFeedConfig,
    OfflineRealtimePipelineStats,
    OfflineSynthSessionConfig,
    build_offline_ma_crossover_pipeline,
    normalize_symbol,
    run_offline_synth_session,
    run_pipeline,
    write_offline_realtime_report,
)

# =============================================================================
# Tests für Symbol-Normalisierung
# =============================================================================


class TestSymbolNormalization:
    """Tests für normalize_symbol()."""

    def test_normalize_symbol_basic(self):
        """Test: Basic Symbol-Normalisierung."""
        assert normalize_symbol("BTC/EUR") == "BTCEUR"
        assert normalize_symbol("ETH/USD") == "ETHUSD"
        assert normalize_symbol("XRP/USDT") == "XRPUSDT"

    def test_normalize_symbol_lowercase(self):
        """Test: Symbol-Normalisierung mit Kleinbuchstaben."""
        assert normalize_symbol("btc/eur") == "BTCEUR"
        assert normalize_symbol("eth/usd") == "ETHUSD"

    def test_normalize_symbol_already_normalized(self):
        """Test: Bereits normalisierte Symbole."""
        assert normalize_symbol("BTCEUR") == "BTCEUR"
        assert normalize_symbol("ETHUSD") == "ETHUSD"


# =============================================================================
# Tests für Synth-Session
# =============================================================================


class TestOfflineSynthSession:
    """Tests für run_offline_synth_session()."""

    def test_synth_session_basic(self):
        """Test: Basic Synth-Session."""
        config = OfflineSynthSessionConfig(
            n_steps=100,
            n_regimes=2,
            seed=42,
        )
        result = run_offline_synth_session(config, symbol="BTCEUR")

        assert result is not None
        assert len(result.df) == 100
        assert result.symbol == "BTCEUR"
        assert result.config == config
        assert result.run_id is not None

    def test_synth_session_has_ohlcv_columns(self):
        """Test: Synth-Session generiert OHLCV-Daten."""
        config = OfflineSynthSessionConfig(n_steps=50, seed=42)
        result = run_offline_synth_session(config, symbol="BTCEUR")

        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required_cols:
            assert col in result.df.columns

    def test_synth_session_high_low_logic(self):
        """Test: High >= Open/Close und Low <= Open/Close."""
        config = OfflineSynthSessionConfig(n_steps=50, seed=42)
        result = run_offline_synth_session(config, symbol="BTCEUR")

        df = result.df

        # High muss >= max(Open, Close) sein
        assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()

        # Low muss <= min(Open, Close) sein
        assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()

    def test_synth_session_reproducibility(self):
        """Test: Gleicher Seed → gleiche Ergebnisse."""
        config1 = OfflineSynthSessionConfig(n_steps=100, seed=42)
        config2 = OfflineSynthSessionConfig(n_steps=100, seed=42)

        result1 = run_offline_synth_session(config1, symbol="BTCEUR")
        result2 = run_offline_synth_session(config2, symbol="BTCEUR")

        pd.testing.assert_frame_equal(
            result1.df[["open", "high", "low", "close"]],
            result2.df[["open", "high", "low", "close"]],
        )

    def test_synth_session_different_regimes(self):
        """Test: Verschiedene n_regimes."""
        config1 = OfflineSynthSessionConfig(n_steps=100, n_regimes=2, seed=42)
        config2 = OfflineSynthSessionConfig(n_steps=100, n_regimes=5, seed=42)

        result1 = run_offline_synth_session(config1, symbol="BTCEUR")
        result2 = run_offline_synth_session(config2, symbol="BTCEUR")

        # Beide sollten 100 Bars haben
        assert len(result1.df) == 100
        assert len(result2.df) == 100

        # Aber verschiedene Preispfade (wegen Regime-Unterschieden)
        # Wir prüfen nur, dass beide valide Daten haben
        assert result1.df["close"].std() > 0
        assert result2.df["close"].std() > 0


# =============================================================================
# Tests für OfflineRealtimeFeed
# =============================================================================


class TestOfflineRealtimeFeed:
    """Tests für OfflineRealtimeFeed."""

    def test_feed_creation_from_synth_result(self):
        """Test: Feed-Erstellung aus Synth-Result."""
        synth_cfg = OfflineSynthSessionConfig(n_steps=50, seed=42)
        synth_result = run_offline_synth_session(synth_cfg, symbol="BTCEUR")

        feed_cfg = OfflineRealtimeFeedConfig(
            symbol="BTCEUR",
            playback_mode="fast_forward",
        )
        feed = OfflineRealtimeFeed.from_synth_session_result(synth_result, feed_cfg)

        assert feed is not None
        assert feed.config.symbol == "BTCEUR"
        assert len(feed.df) == 50

    def test_feed_get_data(self):
        """Test: Feed.get_data() gibt DataFrame zurück."""
        synth_cfg = OfflineSynthSessionConfig(n_steps=50, seed=42)
        synth_result = run_offline_synth_session(synth_cfg, symbol="BTCEUR")

        feed_cfg = OfflineRealtimeFeedConfig(symbol="BTCEUR")
        feed = OfflineRealtimeFeed.from_synth_session_result(synth_result, feed_cfg)

        df = feed.get_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50

    def test_feed_reset(self):
        """Test: Feed.reset() setzt Index zurück."""
        synth_cfg = OfflineSynthSessionConfig(n_steps=50, seed=42)
        synth_result = run_offline_synth_session(synth_cfg, symbol="BTCEUR")

        feed_cfg = OfflineRealtimeFeedConfig(symbol="BTCEUR")
        feed = OfflineRealtimeFeed.from_synth_session_result(synth_result, feed_cfg)

        # Simuliere Fortschritt
        feed._current_idx = 25

        # Reset
        feed.reset()
        assert feed._current_idx == 0


# =============================================================================
# Tests für Reporting
# =============================================================================


class TestReporting:
    """Tests für write_offline_realtime_report()."""

    def test_write_report(self, tmp_path):
        """Test: Report-Generierung."""
        stats = OfflineRealtimePipelineStats(
            run_id="test_run_123",
            run_type="offline_realtime_pipeline",
            symbol="BTC/EUR",
            strategy_id="ma_crossover",
            env_mode="paper",
            synth_n_steps=100,
            synth_n_regimes=3,
            synth_seed=42,
            fast_window=10,
            slow_window=30,
            n_ticks=100,
            n_orders=5,
            n_trades=3,
            gross_pnl=100.0,
            net_pnl=80.0,
            fees_paid=20.0,
            max_drawdown=50.0,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            finished_at=datetime(2024, 1, 1, 12, 5, 0),
            duration_seconds=300.0,
        )

        report_path = write_offline_realtime_report(stats, tmp_path)

        assert report_path.exists()
        assert report_path.name == "summary.html"

        # Prüfe Inhalt
        content = report_path.read_text()
        assert "test_run_123" in content
        assert "BTC/EUR" in content
        assert "ma_crossover" in content
        assert "80.00" in content  # Net PnL


# =============================================================================
# Tests für Pipeline-Builder
# =============================================================================


class TestPipelineBuilder:
    """Tests für build_offline_ma_crossover_pipeline()."""

    def test_build_pipeline_basic(self):
        """Test: Pipeline-Erstellung."""
        # Simuliere CLI-Args
        class Args:
            symbol = "BTC/EUR"
            n_steps = 100
            n_regimes = 3
            seed = 42
            fast_window = 10
            slow_window = 30
            playback_mode = "fast_forward"
            speed_factor = 10.0

        args = Args()
        components = build_offline_ma_crossover_pipeline(args)

        assert "synth_result" in components
        assert "feed" in components
        assert "strategy" in components
        assert "pipeline" in components
        assert "env_config" in components
        assert "run_id" in components
        assert "internal_symbol" in components

        # Prüfe Symbol-Normalisierung
        assert components["internal_symbol"] == "BTCEUR"

        # Prüfe Strategie-Parameter
        assert components["strategy"].fast_window == 10
        assert components["strategy"].slow_window == 30

    def test_build_pipeline_different_symbols(self):
        """Test: Pipeline mit verschiedenen Symbolen."""
        class Args:
            n_steps = 50
            n_regimes = 2
            seed = 42
            fast_window = 5
            slow_window = 15
            playback_mode = "fast_forward"
            speed_factor = 10.0

        # BTC/EUR
        args_btc = Args()
        args_btc.symbol = "BTC/EUR"
        components_btc = build_offline_ma_crossover_pipeline(args_btc)
        assert components_btc["internal_symbol"] == "BTCEUR"

        # ETH/USD
        args_eth = Args()
        args_eth.symbol = "ETH/USD"
        components_eth = build_offline_ma_crossover_pipeline(args_eth)
        assert components_eth["internal_symbol"] == "ETHUSD"


# =============================================================================
# Tests für Pipeline-Ausführung
# =============================================================================


class TestPipelineExecution:
    """Tests für run_pipeline()."""

    def test_run_pipeline_basic(self):
        """Test: Pipeline-Ausführung."""
        # Pipeline-Komponenten bauen
        class Args:
            symbol = "BTC/EUR"
            n_steps = 100
            n_regimes = 3
            seed = 42
            fast_window = 10
            slow_window = 30
            playback_mode = "fast_forward"
            speed_factor = 10.0

        args = Args()
        components = build_offline_ma_crossover_pipeline(args)

        # Pipeline ausführen
        perf_metrics = run_pipeline(
            pipeline=components["pipeline"],
            strategy=components["strategy"],
            feed=components["feed"],
            symbol=components["internal_symbol"],
        )

        assert "n_ticks" in perf_metrics
        assert "n_orders" in perf_metrics
        assert "n_trades" in perf_metrics
        assert "gross_pnl" in perf_metrics
        assert "net_pnl" in perf_metrics
        assert "fees_paid" in perf_metrics
        assert "max_drawdown" in perf_metrics

        # Prüfe sinnvolle Werte
        assert perf_metrics["n_ticks"] == 100
        assert perf_metrics["n_orders"] >= 0
        assert perf_metrics["n_trades"] >= 0

    def test_run_pipeline_different_ma_windows(self):
        """Test: Pipeline mit verschiedenen MA-Fenstern."""
        class Args:
            symbol = "BTC/EUR"
            n_steps = 200
            n_regimes = 5
            seed = 42
            playback_mode = "fast_forward"
            speed_factor = 10.0

        # Fast MA
        args_fast = Args()
        args_fast.fast_window = 5
        args_fast.slow_window = 15
        components_fast = build_offline_ma_crossover_pipeline(args_fast)
        perf_fast = run_pipeline(
            pipeline=components_fast["pipeline"],
            strategy=components_fast["strategy"],
            feed=components_fast["feed"],
            symbol=components_fast["internal_symbol"],
        )

        # Slow MA
        args_slow = Args()
        args_slow.fast_window = 20
        args_slow.slow_window = 50
        components_slow = build_offline_ma_crossover_pipeline(args_slow)
        perf_slow = run_pipeline(
            pipeline=components_slow["pipeline"],
            strategy=components_slow["strategy"],
            feed=components_slow["feed"],
            symbol=components_slow["internal_symbol"],
        )

        # Beide sollten valide Metriken haben
        assert perf_fast["n_ticks"] == 200
        assert perf_slow["n_ticks"] == 200

        # Fast MA sollte tendenziell mehr Trades generieren
        # (aber nicht garantiert, hängt von den Daten ab)
        assert perf_fast["n_orders"] >= 0
        assert perf_slow["n_orders"] >= 0


# =============================================================================
# Integration-Test
# =============================================================================


class TestIntegration:
    """Integration-Tests für das komplette Script."""

    def test_full_pipeline_run(self, tmp_path):
        """Test: Kompletter Pipeline-Run von Args bis Report."""
        # CLI-Args simulieren
        class Args:
            symbol = "BTC/EUR"
            n_steps = 100
            n_regimes = 3
            seed = 42
            fast_window = 10
            slow_window = 30
            playback_mode = "fast_forward"
            speed_factor = 10.0
            output_dir = tmp_path
            verbose = False

        args = Args()

        # Pipeline bauen
        components = build_offline_ma_crossover_pipeline(args)

        # Pipeline ausführen
        started_at = datetime.now()
        perf_metrics = run_pipeline(
            pipeline=components["pipeline"],
            strategy=components["strategy"],
            feed=components["feed"],
            symbol=components["internal_symbol"],
        )
        finished_at = datetime.now()
        duration = (finished_at - started_at).total_seconds()

        # Stats erstellen
        stats = OfflineRealtimePipelineStats(
            run_id=components["run_id"],
            run_type="offline_realtime_pipeline",
            symbol=args.symbol,
            strategy_id="ma_crossover",
            env_mode="paper",
            synth_n_steps=args.n_steps,
            synth_n_regimes=args.n_regimes,
            synth_seed=args.seed,
            fast_window=args.fast_window,
            slow_window=args.slow_window,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            **perf_metrics,
        )

        # Report schreiben
        report_path = write_offline_realtime_report(stats, args.output_dir)

        # Prüfungen
        assert report_path.exists()
        assert report_path.name == "summary.html"
        assert str(args.output_dir) in str(report_path)

        content = report_path.read_text()
        assert "BTC/EUR" in content
        assert "ma_crossover" in content
        assert str(perf_metrics["n_ticks"]) in content
        assert components["run_id"] in content  # Run-ID sollte im Report-Content sein

