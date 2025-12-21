#!/usr/bin/env python3
"""
Tests for Evidence Chain Module (P1)
=====================================

Tests für src/experiments/evidence_chain.py - Artifact-Generierung für Backtests/Research.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.experiments.evidence_chain import (
    ensure_run_dir,
    write_config_snapshot,
    write_stats_json,
    write_equity_csv,
    write_trades_parquet_optional,
    write_report_snippet_md,
)


class TestEnsureRunDir:
    """Tests für ensure_run_dir()."""

    def test_creates_directory(self):
        """Test dass ensure_run_dir() ein Verzeichnis erstellt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_id = "test_run_123"
            run_dir = ensure_run_dir(run_id, base_dir=base)

            assert run_dir.exists()
            assert run_dir.is_dir()
            assert run_dir.name == run_id
            assert run_dir.parent == base

    def test_idempotent(self):
        """Test dass ensure_run_dir() idempotent ist (mehrfache Aufrufe OK)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_id = "test_run_456"

            # Erster Aufruf
            run_dir1 = ensure_run_dir(run_id, base_dir=base)
            # Zweiter Aufruf
            run_dir2 = ensure_run_dir(run_id, base_dir=base)

            assert run_dir1 == run_dir2
            assert run_dir1.exists()


class TestWriteConfigSnapshot:
    """Tests für write_config_snapshot()."""

    def test_writes_json_file(self):
        """Test dass config_snapshot.json geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            meta = {
                "strategy": "ma_crossover",
                "symbol": "BTC/EUR",
                "timestamp": datetime.utcnow().isoformat(),
            }
            params = {"fast": 10, "slow": 30}

            snapshot_path = write_config_snapshot(run_dir, meta, params)

            assert snapshot_path.exists()
            assert snapshot_path.name == "config_snapshot.json"

    def test_roundtrip_json(self):
        """Test dass config_snapshot.json korrekt gelesen werden kann."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            meta = {
                "run_id": "abc123",
                "strategy": "rsi_strategy",
                "git_sha": "abcdef123456",
            }
            params = {"rsi_period": 14, "threshold_low": 30}

            snapshot_path = write_config_snapshot(run_dir, meta, params)

            # Roundtrip
            with open(snapshot_path, "r") as f:
                data = json.load(f)

            assert "meta" in data
            assert "params" in data
            assert data["meta"]["strategy"] == "rsi_strategy"
            assert data["params"]["rsi_period"] == 14


class TestWriteStatsJson:
    """Tests für write_stats_json()."""

    def test_writes_stats_file(self):
        """Test dass stats.json geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            stats = {
                "total_return": 0.25,
                "sharpe": 1.5,
                "max_drawdown": -0.15,
                "total_trades": 42,
            }

            stats_path = write_stats_json(run_dir, stats)

            assert stats_path.exists()
            assert stats_path.name == "stats.json"

    def test_roundtrip_stats(self):
        """Test dass stats.json korrekt gelesen werden kann."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            stats = {
                "sharpe": 2.1,
                "win_rate": 0.55,
                "profit_factor": 1.8,
            }

            stats_path = write_stats_json(run_dir, stats)

            # Roundtrip
            with open(stats_path, "r") as f:
                loaded = json.load(f)

            assert loaded["sharpe"] == 2.1
            assert loaded["win_rate"] == 0.55


class TestWriteEquityCsv:
    """Tests für write_equity_csv()."""

    def test_writes_from_list_of_dicts(self):
        """Test dass equity.csv aus list[dict] geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            equity_data = [
                {"timestamp": "2024-01-01T00:00:00", "equity": 10000.0},
                {"timestamp": "2024-01-01T01:00:00", "equity": 10100.0},
                {"timestamp": "2024-01-01T02:00:00", "equity": 10200.0},
            ]

            csv_path = write_equity_csv(run_dir, equity_data)

            assert csv_path.exists()
            assert csv_path.name == "equity.csv"

            # Roundtrip
            df = pd.read_csv(csv_path)
            assert len(df) == 3
            assert list(df.columns) == ["timestamp", "equity"]
            assert df["equity"].iloc[0] == 10000.0

    def test_writes_from_dataframe(self):
        """Test dass equity.csv aus DataFrame geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            df_equity = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01", periods=5, freq="h"),
                    "equity": [10000, 10050, 10100, 10150, 10200],
                }
            )

            csv_path = write_equity_csv(run_dir, df_equity)

            assert csv_path.exists()

            # Roundtrip
            df_loaded = pd.read_csv(csv_path)
            assert len(df_loaded) == 5

    def test_writes_from_list_of_lists(self):
        """Test dass equity.csv aus list[list] mit Header geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            equity_data = [
                ["timestamp", "equity"],
                ["2024-01-01T00:00:00", 10000.0],
                ["2024-01-01T01:00:00", 10100.0],
            ]

            csv_path = write_equity_csv(run_dir, equity_data)

            assert csv_path.exists()

            # Roundtrip
            df = pd.read_csv(csv_path)
            assert len(df) == 2
            assert "timestamp" in df.columns


