# tests/test_regimes.py
"""
Tests für Regime-Analyse-Modul (Phase 19).

Testbereiche:
1. Config-Laden
2. Regime-Erkennung
3. Regime-Analyse
4. CLI-Sanity
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.regimes import (
    RegimeAnalysisResult,
    RegimeConfig,
    RegimeLabel,
    RegimeStats,
    SweepRobustnessResult,
    analyze_experiment_regimes,
    analyze_regimes_from_equity,
    compute_sweep_robustness,
    create_regime_summary_df,
    detect_regimes,
    format_regime_stats_table,
    get_regime_distribution,
    load_regime_config,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def default_config() -> RegimeConfig:
    """Erstellt eine Default-RegimeConfig für Tests."""
    return RegimeConfig(
        vol_lookback=20,
        vol_low_threshold=0.30,
        vol_high_threshold=0.60,
        vol_annualization_factor=365,
        trend_short_window=20,
        trend_long_window=50,
        trend_slope_threshold=0.02,
    )


@pytest.fixture
def constant_prices() -> pd.DataFrame:
    """Erstellt konstante Preise (low_vol, sideways)."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = np.full(100, 100.0)
    # Kleine zufällige Schwankungen für Stabilität
    prices = prices + np.random.normal(0, 0.01, 100)
    return pd.DataFrame({"close": prices}, index=dates)


@pytest.fixture
def uptrend_prices() -> pd.DataFrame:
    """Erstellt klaren Aufwärtstrend."""
    dates = pd.date_range("2024-01-01", periods=200, freq="D")
    # Starker linearer Aufwärtstrend
    prices = 100.0 + np.arange(200) * 0.5
    return pd.DataFrame({"close": prices}, index=dates)


@pytest.fixture
def downtrend_prices() -> pd.DataFrame:
    """Erstellt klaren Abwärtstrend."""
    dates = pd.date_range("2024-01-01", periods=200, freq="D")
    # Starker linearer Abwärtstrend
    prices = 200.0 - np.arange(200) * 0.5
    return pd.DataFrame({"close": prices}, index=dates)


@pytest.fixture
def high_vol_prices() -> pd.DataFrame:
    """Erstellt hochvolatile Preise."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Hohe Volatilität durch große tägliche Schwankungen
    np.random.seed(42)
    returns = np.random.normal(0, 0.05, 100)  # 5% tägliche Schwankung
    prices = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame({"close": prices}, index=dates)


@pytest.fixture
def sample_equity(constant_prices: pd.DataFrame) -> pd.Series:
    """Erstellt eine Sample-Equity-Curve."""
    initial = 10000.0
    returns = constant_prices["close"].pct_change().fillna(0)
    equity = initial * (1 + returns).cumprod()
    return equity


@pytest.fixture
def sample_regimes(constant_prices: pd.DataFrame, default_config: RegimeConfig) -> pd.DataFrame:
    """Erstellt Sample-Regime-DataFrame."""
    return detect_regimes(constant_prices, default_config)


# =============================================================================
# TESTS: CONFIG LADEN
# =============================================================================


class TestConfigLoading:
    """Tests für Config-Laden."""

    def test_load_default_config_returns_valid_object(self):
        """load_regime_config gibt RegimeConfig zurück."""
        cfg = load_regime_config()
        assert isinstance(cfg, RegimeConfig)
        assert cfg.vol_lookback > 0
        assert cfg.vol_low_threshold > 0
        assert cfg.vol_high_threshold > cfg.vol_low_threshold
        assert cfg.trend_short_window > 0
        assert cfg.trend_long_window > cfg.trend_short_window

    def test_load_config_from_file(self, tmp_path: Path):
        """Config wird korrekt aus TOML geladen."""
        config_content = """
[volatility]
lookback = 30
low_threshold = 0.25
high_threshold = 0.70
annualization_factor = 252

