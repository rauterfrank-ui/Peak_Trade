#!/usr/bin/env python3
"""
Tests für R&D Dashboard API (Phase 76 v1.1).

Testet die API-Endpoints für R&D-Experimente.

v1.1: Neue Tests für:
- Status-Werte: running, failed, success, no_trades
- Neue Felder: run_type, tier, experiment_category, date_str
- Neue Endpoints: /today, /running, /categories
- Run-Type Filter
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.r_and_d_api import (
    load_experiments_from_dir,
    filter_experiments,
    extract_flat_fields,
    compute_summary,
    compute_preset_stats,
    compute_strategy_stats,
    compute_global_stats,
    set_base_dir,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_experiment() -> Dict[str, Any]:
    """Beispiel-Experiment-Dict."""
    return {
        "experiment": {
            "preset_id": "test_preset_v1",
            "strategy": "test_strategy",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "from_date": "2024-01-01",
            "to_date": "2024-12-31",
            "tag": "exp_test_v1",
            "timestamp": "20241208_120000",
        },
        "results": {
            "total_return": 0.15,
            "max_drawdown": -0.08,
            "sharpe": 1.5,
            "total_trades": 42,
            "win_rate": 0.55,
            "profit_factor": 1.8,
        },
        "meta": {
            "tier": "r_and_d",
            "experimental": True,
            "allow_live": False,
            "use_dummy_data": True,
        },
        "_filename": "exp_test_v1_20241208_120000.json",
    }


@pytest.fixture
def sample_experiment_no_trades() -> Dict[str, Any]:
    """Experiment ohne Trades."""
    return {
        "experiment": {
            "preset_id": "empty_preset",
            "strategy": "empty_strategy",
            "symbol": "ETH/USDT",
            "timeframe": "4h",
            "tag": "exp_empty",
            "timestamp": "20241207_100000",
        },
        "results": {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
        },
        "meta": {
            "use_dummy_data": True,
        },
        "_filename": "exp_empty_20241207_100000.json",
    }


@pytest.fixture
def temp_experiments_dir(tmp_path: Path, sample_experiment, sample_experiment_no_trades) -> Path:
    """Temporäres Verzeichnis mit Test-JSON-Dateien."""
    exp_dir = tmp_path / "reports" / "r_and_d_experiments"
    exp_dir.mkdir(parents=True)

    # Schreibe Beispiel-Experimente
    with open(exp_dir / "exp_test_v1_20241208_120000.json", "w") as f:
        json.dump(sample_experiment, f)

    with open(exp_dir / "exp_empty_20241207_100000.json", "w") as f:
        json.dump(sample_experiment_no_trades, f)

    return tmp_path


@pytest.fixture
def client(temp_experiments_dir) -> TestClient:
    """TestClient mit temporärem Experiments-Verzeichnis."""
    # Erstelle App zuerst (setzt BASE_DIR auf echtes Verzeichnis)
    app = create_app()
    # Dann überschreibe mit temporärem Verzeichnis
    set_base_dir(temp_experiments_dir)
    return TestClient(app)


# =============================================================================
# UNIT TESTS - Hilfsfunktionen
# =============================================================================


class TestExtractFlatFields:
    """Tests für extract_flat_fields."""

    def test_extract_all_fields(self, sample_experiment):
        """Extrahiert alle relevanten Felder."""
        flat = extract_flat_fields(sample_experiment)

        assert flat["preset_id"] == "test_preset_v1"
        assert flat["strategy"] == "test_strategy"
        assert flat["symbol"] == "BTC/USDT"
        assert flat["timeframe"] == "1h"
        assert flat["tag"] == "exp_test_v1"
        assert flat["timestamp"] == "20241208_120000"
        assert flat["total_return"] == 0.15
        assert flat["sharpe"] == 1.5
        assert flat["max_drawdown"] == -0.08
        assert flat["total_trades"] == 42
        assert flat["win_rate"] == 0.55
        assert flat["use_dummy_data"] is True
        # v1.1: Status ist jetzt "success" statt "ok"
        assert flat["status"] == "success"

    def test_status_no_trades(self, sample_experiment_no_trades):
        """Status ist 'no_trades' bei 0 Trades."""
        flat = extract_flat_fields(sample_experiment_no_trades)
        assert flat["status"] == "no_trades"


class TestFilterExperiments:
    """Tests für filter_experiments."""

    def test_filter_by_preset(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach preset_id."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, preset="test_preset_v1")
        assert len(filtered) == 1
        assert filtered[0]["experiment"]["preset_id"] == "test_preset_v1"

    def test_filter_by_tag_substr(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach Tag-Substring."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, tag_substr="test")
        assert len(filtered) == 1
        assert "test" in filtered[0]["experiment"]["tag"]

    def test_filter_by_strategy(self, sample_experiment, sample_experiment_no_trades):
        """Filtert nach Strategy."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, strategy="test_strategy")
        assert len(filtered) == 1

    def test_filter_with_trades(self, sample_experiment, sample_experiment_no_trades):
        """Filtert auf Experimente mit Trades."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(experiments, with_trades=True)
        assert len(filtered) == 1
        assert filtered[0]["results"]["total_trades"] == 42

    def test_combined_filters(self, sample_experiment, sample_experiment_no_trades):
        """Kombinierte Filter."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        filtered = filter_experiments(
            experiments,
            preset="test_preset_v1",
            with_trades=True,
        )
        assert len(filtered) == 1


