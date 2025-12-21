# tests/test_live_web.py
"""
Tests für src/live/web/app.py (Phase 34)

Testet die Web-API und Dashboard:
- Health-Endpoint
- Runs-Liste
- Snapshots
- Tail-Events
- Alerts
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

# Skip if FastAPI not installed - must be done before any FastAPI imports
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from src.live.web.app import create_app, WebUIConfig

# Mark all tests in this module as web tests
pytestmark = pytest.mark.web


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Sample Run-Metadaten."""
    return {
        "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
        "mode": "paper",
        "strategy_name": "ma_crossover",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
        "started_at": "2025-12-04T18:00:00+00:00",
        "ended_at": None,
        "config_snapshot": {},
        "notes": "",
    }


@pytest.fixture
def sample_events_data() -> List[Dict[str, Any]]:
    """Sample Events als Liste von Dicts."""
    base_ts = datetime(2025, 12, 4, 18, 0, 0, tzinfo=timezone.utc)
    events = []

    for i in range(20):
        ts = base_ts.replace(minute=i)
        event = {
            "step": i + 1,
            "ts_bar": ts.isoformat(),
            "ts_event": ts.isoformat(),
            "price": 40000.0 + i * 10,
            "open": 40000.0 + i * 10,
            "high": 40050.0 + i * 10,
            "low": 39950.0 + i * 10,
            "close": 40000.0 + i * 10,
            "volume": 100.0,
            "position_size": 0.1 if i >= 5 else 0.0,
            "cash": 9000.0 if i >= 5 else 10000.0,
            "equity": 10000.0 + i * 5,
            "realized_pnl": 50.0 if i >= 10 else 0.0,
            "unrealized_pnl": 25.0 if i >= 5 else 0.0,
            "signal": 1 if i >= 5 else 0,
            "signal_changed": i == 5,
            "orders_generated": 1 if i == 5 else 0,
            "orders_filled": 1 if i == 5 else 0,
            "orders_rejected": 0,
            "orders_blocked": 1 if i == 15 else 0,
            "risk_allowed": i != 15,
            "risk_reasons": "max_total_exposure" if i == 15 else "",
        }
        events.append(event)

    return events


@pytest.fixture
def sample_alerts() -> List[Dict[str, Any]]:
    """Sample Alerts als JSON-Lines."""
    return [
        {
            "rule_id": "risk_blocked",
            "severity": "critical",
            "message": "Test alert 1",
            "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
            "timestamp": "2025-12-04T18:15:00+00:00",
        },
        {
            "rule_id": "large_loss_abs",
            "severity": "warning",
            "message": "Test alert 2",
            "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
            "timestamp": "2025-12-04T18:20:00+00:00",
        },
    ]


@pytest.fixture
def temp_runs_dir(
    sample_metadata: Dict[str, Any],
    sample_events_data: List[Dict[str, Any]],
    sample_alerts: List[Dict[str, Any]],
) -> Path:
    """Erstellt ein temporäres Runs-Verzeichnis mit Testdaten."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        run_dir = base_dir / sample_metadata["run_id"]
        run_dir.mkdir(parents=True)

        # meta.json schreiben
        meta_path = run_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadata, f)

        # events.parquet schreiben
        events_df = pd.DataFrame(sample_events_data)
        events_path = run_dir / "events.parquet"
        events_df.to_parquet(events_path, index=False)

        # alerts.jsonl schreiben
        alerts_path = run_dir / "alerts.jsonl"
        with open(alerts_path, "w", encoding="utf-8") as f:
            for alert in sample_alerts:
                f.write(json.dumps(alert) + "\n")

        yield base_dir


@pytest.fixture
def test_client(temp_runs_dir: Path) -> TestClient:
    """Erstellt einen TestClient mit temporärem Runs-Verzeichnis."""
    config = WebUIConfig(base_runs_dir=str(temp_runs_dir))
    app = create_app(config=config)
    return TestClient(app)


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests für /health Endpoint."""

    def test_health_check(self, test_client: TestClient) -> None:
        """Test Health-Check-Endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


# =============================================================================
# Runs Endpoint Tests
# =============================================================================


class TestRunsEndpoint:
    """Tests für /runs Endpoint."""

    def test_list_runs(self, test_client: TestClient) -> None:
        """Test Runs-Liste."""
        response = test_client.get("/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_run_metadata_fields(self, test_client: TestClient) -> None:
        """Test Run-Metadaten-Felder."""
        response = test_client.get("/runs")
        assert response.status_code == 200
        data = response.json()
        run = data[0]
        assert "run_id" in run
        assert "mode" in run
        assert "strategy_name" in run
        assert "symbol" in run
        assert "timeframe" in run

    def test_empty_runs_dir(self) -> None:
        """Test leeres Runs-Verzeichnis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = WebUIConfig(base_runs_dir=tmpdir)
            app = create_app(config=config)
            client = TestClient(app)

            response = client.get("/runs")
            assert response.status_code == 200
            data = response.json()
            assert data == []


# =============================================================================
# Snapshot Endpoint Tests
# =============================================================================


