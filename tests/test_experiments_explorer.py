#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_experiments_explorer.py
"""
Peak_Trade – Tests für Experiment & Metrics Explorer (Phase 22)
===============================================================
Unit-Tests für:
- src/analytics/explorer.py (ExperimentExplorer, Dataclasses, etc.)
- scripts/experiments_explorer.py (CLI-Tool)

Run:
    pytest tests/test_experiments_explorer.py -v
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytest

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.explorer import (
    ExperimentFilter,
    ExperimentSummary,
    RankedExperiment,
    SweepOverview,
    ExperimentExplorer,
    get_explorer,
    quick_list,
    quick_rank,
    quick_sweep_summary,
    _parse_timestamp,
    _extract_tag,
    _extract_tags_list,
    _parse_params,
    _row_to_summary,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_experiments_csv(tmp_path: Path) -> Path:
    """Erstellt eine temporäre Experiments-CSV mit Testdaten."""
    csv_path = tmp_path / "experiments.csv"

    # Testdaten erstellen
    rows = [
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "backtest",
            "run_name": "backtest_ma_crossover_test1",
            "timestamp": "2024-12-01T10:00:00Z",
            "strategy_key": "ma_crossover",
            "symbol": "BTC/EUR",
            "portfolio_name": "",
            "sweep_name": "",
            "scan_name": "",
            "total_return": 0.15,
            "cagr": 0.12,
            "max_drawdown": -0.08,
            "sharpe": 1.5,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"short_window": 10, "long_window": 50}),
            "stats_json": json.dumps({"total_return": 0.15, "sharpe": 1.5, "win_rate": 0.55}),
            "metadata_json": json.dumps({"tag": "test-run"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "backtest",
            "run_name": "backtest_ma_crossover_test2",
            "timestamp": "2024-12-02T10:00:00Z",
            "strategy_key": "ma_crossover",
            "symbol": "ETH/EUR",
            "portfolio_name": "",
            "sweep_name": "",
            "scan_name": "",
            "total_return": 0.20,
            "cagr": 0.18,
            "max_drawdown": -0.10,
            "sharpe": 1.8,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"short_window": 15, "long_window": 60}),
            "stats_json": json.dumps({"total_return": 0.20, "sharpe": 1.8}),
            "metadata_json": json.dumps({"tag": "test-run"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "backtest",
            "run_name": "backtest_rsi_test1",
            "timestamp": "2024-12-03T10:00:00Z",
            "strategy_key": "rsi_reversion",
            "symbol": "BTC/EUR",
            "portfolio_name": "",
            "sweep_name": "",
            "scan_name": "",
            "total_return": 0.10,
            "cagr": 0.08,
            "max_drawdown": -0.05,
            "sharpe": 1.2,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"rsi_period": 14}),
            "stats_json": json.dumps({"total_return": 0.10, "sharpe": 1.2}),
            "metadata_json": json.dumps({"tag": "production"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "sweep",
            "run_name": "sweep_ma_opt_v1_001",
            "timestamp": "2024-12-04T10:00:00Z",
            "strategy_key": "ma_crossover",
            "symbol": "BTC/EUR",
            "portfolio_name": "",
            "sweep_name": "ma_opt_v1",
            "scan_name": "",
            "total_return": 0.25,
            "cagr": 0.22,
            "max_drawdown": -0.07,
            "sharpe": 2.0,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"short_window": 8, "long_window": 40}),
            "stats_json": json.dumps({"total_return": 0.25, "sharpe": 2.0}),
            "metadata_json": json.dumps({"tag": "sweep"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "sweep",
            "run_name": "sweep_ma_opt_v1_002",
            "timestamp": "2024-12-04T11:00:00Z",
            "strategy_key": "ma_crossover",
            "symbol": "BTC/EUR",
            "portfolio_name": "",
            "sweep_name": "ma_opt_v1",
            "scan_name": "",
            "total_return": 0.18,
            "cagr": 0.15,
            "max_drawdown": -0.09,
            "sharpe": 1.6,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"short_window": 12, "long_window": 55}),
            "stats_json": json.dumps({"total_return": 0.18, "sharpe": 1.6}),
            "metadata_json": json.dumps({"tag": "sweep"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "sweep",
            "run_name": "sweep_ma_opt_v1_003",
            "timestamp": "2024-12-04T12:00:00Z",
            "strategy_key": "ma_crossover",
            "symbol": "BTC/EUR",
            "portfolio_name": "",
            "sweep_name": "ma_opt_v1",
            "scan_name": "",
            "total_return": 0.22,
            "cagr": 0.19,
            "max_drawdown": -0.06,
            "sharpe": 1.9,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({"short_window": 10, "long_window": 45}),
            "stats_json": json.dumps({"total_return": 0.22, "sharpe": 1.9}),
            "metadata_json": json.dumps({"tag": "sweep"}),
        },
        {
            "run_id": str(uuid.uuid4()),
            "run_type": "portfolio_backtest",
            "run_name": "portfolio_test_v1",
            "timestamp": "2024-12-05T10:00:00Z",
            "strategy_key": "",
            "symbol": "",
            "portfolio_name": "core_portfolio",
            "sweep_name": "",
            "scan_name": "",
            "total_return": 0.12,
            "cagr": 0.10,
            "max_drawdown": -0.04,
            "sharpe": 1.4,
            "report_dir": "",
            "report_prefix": "",
            "params_json": json.dumps({}),
            "stats_json": json.dumps({"total_return": 0.12, "sharpe": 1.4}),
            "metadata_json": json.dumps({"tag": "portfolio"}),
        },
    ]

    # CSV schreiben
    fieldnames = list(rows[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


@pytest.fixture
def explorer(temp_experiments_csv: Path) -> ExperimentExplorer:
    """Erstellt einen ExperimentExplorer mit temporärer CSV."""
    return ExperimentExplorer(experiments_csv=temp_experiments_csv)


# =============================================================================
# TESTS: HELPER FUNCTIONS
# =============================================================================


class TestHelperFunctions:
    """Tests für Helper-Funktionen."""

    def test_parse_timestamp_valid(self):
        """Test: Gültiger Timestamp."""
        ts = _parse_timestamp("2024-12-01T10:00:00Z")
        assert ts is not None
        assert ts.year == 2024
        assert ts.month == 12
        assert ts.day == 1

    def test_parse_timestamp_invalid(self):
        """Test: Ungültiger Timestamp."""
        assert _parse_timestamp("invalid") is None
        assert _parse_timestamp("") is None
        assert _parse_timestamp(None) is None

    def test_extract_tag(self):
        """Test: Tag aus metadata_json extrahieren."""
        meta = json.dumps({"tag": "my-tag"})
        assert _extract_tag(meta) == "my-tag"

        # Kein Tag
        meta = json.dumps({"other": "value"})
        assert _extract_tag(meta) is None

        # Ungültiges JSON
        assert _extract_tag("invalid") is None

    def test_extract_tags_list(self):
        """Test: Tags als Liste extrahieren."""
        meta = json.dumps({"tag": "my-tag"})
        tags = _extract_tags_list(meta)
        assert tags == ["my-tag"]

        # Kein Tag
        meta = json.dumps({})
        assert _extract_tags_list(meta) == []

    def test_parse_params(self):
        """Test: Parameter aus JSON parsen."""
        params = _parse_params(json.dumps({"a": 1, "b": "test"}))
        assert params == {"a": 1, "b": "test"}

        # Leeres JSON
        assert _parse_params("{}") == {}
        assert _parse_params("") == {}
        assert _parse_params(None) == {}


# =============================================================================
# TESTS: DATACLASSES
# =============================================================================


class TestDataclasses:
    """Tests für Dataclasses."""

    def test_experiment_filter_defaults(self):
        """Test: ExperimentFilter mit Defaults."""
        flt = ExperimentFilter()
        assert flt.run_types is None
        assert flt.strategies is None
        assert flt.limit is None

    def test_experiment_filter_with_values(self):
        """Test: ExperimentFilter mit Werten."""
        flt = ExperimentFilter(
            run_types=["backtest", "sweep"],
            strategies=["ma_crossover"],
            limit=10,
        )
        assert flt.run_types == ["backtest", "sweep"]
        assert flt.strategies == ["ma_crossover"]
        assert flt.limit == 10

    def test_experiment_summary_creation(self):
        """Test: ExperimentSummary erstellen."""
        summary = ExperimentSummary(
            experiment_id="test-id",
            run_type="backtest",
            run_name="test-run",
            strategy_name="ma_crossover",
            metrics={"sharpe": 1.5, "total_return": 0.15},
        )
        assert summary.experiment_id == "test-id"
        assert summary.metrics["sharpe"] == 1.5

    def test_ranked_experiment(self):
        """Test: RankedExperiment erstellen."""
        summary = ExperimentSummary(
            experiment_id="test-id",
            run_type="backtest",
            run_name="test",
        )
        ranked = RankedExperiment(
            summary=summary,
            rank=1,
            sort_key="sharpe",
            sort_value=1.5,
        )
        assert ranked.rank == 1
        assert ranked.sort_key == "sharpe"

    def test_sweep_overview(self):
        """Test: SweepOverview erstellen."""
        overview = SweepOverview(
            sweep_name="my_sweep",
            strategy_key="ma_crossover",
            run_count=10,
            metric_stats={"min": 0.5, "max": 2.0, "mean": 1.2},
        )
        assert overview.sweep_name == "my_sweep"
        assert overview.run_count == 10


# =============================================================================
# TESTS: EXPERIMENT EXPLORER
# =============================================================================


class TestExperimentExplorer:
    """Tests für ExperimentExplorer."""

    def test_list_experiments_no_filter(self, explorer: ExperimentExplorer):
        """Test: Alle Experimente listen (ohne Filter)."""
        experiments = explorer.list_experiments()
        assert len(experiments) == 7  # 3 backtests + 3 sweeps + 1 portfolio

    def test_list_experiments_by_run_type(self, explorer: ExperimentExplorer):
        """Test: Filter nach run_type."""
        flt = ExperimentFilter(run_types=["backtest"])
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 3
        for exp in experiments:
            assert exp.run_type == "backtest"

    def test_list_experiments_by_strategy(self, explorer: ExperimentExplorer):
        """Test: Filter nach strategy_key."""
        flt = ExperimentFilter(strategies=["ma_crossover"])
        experiments = explorer.list_experiments(flt)
        # 2 backtests + 3 sweeps = 5
        assert len(experiments) == 5
        for exp in experiments:
            assert exp.strategy_name == "ma_crossover"

    def test_list_experiments_by_tag(self, explorer: ExperimentExplorer):
        """Test: Filter nach Tag."""
        flt = ExperimentFilter(tags=["test-run"])
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 2

    def test_list_experiments_by_sweep_name(self, explorer: ExperimentExplorer):
        """Test: Filter nach sweep_name."""
        flt = ExperimentFilter(sweep_names=["ma_opt_v1"])
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 3
        for exp in experiments:
            assert exp.sweep_name == "ma_opt_v1"

    def test_list_experiments_with_limit(self, explorer: ExperimentExplorer):
        """Test: Limit für Ergebnisse."""
        flt = ExperimentFilter(limit=2)
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 2

    def test_list_experiments_combined_filter(self, explorer: ExperimentExplorer):
        """Test: Kombinierte Filter."""
        flt = ExperimentFilter(
            run_types=["backtest"],
            strategies=["ma_crossover"],
        )
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 2

    def test_rank_experiments_by_sharpe(self, explorer: ExperimentExplorer):
        """Test: Ranking nach Sharpe."""
        ranked = explorer.rank_experiments(metric="sharpe", top_n=5)
        assert len(ranked) == 5
        # Sollte absteigend sortiert sein
        for i in range(len(ranked) - 1):
            assert ranked[i].sort_value >= ranked[i + 1].sort_value

    def test_rank_experiments_by_sharpe_ascending(self, explorer: ExperimentExplorer):
        """Test: Ranking nach Sharpe (aufsteigend)."""
        ranked = explorer.rank_experiments(metric="sharpe", top_n=3, descending=False)
        assert len(ranked) == 3
        # Sollte aufsteigend sortiert sein
        for i in range(len(ranked) - 1):
            assert ranked[i].sort_value <= ranked[i + 1].sort_value

    def test_rank_experiments_with_filter(self, explorer: ExperimentExplorer):
        """Test: Ranking mit Filter."""
        flt = ExperimentFilter(run_types=["sweep"])
        ranked = explorer.rank_experiments(flt, metric="sharpe", top_n=10)
        assert len(ranked) == 3
        for r in ranked:
            assert r.summary.run_type == "sweep"

    def test_get_experiment_details(self, explorer: ExperimentExplorer):
        """Test: Details zu einem Experiment abrufen."""
        # Erst ein Experiment holen
        experiments = explorer.list_experiments()
        assert len(experiments) > 0

        exp_id = experiments[0].experiment_id
        details = explorer.get_experiment_details(exp_id)

        assert details is not None
        assert details.experiment_id == exp_id

    def test_get_experiment_details_not_found(self, explorer: ExperimentExplorer):
        """Test: Nicht existierendes Experiment."""
        details = explorer.get_experiment_details("non-existent-id")
        assert details is None

    def test_summarize_sweep(self, explorer: ExperimentExplorer):
        """Test: Sweep-Übersicht erstellen."""
        overview = explorer.summarize_sweep("ma_opt_v1", metric="sharpe", top_n=5)

        assert overview is not None
        assert overview.sweep_name == "ma_opt_v1"
        assert overview.strategy_key == "ma_crossover"
        assert overview.run_count == 3
        assert len(overview.best_runs) == 3
        assert "short_window" in overview.param_ranges
        assert "long_window" in overview.param_ranges

    def test_summarize_sweep_not_found(self, explorer: ExperimentExplorer):
        """Test: Nicht existierender Sweep."""
        overview = explorer.summarize_sweep("non_existent_sweep")
        assert overview is None

    def test_summarize_sweep_metric_stats(self, explorer: ExperimentExplorer):
        """Test: Metrik-Statistiken in Sweep-Übersicht."""
        overview = explorer.summarize_sweep("ma_opt_v1", metric="sharpe")

        assert "min" in overview.metric_stats
        assert "max" in overview.metric_stats
        assert "mean" in overview.metric_stats
        assert overview.metric_stats["min"] <= overview.metric_stats["max"]

    def test_list_sweeps(self, explorer: ExperimentExplorer):
        """Test: Alle Sweeps listen."""
        sweeps = explorer.list_sweeps()
        assert "ma_opt_v1" in sweeps

    def test_compare_sweeps(self, explorer: ExperimentExplorer):
        """Test: Sweeps vergleichen."""
        # Nur ein Sweep in Testdaten
        overviews = explorer.compare_sweeps(["ma_opt_v1"], metric="sharpe")
        assert len(overviews) == 1
        assert overviews[0].sweep_name == "ma_opt_v1"

    def test_get_unique_strategies(self, explorer: ExperimentExplorer):
        """Test: Einzigartige Strategien abrufen."""
        strategies = explorer.get_unique_strategies()
        assert "ma_crossover" in strategies
        assert "rsi_reversion" in strategies

    def test_get_unique_run_types(self, explorer: ExperimentExplorer):
        """Test: Einzigartige Run-Types abrufen."""
        run_types = explorer.get_unique_run_types()
        assert "backtest" in run_types
        assert "sweep" in run_types
        assert "portfolio_backtest" in run_types

    def test_count_experiments(self, explorer: ExperimentExplorer):
        """Test: Experimente zählen."""
        count = explorer.count_experiments()
        assert count == 7

        flt = ExperimentFilter(run_types=["backtest"])
        count = explorer.count_experiments(flt)
        assert count == 3

    def test_export_to_csv(self, explorer: ExperimentExplorer, tmp_path: Path):
        """Test: CSV-Export."""
        output_path = tmp_path / "export.csv"
        flt = ExperimentFilter(run_types=["backtest"])

        result_path = explorer.export_to_csv(flt, output_path)

        assert result_path.exists()
        # CSV lesen und prüfen
        with result_path.open("r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

    def test_export_to_markdown(self, explorer: ExperimentExplorer, tmp_path: Path):
        """Test: Markdown-Export."""
        output_path = tmp_path / "export.md"

        result_path = explorer.export_to_markdown(
            output_path=output_path,
            metric="sharpe",
            top_n=5,
        )

        assert result_path.exists()
        content = result_path.read_text()
        assert "Peak_Trade" in content
        assert "Rank" in content


# =============================================================================
# TESTS: CONVENIENCE FUNCTIONS
# =============================================================================


class TestConvenienceFunctions:
    """Tests für Convenience-Funktionen."""

    def test_get_explorer(self, temp_experiments_csv: Path):
        """Test: Factory-Funktion."""
        explorer = get_explorer(temp_experiments_csv)
        assert isinstance(explorer, ExperimentExplorer)

    def test_quick_list(self, temp_experiments_csv: Path, monkeypatch):
        """Test: quick_list Funktion."""
        # Monkey-patch den Default-Pfad
        from src.analytics import explorer as explorer_module

        monkeypatch.setattr(explorer_module, "EXPERIMENTS_CSV", temp_experiments_csv)

        experiments = quick_list(run_type="backtest", limit=10)
        assert len(experiments) > 0
        for exp in experiments:
            assert exp.run_type == "backtest"

    def test_quick_rank(self, temp_experiments_csv: Path, monkeypatch):
        """Test: quick_rank Funktion."""
        from src.analytics import explorer as explorer_module

        monkeypatch.setattr(explorer_module, "EXPERIMENTS_CSV", temp_experiments_csv)

        ranked = quick_rank(metric="sharpe", top_n=5)
        assert len(ranked) == 5

    def test_quick_sweep_summary(self, temp_experiments_csv: Path, monkeypatch):
        """Test: quick_sweep_summary Funktion."""
        from src.analytics import explorer as explorer_module

        monkeypatch.setattr(explorer_module, "EXPERIMENTS_CSV", temp_experiments_csv)

        overview = quick_sweep_summary("ma_opt_v1", metric="sharpe")
        assert overview is not None
        assert overview.sweep_name == "ma_opt_v1"


# =============================================================================
# TESTS: EMPTY/EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests für Edge Cases."""

    def test_empty_csv(self, tmp_path: Path):
        """Test: Leere CSV-Datei."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("run_id,run_type,run_name,timestamp\n")

        explorer = ExperimentExplorer(csv_path)
        experiments = explorer.list_experiments()
        assert len(experiments) == 0

    def test_non_existent_csv(self, tmp_path: Path):
        """Test: Nicht existierende CSV."""
        csv_path = tmp_path / "non_existent.csv"

        explorer = ExperimentExplorer(csv_path)
        experiments = explorer.list_experiments()
        assert len(experiments) == 0

    def test_filter_no_matches(self, explorer: ExperimentExplorer):
        """Test: Filter ohne Treffer."""
        flt = ExperimentFilter(strategies=["non_existent_strategy"])
        experiments = explorer.list_experiments(flt)
        assert len(experiments) == 0

    def test_rank_invalid_metric(self, explorer: ExperimentExplorer):
        """Test: Ranking mit ungültiger Metrik."""
        ranked = explorer.rank_experiments(metric="non_existent_metric")
        assert len(ranked) == 0


# =============================================================================
# TESTS: CLI (BASIC SANITY)
# =============================================================================


class TestCLI:
    """Sanity-Tests für CLI-Tool."""

    def test_cli_help(self):
        """Test: CLI --help funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/experiments_explorer.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "Experiment" in result.stdout or "experiment" in result.stdout.lower()

    def test_cli_list_help(self):
        """Test: CLI list --help funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/experiments_explorer.py", "list", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "--run-type" in result.stdout

    def test_cli_top_help(self):
        """Test: CLI top --help funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/experiments_explorer.py", "top", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "--metric" in result.stdout

    def test_cli_sweep_summary_help(self):
        """Test: CLI sweep-summary --help funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/experiments_explorer.py", "sweep-summary", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "--sweep-name" in result.stdout


# =============================================================================
# TESTS: INTEGRATION
# =============================================================================


class TestIntegration:
    """Integrationstests."""

    def test_full_workflow(self, explorer: ExperimentExplorer, tmp_path: Path):
        """Test: Vollständiger Workflow."""
        # 1. Alle Experimente listen
        all_experiments = explorer.list_experiments()
        assert len(all_experiments) > 0

        # 2. Nach Strategie filtern
        flt = ExperimentFilter(strategies=["ma_crossover"])
        ma_experiments = explorer.list_experiments(flt)
        assert len(ma_experiments) > 0

        # 3. Ranking
        ranked = explorer.rank_experiments(flt, metric="sharpe", top_n=5)
        assert len(ranked) > 0
        assert ranked[0].rank == 1

        # 4. Sweep-Summary
        overview = explorer.summarize_sweep("ma_opt_v1", metric="sharpe")
        assert overview is not None
        assert overview.run_count == 3

        # 5. Export
        csv_path = tmp_path / "workflow_export.csv"
        explorer.export_to_csv(flt, csv_path)
        assert csv_path.exists()

    def test_metrics_extraction(self, explorer: ExperimentExplorer):
        """Test: Metriken werden korrekt extrahiert."""
        experiments = explorer.list_experiments()

        for exp in experiments:
            if exp.metrics:
                # Metriken sollten floats sein
                for key, val in exp.metrics.items():
                    assert isinstance(val, (int, float)), f"Metric {key} is not numeric"

    def test_params_extraction(self, explorer: ExperimentExplorer):
        """Test: Parameter werden korrekt extrahiert."""
        flt = ExperimentFilter(run_types=["sweep"])
        experiments = explorer.list_experiments(flt)

        for exp in experiments:
            # Sweep-Runs sollten Parameter haben
            assert exp.params is not None
            assert len(exp.params) > 0


# =============================================================================
# TESTS: IMPORTS
# =============================================================================


class TestImports:
    """Tests für korrektes Import-Verhalten."""

    def test_import_from_analytics(self):
        """Test: Import aus src.analytics funktioniert."""
        from src.analytics import (
            ExperimentFilter,
            ExperimentSummary,
            RankedExperiment,
            SweepOverview,
            ExperimentExplorer,
            get_explorer,
            quick_list,
            quick_rank,
            quick_sweep_summary,
        )

        # Alle sollten importierbar sein
        assert ExperimentFilter is not None
        assert ExperimentSummary is not None
        assert RankedExperiment is not None
        assert SweepOverview is not None
        assert ExperimentExplorer is not None

    def test_import_from_explorer(self):
        """Test: Direkter Import aus explorer.py funktioniert."""
        from src.analytics.explorer import (
            ExperimentFilter,
            ExperimentSummary,
            ExperimentExplorer,
        )

        assert ExperimentFilter is not None