class TestComputeStats:
    """Tests für Statistik-Funktionen."""

    def test_compute_summary(self, sample_experiment, sample_experiment_no_trades):
        """Berechnet Summary korrekt."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        summary = compute_summary(experiments)

        assert summary["total_experiments"] == 2
        assert summary["experiments_with_trades"] == 1
        assert summary["experiments_with_dummy_data"] == 2
        assert summary["unique_presets"] == 2
        assert summary["unique_strategies"] == 2
        # v1.1: Status ist jetzt "success" statt "ok"
        assert summary["by_status"]["success"] == 1
        assert summary["by_status"]["no_trades"] == 1

    def test_compute_preset_stats(self, sample_experiment, sample_experiment_no_trades):
        """Berechnet Preset-Stats korrekt."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        stats = compute_preset_stats(experiments)

        assert len(stats) == 2
        preset_map = {s["preset_id"]: s for s in stats}
        assert preset_map["test_preset_v1"]["experiment_count"] == 1
        assert preset_map["test_preset_v1"]["avg_sharpe"] == 1.5

    def test_compute_strategy_stats(self, sample_experiment, sample_experiment_no_trades):
        """Berechnet Strategy-Stats korrekt."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        stats = compute_strategy_stats(experiments)

        assert len(stats) == 2
        strategy_map = {s["strategy"]: s for s in stats}
        assert strategy_map["test_strategy"]["experiment_count"] == 1
        assert strategy_map["test_strategy"]["avg_return"] == 0.15

    def test_compute_global_stats(self, sample_experiment, sample_experiment_no_trades):
        """Berechnet globale Stats korrekt."""
        experiments = [sample_experiment, sample_experiment_no_trades]
        stats = compute_global_stats(experiments)

        assert stats["total_experiments"] == 2
        assert stats["unique_presets"] == 2
        assert stats["unique_strategies"] == 2
        assert stats["experiments_with_trades"] == 1
        assert stats["avg_sharpe"] == 0.75  # (1.5 + 0) / 2

    def test_compute_global_stats_empty(self):
        """Globale Stats bei leerer Liste."""
        stats = compute_global_stats([])
        assert stats["total_experiments"] == 0
        assert stats["avg_sharpe"] == 0.0


# =============================================================================
# INTEGRATION TESTS - API Endpoints
# =============================================================================


class TestAPIExperiments:
    """Tests für /api/r_and_d/experiments."""

    def test_list_experiments_ok(self, client):
        """Liste gibt 200 und JSON mit items."""
        resp = client.get("/api/r_and_d/experiments")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_experiments_with_filter(self, client):
        """Filter nach Preset funktioniert."""
        resp = client.get("/api/r_and_d/experiments?preset=test_preset_v1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered"] == 1
        assert data["items"][0]["preset_id"] == "test_preset_v1"

    def test_list_experiments_with_trades(self, client):
        """Filter with_trades funktioniert."""
        resp = client.get("/api/r_and_d/experiments?with_trades=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered"] == 1
        for item in data["items"]:
            assert item["total_trades"] > 0

    def test_list_experiments_limit(self, client):
        """Limit-Parameter funktioniert."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] <= 1