class TestSnapshotEndpoint:
    """Tests für /runs/{run_id}/snapshot Endpoint."""

    def test_get_snapshot(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Snapshot-Endpoint."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/snapshot")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["mode"] == "paper"
        assert data["strategy_name"] == "ma_crossover"

    def test_snapshot_fields(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Snapshot-Felder."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/snapshot")
        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "run_id",
            "mode",
            "strategy_name",
            "symbol",
            "timeframe",
            "total_steps",
            "total_orders",
            "total_blocked_orders",
            "equity",
            "realized_pnl",
            "unrealized_pnl",
        ]
        for field in expected_fields:
            assert field in data

    def test_snapshot_values(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Snapshot-Werte."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/snapshot")
        assert response.status_code == 200
        data = response.json()

        assert data["total_steps"] == 20
        assert data["total_orders"] == 1  # Nur bei Step 5

    def test_snapshot_not_found(self, test_client: TestClient) -> None:
        """Test nicht existierender Run."""
        response = test_client.get("/runs/nonexistent_run/snapshot")
        assert response.status_code == 404


# =============================================================================
# Tail Endpoint Tests
# =============================================================================


class TestTailEndpoint:
    """Tests für /runs/{run_id}/tail Endpoint."""

    def test_get_tail_default(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Tail-Endpoint mit Default-Limit."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/tail")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 20  # Alle 20 Events

    def test_get_tail_with_limit(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Tail-Endpoint mit Limit."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/tail?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_tail_row_fields(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Tail-Row-Felder."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/tail?limit=1")
        assert response.status_code == 200
        data = response.json()
        row = data[0]

        expected_fields = [
            "ts_bar",
            "equity",
            "realized_pnl",
            "unrealized_pnl",
            "position_size",
            "orders_count",
            "risk_allowed",
            "risk_reasons",
        ]
        for field in expected_fields:
            assert field in row

    def test_tail_not_found(self, test_client: TestClient) -> None:
        """Test nicht existierender Run."""
        response = test_client.get("/runs/nonexistent_run/tail")
        assert response.status_code == 404


# =============================================================================
# Alerts Endpoint Tests
# =============================================================================


class TestAlertsEndpoint:
    """Tests für /runs/{run_id}/alerts Endpoint."""

    def test_get_alerts(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Alerts-Endpoint."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_alerts_with_limit(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Alerts-Endpoint mit Limit."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/alerts?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_alert_fields(
        self,
        test_client: TestClient,
        sample_metadata: Dict[str, Any],
    ) -> None:
        """Test Alert-Felder."""
        run_id = sample_metadata["run_id"]
        response = test_client.get(f"/runs/{run_id}/alerts?limit=1")
        assert response.status_code == 200
        data = response.json()
        alert = data[0]

        expected_fields = ["rule_id", "severity", "message", "run_id", "timestamp"]
        for field in expected_fields:
            assert field in alert

    def test_alerts_empty(self) -> None:
        """Test Run ohne Alerts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            run_dir = base_dir / "test_run"
            run_dir.mkdir(parents=True)

            # Nur meta.json
            meta = {
                "run_id": "test_run",
                "mode": "paper",
                "strategy_name": "test",
                "symbol": "BTC/EUR",
                "timeframe": "1m",
            }
            with open(run_dir / "meta.json", "w") as f:
                json.dump(meta, f)

            config = WebUIConfig(base_runs_dir=str(base_dir))
            app = create_app(config=config)
            client = TestClient(app)

            response = client.get("/runs/test_run/alerts")
            assert response.status_code == 200
            data = response.json()
            assert data == []


# =============================================================================
# Dashboard Endpoint Tests
# =============================================================================


class TestDashboardEndpoint:
    """Tests für Dashboard-Endpoint."""

    def test_dashboard_root(self, test_client: TestClient) -> None:
        """Test Dashboard unter /."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Peak_Trade" in response.text

    def test_dashboard_alias(self, test_client: TestClient) -> None:
        """Test Dashboard unter /dashboard."""
        response = test_client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_contains_js(self, test_client: TestClient) -> None:
        """Test Dashboard enthält JavaScript."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "<script>" in response.text
        assert "fetchJSON" in response.text


# =============================================================================
# Config Tests
# =============================================================================


class TestWebUIConfig:
    """Tests für WebUIConfig."""

    def test_default_values(self) -> None:
        """Test Default-Werte."""
        cfg = WebUIConfig()
        assert cfg.enabled is True
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8000
        assert cfg.base_runs_dir == "live_runs"
        assert cfg.auto_refresh_seconds == 5

    def test_custom_values(self) -> None:
        """Test Custom-Werte."""
        cfg = WebUIConfig(
            host="0.0.0.0",
            port=9000,
            base_runs_dir="/custom/path",
            auto_refresh_seconds=10,
        )
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 9000
        assert cfg.base_runs_dir == "/custom/path"
        assert cfg.auto_refresh_seconds == 10


# =============================================================================
# App Factory Tests
# =============================================================================


class TestAppFactory:
    """Tests für create_app Factory."""

    def test_create_app_default(self) -> None:
        """Test App-Erstellung mit Defaults."""
        app = create_app()
        assert app is not None
        assert app.title == "Peak_Trade Live Dashboard"

    def test_create_app_with_config(self) -> None:
        """Test App-Erstellung mit Config."""
        config = WebUIConfig(auto_refresh_seconds=10)
        app = create_app(config=config)
        assert app is not None

    def test_create_app_with_base_dir(self) -> None:
        """Test App-Erstellung mit Base-Dir-Override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = create_app(base_runs_dir=tmpdir)
            assert app is not None