class TestWriteTradesParquetOptional:
    """Tests für write_trades_parquet_optional()."""

    def test_returns_none_if_no_data(self):
        """Test dass None zurückgegeben wird wenn keine Trades."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            result = write_trades_parquet_optional(run_dir, None)
            assert result is None

    def test_returns_none_if_parquet_not_available(self, monkeypatch):
        """Test dass None zurückgegeben wird wenn parquet engine fehlt."""

        # Mocke pd.DataFrame.to_parquet um ImportError zu simulieren
        def mock_to_parquet(*args, **kwargs):
            raise ImportError("No module named 'pyarrow'")

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            trades_data = pd.DataFrame(
                {
                    "timestamp": ["2024-01-01T00:00:00"],
                    "symbol": ["BTC/EUR"],
                    "side": ["buy"],
                }
            )

            monkeypatch.setattr(pd.DataFrame, "to_parquet", mock_to_parquet)

            result = write_trades_parquet_optional(run_dir, trades_data)
            assert result is None

    def test_writes_parquet_if_available(self):
        """Test dass trades.parquet geschrieben wird wenn deps vorhanden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            trades_data = pd.DataFrame(
                {
                    "timestamp": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
                    "symbol": ["BTC/EUR", "BTC/EUR"],
                    "side": ["buy", "sell"],
                    "quantity": [0.1, 0.1],
                }
            )

            result = write_trades_parquet_optional(run_dir, trades_data)

            # Result kann None sein (wenn parquet nicht installiert) oder ein Path
            # Wenn es ein Path ist, prüfen wir dass die Datei existiert
            if result is not None:
                assert result.exists()
                assert result.name == "trades.parquet"


class TestWriteReportSnippetMd:
    """Tests für write_report_snippet_md()."""

    def test_writes_markdown_file(self):
        """Test dass report_snippet.md geschrieben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            summary = {
                "run_id": "test_123",
                "strategy": "ma_crossover",
                "total_return": 0.25,
                "sharpe": 1.5,
            }

            md_path = write_report_snippet_md(run_dir, summary)

            assert md_path.exists()
            assert md_path.name == "report_snippet.md"

    def test_markdown_contains_stats(self):
        """Test dass report_snippet.md die Stats enthält."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            summary = {
                "run_id": "abc123",
                "strategy": "rsi_strategy",
                "total_return": 0.35,
                "sharpe": 2.1,
                "max_drawdown": -0.12,
            }

            md_path = write_report_snippet_md(run_dir, summary)

            content = md_path.read_text()

            # Prüfe dass Key-Stats im Markdown sind
            assert "abc123" in content or "rsi_strategy" in content
            assert "0.35" in content or "35" in content  # Return
            assert "2.1" in content  # Sharpe
