#!/usr/bin/env python3
"""
Tests für R&D Dashboard API (Phase 76/77/78 v1.3).

110+ spezialisierte API-Tests für das R&D-Dashboard.

Testet die API-Endpoints für R&D-Experimente.

v1.3: Neue Tests für Phase 78:
- Batch-Endpoint für Multi-Run-Comparison
- Comparison-View Route
- Validierung für min/max IDs
- Best-Metrics Berechnung

v1.2: Neue Tests für Phase 77:
- Report-Links (find_report_links)
- Duration-Info (compute_duration_info)
- Detail-Endpoint v1.2 mit erweiterten Feldern
- HTML Detail-View Route

v1.1: Neue Tests für:
- Status-Werte: running, failed, success, no_trades
- Neue Felder: run_type, tier, experiment_category, date_str
- Neue Endpoints: /today, /running, /categories
- Run-Type Filter
- Paging / Limit (Boundary Tests, Min/Max Validation)
- Edge-Cases (fehlende Timestamps, leere Results)
- Filter-Kombinationen
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

# Skip if FastAPI not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

# Mark all tests in this module as web tests
pytestmark = pytest.mark.web

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
    # v1.2 (Phase 77)
    find_report_links,
    compute_duration_info,
    format_duration,
    # v1.3 (Phase 78)
    find_experiment_by_run_id,
    build_experiment_detail,
    compute_best_metrics,
    parse_and_validate_run_ids,
    RnDBatchResponse,
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


# =============================================================================
# ADDITIONAL TESTS - Paging, Edge Cases & Filter Kombinationen
# =============================================================================


class TestAPIPagingAndLimits:
    """Tests für Paging und Limit-Verhalten."""

    def test_experiments_limit_boundary_min(self, client):
        """Limit Minimum (1) funktioniert."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] <= 1

    def test_experiments_limit_boundary_max(self, client):
        """Limit Maximum (5000) akzeptiert."""
        resp = client.get("/api/r_and_d/experiments?limit=5000")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_experiments_limit_over_max_validation(self, client):
        """Limit über Maximum (5000+) gibt Validation Error."""
        resp = client.get("/api/r_and_d/experiments?limit=5001")
        # FastAPI ValidationError
        assert resp.status_code == 422

    def test_today_endpoint_limit(self, client):
        """Today-Endpoint Limit funktioniert (v1.1)."""
        resp = client.get("/api/r_and_d/today?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1


class TestAPIFilterCombinations:
    """Tests für verschiedene Filter-Kombinationen."""

    def test_combined_preset_and_strategy(self, client):
        """Kombination Preset + Strategy Filter."""
        resp = client.get("/api/r_and_d/experiments?preset=test_preset_v1&strategy=test_strategy")
        assert resp.status_code == 200
        data = resp.json()
        # Sollte 1 oder 0 Treffer haben
        assert "items" in data

    def test_combined_all_filters(self, client):
        """Kombination aller Filter."""
        resp = client.get(
            "/api/r_and_d/experiments"
            "?preset=test_preset_v1"
            "&strategy=test_strategy"
            "&tag_substr=test"
            "&with_trades=true"
            "&limit=10"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "filtered" in data

    def test_filter_with_nonexistent_preset(self, client):
        """Filter mit nicht existierendem Preset gibt leere Liste."""
        resp = client.get("/api/r_and_d/experiments?preset=nonexistent_preset_xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered"] == 0
        assert len(data["items"]) == 0


class TestAPIEdgeCases:
    """Tests für Edge-Cases und Grenzfälle."""

    def test_empty_tag_substr_filter(self, client):
        """Leerer tag_substr Filter wird ignoriert."""
        resp = client.get("/api/r_and_d/experiments?tag_substr=")
        assert resp.status_code == 200
        data = resp.json()
        # Sollte alle Experimente zurückgeben
        assert data["filtered"] == data["total"]

    def test_stats_endpoint_returns_median(self, client):
        """Stats-Endpoint liefert Median-Werte."""
        resp = client.get("/api/r_and_d/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "median_sharpe" in data
        assert "median_return" in data
        # Typ-Check
        assert isinstance(data["median_sharpe"], (int, float))
        assert isinstance(data["median_return"], (int, float))


class TestDailyStatsCalculation:
    """Tests für Daily-Stats-Berechnung."""

    def test_today_success_count_type(self, client):
        """success_count ist Integer (v1.1)."""
        resp = client.get("/api/r_and_d/today")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["success_count"], int)

    def test_today_failed_count_type(self, client):
        """failed_count ist Integer (v1.1)."""
        resp = client.get("/api/r_and_d/today")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["failed_count"], int)


class TestExtractFlatFieldsEdgeCases:
    """Edge-Case Tests für extract_flat_fields."""

    def test_missing_timestamp_graceful(self):
        """Fehlender Timestamp wird graceful behandelt."""
        exp = {
            "experiment": {"preset_id": "test"},
            "results": {"total_trades": 0},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["timestamp"] == ""
        assert flat["date_str"] == ""

    def test_short_timestamp_graceful(self):
        """Kurzer Timestamp wird graceful behandelt."""
        exp = {
            "experiment": {"preset_id": "test", "timestamp": "2024"},
            "results": {"total_trades": 0},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        # date_str sollte leer sein bei zu kurzem Timestamp
        assert flat["date_str"] == ""

    def test_missing_results_graceful(self):
        """Fehlende Results werden mit Defaults behandelt."""
        exp = {
            "experiment": {"preset_id": "test", "timestamp": "20241208_120000"},
            "results": {},
            "meta": {},
            "_filename": "test.json",
        }
        flat = extract_flat_fields(exp)
        assert flat["total_return"] == 0.0
        assert flat["sharpe"] == 0.0
        assert flat["total_trades"] == 0


# =============================================================================
# PHASE 77: NEW TESTS FOR DETAIL VIEW & REPORT LINKS
# =============================================================================


class TestDetailEndpointV12:
    """Tests für den erweiterten Detail-Endpoint (v1.2 / Phase 77)."""

    def test_detail_returns_report_links_field(self, client):
        """Detail-Endpoint liefert report_links Feld (v1.2)."""
        # Erst ein Experiment finden
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "report_links" in data
            assert isinstance(data["report_links"], list)

    def test_detail_returns_status_field(self, client):
        """Detail-Endpoint liefert status Feld (v1.2)."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "status" in data
            assert data["status"] in ["success", "running", "failed", "no_trades"]

    def test_detail_returns_run_type_field(self, client):
        """Detail-Endpoint liefert run_type Feld (v1.2)."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "run_type" in data
            assert data["run_type"] in ["backtest", "sweep", "monte_carlo", "walkforward"]

    def test_detail_returns_tier_field(self, client):
        """Detail-Endpoint liefert tier Feld (v1.2)."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "tier" in data

    def test_detail_returns_experiment_category_field(self, client):
        """Detail-Endpoint liefert experiment_category Feld (v1.2)."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "experiment_category" in data

    def test_detail_returns_duration_info_field(self, client):
        """Detail-Endpoint liefert duration_info Feld (v1.2)."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/api/r_and_d/experiments/{run_id}")
            assert detail_resp.status_code == 200
            data = detail_resp.json()
            assert "duration_info" in data
            # duration_info kann None sein, ist aber immer vorhanden

    def test_detail_404_for_nonexistent_run_id(self, client):
        """Detail-Endpoint gibt 404 für nicht existierende Run-ID."""
        resp = client.get("/api/r_and_d/experiments/nonexistent_run_id_xyz_123")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data


class TestFindReportLinks:
    """Tests für die find_report_links Funktion (Phase 77)."""

    def test_returns_list(self):
        """find_report_links gibt immer eine Liste zurück."""
        exp = {
            "experiment": {"tag": "test", "preset_id": "test", "timestamp": "20241208"},
            "meta": {},
        }
        result = find_report_links("test_run_id", exp)
        assert isinstance(result, list)

    def test_empty_experiment_returns_empty_list(self):
        """Leeres Experiment gibt leere Liste zurück."""
        exp = {"experiment": {}, "meta": {}}
        result = find_report_links("empty_run", exp)
        assert isinstance(result, list)

    def test_report_link_structure(self):
        """Report-Links haben korrekte Struktur."""
        exp = {
            "experiment": {"tag": "test", "preset_id": "test", "timestamp": "20241208"},
            "meta": {},
        }
        result = find_report_links("test_run_id", exp)
        # Auch wenn leer, prüfen wir das Format für gefundene Links
        for link in result:
            assert "type" in link
            assert "label" in link
            assert "path" in link
            assert "url" in link
            assert "exists" in link

    def test_report_link_types(self):
        """Report-Link-Typen sind valide."""
        valid_types = {"html", "markdown", "json", "png", "file"}
        exp = {
            "experiment": {"tag": "test", "preset_id": "test", "timestamp": "20241208"},
            "meta": {},
        }
        result = find_report_links("test_run_id", exp)
        for link in result:
            assert link["type"] in valid_types


class TestComputeDurationInfo:
    """Tests für die compute_duration_info Funktion (Phase 77)."""

    def test_returns_none_for_empty_experiment(self):
        """Leeres Experiment gibt None zurück."""
        exp = {"experiment": {}, "meta": {}}
        result = compute_duration_info(exp)
        assert result is None

    def test_returns_dict_with_start_time(self):
        """Experiment mit Timestamp gibt Dict mit start_time zurück."""
        exp = {
            "experiment": {"timestamp": "20241208_120000"},
            "meta": {},
        }
        result = compute_duration_info(exp)
        assert result is not None
        assert "start_time" in result
        assert result["start_time"] == "20241208_120000"

    def test_calculates_duration_when_end_time_present(self):
        """Duration wird berechnet wenn end_time vorhanden."""
        exp = {
            "experiment": {"timestamp": "20241208_120000"},
            "meta": {
                "start_time": "20241208_120000",
                "end_time": "20241208_121500",  # 15 Minuten später
            },
        }
        result = compute_duration_info(exp)
        assert result is not None
        if "duration_seconds" in result:
            # 15 Minuten = 900 Sekunden
            assert result["duration_seconds"] == 900

    def test_graceful_with_invalid_timestamps(self):
        """Ungültige Timestamps werden graceful behandelt."""
        exp = {
            "experiment": {"timestamp": "invalid"},
            "meta": {"end_time": "also_invalid"},
        }
        result = compute_duration_info(exp)
        # Sollte nicht crashen
        assert result is None or isinstance(result, dict)


class TestFormatDuration:
    """Tests für die format_duration Funktion (Phase 77)."""

    def test_formats_seconds(self):
        """Sekunden werden korrekt formatiert."""
        assert format_duration(30) == "30.0s"
        assert format_duration(59.9) == "59.9s"

    def test_formats_minutes(self):
        """Minuten werden korrekt formatiert."""
        assert format_duration(60) == "1.0m"
        assert format_duration(120) == "2.0m"
        assert format_duration(900) == "15.0m"

    def test_formats_hours(self):
        """Stunden werden korrekt formatiert."""
        assert format_duration(3600) == "1.0h"
        assert format_duration(7200) == "2.0h"

    def test_zero_duration(self):
        """Null-Dauer wird korrekt formatiert."""
        assert format_duration(0) == "0.0s"


class TestHTMLDetailRoute:
    """Tests für die HTML Detail-Route (Phase 77)."""

    def test_detail_page_returns_html(self, client):
        """Detail-Page gibt HTML zurück."""
        # Erst ein Experiment finden
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/r_and_d/experiment/{run_id}")
            assert detail_resp.status_code == 200
            assert "text/html" in detail_resp.headers.get("content-type", "")

    def test_detail_page_404_for_nonexistent(self, client):
        """Detail-Page gibt 404 für nicht existierendes Experiment."""
        resp = client.get("/r_and_d/experiment/nonexistent_xyz_123")
        assert resp.status_code == 404

    def test_detail_page_contains_run_id(self, client):
        """Detail-Page enthält die Run-ID."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        if resp.json()["items"]:
            run_id = resp.json()["items"][0]["run_id"]
            detail_resp = client.get(f"/r_and_d/experiment/{run_id}")
            assert detail_resp.status_code == 200
            # Run-ID sollte irgendwo in der HTML-Response sein
            assert run_id in detail_resp.text or run_id.replace("_", "") in detail_resp.text


class TestReportLinkTypes:
    """Tests für verschiedene Report-Link-Typen."""

    def test_html_report_label(self):
        """HTML-Reports haben korrektes Label."""
        exp = {"experiment": {}, "meta": {}}
        # Die Funktion erstellt Links nur für existierende Dateien
        # Daher prüfen wir hier nur die Grundstruktur
        result = find_report_links("test", exp)
        for link in result:
            if link["type"] == "html":
                assert "HTML" in link["label"] or "html" in link["label"].lower()

    def test_markdown_report_label(self):
        """Markdown-Reports haben korrektes Label."""
        exp = {"experiment": {}, "meta": {}}
        result = find_report_links("test", exp)
        for link in result:
            if link["type"] == "markdown":
                assert "Markdown" in link["label"] or "md" in link["label"].lower()

    def test_png_chart_label(self):
        """PNG-Charts haben korrektes Label."""
        exp = {"experiment": {}, "meta": {}}
        result = find_report_links("test", exp)
        for link in result:
            if link["type"] == "png":
                assert "Chart" in link["label"] or "png" in link["label"].lower()


# =============================================================================
# PHASE 78: BATCH-ENDPOINT & COMPARISON-VIEW TESTS
# =============================================================================


class TestBatchEndpoint:
    """Tests für den Batch-Endpoint (v1.3 / Phase 78)."""

    def test_batch_endpoint_ok(self, client):
        """Batch-Endpoint mit 2 gültigen IDs gibt 200."""
        # Hole erst 2 existierende Run-IDs
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_ids}")
            assert batch_resp.status_code == 200
            data = batch_resp.json()
            assert "experiments" in data
            assert "found_ids" in data
            assert "not_found_ids" in data
            assert data["total_found"] == 2

    def test_batch_endpoint_response_structure(self, client):
        """Batch-Response hat korrekte Struktur."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_ids}")
            assert batch_resp.status_code == 200
            data = batch_resp.json()

            # Pflichtfelder prüfen
            assert "experiments" in data
            assert "requested_ids" in data
            assert "found_ids" in data
            assert "not_found_ids" in data
            assert "total_requested" in data
            assert "total_found" in data

            # Typen prüfen
            assert isinstance(data["experiments"], list)
            assert isinstance(data["requested_ids"], list)
            assert isinstance(data["found_ids"], list)
            assert isinstance(data["not_found_ids"], list)

    def test_batch_endpoint_experiment_fields(self, client):
        """Batch-Experimente haben erwartete Felder."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_ids}")
            assert batch_resp.status_code == 200
            data = batch_resp.json()

            for exp in data["experiments"]:
                # Basisfelder
                assert "run_id" in exp
                assert "experiment" in exp
                assert "results" in exp
                assert "status" in exp
                # Flache Felder für Comparison
                assert "total_return" in exp
                assert "sharpe" in exp
                assert "max_drawdown" in exp
                assert "total_trades" in exp
                assert "win_rate" in exp


class TestBatchEndpointValidation:
    """Tests für Batch-Endpoint Validierung."""

    def test_batch_min_ids_required(self, client):
        """Batch braucht mindestens 2 IDs."""
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=single_id")
        assert resp.status_code == 400
        assert "Mindestens 2" in resp.json().get("detail", "")

    def test_batch_empty_ids_rejected(self, client):
        """Leere IDs werden abgelehnt."""
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=")
        assert resp.status_code == 400

    def test_batch_max_ids_limit(self, client):
        """Batch erlaubt maximal 10 IDs."""
        # Generiere 11 Fake-IDs
        ids = ",".join([f"fake_id_{i}" for i in range(11)])
        resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={ids}")
        assert resp.status_code == 400
        assert "Maximal 10" in resp.json().get("detail", "")

    def test_batch_10_ids_accepted(self, client):
        """Genau 10 IDs werden akzeptiert."""
        ids = ",".join([f"fake_id_{i}" for i in range(10)])
        resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={ids}")
        # 404 weil IDs nicht existieren, aber kein 400 für Limit
        assert resp.status_code == 404

    def test_batch_deduplicates_ids(self, client):
        """Batch dedupliziert IDs."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        items = resp.json().get("items", [])

        if items:
            run_id = items[0]["run_id"]
            # Gleiche ID zweimal senden
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_id},{run_id}")
            # Sollte 400 sein weil nach Deduplizierung nur 1 ID
            assert batch_resp.status_code == 400


class TestBatchEndpointPartialMatch:
    """Tests für teilweise gültige Batch-Anfragen."""

    def test_batch_partial_match_returns_200(self, client):
        """Teilweise gültige IDs geben 200 mit found/not_found."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        items = resp.json().get("items", [])

        if items:
            valid_id = items[0]["run_id"]
            invalid_id = "nonexistent_fake_id_xyz"

            batch_resp = client.get(
                f"/api/r_and_d/experiments/batch?run_ids={valid_id},{invalid_id}"
            )
            assert batch_resp.status_code == 200
            data = batch_resp.json()

            assert len(data["found_ids"]) == 1
            assert len(data["not_found_ids"]) == 1
            assert valid_id in data["found_ids"]
            assert invalid_id in data["not_found_ids"]

    def test_batch_all_invalid_returns_404(self, client):
        """Nur ungültige IDs geben 404."""
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=fake_id_1,fake_id_2")
        assert resp.status_code == 404
        assert "Keine gültigen" in resp.json().get("detail", "")


class TestComparisonRoute:
    """Tests für die HTML Comparison-Route (Phase 78)."""

    def test_comparison_page_returns_html(self, client):
        """Comparison-Page gibt HTML zurück."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            comp_resp = client.get(f"/r_and_d/comparison?run_ids={run_ids}")
            assert comp_resp.status_code == 200
            assert "text/html" in comp_resp.headers.get("content-type", "")

    def test_comparison_page_shows_experiments(self, client):
        """Comparison-Page zeigt Experiment-Daten."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            comp_resp = client.get(f"/r_and_d/comparison?run_ids={run_ids}")
            assert comp_resp.status_code == 200
            # Prüfe ob Experiment-IDs im HTML vorkommen
            text = comp_resp.text
            assert items[0]["run_id"] in text or items[0]["run_id"][:20] in text

    def test_comparison_page_no_ids_shows_error(self, client):
        """Comparison ohne IDs zeigt Fehler."""
        resp = client.get("/r_and_d/comparison")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        # Sollte eine Fehlermeldung oder leere Ansicht zeigen
        assert "Keine Run-IDs" in resp.text or "Keine Experimente" in resp.text

    def test_comparison_page_single_id_shows_error(self, client):
        """Comparison mit nur 1 ID zeigt Fehler."""
        resp = client.get("/api/r_and_d/experiments?limit=1")
        items = resp.json().get("items", [])

        if items:
            run_id = items[0]["run_id"]
            comp_resp = client.get(f"/r_and_d/comparison?run_ids={run_id}")
            assert comp_resp.status_code == 200
            # Sollte Hinweis auf min. 2 Experimente zeigen
            assert "Mindestens 2" in comp_resp.text

    def test_comparison_page_too_many_ids_shows_error(self, client):
        """Comparison mit > 10 IDs zeigt Fehler."""
        ids = ",".join([f"fake_id_{i}" for i in range(11)])
        resp = client.get(f"/r_and_d/comparison?run_ids={ids}")
        assert resp.status_code == 200
        assert "Maximal 10" in resp.text

    def test_comparison_page_has_best_metrics(self, client):
        """Comparison-Page hat Best-Metric-Markierung."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            comp_resp = client.get(f"/r_and_d/comparison?run_ids={run_ids}")
            assert comp_resp.status_code == 200
            # Prüfe ob Best-Metric-Symbol vorhanden
            assert "★" in comp_resp.text or "best" in comp_resp.text.lower()


class TestRAndDExperimentsPageV13:
    """Tests für v1.3 Features der HTML-Page (Phase 78)."""

    def test_page_has_compare_checkbox_header(self, client):
        """Page hat Checkbox-Spalten-Header."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        # Prüfe ob Comparison-UI-Elemente vorhanden
        assert "compare-checkbox" in resp.text or "⚖️" in resp.text

    def test_page_has_compare_bar(self, client):
        """Page hat Compare-Leiste (initial hidden)."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "compare-bar" in resp.text
        assert "compare-btn" in resp.text

    def test_page_has_comparison_javascript(self, client):
        """Page hat JavaScript für Comparison-Logik."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "toggleRunSelection" in resp.text
        assert "openComparison" in resp.text
        assert "MAX_SELECTION" in resp.text

    def test_page_shows_updated_version(self, client):
        """Page zeigt v1.3 im Footer."""
        resp = client.get("/r_and_d")
        assert resp.status_code == 200
        assert "v1.3" in resp.text or "Phase 76/77/78" in resp.text


# =============================================================================
# PHASE 78 v1.1: HELPER-FUNKTIONEN TESTS
# =============================================================================


class TestFindExperimentByRunId:
    """Tests für die zentralisierte Lookup-Funktion (v1.3)."""

    def test_find_by_exact_run_id(self, sample_experiment):
        """Exakter Match auf Run-ID funktioniert."""
        experiments = [sample_experiment]
        result = find_experiment_by_run_id(experiments, "exp_test_v1_20241208_120000")
        assert result is not None
        assert result["_filename"] == "exp_test_v1_20241208_120000.json"

    def test_find_by_filename_with_json(self, sample_experiment):
        """Match auf Filename mit .json funktioniert."""
        experiments = [sample_experiment]
        result = find_experiment_by_run_id(experiments, "exp_test_v1_20241208_120000.json")
        assert result is not None

    def test_find_by_exact_timestamp(self, sample_experiment):
        """Exakter Match auf Timestamp funktioniert."""
        experiments = [sample_experiment]
        result = find_experiment_by_run_id(experiments, "20241208_120000")
        assert result is not None

    def test_not_found_returns_none(self, sample_experiment):
        """Nicht gefundene ID gibt None zurück."""
        experiments = [sample_experiment]
        result = find_experiment_by_run_id(experiments, "nonexistent_run_id")
        assert result is None

    def test_empty_run_id_returns_none(self, sample_experiment):
        """Leere Run-ID gibt None zurück."""
        experiments = [sample_experiment]
        assert find_experiment_by_run_id(experiments, "") is None
        assert find_experiment_by_run_id(experiments, "   ") is None

    def test_no_partial_timestamp_match(self, sample_experiment):
        """Partial-Match auf Timestamp funktioniert NICHT (stricter matching)."""
        experiments = [sample_experiment]
        # Nur exakter Timestamp-Match, nicht Substring
        result = find_experiment_by_run_id(experiments, "20241208")
        assert result is None  # Sollte None sein weil kein exakter Match


class TestBuildExperimentDetail:
    """Tests für build_experiment_detail (v1.3)."""

    def test_builds_all_required_fields(self, sample_experiment):
        """Alle erforderlichen Felder werden gebaut."""
        detail = build_experiment_detail(sample_experiment)

        # Basis-Felder
        assert "filename" in detail
        assert "run_id" in detail
        assert "experiment" in detail
        assert "results" in detail
        assert "meta" in detail

        # Erweiterte Felder
        assert "status" in detail
        assert "run_type" in detail
        assert "tier" in detail
        assert "report_links" in detail
        assert "duration_info" in detail

        # Flache Metriken
        assert "total_return" in detail
        assert "sharpe" in detail
        assert "max_drawdown" in detail

    def test_extracts_correct_values(self, sample_experiment):
        """Korrekte Werte werden extrahiert."""
        detail = build_experiment_detail(sample_experiment)

        assert detail["run_id"] == "exp_test_v1_20241208_120000"
        assert detail["total_return"] == 0.15
        assert detail["sharpe"] == 1.5
        assert detail["status"] == "success"


class TestComputeBestMetrics:
    """Tests für compute_best_metrics (v1.3)."""

    def test_empty_list_returns_empty_dict(self):
        """Leere Liste gibt leeres Dict."""
        result = compute_best_metrics([])
        assert result == {}

    def test_single_experiment_is_best(self):
        """Einzelnes Experiment hat alle besten Werte."""
        experiments = [{"total_return": 0.1, "sharpe": 1.5, "win_rate": 0.6}]
        result = compute_best_metrics(experiments)

        assert result["total_return"] == 0.1
        assert result["sharpe"] == 1.5
        assert result["win_rate"] == 0.6

    def test_finds_max_for_higher_is_better(self):
        """Findet Maximum für 'höher ist besser' Metriken."""
        experiments = [
            {"total_return": 0.1, "sharpe": 1.0, "win_rate": 0.5},
            {"total_return": 0.2, "sharpe": 1.5, "win_rate": 0.6},
            {"total_return": 0.15, "sharpe": 2.0, "win_rate": 0.55},
        ]
        result = compute_best_metrics(experiments)

        assert result["total_return"] == 0.2
        assert result["sharpe"] == 2.0
        assert result["win_rate"] == 0.6

    def test_drawdown_best_is_closest_to_zero(self):
        """Für Drawdown ist der nächste zu 0 am besten."""
        experiments = [
            {"max_drawdown": -0.20},
            {"max_drawdown": -0.05},  # Am besten (nächste zu 0)
            {"max_drawdown": -0.15},
        ]
        result = compute_best_metrics(experiments)

        assert result["max_drawdown"] == -0.05

    def test_handles_none_values(self):
        """None-Werte werden ignoriert."""
        experiments = [
            {"total_return": None, "sharpe": 1.0},
            {"total_return": 0.1, "sharpe": None},
        ]
        result = compute_best_metrics(experiments)

        assert result["total_return"] == 0.1
        assert result["sharpe"] == 1.0


class TestParseAndValidateRunIds:
    """Tests für parse_and_validate_run_ids (v1.3)."""

    def test_parses_comma_separated_ids(self):
        """Komma-separierte IDs werden geparst."""
        result = parse_and_validate_run_ids("id1,id2,id3")
        assert result == ["id1", "id2", "id3"]

    def test_trims_whitespace(self):
        """Whitespace wird entfernt."""
        result = parse_and_validate_run_ids("  id1 , id2  ,  id3  ")
        assert result == ["id1", "id2", "id3"]

    def test_removes_empty_entries(self):
        """Leere Einträge werden entfernt."""
        result = parse_and_validate_run_ids("id1,,id2,  ,id3")
        assert result == ["id1", "id2", "id3"]

    def test_deduplicates_ids(self):
        """Duplikate werden entfernt (Reihenfolge beibehalten)."""
        result = parse_and_validate_run_ids("id1,id2,id1,id3,id2")
        assert result == ["id1", "id2", "id3"]

    def test_raises_on_too_few_ids(self):
        """Wirft ValueError bei zu wenig IDs (v1.3.1: Framework-agnostisch)."""
        with pytest.raises(ValueError) as exc_info:
            parse_and_validate_run_ids("single_id")

        assert "Mindestens 2" in str(exc_info.value)

    def test_raises_on_too_many_ids(self):
        """Wirft ValueError bei zu vielen IDs (v1.3.1: Framework-agnostisch)."""
        ids = ",".join([f"id_{i}" for i in range(15)])
        with pytest.raises(ValueError) as exc_info:
            parse_and_validate_run_ids(ids, max_ids=10)

        assert "Maximal 10" in str(exc_info.value)

    def test_custom_min_max_limits(self):
        """Custom Min/Max Limits funktionieren."""
        # Sollte funktionieren mit min=1
        result = parse_and_validate_run_ids("single_id", min_ids=1)
        assert result == ["single_id"]

        # Sollte mit custom max funktionieren
        with pytest.raises(ValueError):
            parse_and_validate_run_ids("id1,id2,id3,id4,id5", max_ids=3)


class TestParseAndValidateRunIdsEdgeCases:
    """Zusätzliche Edge-Case-Tests für parse_and_validate_run_ids (v1.3.1)."""

    def test_exactly_min_ids_accepted(self):
        """Genau min_ids werden akzeptiert (Boundary-Test)."""
        result = parse_and_validate_run_ids("id1,id2", min_ids=2, max_ids=10)
        assert result == ["id1", "id2"]

    def test_exactly_max_ids_accepted(self):
        """Genau max_ids werden akzeptiert (Boundary-Test)."""
        ids = ",".join([f"id_{i}" for i in range(10)])
        result = parse_and_validate_run_ids(ids, min_ids=1, max_ids=10)
        assert len(result) == 10
        assert result[0] == "id_0"
        assert result[-1] == "id_9"

    def test_dedup_reduces_below_min_raises(self):
        """Deduplizierung kann unter min_ids fallen → ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_and_validate_run_ids("id1, id1", min_ids=2, max_ids=10)
        assert "Mindestens 2 Run-IDs erforderlich" in str(exc_info.value)

    def test_all_whitespace_raises(self):
        """Nur Whitespace-IDs werden zu leerer Liste → ValueError."""
        with pytest.raises(ValueError):
            parse_and_validate_run_ids("   ,   ,   ", min_ids=2, max_ids=10)


class TestComputeBestMetricsEdgeCases:
    """Zusätzliche Edge-Case-Tests für compute_best_metrics (v1.3.1)."""

    def test_all_negative_returns(self):
        """Alle negativen Returns → der am wenigsten negative gewinnt."""
        experiments = [
            {"total_return": -0.20},
            {"total_return": -0.05},  # Best (am wenigsten negativ)
            {"total_return": -0.15},
        ]
        result = compute_best_metrics(experiments)
        assert result["total_return"] == -0.05

    def test_mixed_missing_fields(self):
        """Experimente mit unterschiedlich fehlenden Feldern."""
        experiments = [
            {"total_return": 0.1, "sharpe": 1.0},  # kein win_rate
            {"total_return": 0.2},  # kein sharpe, kein win_rate
            {"sharpe": 2.0, "win_rate": 0.7},  # kein total_return
        ]
        result = compute_best_metrics(experiments)
        assert result["total_return"] == 0.2
        assert result["sharpe"] == 2.0
        assert result["win_rate"] == 0.7

    def test_all_none_values_for_metric(self):
        """Alle None-Werte für eine Metrik → Metrik nicht im Ergebnis."""
        experiments = [
            {"total_return": None, "sharpe": 1.0},
            {"total_return": None, "sharpe": 2.0},
        ]
        result = compute_best_metrics(experiments)
        assert "total_return" not in result
        assert result["sharpe"] == 2.0


class TestBatchEndpointValueErrorConversion:
    """Tests für ValueError → HTTPException Konvertierung im Batch-Endpoint."""

    def test_batch_endpoint_converts_valueerror_to_400(self, client):
        """Batch-Endpoint konvertiert ValueError zu HTTP 400."""
        # Nur eine ID → ValueError → HTTPException 400
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=single_id")
        assert resp.status_code == 400
        assert "Mindestens 2" in resp.json().get("detail", "")

    def test_batch_endpoint_too_many_ids_400(self, client):
        """Zu viele IDs → HTTP 400."""
        ids = ",".join([f"id_{i}" for i in range(15)])
        resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={ids}")
        assert resp.status_code == 400
        assert "Maximal" in resp.json().get("detail", "")


class TestBatchEndpointV13Response:
    """Tests für v1.3 Batch-Response-Struktur."""

    def test_batch_response_includes_best_metrics(self, client):
        """Batch-Response enthält best_metrics (v1.3)."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_ids}")
            assert batch_resp.status_code == 200
            data = batch_resp.json()

            assert "best_metrics" in data
            assert isinstance(data["best_metrics"], dict)

    def test_batch_response_validates_pydantic_model(self, client):
        """Batch-Response entspricht RnDBatchResponse-Modell."""
        resp = client.get("/api/r_and_d/experiments?limit=2")
        items = resp.json().get("items", [])

        if len(items) >= 2:
            run_ids = f"{items[0]['run_id']},{items[1]['run_id']}"
            batch_resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={run_ids}")
            assert batch_resp.status_code == 200
            data = batch_resp.json()

            # Validiere gegen Pydantic-Modell
            response = RnDBatchResponse(**data)
            assert response.total_found == 2
            assert len(response.experiments) == 2


class TestBatchEndpointEdgeCases:
    """Zusätzliche Edge-Case-Tests für Batch-Endpoint (v1.3)."""

    def test_whitespace_only_ids_rejected(self, client):
        """Nur-Whitespace IDs werden abgelehnt."""
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=   ,   ,   ")
        assert resp.status_code == 400

    def test_very_long_run_id_handled(self, client):
        """Sehr lange Run-IDs werden sauber behandelt."""
        long_id = "a" * 500
        resp = client.get(f"/api/r_and_d/experiments/batch?run_ids={long_id},{long_id}a")
        # Sollte 404 sein (nicht gefunden), nicht crashen
        assert resp.status_code in [400, 404]

    def test_special_characters_in_ids(self, client):
        """Sonderzeichen in IDs werden sauber behandelt."""
        # URL-encoded special chars
        resp = client.get("/api/r_and_d/experiments/batch?run_ids=id%20with%20space,id-with-dash")
        assert resp.status_code in [400, 404]
