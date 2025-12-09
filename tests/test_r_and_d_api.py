#!/usr/bin/env python3
"""
Tests für R&D Dashboard API (Phase 76/77 v1.2).

80+ spezialisierte API-Tests für das R&D-Dashboard.

Testet die API-Endpoints für R&D-Experimente.

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
    # v1.2 (Phase 77)
    find_report_links,
    compute_duration_info,
    format_duration,
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