class TestAPIExperimentDetail:
    """Tests für /api/r_and_d/experiments/{run_id}."""

    def test_get_experiment_detail_ok(self, client):
        """Detail gibt 200 mit Experiment-Daten."""
        resp = client.get("/api/r_and_d/experiments/exp_test_v1_20241208_120000")
        assert resp.status_code == 200
        data = resp.json()
        assert "experiment" in data
        assert "results" in data
        assert "meta" in data
        assert data["experiment"]["preset_id"] == "test_preset_v1"

    def test_get_experiment_detail_by_timestamp(self, client):
        """Detail-Suche mit Timestamp-Substring."""
        resp = client.get("/api/r_and_d/experiments/20241208_120000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["experiment"]["timestamp"] == "20241208_120000"

    def test_get_experiment_detail_not_found(self, client):
        """404 bei nicht existierendem Experiment."""
        resp = client.get("/api/r_and_d/experiments/nonexistent_run_id")
        assert resp.status_code == 404


class TestAPISummary:
    """Tests für /api/r_and_d/summary."""

    def test_summary_ok(self, client):
        """Summary gibt 200 mit korrekten Feldern."""
        resp = client.get("/api/r_and_d/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_experiments" in data
        assert "experiments_with_trades" in data
        assert "unique_presets" in data
        assert "by_status" in data


class TestAPIPresets:
    """Tests für /api/r_and_d/presets."""

    def test_presets_ok(self, client):
        """Presets gibt 200 mit Liste."""
        resp = client.get("/api/r_and_d/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "preset_id" in data[0]
        assert "experiment_count" in data[0]
        assert "avg_sharpe" in data[0]


class TestAPIStrategies:
    """Tests für /api/r_and_d/strategies."""

    def test_strategies_ok(self, client):
        """Strategies gibt 200 mit Liste."""
        resp = client.get("/api/r_and_d/strategies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "strategy" in data[0]
        assert "experiment_count" in data[0]


class TestAPIStats:
    """Tests für /api/r_and_d/stats."""

    def test_stats_ok(self, client):
        """Stats gibt 200 mit korrekten Feldern."""
        resp = client.get("/api/r_and_d/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_experiments" in data
        assert "unique_presets" in data
        assert "avg_sharpe" in data
        assert "median_sharpe" in data


class TestAPIHealth:
    """Test Health-Endpoint (bestehend)."""

    def test_health_ok(self, client):
        """Health gibt 200."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


# =============================================================================
# HTML PAGE TESTS
# =============================================================================


class TestRAndDExperimentsPage:
    """Tests für /r_and_d HTML-Page."""

    def test_page_loads_ok(self, client):
        """R&D Experiments Page gibt 200 und HTML."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        # v1.1: Neuer Titel
        assert "R&D Experiments Hub" in resp.text

    def test_page_with_filters(self, client):
        """Page mit Filtern funktioniert."""
        resp = client.get("/r_and_d?preset=test_preset_v1&with_trades=true")
        assert resp.status_code == 200
        assert "test_preset_v1" in resp.text

    def test_page_shows_stats(self, client):
        """Page zeigt Statistiken an."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        # Prüfe ob Stats-Kacheln vorhanden sind
        assert "Gesamt" in resp.text

    def test_page_shows_table(self, client):
        """Page zeigt Tabelle mit Experimenten."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        # Prüfe ob Tabellen-Header vorhanden sind
        assert "Timestamp" in resp.text
        assert "Preset" in resp.text
        assert "Sharpe" in resp.text

    def test_page_with_run_type_filter(self, client):
        """Page mit Run-Type Filter (v1.1)."""
        resp = client.get("/r_and_d?run_type=backtest")
        assert resp.status_code == 200


# =============================================================================
# v1.1 TESTS - Neue Features
# =============================================================================


class TestExtractFlatFieldsV11:
    """Tests für v1.1 Felder in extract_flat_fields."""

    def test_extract_date_str(self, sample_experiment):
        """date_str wird korrekt extrahiert (v1.1)."""
        flat = extract_flat_fields(sample_experiment)
        assert flat["date_str"] == "2024-12-08"

    def test_extract_run_type_default(self, sample_experiment):
        """run_type default ist backtest (v1.1)."""
        flat = extract_flat_fields(sample_experiment)
        assert flat["run_type"] == "backtest"

    def test_extract_run_type_from_tag_sweep(self):
        """run_type aus Tag mit 'sweep' (v1.1)."""
        exp = {
            "experiment": {"tag": "exp_sweep_v1", "timestamp": "20241208_120000"},
            "results": {"total_trades": 10},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["run_type"] == "sweep"

    def test_extract_run_type_from_tag_monte_carlo(self):
        """run_type aus Tag mit 'monte' (v1.1)."""
        exp = {
            "experiment": {"tag": "exp_monte_carlo_v1", "timestamp": "20241208_120000"},
            "results": {"total_trades": 10},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["run_type"] == "monte_carlo"

    def test_extract_tier_default(self, sample_experiment):
        """tier default ist r_and_d (v1.1)."""
        flat = extract_flat_fields(sample_experiment)
        assert flat["tier"] == "r_and_d"

    def test_extract_experiment_category_cycles(self):
        """experiment_category wird aus Strategy abgeleitet (v1.1)."""
        exp = {
            "experiment": {
                "strategy": "ehlers_cycle_filter",
                "preset_id": "ehlers_super_smoother_v1",
                "timestamp": "20241208_120000",
            },
            "results": {"total_trades": 10},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["experiment_category"] == "cycles"

    def test_extract_experiment_category_ml(self):
        """experiment_category für ML-Strategien (v1.1)."""
        exp = {
            "experiment": {
                "strategy": "meta_labeling",
                "preset_id": "lopez_meta_labeling_v1",
                "timestamp": "20241208_120000",
            },
            "results": {"total_trades": 10},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["experiment_category"] == "ml"


class TestDetermineStatusV11:
    """Tests für erweiterte Status-Werte (v1.1)."""

    def test_status_success(self, sample_experiment):
        """Status success bei Trades > 0 (v1.1)."""
        from src.webui.r_and_d_api import determine_status

        status = determine_status(sample_experiment)
        assert status == "success"

    def test_status_running(self):
        """Status running aus meta.status (v1.1)."""
        from src.webui.r_and_d_api import determine_status

        exp = {"meta": {"status": "running"}, "results": {}}
        status = determine_status(exp)
        assert status == "running"

    def test_status_failed_from_status(self):
        """Status failed aus meta.status (v1.1)."""
        from src.webui.r_and_d_api import determine_status

        exp = {"meta": {"status": "failed"}, "results": {}}
        status = determine_status(exp)
        assert status == "failed"

    def test_status_failed_from_error(self):
        """Status failed bei error in meta (v1.1)."""
        from src.webui.r_and_d_api import determine_status

        exp = {"meta": {"error": "Some error"}, "results": {"total_trades": 0}}
        status = determine_status(exp)
        assert status == "failed"

    def test_status_no_trades(self, sample_experiment_no_trades):
        """Status no_trades bei 0 Trades (v1.1)."""
        from src.webui.r_and_d_api import determine_status

        status = determine_status(sample_experiment_no_trades)
        assert status == "no_trades"


class TestAPITodayEndpoint:
    """Tests für /api/r_and_d/today (v1.1)."""

    def test_today_endpoint_ok(self, client):
        """Today-Endpoint gibt 200 (v1.1)."""
        resp = client.get("/api/r_and_d/today")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "count" in data
        assert "date" in data
        assert "success_count" in data
        assert "failed_count" in data

    def test_today_endpoint_date_format(self, client):
        """Today-Endpoint gibt korrektes Datumsformat (v1.1)."""
        resp = client.get("/api/r_and_d/today")
        assert resp.status_code == 200
        data = resp.json()
        # Format: YYYY-MM-DD
        assert len(data["date"]) == 10
        assert data["date"].count("-") == 2


class TestAPIRunningEndpoint:
    """Tests für /api/r_and_d/running (v1.1)."""

    def test_running_endpoint_ok(self, client):
        """Running-Endpoint gibt 200 (v1.1)."""
        resp = client.get("/api/r_and_d/running")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)


class TestAPICategoriesEndpoint:
    """Tests für /api/r_and_d/categories (v1.1)."""

    def test_categories_endpoint_ok(self, client):
        """Categories-Endpoint gibt 200 (v1.1)."""
        resp = client.get("/api/r_and_d/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert "run_types" in data
        assert "category_labels" in data
        assert "run_type_labels" in data

    def test_categories_endpoint_labels(self, client):
        """Categories-Endpoint hat korrekte Labels (v1.1)."""
        resp = client.get("/api/r_and_d/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "cycles" in data["category_labels"]
        assert "backtest" in data["run_type_labels"]


class TestRAndDExperimentsPageV11:
    """Tests für v1.1 Features der HTML-Page."""

    def test_page_shows_hub_header(self, client):
        """Page zeigt R&D Hub Header (v1.1)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "R&D Experiments Hub" in resp.text
        assert "v1.1" in resp.text

    def test_page_shows_daily_summary(self, client):
        """Page zeigt Daily Summary (v1.1)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "Heute fertig" in resp.text or "heute" in resp.text.lower()

    def test_page_shows_status_column(self, client):
        """Page zeigt Status-Spalte (v1.1)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "Status" in resp.text

    def test_page_shows_type_column(self, client):
        """Page zeigt Type-Spalte (v1.1)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "Type" in resp.text

    def test_page_has_run_type_filter(self, client):
        """Page hat Run-Type Filter (v1.1)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "Run-Type" in resp.text or "run_type" in resp.text
