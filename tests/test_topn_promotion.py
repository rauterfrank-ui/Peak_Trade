# tests/test_topn_promotion.py
"""
Tests für src/experiments/topn_promotion.py (Phase 42)
======================================================

Testet Top-N Promotion Pipeline für Sweep-Ergebnisse.
"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import pandas as pd
import toml

from src.experiments.topn_promotion import (
    TopNPromotionConfig,
    load_sweep_results,
    select_top_n,
    export_top_n,
    find_sweep_results,
)


# =============================================================================
# CONFIG TESTS
# =============================================================================


class TestTopNPromotionConfig:
    """Tests für TopNPromotionConfig."""

    def test_basic_creation(self):
        """Einfache Erstellung funktioniert."""
        config = TopNPromotionConfig(sweep_name="test_sweep")

        assert config.sweep_name == "test_sweep"
        assert config.metric_primary == "metric_sharpe_ratio"
        assert config.metric_fallback == "metric_total_return"
        assert config.top_n == 5
        assert isinstance(config.output_path, Path)
        assert isinstance(config.experiments_dir, Path)

    def test_custom_values(self):
        """Custom-Werte werden korrekt gesetzt."""
        config = TopNPromotionConfig(
            sweep_name="custom",
            metric_primary="metric_total_return",
            top_n=10,
            output_path="custom/output",
        )

        assert config.metric_primary == "metric_total_return"
        assert config.top_n == 10
        assert config.output_path == Path("custom/output")

    def test_path_normalization(self):
        """String-Pfade werden zu Path-Objekten konvertiert."""
        config = TopNPromotionConfig(
            sweep_name="test",
            output_path="reports/sweeps",
            experiments_dir="reports/experiments",
        )

        assert isinstance(config.output_path, Path)
        assert isinstance(config.experiments_dir, Path)


# =============================================================================
# SELECT TOP N TESTS
# =============================================================================


class TestSelectTopN:
    """Tests für select_top_n()."""

    def test_select_top_n_basic(self):
        """Top-N Auswahl funktioniert mit vorhandener Metrik."""
        df = pd.DataFrame({
            "param_rsi_period": [7, 14, 21, 7, 14],
            "metric_sharpe_ratio": [1.5, 2.0, 0.8, 1.2, 1.8],
            "metric_total_return": [0.1, 0.2, 0.05, 0.08, 0.15],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            metric_primary="metric_sharpe_ratio",
            top_n=3,
        )

        result, metric_used = select_top_n(df, config)

        assert metric_used == "metric_sharpe_ratio"
        assert len(result) == 3
        assert "rank" in result.columns
        assert result.iloc[0]["rank"] == 1
        assert result.iloc[0]["metric_sharpe_ratio"] == 2.0  # Höchster Wert
        # Prüfe dass alle Werte >= dem dritten sind (Top-3)
        assert all(result["metric_sharpe_ratio"] >= 1.2)
        assert result["metric_sharpe_ratio"].min() >= 1.2

    def test_select_top_n_fallback(self):
        """Fallback-Metrik wird verwendet, wenn primary fehlt."""
        df = pd.DataFrame({
            "param_rsi_period": [7, 14, 21],
            "metric_total_return": [0.1, 0.2, 0.05],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            metric_primary="metric_sharpe_ratio",  # Fehlt
            metric_fallback="metric_total_return",
            top_n=2,
        )

        result, metric_used = select_top_n(df, config)

        assert metric_used == "metric_total_return"  # Fallback verwendet
        assert len(result) == 2
        assert result.iloc[0]["metric_total_return"] == 0.2  # Höchster Return

    def test_select_top_n_filters_nan(self):
        """NaN-Werte werden gefiltert."""
        df = pd.DataFrame({
            "param_rsi_period": [7, 14, 21, 7],
            "metric_sharpe_ratio": [1.5, float("nan"), 0.8, 1.2],
            "metric_total_return": [0.1, 0.2, 0.05, 0.08],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            metric_primary="metric_sharpe_ratio",
            top_n=5,
        )

        result, metric_used = select_top_n(df, config)

        # Nur 3 gültige Werte (NaN wurde gefiltert)
        assert len(result) == 3
        assert all(pd.notna(result["metric_sharpe_ratio"]))

    def test_select_top_n_no_valid_metric_raises(self):
        """Fehler wenn keine gültige Metrik gefunden wird."""
        df = pd.DataFrame({
            "param_rsi_period": [7, 14],
            "other_col": [1, 2],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            metric_primary="metric_sharpe_ratio",
            metric_fallback="metric_total_return",
        )

        with pytest.raises(ValueError, match="Weder.*noch.*gefunden"):
            select_top_n(df, config)

    def test_select_top_n_all_nan_raises(self):
        """Fehler wenn alle Werte NaN sind."""
        df = pd.DataFrame({
            "param_rsi_period": [7, 14],
            "metric_sharpe_ratio": [float("nan"), float("nan")],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            metric_primary="metric_sharpe_ratio",
        )

        with pytest.raises(ValueError, match="Keine gültigen Runs"):
            select_top_n(df, config)


# =============================================================================
# EXPORT TOP N TESTS
# =============================================================================


class TestExportTopN:
    """Tests für export_top_n()."""

    def test_export_top_n_creates_file(self):
        """TOML-Datei wird erstellt."""
        df_top = pd.DataFrame({
            "rank": [1, 2],
            "param_rsi_period": [14, 7],
            "param_oversold_level": [30, 20],
            "metric_sharpe_ratio": [2.0, 1.5],
            "metric_total_return": [0.2, 0.1],
            "experiment_id": ["abc123", "def456"],
        })

        config = TopNPromotionConfig(
            sweep_name="test_sweep",
            output_path=Path("test_output"),
        )

        with TemporaryDirectory() as tmpdir:
            config.output_path = Path(tmpdir)
            output_path = export_top_n(df_top, config)

            assert output_path.exists()
            assert output_path.name == "test_sweep_top_candidates.toml"

    def test_export_top_n_toml_structure(self):
        """TOML-Struktur ist korrekt."""
        df_top = pd.DataFrame({
            "rank": [1],
            "param_rsi_period": [14],
            "param_oversold_level": [30],
            "metric_sharpe_ratio": [2.0],
            "metric_total_return": [0.2],
        })

        config = TopNPromotionConfig(
            sweep_name="test_sweep",
            metric_primary="metric_sharpe_ratio",
        )

        with TemporaryDirectory() as tmpdir:
            config.output_path = Path(tmpdir)
            output_path = export_top_n(df_top, config)

            # Lade und parse TOML
            with open(output_path, "r") as f:
                data = toml.load(f)

            assert "meta" in data
            assert data["meta"]["sweep_name"] == "test_sweep"
            assert data["meta"]["metric_used"] == "metric_sharpe_ratio"
            assert data["meta"]["top_n"] == 1

            assert "candidates" in data
            assert len(data["candidates"]) == 1

            candidate = data["candidates"][0]
            assert candidate["rank"] == 1
            assert candidate["sharpe_ratio"] == 2.0
            assert candidate["total_return"] == 0.2
            assert "params" in candidate
            assert candidate["params"]["rsi_period"] == 14
            assert candidate["params"]["oversold_level"] == 30

    def test_export_top_n_creates_directory(self):
        """Output-Verzeichnis wird erstellt falls nicht vorhanden."""
        df_top = pd.DataFrame({
            "rank": [1],
            "param_rsi_period": [14],
            "metric_sharpe_ratio": [2.0],
        })

        config = TopNPromotionConfig(
            sweep_name="test",
            output_path=Path("test_output/new_dir"),
        )

        with TemporaryDirectory() as tmpdir:
            config.output_path = Path(tmpdir) / "new_dir"
            output_path = export_top_n(df_top, config)

            assert config.output_path.exists()
            assert output_path.exists()


# =============================================================================
# FIND SWEEP RESULTS TESTS
# =============================================================================


class TestFindSweepResults:
    """Tests für find_sweep_results()."""

    def test_find_sweep_results_csv(self):
        """CSV-Datei wird gefunden."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            csv_file = exp_dir / "rsi_reversion_basic_abc123_20241206.csv"
            csv_file.touch()

            result = find_sweep_results("rsi_reversion_basic", exp_dir)

            assert result == csv_file

    def test_find_sweep_results_parquet(self):
        """Parquet-Datei wird gefunden wenn CSV fehlt."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            parquet_file = exp_dir / "rsi_reversion_basic_abc123_20241206.parquet"
            parquet_file.touch()

            result = find_sweep_results("rsi_reversion_basic", exp_dir)

            assert result == parquet_file

    def test_find_sweep_results_returns_newest(self):
        """Neueste Datei wird zurückgegeben."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            old_file = exp_dir / "rsi_reversion_basic_old.csv"
            new_file = exp_dir / "rsi_reversion_basic_new.csv"
            old_file.touch()
            new_file.touch()

            result = find_sweep_results("rsi_reversion_basic", exp_dir)

            # Neueste Datei (zuletzt erstellt)
            assert result in [old_file, new_file]

    def test_find_sweep_results_not_found(self):
        """None wird zurückgegeben wenn nichts gefunden wird."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)

            result = find_sweep_results("nonexistent", exp_dir)

            assert result is None

    def test_find_sweep_results_fallback_strategy_name(self):
        """Fallback auf strategy_name funktioniert."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            # Datei mit strategy_name statt full sweep_name
            strategy_file = exp_dir / "rsi_reversion_abc123.csv"
            strategy_file.touch()

            result = find_sweep_results("rsi_reversion_basic", exp_dir)

            assert result == strategy_file