[trend]
short_window = 15
long_window = 60
slope_threshold = 0.03
"""
        config_file = tmp_path / "test_regimes.toml"
        config_file.write_text(config_content)

        cfg = load_regime_config(config_file)

        assert cfg.vol_lookback == 30
        assert cfg.vol_low_threshold == 0.25
        assert cfg.vol_high_threshold == 0.70
        assert cfg.vol_annualization_factor == 252
        assert cfg.trend_short_window == 15
        assert cfg.trend_long_window == 60
        assert cfg.trend_slope_threshold == 0.03

    def test_load_config_missing_file_returns_defaults(self, tmp_path: Path):
        """Fehlende Config-Datei gibt Default-Werte."""
        missing_path = tmp_path / "nonexistent.toml"
        cfg = load_regime_config(missing_path)

        # Sollte Default-Werte haben
        assert cfg.vol_lookback == 20
        assert cfg.trend_short_window == 20

    def test_config_to_dict(self, default_config: RegimeConfig):
        """RegimeConfig.to_dict() funktioniert."""
        d = default_config.to_dict()
        assert isinstance(d, dict)
        assert "vol_lookback" in d
        assert "trend_short_window" in d
        assert d["vol_lookback"] == 20


# =============================================================================
# TESTS: REGIME-ERKENNUNG
# =============================================================================


class TestRegimeDetection:
    """Tests für Regime-Erkennung."""

    def test_detect_regimes_returns_dataframe(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """detect_regimes gibt DataFrame mit Regime-Spalten zurück."""
        result = detect_regimes(constant_prices, default_config)

        assert isinstance(result, pd.DataFrame)
        assert "vol_regime" in result.columns
        assert "trend_regime" in result.columns
        assert "regime" in result.columns
        assert "volatility" in result.columns
        assert "ma_delta" in result.columns

    def test_detect_regimes_preserves_original_columns(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Original-Spalten bleiben erhalten."""
        result = detect_regimes(constant_prices, default_config)
        assert "close" in result.columns

    def test_constant_prices_classified_as_low_vol(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Konstante Preise sollten low_vol sein."""
        result = detect_regimes(constant_prices, default_config)

        # Die meisten Bars sollten low_vol sein (nach Warmup)
        vol_counts = result["vol_regime"].value_counts()
        assert "low_vol" in vol_counts.index
        # Mindestens 50% sollten low_vol sein
        assert vol_counts.get("low_vol", 0) > len(result) * 0.5

    def test_uptrend_classified_as_uptrend(
        self, uptrend_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Aufwärtstrend wird als uptrend erkannt."""
        result = detect_regimes(uptrend_prices, default_config)

        # Nach Warmup sollten die meisten Bars uptrend sein
        trend_counts = result["trend_regime"].value_counts()
        assert "uptrend" in trend_counts.index
        # Mindestens 60% sollten uptrend sein (wegen Warmup)
        assert trend_counts.get("uptrend", 0) > len(result) * 0.6

    def test_downtrend_classified_as_downtrend(
        self, downtrend_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Abwärtstrend wird als downtrend erkannt."""
        result = detect_regimes(downtrend_prices, default_config)

        trend_counts = result["trend_regime"].value_counts()
        assert "downtrend" in trend_counts.index
        # Mindestens 60% sollten downtrend sein
        assert trend_counts.get("downtrend", 0) > len(result) * 0.6

    def test_high_vol_prices_classified_as_high_vol(
        self, high_vol_prices: pd.DataFrame
    ):
        """Hochvolatile Preise werden als high_vol erkannt."""
        # Niedrigere Schwellen für den Test
        cfg = RegimeConfig(
            vol_lookback=10,
            vol_low_threshold=0.10,
            vol_high_threshold=0.30,
        )
        result = detect_regimes(high_vol_prices, cfg)

        vol_counts = result["vol_regime"].value_counts()
        # Sollte high_vol oder mid_vol enthalten (nicht nur low_vol)
        assert "high_vol" in vol_counts.index or "mid_vol" in vol_counts.index

    def test_detect_regimes_raises_on_missing_column(
        self, default_config: RegimeConfig
    ):
        """KeyError bei fehlender Preis-Spalte."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        with pytest.raises(KeyError):
            detect_regimes(df, default_config, price_col="close")

    def test_combined_regime_format(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Kombiniertes Regime hat korrektes Format."""
        result = detect_regimes(constant_prices, default_config)

        for regime in result["regime"]:
            # Format: vol_regime_trend_regime
            parts = regime.split("_")
            assert len(parts) >= 3  # z.B. "low_vol_sideways"
            assert parts[0] in ["low", "mid", "high"]
            assert parts[1] == "vol"


class TestRegimeDistribution:
    """Tests für Regime-Verteilung."""

    def test_get_regime_distribution_returns_dict(
        self, sample_regimes: pd.DataFrame
    ):
        """get_regime_distribution gibt Dict zurück."""
        dist = get_regime_distribution(sample_regimes)
        assert isinstance(dist, dict)

    def test_regime_distribution_sums_to_one(
        self, sample_regimes: pd.DataFrame
    ):
        """Verteilung summiert sich zu ~1.0."""
        dist = get_regime_distribution(sample_regimes)
        total = sum(dist.values())
        assert abs(total - 1.0) < 0.01

    def test_empty_dataframe_returns_empty_dict(self):
        """Leerer DataFrame gibt leeres Dict."""
        empty_df = pd.DataFrame()
        dist = get_regime_distribution(empty_df)
        assert dist == {}


# =============================================================================
# TESTS: REGIME-ANALYSE
# =============================================================================


class TestRegimeAnalysis:
    """Tests für Regime-Performance-Analyse."""

    def test_analyze_regimes_from_equity_returns_list(
        self, sample_equity: pd.Series, sample_regimes: pd.DataFrame
    ):
        """analyze_regimes_from_equity gibt Liste von RegimeStats zurück."""
        stats = analyze_regimes_from_equity(sample_equity, sample_regimes)
        assert isinstance(stats, list)
        assert all(isinstance(s, RegimeStats) for s in stats)

    def test_regime_stats_fields_populated(
        self, sample_equity: pd.Series, sample_regimes: pd.DataFrame
    ):
        """RegimeStats-Felder sind sinnvoll gefüllt."""
        stats = analyze_regimes_from_equity(sample_equity, sample_regimes)

        for s in stats:
            assert isinstance(s.regime, str)
            assert 0.0 <= s.weight <= 1.0
            assert s.bar_count > 0
            # return_mean und return_std sollten numerisch sein
            assert isinstance(s.return_mean, float)
            assert isinstance(s.return_std, float)

    def test_weights_sum_to_approximately_one(
        self, sample_equity: pd.Series, sample_regimes: pd.DataFrame
    ):
        """Gewichte summieren sich zu ~1.0."""
        stats = analyze_regimes_from_equity(sample_equity, sample_regimes)
        total_weight = sum(s.weight for s in stats)
        assert abs(total_weight - 1.0) < 0.01

    def test_empty_equity_returns_empty_list(
        self, sample_regimes: pd.DataFrame
    ):
        """Leere Equity gibt leere Liste."""
        empty_equity = pd.Series(dtype=float)
        stats = analyze_regimes_from_equity(empty_equity, sample_regimes)
        assert stats == []

    def test_mismatched_indices_handled(self):
        """Nicht überlappende Indices werden behandelt."""
        equity = pd.Series(
            [100, 101, 102],
            index=pd.date_range("2024-01-01", periods=3)
        )
        regimes = pd.DataFrame(
            {"regime": ["a", "b", "c"]},
            index=pd.date_range("2024-06-01", periods=3)  # Andere Zeitperiode
        )
        stats = analyze_regimes_from_equity(equity, regimes)
        assert stats == []


class TestExperimentRegimeAnalysis:
    """Tests für High-Level Experiment-Analyse."""

    def test_analyze_experiment_regimes_returns_result(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """analyze_experiment_regimes gibt RegimeAnalysisResult zurück."""
        equity = pd.Series(
            10000.0 * (1 + constant_prices["close"].pct_change().fillna(0)).cumprod(),
            index=constant_prices.index,
        )

        result = analyze_experiment_regimes(
            prices=constant_prices,
            equity=equity,
            cfg=default_config,
            experiment_id="test-123",
            strategy_name="test_strategy",
        )

        assert isinstance(result, RegimeAnalysisResult)
        assert result.experiment_id == "test-123"
        assert result.strategy_name == "test_strategy"

    def test_result_has_overall_metrics(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Ergebnis hat Overall-Metriken."""
        equity = pd.Series(
            10000.0 * (1 + constant_prices["close"].pct_change().fillna(0)).cumprod(),
            index=constant_prices.index,
        )

        result = analyze_experiment_regimes(
            prices=constant_prices,
            equity=equity,
            cfg=default_config,
        )

        assert isinstance(result.overall_return, float)
        # overall_sharpe kann None sein bei wenig Daten

    def test_result_has_regime_distribution(
        self, constant_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """Ergebnis enthält Regime-Verteilung."""
        equity = pd.Series(
            10000.0 * (1 + constant_prices["close"].pct_change().fillna(0)).cumprod(),
            index=constant_prices.index,
        )

        result = analyze_experiment_regimes(
            prices=constant_prices,
            equity=equity,
            cfg=default_config,
        )

        assert isinstance(result.regime_distribution, dict)
        assert len(result.regime_distribution) > 0

    def test_get_best_worst_regime(
        self, uptrend_prices: pd.DataFrame, default_config: RegimeConfig
    ):
        """get_best_regime und get_worst_regime funktionieren."""
        # Erstelle Equity mit positivem Return
        returns = uptrend_prices["close"].pct_change().fillna(0)
        equity = pd.Series(
            10000.0 * (1 + returns).cumprod(),
            index=uptrend_prices.index,
        )

        result = analyze_experiment_regimes(
            prices=uptrend_prices,
            equity=equity,
            cfg=default_config,
        )

        # Diese können None sein wenn keine gültigen Sharpe-Werte
        best = result.get_best_regime()
        worst = result.get_worst_regime()
        # Keine Assertion auf Werte, nur dass sie nicht crashen


# =============================================================================
# TESTS: SWEEP ROBUSTHEIT
# =============================================================================


class TestSweepRobustness:
    """Tests für Sweep-Robustheits-Berechnung."""

    def test_compute_sweep_robustness_returns_result(self):
        """compute_sweep_robustness gibt SweepRobustnessResult zurück."""
        results = [
            RegimeAnalysisResult(
                experiment_id=f"exp-{i}",
                regimes=[
                    RegimeStats(
                        regime="low_vol_uptrend",
                        weight=0.5,
                        bar_count=100,
                        return_sum=0.1,
                        return_mean=0.001,
                        return_std=0.01,
                        sharpe=1.5,
                    ),
                    RegimeStats(
                        regime="high_vol_downtrend",
                        weight=0.5,
                        bar_count=100,
                        return_sum=-0.05,
                        return_mean=-0.0005,
                        return_std=0.02,
                        sharpe=-0.5,
                    ),
                ],
            )
            for i in range(5)
        ]

        robustness = compute_sweep_robustness(results, sweep_name="test_sweep")

        assert isinstance(robustness, SweepRobustnessResult)
        assert robustness.sweep_name == "test_sweep"
        assert robustness.run_count == 5

    def test_robustness_score_calculated(self):
        """Robustness Score wird berechnet."""
        # Alle Runs haben positive Sharpe in allen Regimes
        results = [
            RegimeAnalysisResult(
                regimes=[
                    RegimeStats(
                        regime="regime_a",
                        weight=0.5,
                        bar_count=50,
                        return_sum=0.05,
                        return_mean=0.001,
                        return_std=0.01,
                        sharpe=1.0,  # positiv
                    ),
                ]
            )
            for _ in range(3)
        ]

        robustness = compute_sweep_robustness(results)
        assert robustness.robustness_score == 1.0  # Alle positiv

    def test_empty_results_handled(self):
        """Leere Ergebnisse werden behandelt."""
        robustness = compute_sweep_robustness([])
        assert robustness.run_count == 0
        assert robustness.robustness_score == 0.0


# =============================================================================
# TESTS: UTILITIES
# =============================================================================


class TestUtilities:
    """Tests für Utility-Funktionen."""

    def test_format_regime_stats_table(self):
        """format_regime_stats_table gibt String zurück."""
        stats = [
            RegimeStats(
                regime="test_regime",
                weight=0.5,
                bar_count=100,
                return_sum=0.1,
                return_mean=0.001,
                return_std=0.01,
                sharpe=1.5,
                max_drawdown=-0.05,
            )
        ]

        table = format_regime_stats_table(stats)

        assert isinstance(table, str)
        assert "test_regime" in table
        assert "0.001" in table or "0.0010" in table

    def test_format_empty_stats(self):
        """Leere Stats werden behandelt."""
        table = format_regime_stats_table([])
        assert isinstance(table, str)
        assert "Keine" in table

    def test_create_regime_summary_df(self):
        """create_regime_summary_df erstellt DataFrame."""
        results = [
            RegimeAnalysisResult(
                experiment_id="exp-1",
                strategy_name="strat_a",
                overall_return=0.15,
                overall_sharpe=1.2,
                regimes=[
                    RegimeStats(
                        regime="regime_x",
                        weight=1.0,
                        bar_count=100,
                        return_sum=0.15,
                        return_mean=0.0015,
                        return_std=0.01,
                        sharpe=1.2,
                    )
                ],
            )
        ]

        df = create_regime_summary_df(results)

        assert isinstance(df, pd.DataFrame)
        assert "experiment_id" in df.columns
        assert "overall_return" in df.columns


# =============================================================================
# TESTS: CLI SANITY
# =============================================================================


class TestCLISanity:
    """CLI-Sanity-Tests."""

    def test_cli_help_runs(self):
        """CLI --help läuft ohne Fehler."""
        result = subprocess.run(
            [sys.executable, "scripts/analyze_regimes.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "Regime-Analyse" in result.stdout or "usage" in result.stdout.lower()

    def test_cli_subcommands_have_help(self):
        """Subcommands haben --help."""
        subcommands = ["single", "strategy", "sweep"]

        for cmd in subcommands:
            result = subprocess.run(
                [sys.executable, "scripts/analyze_regimes.py", cmd, "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            assert result.returncode == 0


# =============================================================================
# TESTS: DATACLASSES
# =============================================================================


class TestDataclasses:
    """Tests für Dataclass-Funktionalität."""

    def test_regime_label_combined(self):
        """RegimeLabel.combined gibt korrekte Kombination."""
        label = RegimeLabel(
            timestamp=pd.Timestamp("2024-01-01"),
            vol_regime="low_vol",
            trend_regime="uptrend",
        )
        assert label.combined == "low_vol_uptrend"

    def test_regime_stats_to_dict(self):
        """RegimeStats.to_dict funktioniert."""
        stats = RegimeStats(
            regime="test",
            weight=0.5,
            bar_count=100,
            return_sum=0.1,
            return_mean=0.001,
            return_std=0.01,
            sharpe=1.0,
            max_drawdown=-0.05,
            total_return=0.1,
        )
        d = stats.to_dict()
        assert d["regime"] == "test"
        assert d["weight"] == 0.5
        assert d["sharpe"] == 1.0

    def test_regime_analysis_result_to_dict(self):
        """RegimeAnalysisResult.to_dict funktioniert."""
        result = RegimeAnalysisResult(
            experiment_id="exp-1",
            strategy_name="test",
            regimes=[],
            overall_return=0.1,
            overall_sharpe=1.0,
            regime_distribution={"a": 0.5, "b": 0.5},
        )
        d = result.to_dict()
        assert d["experiment_id"] == "exp-1"
        assert d["overall_return"] == 0.1
        assert "regime_distribution" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
