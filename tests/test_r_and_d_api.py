#!/usr/bin/env python3
"""
Tests für R&D Dashboard API (Phase 76).

Testet die API-Endpoints für R&D-Experimente.
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
        assert flat["status"] == "ok"

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
        assert summary["by_status"]["ok"] == 1
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