# =============================================================================
# LOAD SWEEP RESULTS TESTS
# =============================================================================


class TestLoadSweepResults:
    """Tests für load_sweep_results()."""

    def test_load_sweep_results_csv(self):
        """CSV-Datei wird geladen."""
        df_test = pd.DataFrame({
            "param_rsi_period": [7, 14],
            "metric_sharpe_ratio": [1.5, 2.0],
        })

        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            csv_file = exp_dir / "test_sweep_abc123.csv"
            df_test.to_csv(csv_file, index=False)

            config = TopNPromotionConfig(
                sweep_name="test_sweep",
                experiments_dir=exp_dir,
            )

            result = load_sweep_results(config)

            assert len(result) == 2
            assert "param_rsi_period" in result.columns

    def test_load_sweep_results_parquet(self):
        """Parquet-Datei wird geladen."""
        df_test = pd.DataFrame({
            "param_rsi_period": [7, 14],
            "metric_sharpe_ratio": [1.5, 2.0],
        })

        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            parquet_file = exp_dir / "test_sweep_abc123.parquet"
            df_test.to_parquet(parquet_file, index=False)

            config = TopNPromotionConfig(
                sweep_name="test_sweep",
                experiments_dir=exp_dir,
            )

            result = load_sweep_results(config)

            assert len(result) == 2
            assert "param_rsi_period" in result.columns

    def test_load_sweep_results_not_found_raises(self):
        """FileNotFoundError wenn keine Ergebnisse gefunden werden."""
        with TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)

            config = TopNPromotionConfig(
                sweep_name="nonexistent",
                experiments_dir=exp_dir,
            )

            with pytest.raises(FileNotFoundError, match="Keine Ergebnisse gefunden"):
                load_sweep_results(config)

