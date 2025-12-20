# tests/test_webui_live_track.py
"""
Tests für das Live-Track Panel im Web-Dashboard (Phase 82/85).

Testet (Phase 82):
- LiveSessionSummary Pydantic-Modell
- get_recent_live_sessions() Service-Funktion
- /api/live_sessions API-Endpoint
- Dashboard-Rendering mit Live-Track-Daten

Testet (Phase 85 - Session Explorer):
- LiveSessionDetail Pydantic-Modell
- get_filtered_sessions() mit Mode/Status-Filter
- get_session_by_id() für Detail-Ansicht
- get_session_stats() für Statistiken
- /api/live_sessions/{session_id} Detail-Endpoint
- /api/live_sessions/stats Stats-Endpoint
- /session/{session_id} HTML Detail-Page

Run:
    pytest tests/test_webui_live_track.py -v
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pytest

# Skip if FastAPI not installed - all tests in this module require web stack
pytest.importorskip("fastapi")

# Mark all tests in this module as web tests
pytestmark = pytest.mark.web


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_sessions_dir(tmp_path: Path) -> Path:
    """Erstellt ein temporäres Verzeichnis für Session-Records."""
    sessions_dir = tmp_path / "live_sessions"
    sessions_dir.mkdir(parents=True)
    return sessions_dir


@pytest.fixture
def sample_session_data() -> Dict[str, Any]:
    """Sample-Daten für eine Session."""
    return {
        "session_id": "session_20251208_test_001",
        "run_id": "run_123",
        "run_type": "live_session_shadow",
        "mode": "shadow",
        "env_name": "kraken_futures_testnet",
        "symbol": "BTC/USDT",
        "status": "completed",
        "started_at": "2024-12-08T12:00:00",
        "finished_at": "2024-12-08T13:00:00",
        "config": {"strategy_name": "ma_crossover"},
        "metrics": {
            "realized_pnl": 150.0,
            "max_drawdown": 0.05,
            "num_orders": 10,
        },
        "cli_args": ["python", "run_session.py"],
        "error": None,
        "created_at": "2024-12-08T13:00:00",
    }


def create_session_file(
    sessions_dir: Path,
    data: Dict[str, Any],
    index: int = 0,
) -> Path:
    """Erstellt eine Session-JSON-Datei."""
    filename = f"20241208T1{index:02d}000_live_session_shadow_{data['session_id']}.json"
    filepath = sessions_dir / filename
    filepath.write_text(json.dumps(data), encoding="utf-8")
    return filepath


# =============================================================================
# Tests: LiveSessionSummary Model
# =============================================================================


class TestLiveSessionSummaryModel:
    """Tests für das LiveSessionSummary Pydantic-Modell."""

    def test_create_minimal_summary(self):
        """Test: Minimales Summary erstellen."""
        from src.webui.live_track import LiveSessionSummary

        summary = LiveSessionSummary(
            session_id="test_session",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            mode="shadow",
            status="completed",
        )

        assert summary.session_id == "test_session"
        assert summary.mode == "shadow"
        assert summary.status == "completed"
        assert summary.ended_at is None
        assert summary.realized_pnl is None

    def test_create_full_summary(self):
        """Test: Vollständiges Summary erstellen."""
        from src.webui.live_track import LiveSessionSummary

        summary = LiveSessionSummary(
            session_id="test_session_full",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            ended_at=datetime(2024, 12, 8, 13, 0, 0),
            mode="testnet",
            environment="kraken_futures / BTC/USDT",
            status="completed",
            realized_pnl=150.0,
            max_drawdown=0.05,
            num_orders=10,
            notes="Test notes",
        )

        assert summary.session_id == "test_session_full"
        assert summary.mode == "testnet"
        assert summary.environment == "kraken_futures / BTC/USDT"
        assert summary.realized_pnl == 150.0
        assert summary.max_drawdown == 0.05
        assert summary.num_orders == 10

    def test_summary_json_serialization(self):
        """Test: Summary kann zu JSON serialisiert werden."""
        from src.webui.live_track import LiveSessionSummary

        summary = LiveSessionSummary(
            session_id="test_json",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            mode="shadow",
            status="completed",
            realized_pnl=100.0,
        )

        json_data = summary.model_dump()
        assert json_data["session_id"] == "test_json"
        assert json_data["realized_pnl"] == 100.0

    def test_summary_valid_status_values(self):
        """Test: Nur gültige Status-Werte akzeptiert."""
        from src.webui.live_track import LiveSessionSummary

        for status in ["started", "completed", "failed", "aborted"]:
            summary = LiveSessionSummary(
                session_id=f"test_{status}",
                started_at=datetime.utcnow(),
                mode="shadow",
                status=status,
            )
            assert summary.status == status


# =============================================================================
# Tests: get_recent_live_sessions Service
# =============================================================================


class TestGetRecentLiveSessions:
    """Tests für die get_recent_live_sessions Service-Funktion."""

    def test_empty_registry_returns_empty_list(self, temp_sessions_dir):
        """Test: Leere Registry gibt leere Liste zurück."""
        from src.webui.live_track import get_recent_live_sessions

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)
        assert sessions == []

    def test_nonexistent_dir_returns_empty_list(self, tmp_path):
        """Test: Nicht existierendes Verzeichnis gibt leere Liste zurück."""
        from src.webui.live_track import get_recent_live_sessions

        sessions = get_recent_live_sessions(
            limit=10, base_dir=tmp_path / "nonexistent"
        )
        assert sessions == []

    def test_loads_sessions_from_registry(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Sessions werden aus der Registry geladen."""
        from src.webui.live_track import get_recent_live_sessions

        # Session-Datei erstellen
        create_session_file(temp_sessions_dir, sample_session_data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert len(sessions) == 1
        assert sessions[0].session_id == "session_20251208_test_001"
        assert sessions[0].mode == "shadow"
        assert sessions[0].status == "completed"
        assert sessions[0].realized_pnl == 150.0

    def test_respects_limit_parameter(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Limit-Parameter wird respektiert."""
        from src.webui.live_track import get_recent_live_sessions

        # 5 Sessions erstellen
        for i in range(5):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i:03d}"
            create_session_file(temp_sessions_dir, data, index=i)

        sessions = get_recent_live_sessions(limit=3, base_dir=temp_sessions_dir)
        assert len(sessions) == 3

    def test_sorted_by_ended_at_descending(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Sessions sind nach ended_at sortiert (neueste zuerst)."""
        from src.webui.live_track import get_recent_live_sessions

        # Sessions mit unterschiedlichen Endzeiten erstellen
        for i in range(3):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i:03d}"
            end_time = datetime(2024, 12, 8, 10 + i, 0, 0)
            data["finished_at"] = end_time.isoformat()
            create_session_file(temp_sessions_dir, data, index=i)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        # Neueste zuerst (session_002 hat höchste Endzeit)
        assert sessions[0].session_id == "session_002"

    def test_handles_missing_optional_fields(self, temp_sessions_dir):
        """Test: Fehlende optionale Felder werden korrekt behandelt."""
        from src.webui.live_track import get_recent_live_sessions

        minimal_data = {
            "session_id": "session_minimal",
            "run_id": None,
            "run_type": "live_session_shadow",
            "mode": "shadow",
            "env_name": "",
            "symbol": "",
            "status": "completed",
            "started_at": "2024-12-08T12:00:00",
            "finished_at": None,
            "config": {},
            "metrics": {},
            "cli_args": [],
            "error": None,
            "created_at": "2024-12-08T12:00:00",
        }
        create_session_file(temp_sessions_dir, minimal_data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert len(sessions) == 1
        assert sessions[0].session_id == "session_minimal"
        assert sessions[0].realized_pnl is None
        assert sessions[0].max_drawdown is None

    def test_skips_corrupted_json_files(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Beschädigte JSON-Dateien werden übersprungen."""
        from src.webui.live_track import get_recent_live_sessions

        # Gültige Session erstellen
        create_session_file(temp_sessions_dir, sample_session_data)

        # Beschädigte Datei erstellen
        corrupted_file = temp_sessions_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json", encoding="utf-8")

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert len(sessions) == 1
        assert sessions[0].session_id == "session_20251208_test_001"

    def test_environment_built_from_env_and_symbol(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Environment wird aus env_name und symbol zusammengebaut."""
        from src.webui.live_track import get_recent_live_sessions

        create_session_file(temp_sessions_dir, sample_session_data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert sessions[0].environment == "kraken_futures_testnet / BTC/USDT"


# =============================================================================
# Tests: API Endpoint
# =============================================================================


class TestApiLiveSessionsEndpoint:
    """Tests für den /api/live_sessions API-Endpoint."""

    @pytest.fixture
    def test_client(self):
        """Erstellt einen TestClient für die FastAPI-App."""
        from fastapi.testclient import TestClient
        from src.webui.app import create_app

        app = create_app()
        return TestClient(app)

    def test_endpoint_returns_200(self, test_client):
        """Test: Endpoint gibt 200 zurück."""
        response = test_client.get("/api/live_sessions")
        assert response.status_code == 200

    def test_endpoint_returns_list(self, test_client):
        """Test: Endpoint gibt eine Liste zurück."""
        response = test_client.get("/api/live_sessions")
        assert isinstance(response.json(), list)

    def test_endpoint_respects_limit_param(self, test_client):
        """Test: Limit-Parameter wird akzeptiert."""
        response = test_client.get("/api/live_sessions?limit=5")
        assert response.status_code == 200

    def test_endpoint_validates_limit_min(self, test_client):
        """Test: Limit muss >= 1 sein."""
        response = test_client.get("/api/live_sessions?limit=0")
        assert response.status_code == 422  # Validation error

    def test_endpoint_validates_limit_max(self, test_client):
        """Test: Limit muss <= 100 sein."""
        response = test_client.get("/api/live_sessions?limit=101")
        assert response.status_code == 422  # Validation error

    def test_health_endpoint(self, test_client):
        """Test: Health-Endpoint funktioniert."""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# =============================================================================
# Tests: Dashboard HTML Rendering
# =============================================================================


class TestDashboardRendering:
    """Tests für das Dashboard HTML-Rendering mit Live-Track-Daten."""

    @pytest.fixture
    def test_client(self):
        """Erstellt einen TestClient für die FastAPI-App."""
        from fastapi.testclient import TestClient
        from src.webui.app import create_app

        app = create_app()
        return TestClient(app)

    def test_dashboard_returns_200(self, test_client):
        """Test: Dashboard gibt 200 zurück."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_dashboard_contains_live_track_section(self, test_client):
        """Test: Dashboard enthält Live-Track-Sektion."""
        response = test_client.get("/")
        assert "Live-Track" in response.text

    def test_dashboard_shows_empty_state(self, test_client):
        """Test: Dashboard zeigt leeren Zustand wenn keine Sessions."""
        response = test_client.get("/")
        # Entweder Sessions vorhanden oder "Keine Live-Sessions gefunden"
        assert (
            "Session(s) geladen" in response.text
            or "Keine Live-Sessions gefunden" in response.text
        )


# =============================================================================
# Tests: Integration mit Live-Session-Registry
# =============================================================================


class TestIntegrationWithRegistry:
    """Integrationstests mit der echten Live-Session-Registry."""

    def test_uses_registry_list_session_records(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: get_recent_live_sessions verwendet list_session_records."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
        )
        from src.webui.live_track import get_recent_live_sessions

        # Session über die echte Registry erstellen
        record = LiveSessionRecord(
            session_id="integration_test_session",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test_env",
            symbol="ETH/USD",
            status="completed",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            finished_at=datetime(2024, 12, 8, 13, 0, 0),
            config={"strategy": "test"},
            metrics={"realized_pnl": 200.0, "max_drawdown": 0.03},
        )
        register_live_session_run(record, base_dir=temp_sessions_dir)

        # Über live_track Service laden
        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert len(sessions) == 1
        assert sessions[0].session_id == "integration_test_session"
        assert sessions[0].mode == "shadow"
        assert sessions[0].realized_pnl == 200.0
        assert sessions[0].max_drawdown == 0.03


# =============================================================================
# Tests: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests für Edge Cases und Grenzfälle."""

    def test_session_with_negative_pnl(self, temp_sessions_dir, sample_session_data):
        """Test: Session mit negativem PnL wird korrekt geladen."""
        from src.webui.live_track import get_recent_live_sessions

        data = sample_session_data.copy()
        data["metrics"]["realized_pnl"] = -50.0
        create_session_file(temp_sessions_dir, data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert sessions[0].realized_pnl == -50.0

    def test_session_with_failed_status(self, temp_sessions_dir, sample_session_data):
        """Test: Session mit 'failed' Status und Error-Message."""
        from src.webui.live_track import get_recent_live_sessions

        data = sample_session_data.copy()
        data["status"] = "failed"
        data["error"] = "Connection timeout"
        create_session_file(temp_sessions_dir, data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert sessions[0].status == "failed"
        assert sessions[0].notes == "Connection timeout"

    def test_session_with_running_status(self, temp_sessions_dir, sample_session_data):
        """Test: Laufende Session ohne finished_at."""
        from src.webui.live_track import get_recent_live_sessions

        data = sample_session_data.copy()
        data["status"] = "started"
        data["finished_at"] = None
        create_session_file(temp_sessions_dir, data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        assert sessions[0].status == "started"
        assert sessions[0].ended_at is None

    def test_very_long_session_id_truncated_in_environment(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Sehr lange Session-IDs werden im Summary erhalten."""
        from src.webui.live_track import get_recent_live_sessions

        long_id = "session_" + "x" * 100
        data = sample_session_data.copy()
        data["session_id"] = long_id
        create_session_file(temp_sessions_dir, data)

        sessions = get_recent_live_sessions(limit=10, base_dir=temp_sessions_dir)

        # Session-ID wird vollständig beibehalten
        assert sessions[0].session_id == long_id


# =============================================================================
# Phase 85 Tests: LiveSessionDetail Model
# =============================================================================


class TestLiveSessionDetailModel:
    """Tests für das LiveSessionDetail Pydantic-Modell (Phase 85)."""

    def test_create_detail_with_all_fields(self):
        """Test: Detail mit allen Feldern erstellen."""
        from src.webui.live_track import LiveSessionDetail

        detail = LiveSessionDetail(
            session_id="detail_test_001",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            ended_at=datetime(2024, 12, 8, 13, 0, 0),
            mode="shadow",
            environment="kraken / BTC/USDT",
            status="completed",
            realized_pnl=150.0,
            max_drawdown=0.05,
            num_orders=10,
            duration_seconds=3600,
            is_live_warning=False,
            run_id="run_123",
            run_type="live_session_shadow",
            env_name="kraken_futures_testnet",
            symbol="BTC/USDT",
            config={"strategy_name": "ma_crossover"},
            metrics={"realized_pnl": 150.0, "num_trades": 5},
            cli_args=["python", "run_session.py", "--mode", "shadow"],
            created_at=datetime(2024, 12, 8, 13, 0, 0),
        )

        assert detail.session_id == "detail_test_001"
        assert detail.run_type == "live_session_shadow"
        assert detail.config == {"strategy_name": "ma_crossover"}
        assert detail.cli_args == ["python", "run_session.py", "--mode", "shadow"]
        assert detail.duration_seconds == 3600
        assert detail.is_live_warning is False

    def test_detail_live_warning_flag(self):
        """Test: Live-Warnung wird korrekt gesetzt."""
        from src.webui.live_track import LiveSessionDetail

        detail = LiveSessionDetail(
            session_id="live_session",
            started_at=datetime.utcnow(),
            mode="live",
            status="completed",
            is_live_warning=True,
        )

        assert detail.is_live_warning is True

    def test_detail_json_serialization(self):
        """Test: Detail kann zu JSON serialisiert werden."""
        from src.webui.live_track import LiveSessionDetail

        detail = LiveSessionDetail(
            session_id="json_test",
            started_at=datetime(2024, 12, 8, 12, 0, 0),
            mode="shadow",
            status="completed",
            config={"key": "value"},
        )

        json_data = detail.model_dump()
        assert json_data["session_id"] == "json_test"
        assert json_data["config"] == {"key": "value"}


# =============================================================================
# Phase 85 Tests: get_filtered_sessions
# =============================================================================


class TestGetFilteredSessions:
    """Tests für get_filtered_sessions (Phase 85)."""

    def test_filter_by_mode(self, temp_sessions_dir, sample_session_data):
        """Test: Filter nach Mode funktioniert."""
        from src.webui.live_track import get_filtered_sessions

        # Shadow-Session erstellen
        shadow_data = sample_session_data.copy()
        shadow_data["session_id"] = "shadow_001"
        shadow_data["mode"] = "shadow"
        create_session_file(temp_sessions_dir, shadow_data, index=0)

        # Testnet-Session erstellen
        testnet_data = sample_session_data.copy()
        testnet_data["session_id"] = "testnet_001"
        testnet_data["mode"] = "testnet"
        create_session_file(temp_sessions_dir, testnet_data, index=1)

        # Nur Shadow filtern
        sessions = get_filtered_sessions(
            limit=10, mode_filter="shadow", base_dir=temp_sessions_dir
        )

        assert len(sessions) == 1
        assert sessions[0].mode == "shadow"

    def test_filter_by_status(self, temp_sessions_dir, sample_session_data):
        """Test: Filter nach Status funktioniert."""
        from src.webui.live_track import get_filtered_sessions

        # Completed-Session
        completed = sample_session_data.copy()
        completed["session_id"] = "completed_001"
        completed["status"] = "completed"
        create_session_file(temp_sessions_dir, completed, index=0)

        # Failed-Session
        failed = sample_session_data.copy()
        failed["session_id"] = "failed_001"
        failed["status"] = "failed"
        create_session_file(temp_sessions_dir, failed, index=1)

        # Nur Failed filtern
        sessions = get_filtered_sessions(
            limit=10, status_filter="failed", base_dir=temp_sessions_dir
        )

        assert len(sessions) == 1
        assert sessions[0].status == "failed"

    def test_filter_combined_mode_and_status(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Kombinierter Filter (Mode + Status)."""
        from src.webui.live_track import get_filtered_sessions

        # Shadow + Completed
        s1 = sample_session_data.copy()
        s1["session_id"] = "shadow_completed"
        s1["mode"] = "shadow"
        s1["status"] = "completed"
        create_session_file(temp_sessions_dir, s1, index=0)

        # Shadow + Failed
        s2 = sample_session_data.copy()
        s2["session_id"] = "shadow_failed"
        s2["mode"] = "shadow"
        s2["status"] = "failed"
        create_session_file(temp_sessions_dir, s2, index=1)

        # Testnet + Completed
        s3 = sample_session_data.copy()
        s3["session_id"] = "testnet_completed"
        s3["mode"] = "testnet"
        s3["status"] = "completed"
        create_session_file(temp_sessions_dir, s3, index=2)

        # Filter: Shadow + Completed
        sessions = get_filtered_sessions(
            limit=10,
            mode_filter="shadow",
            status_filter="completed",
            base_dir=temp_sessions_dir,
        )

        assert len(sessions) == 1
        assert sessions[0].session_id == "shadow_completed"

    def test_no_filter_returns_all(self, temp_sessions_dir, sample_session_data):
        """Test: Ohne Filter werden alle Sessions zurückgegeben."""
        from src.webui.live_track import get_filtered_sessions

        for i in range(3):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i:03d}"
            create_session_file(temp_sessions_dir, data, index=i)

        sessions = get_filtered_sessions(limit=10, base_dir=temp_sessions_dir)

        assert len(sessions) == 3


# =============================================================================
# Phase 85 Tests: get_session_by_id
# =============================================================================


class TestGetSessionById:
    """Tests für get_session_by_id (Phase 85)."""

    def test_find_existing_session(self, temp_sessions_dir, sample_session_data):
        """Test: Existierende Session wird gefunden."""
        from src.webui.live_track import get_session_by_id

        create_session_file(temp_sessions_dir, sample_session_data)

        detail = get_session_by_id(
            "session_20251208_test_001", base_dir=temp_sessions_dir
        )

        assert detail is not None
        assert detail.session_id == "session_20251208_test_001"
        assert detail.mode == "shadow"
        assert detail.config == {"strategy_name": "ma_crossover"}

    def test_nonexistent_session_returns_none(self, temp_sessions_dir):
        """Test: Nicht existierende Session gibt None zurück."""
        from src.webui.live_track import get_session_by_id

        detail = get_session_by_id("nonexistent_id", base_dir=temp_sessions_dir)

        assert detail is None

    def test_detail_includes_all_fields(
        self, temp_sessions_dir, sample_session_data
    ):
        """Test: Detail enthält alle Felder."""
        from src.webui.live_track import get_session_by_id

        create_session_file(temp_sessions_dir, sample_session_data)

        detail = get_session_by_id(
            "session_20251208_test_001", base_dir=temp_sessions_dir
        )

        assert detail.run_type == "live_session_shadow"
        assert detail.env_name == "kraken_futures_testnet"
        assert detail.symbol == "BTC/USDT"
        assert detail.metrics == {
            "realized_pnl": 150.0,
            "max_drawdown": 0.05,
            "num_orders": 10,
        }
        assert detail.cli_args == ["python", "run_session.py"]

    def test_detail_duration_computed(self, temp_sessions_dir, sample_session_data):
        """Test: Duration wird berechnet."""
        from src.webui.live_track import get_session_by_id

        create_session_file(temp_sessions_dir, sample_session_data)

        detail = get_session_by_id(
            "session_20251208_test_001", base_dir=temp_sessions_dir
        )

        # 1 Stunde = 3600 Sekunden
        assert detail.duration_seconds == 3600


# =============================================================================
# Phase 85 Tests: get_session_stats
# =============================================================================


class TestGetSessionStats:
    """Tests für get_session_stats (Phase 85)."""

    def test_stats_empty_registry(self, temp_sessions_dir):
        """Test: Leere Registry gibt Default-Stats zurück."""
        from src.webui.live_track import get_session_stats

        stats = get_session_stats(base_dir=temp_sessions_dir)

        assert stats["total_sessions"] == 0
        assert stats["by_mode"] == {}
        assert stats["by_status"] == {}

    def test_stats_with_sessions(self, temp_sessions_dir, sample_session_data):
        """Test: Stats werden korrekt berechnet."""
        from src.webui.live_track import get_session_stats

        # Mehrere Sessions erstellen
        for i in range(3):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i:03d}"
            data["mode"] = "shadow" if i < 2 else "testnet"
            create_session_file(temp_sessions_dir, data, index=i)

        stats = get_session_stats(base_dir=temp_sessions_dir)

        assert stats["total_sessions"] == 3
        assert stats["by_mode"]["shadow"] == 2
        assert stats["by_mode"]["testnet"] == 1

    def test_stats_total_pnl(self, temp_sessions_dir, sample_session_data):
        """Test: Total PnL wird summiert."""
        from src.webui.live_track import get_session_stats

        for i, pnl in enumerate([100.0, 50.0, -30.0]):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i:03d}"
            data["metrics"]["realized_pnl"] = pnl
            create_session_file(temp_sessions_dir, data, index=i)

        stats = get_session_stats(base_dir=temp_sessions_dir)

        assert stats["total_pnl"] == 120.0  # 100 + 50 - 30


# =============================================================================
# Phase 85 Tests: API Endpoints
# =============================================================================


class TestPhase85ApiEndpoints:
    """Tests für die neuen Phase 85 API-Endpoints."""

    @pytest.fixture
    def test_client(self):
        """Erstellt einen TestClient für die FastAPI-App."""
        from fastapi.testclient import TestClient
        from src.webui.app import create_app

        app = create_app()
        return TestClient(app)

    def test_filter_endpoint_accepts_mode(self, test_client):
        """Test: /api/live_sessions akzeptiert mode-Parameter."""
        response = test_client.get("/api/live_sessions?mode=shadow")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_endpoint_accepts_status(self, test_client):
        """Test: /api/live_sessions akzeptiert status-Parameter."""
        response = test_client.get("/api/live_sessions?status=completed")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_endpoint_combined(self, test_client):
        """Test: /api/live_sessions akzeptiert beide Parameter."""
        response = test_client.get(
            "/api/live_sessions?mode=shadow&status=completed&limit=5"
        )
        assert response.status_code == 200

    def test_stats_endpoint(self, test_client):
        """Test: /api/live_sessions/stats Endpoint."""
        response = test_client.get("/api/live_sessions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "by_mode" in data
        assert "by_status" in data

    def test_detail_endpoint_not_found(self, test_client):
        """Test: /api/live_sessions/{id} gibt 404 wenn nicht gefunden."""
        response = test_client.get("/api/live_sessions/nonexistent_session_id")
        assert response.status_code == 404

    def test_session_detail_page_not_found(self, test_client):
        """Test: /session/{id} gibt 404 wenn nicht gefunden."""
        response = test_client.get("/session/nonexistent_session_id")
        assert response.status_code == 404


# =============================================================================
# Phase 85 Tests: Dashboard with Filters
# =============================================================================


class TestDashboardWithFilters:
    """Tests für Dashboard mit Filter-UI (Phase 85)."""

    @pytest.fixture
    def test_client(self):
        """Erstellt einen TestClient für die FastAPI-App."""
        from fastapi.testclient import TestClient
        from src.webui.app import create_app

        app = create_app()
        return TestClient(app)

    def test_dashboard_accepts_mode_filter(self, test_client):
        """Test: Dashboard akzeptiert mode Query-Parameter."""
        response = test_client.get("/?mode=shadow")
        assert response.status_code == 200
        assert "shadow" in response.text.lower()

    def test_dashboard_accepts_status_filter(self, test_client):
        """Test: Dashboard akzeptiert status Query-Parameter."""
        response = test_client.get("/?status=completed")
        assert response.status_code == 200

    def test_dashboard_contains_filter_ui(self, test_client):
        """Test: Dashboard enthält Filter-UI."""
        response = test_client.get("/")
        assert response.status_code == 200
        # Filter-Links sollten vorhanden sein
        assert "Filter" in response.text

    def test_dashboard_session_explorer_title(self, test_client):
        """Test: Dashboard zeigt Session Explorer Titel."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "Session Explorer" in response.text


# =============================================================================
# Phase 85 Tests: compute_duration_seconds
# =============================================================================


class TestComputeDurationSeconds:
    """Tests für compute_duration_seconds Helper (Phase 85)."""

    def test_duration_one_hour(self):
        """Test: 1 Stunde Dauer."""
        from src.webui.live_track import compute_duration_seconds

        start = datetime(2024, 12, 8, 12, 0, 0)
        end = datetime(2024, 12, 8, 13, 0, 0)

        duration = compute_duration_seconds(start, end)
        assert duration == 3600

    def test_duration_with_none_start(self):
        """Test: None start gibt None zurück."""
        from src.webui.live_track import compute_duration_seconds

        duration = compute_duration_seconds(None, datetime.utcnow())
        assert duration is None

    def test_duration_with_none_end(self):
        """Test: None end gibt None zurück."""
        from src.webui.live_track import compute_duration_seconds

        duration = compute_duration_seconds(datetime.utcnow(), None)
        assert duration is None

    def test_duration_short_session(self):
        """Test: Kurze Session (5 Minuten)."""
        from src.webui.live_track import compute_duration_seconds

        start = datetime(2024, 12, 8, 12, 0, 0)
        end = datetime(2024, 12, 8, 12, 5, 0)

        duration = compute_duration_seconds(start, end)
        assert duration == 300
