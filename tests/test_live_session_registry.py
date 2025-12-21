# tests/test_live_session_registry.py
"""
Tests für Live Session Registry (Phase 81).

Testet die Integration von Live-/Paper-/Shadow-/Testnet-Sessions
in das JSON-basierte Registry-System.

Komponenten:
- LiveSessionRecord Dataclass (mit session_id, run_id, started_at, etc.)
- register_live_session_run() Helper
- list_session_records() Query-Funktion
- get_session_summary() Aggregation
- Markdown/HTML Report Renderer

Run:
    pytest tests/test_live_session_registry.py -v
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest


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
def sample_record() -> "LiveSessionRecord":
    """Erstellt einen Sample LiveSessionRecord."""
    from src.experiments.live_session_registry import LiveSessionRecord

    return LiveSessionRecord(
        session_id="session_20251208_001",
        run_id="experiment_run_123",
        run_type="live_session_shadow",
        mode="shadow",
        env_name="kraken_futures_testnet",
        symbol="BTC/USDT",
        status="completed",
        started_at=datetime(2024, 12, 8, 12, 0, 0),
        finished_at=datetime(2024, 12, 8, 13, 0, 0),
        config={
            "strategy_name": "ma_crossover",
            "timeframe": "1m",
            "warmup_candles": 200,
        },
        metrics={
            "realized_pnl": 150.0,
            "max_drawdown": 0.05,
            "num_orders": 10,
            "num_trades": 8,
        },
        cli_args=["python", "scripts/run_execution_session.py", "--mode", "shadow"],
        error=None,
    )


@pytest.fixture
def sample_record_dict() -> Dict[str, Any]:
    """Erstellt ein Sample-Record als Dict."""
    return {
        "session_id": "session_20251208_001",
        "run_id": "experiment_run_123",
        "run_type": "live_session_shadow",
        "mode": "shadow",
        "env_name": "kraken_futures_testnet",
        "symbol": "BTC/USDT",
        "status": "completed",
        "started_at": "2024-12-08T12:00:00",
        "finished_at": "2024-12-08T13:00:00",
        "config": {
            "strategy_name": "ma_crossover",
            "timeframe": "1m",
        },
        "metrics": {
            "realized_pnl": 150.0,
            "max_drawdown": 0.05,
        },
        "cli_args": ["python", "run_session.py", "--mode", "shadow"],
        "error": None,
        "created_at": "2024-12-08T13:00:00",
    }


# =============================================================================
# Test 1: test_live_session_record_roundtrip_dict
# =============================================================================


class TestLiveSessionRecordRoundtrip:
    """Tests für LiveSessionRecord Roundtrip (to_dict / from_dict)."""

    def test_live_session_record_roundtrip_dict(self, sample_record):
        """
        Test: LiveSessionRecord.from_dict(record.to_dict()) ergibt äquivalentes Objekt.
        """
        from src.experiments.live_session_registry import LiveSessionRecord

        # to_dict
        data = sample_record.to_dict()

        # Verify dict structure
        assert data["session_id"] == "session_20251208_001"
        assert data["run_id"] == "experiment_run_123"
        assert data["run_type"] == "live_session_shadow"
        assert data["mode"] == "shadow"
        assert data["env_name"] == "kraken_futures_testnet"
        assert data["symbol"] == "BTC/USDT"
        assert data["status"] == "completed"
        assert "started_at" in data
        assert "finished_at" in data
        assert data["config"]["strategy_name"] == "ma_crossover"
        assert data["metrics"]["realized_pnl"] == 150.0
        assert data["cli_args"] == [
            "python",
            "scripts/run_execution_session.py",
            "--mode",
            "shadow",
        ]

        # from_dict
        restored = LiveSessionRecord.from_dict(data)

        # Verify restored object matches original
        assert restored.session_id == sample_record.session_id
        assert restored.run_id == sample_record.run_id
        assert restored.run_type == sample_record.run_type
        assert restored.mode == sample_record.mode
        assert restored.env_name == sample_record.env_name
        assert restored.symbol == sample_record.symbol
        assert restored.status == sample_record.status
        assert restored.started_at == sample_record.started_at
        assert restored.finished_at == sample_record.finished_at
        assert dict(restored.config) == dict(sample_record.config)
        assert dict(restored.metrics) == dict(sample_record.metrics)
        assert list(restored.cli_args) == list(sample_record.cli_args)
        assert restored.error == sample_record.error

    def test_roundtrip_with_none_values(self):
        """Test: Roundtrip mit None-Werten funktioniert."""
        from src.experiments.live_session_registry import LiveSessionRecord

        record = LiveSessionRecord(
            session_id="session_minimal",
            run_id=None,
            run_type="live_session_testnet",
            mode="testnet",
            env_name="",
            symbol="ETH/EUR",
            status="started",
            started_at=datetime(2024, 12, 8, 10, 0, 0),
            finished_at=None,
            config={},
            metrics={},
            cli_args=[],
            error=None,
        )

        data = record.to_dict()
        restored = LiveSessionRecord.from_dict(data)

        assert restored.session_id == "session_minimal"
        assert restored.run_id is None
        assert restored.finished_at is None
        assert restored.error is None


# =============================================================================
# Test 2: test_register_live_session_run_writes_json
# =============================================================================


class TestRegisterLiveSessionRunWritesJson:
    """Tests für register_live_session_run() JSON-Schreibfunktion."""

    def test_register_live_session_run_writes_json(self, sample_record, temp_sessions_dir):
        """
        Test: register_live_session_run() schreibt JSON-Datei.
        """
        from src.experiments.live_session_registry import register_live_session_run

        # Registriere Session
        path = register_live_session_run(sample_record, base_dir=temp_sessions_dir)

        # Prüfe, dass genau eine .json-Datei existiert
        json_files = list(temp_sessions_dir.glob("*.json"))
        assert len(json_files) == 1

        # Lade JSON und prüfe Felder
        with path.open("r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["session_id"] == "session_20251208_001"
        assert saved_data["run_type"] == "live_session_shadow"
        assert saved_data["metrics"]["realized_pnl"] == 150.0
        assert saved_data["metrics"]["max_drawdown"] == 0.05
        assert saved_data["config"]["strategy_name"] == "ma_crossover"
        assert saved_data["status"] == "completed"

    def test_register_creates_directory_if_missing(self, tmp_path):
        """Test: Verzeichnis wird erstellt falls nicht vorhanden."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
        )

        non_existent_dir = tmp_path / "new_dir" / "sessions"
        assert not non_existent_dir.exists()

        record = LiveSessionRecord(
            session_id="session_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test_env",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
        )

        path = register_live_session_run(record, base_dir=non_existent_dir)

        assert non_existent_dir.exists()
        assert path.exists()

    def test_filename_format(self, sample_record, temp_sessions_dir):
        """Test: Dateiname hat korrektes Format."""
        from src.experiments.live_session_registry import register_live_session_run

        path = register_live_session_run(sample_record, base_dir=temp_sessions_dir)

        # Format: <timestamp>_<run_type>_<session_id>.json
        filename = path.name
        assert filename.endswith(".json")
        assert "live_session_shadow" in filename
        assert "session_20251208_001" in filename


# =============================================================================
# Test 3: test_list_session_records_filters_and_limit
# =============================================================================


class TestListSessionRecordsFiltersAndLimit:
    """Tests für list_session_records() Filter und Limit."""

    def test_list_session_records_filters_and_limit(self, temp_sessions_dir):
        """
        Test: list_session_records() filtert nach run_type, status und limit.
        """
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            list_session_records,
        )

        # Erstelle mehrere Records mit unterschiedlichen run_type / status
        base_time = datetime(2024, 12, 8, 10, 0, 0)

        records_to_create = [
            # Shadow, completed
            ("session_001", "live_session_shadow", "shadow", "completed"),
            ("session_002", "live_session_shadow", "shadow", "completed"),
            ("session_003", "live_session_shadow", "shadow", "failed"),
            # Testnet, completed
            ("session_004", "live_session_testnet", "testnet", "completed"),
            ("session_005", "live_session_testnet", "testnet", "aborted"),
        ]

        for i, (sid, rtype, mode, status) in enumerate(records_to_create):
            record = LiveSessionRecord(
                session_id=sid,
                run_id=None,
                run_type=rtype,
                mode=mode,
                env_name="test_env",
                symbol="BTC/USD",
                status=status,
                started_at=base_time + timedelta(minutes=i),
            )
            register_live_session_run(record, base_dir=temp_sessions_dir)

        # Test: Filter nach run_type="live_session_shadow"
        shadow_records = list_session_records(
            base_dir=temp_sessions_dir, run_type="live_session_shadow"
        )
        assert len(shadow_records) == 3
        assert all(r.run_type == "live_session_shadow" for r in shadow_records)

        # Test: Filter nach status="completed"
        completed_records = list_session_records(base_dir=temp_sessions_dir, status="completed")
        assert len(completed_records) == 3
        assert all(r.status == "completed" for r in completed_records)

        # Test: Limit=1 gibt nur einen Record zurück
        limited_records = list_session_records(base_dir=temp_sessions_dir, limit=1)
        assert len(limited_records) == 1

        # Test: Kombination von Filtern
        shadow_completed = list_session_records(
            base_dir=temp_sessions_dir,
            run_type="live_session_shadow",
            status="completed",
        )
        assert len(shadow_completed) == 2

    def test_list_returns_newest_first(self, temp_sessions_dir):
        """Test: Records werden nach Timestamp sortiert (neueste zuerst)."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            list_session_records,
        )

        # Erstelle Records mit unterschiedlichen Timestamps
        for i in range(3):
            record = LiveSessionRecord(
                session_id=f"session_{i:03d}",
                run_id=None,
                run_type="live_session_shadow",
                mode="shadow",
                env_name="test",
                symbol="BTC/USD",
                status="completed",
                started_at=datetime(2024, 12, 8, 10 + i, 0, 0),
            )
            register_live_session_run(record, base_dir=temp_sessions_dir)

        records = list_session_records(base_dir=temp_sessions_dir)

        # Neueste zuerst (session_002 hat höchsten Timestamp)
        assert records[0].session_id == "session_002"

    def test_list_empty_directory(self, temp_sessions_dir):
        """Test: Leeres Verzeichnis gibt leere Liste zurück."""
        from src.experiments.live_session_registry import list_session_records

        records = list_session_records(base_dir=temp_sessions_dir)
        assert records == []

    def test_list_nonexistent_directory(self, tmp_path):
        """Test: Nicht existierendes Verzeichnis gibt leere Liste zurück."""
        from src.experiments.live_session_registry import list_session_records

        records = list_session_records(base_dir=tmp_path / "nonexistent")
        assert records == []

    def test_list_skips_corrupted_files(self, temp_sessions_dir):
        """Test: Beschädigte JSON-Dateien werden übersprungen."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            list_session_records,
        )

        # Gültigen Record erstellen
        record = LiveSessionRecord(
            session_id="valid_session",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
        )
        register_live_session_run(record, base_dir=temp_sessions_dir)

        # Beschädigte JSON-Datei erstellen
        corrupted_file = temp_sessions_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json content")

        # list_session_records sollte nur den gültigen Record zurückgeben
        records = list_session_records(base_dir=temp_sessions_dir)
        assert len(records) == 1
        assert records[0].session_id == "valid_session"


# =============================================================================
# Test 4: test_get_session_summary_basic
# =============================================================================


class TestGetSessionSummaryBasic:
    """Tests für get_session_summary() Aggregation."""

    def test_get_session_summary_basic(self, temp_sessions_dir):
        """
        Test: get_session_summary() berechnet korrekte Aggregationen.
        """
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            get_session_summary,
        )

        # Erstelle 3 Records mit metrics
        records_data = [
            {
                "session_id": "session_001",
                "status": "completed",
                "metrics": {"realized_pnl": 100.0, "max_drawdown": 0.03},
            },
            {
                "session_id": "session_002",
                "status": "completed",
                "metrics": {"realized_pnl": 50.0, "max_drawdown": 0.06},
            },
            {
                "session_id": "session_003",
                "status": "failed",
                "metrics": {"realized_pnl": -30.0, "max_drawdown": 0.09},
            },
        ]

        for i, data in enumerate(records_data):
            record = LiveSessionRecord(
                session_id=data["session_id"],
                run_id=None,
                run_type="live_session_shadow",
                mode="shadow",
                env_name="test",
                symbol="BTC/USD",
                status=data["status"],
                started_at=datetime(2024, 12, 8, 10 + i, 0, 0),
                metrics=data["metrics"],
            )
            register_live_session_run(record, base_dir=temp_sessions_dir)

        # Summary abrufen
        summary = get_session_summary(base_dir=temp_sessions_dir)

        # num_sessions stimmt
        assert summary["num_sessions"] == 3

        # total_realized_pnl ist Summe: 100 + 50 + (-30) = 120
        assert summary["total_realized_pnl"] == 120.0

        # avg_max_drawdown ist Mittelwert: (0.03 + 0.06 + 0.09) / 3 = 0.06
        assert abs(summary["avg_max_drawdown"] - 0.06) < 0.001

        # by_status zählt korrekt
        assert summary["by_status"]["completed"] == 2
        assert summary["by_status"]["failed"] == 1

        # first/last started_at sind vorhanden
        assert "first_started_at" in summary
        assert "last_started_at" in summary

    def test_summary_empty_directory(self, temp_sessions_dir):
        """Test: Summary für leeres Verzeichnis."""
        from src.experiments.live_session_registry import get_session_summary

        summary = get_session_summary(base_dir=temp_sessions_dir)

        assert summary["num_sessions"] == 0
        assert summary["by_status"] == {}
        assert summary["total_realized_pnl"] == 0.0
        assert summary["avg_max_drawdown"] == 0.0

    def test_summary_with_run_type_filter(self, temp_sessions_dir):
        """Test: Summary mit run_type Filter."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            get_session_summary,
        )

        # Shadow-Records
        for i in range(2):
            record = LiveSessionRecord(
                session_id=f"shadow_{i}",
                run_id=None,
                run_type="live_session_shadow",
                mode="shadow",
                env_name="test",
                symbol="BTC/USD",
                status="completed",
                started_at=datetime(2024, 12, 8, 10 + i, 0, 0),
                metrics={"realized_pnl": 100.0},
            )
            register_live_session_run(record, base_dir=temp_sessions_dir)

        # Testnet-Record
        record = LiveSessionRecord(
            session_id="testnet_0",
            run_id=None,
            run_type="live_session_testnet",
            mode="testnet",
            env_name="test",
            symbol="ETH/USD",
            status="completed",
            started_at=datetime(2024, 12, 8, 15, 0, 0),
            metrics={"realized_pnl": 50.0},
        )
        register_live_session_run(record, base_dir=temp_sessions_dir)

        # Summary nur für Shadow
        shadow_summary = get_session_summary(
            base_dir=temp_sessions_dir, run_type="live_session_shadow"
        )
        assert shadow_summary["num_sessions"] == 2
        assert shadow_summary["total_realized_pnl"] == 200.0


# =============================================================================
# Test 5: test_registry_failure_does_not_raise_if_caught_in_caller
# =============================================================================


class TestRegistryFailureHandling:
    """Tests für Safety-Design: Registry-Fehler brechen Sessions nicht."""

    def test_registry_failure_does_not_raise_if_caught_in_caller(self, sample_record, tmp_path):
        """
        Test: Wenn register_live_session_run() fehlschlägt (z.B. IO-Fehler),
        kann der Caller die Exception abfangen und die Session fortsetzen.
        """
        from src.experiments.live_session_registry import register_live_session_run

        # Simuliere einen IO-Fehler durch ein ungültiges Verzeichnis
        # (z.B. als Datei statt Verzeichnis)
        fake_dir = tmp_path / "fake_file"
        fake_dir.write_text("I am a file, not a directory")

        # register_live_session_run sollte eine Exception werfen
        with pytest.raises(Exception):
            register_live_session_run(sample_record, base_dir=fake_dir)

    def test_safe_registration_pattern(self, sample_record, tmp_path):
        """
        Test: Demonstriert das Safety-Pattern aus run_execution_session.py.
        """
        from src.experiments.live_session_registry import register_live_session_run

        # Simuliere das Safety-Pattern
        registry_error = None
        registry_path = None

        try:
            # Versuche zu registrieren (mit gültigem Pfad)
            registry_path = register_live_session_run(sample_record, base_dir=tmp_path / "sessions")
        except Exception as e:
            # Registry-Fehler nur loggen, nicht weitergeben
            registry_error = str(e)

        # Session läuft weiter, auch wenn Registry fehlschlägt
        assert registry_error is None
        assert registry_path is not None

    def test_safe_registration_pattern_with_mock_failure(self, sample_record):
        """
        Test: Registry-Fehler werden abgefangen, Session läuft weiter.
        """
        from src.experiments.live_session_registry import register_live_session_run

        # Mock den IO-Fehler
        with patch(
            "src.experiments.live_session_registry._ensure_dir",
            side_effect=PermissionError("No permission"),
        ):
            registry_error = None
            registry_path = None

            try:
                registry_path = register_live_session_run(sample_record)
            except Exception as e:
                registry_error = str(e)

            # Der Fehler wurde geworfen (wie erwartet)
            assert registry_error is not None
            assert "No permission" in registry_error
            assert registry_path is None


# =============================================================================
# Tests: Markdown/HTML Renderer
# =============================================================================


class TestReportRenderers:
    """Tests für Markdown und HTML Report Renderer."""

    def test_render_session_markdown(self, sample_record):
        """Test: render_session_markdown() erzeugt gültigen Markdown."""
        from src.experiments.live_session_registry import render_session_markdown

        md = render_session_markdown(sample_record)

        assert "# Live-Session session_20251208_001" in md
        assert "**Run-Type:** `live_session_shadow`" in md
        assert "**Mode:** `shadow`" in md
        assert "**Status:** `completed`" in md
        assert "**Symbol:** `BTC/USDT`" in md
        assert "## Config" in md
        assert "## Metrics" in md
        assert '"realized_pnl": 150.0' in md
        assert "## CLI-Aufruf" in md

    def test_render_session_markdown_with_error(self):
        """Test: Markdown mit Fehler-Block."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            render_session_markdown,
        )

        record = LiveSessionRecord(
            session_id="error_session",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="failed",
            started_at=datetime.utcnow(),
            error="Connection timeout",
        )

        md = render_session_markdown(record)
        assert "**Error:** `Connection timeout`" in md

    def test_render_sessions_markdown_empty(self):
        """Test: Markdown für leere Liste."""
        from src.experiments.live_session_registry import render_sessions_markdown

        md = render_sessions_markdown([])
        assert "Keine Sessions gefunden" in md

    def test_render_sessions_markdown_multiple(self, sample_record):
        """Test: Markdown für mehrere Sessions."""
        from src.experiments.live_session_registry import render_sessions_markdown

        md = render_sessions_markdown([sample_record, sample_record])
        assert md.count("# Live-Session") >= 2
        assert "---" in md

    def test_render_session_html(self, sample_record):
        """Test: render_session_html() erzeugt gültiges HTML."""
        from src.experiments.live_session_registry import render_session_html

        html_content = render_session_html(sample_record)

        assert "<!DOCTYPE html>" in html_content
        assert "<title>Live-Session session_20251208_001</title>" in html_content
        assert "<h1>Live-Session session_20251208_001</h1>" in html_content
        assert "live_session_shadow" in html_content
        assert "BTC/USDT" in html_content
        assert "Config" in html_content
        assert "Metrics" in html_content

    def test_render_sessions_html_empty(self):
        """Test: HTML für leere Liste."""
        from src.experiments.live_session_registry import render_sessions_html

        html_content = render_sessions_html([])
        assert "Keine Sessions gefunden" in html_content

    def test_render_sessions_html_table(self, sample_record):
        """Test: HTML-Tabelle für mehrere Sessions."""
        from src.experiments.live_session_registry import render_sessions_html

        html_content = render_sessions_html([sample_record, sample_record])
        assert "<table>" in html_content
        assert "<tr>" in html_content


# =============================================================================
# Tests: Constants
# =============================================================================


class TestConstants:
    """Tests für Modul-Konstanten."""

    def test_run_type_constants(self):
        """Test: Run-Type-Konstanten sind definiert."""
        from src.experiments.live_session_registry import (
            RUN_TYPE_LIVE_SESSION,
            RUN_TYPE_LIVE_SESSION_SHADOW,
            RUN_TYPE_LIVE_SESSION_TESTNET,
            RUN_TYPE_LIVE_SESSION_PAPER,
            RUN_TYPE_LIVE_SESSION_LIVE,
        )

        assert RUN_TYPE_LIVE_SESSION == "live_session"
        assert RUN_TYPE_LIVE_SESSION_SHADOW == "live_session_shadow"
        assert RUN_TYPE_LIVE_SESSION_TESTNET == "live_session_testnet"
        assert RUN_TYPE_LIVE_SESSION_PAPER == "live_session_paper"
        assert RUN_TYPE_LIVE_SESSION_LIVE == "live_session_live"

    def test_status_constants(self):
        """Test: Status-Konstanten sind definiert."""
        from src.experiments.live_session_registry import (
            STATUS_STARTED,
            STATUS_COMPLETED,
            STATUS_FAILED,
            STATUS_ABORTED,
        )

        assert STATUS_STARTED == "started"
        assert STATUS_COMPLETED == "completed"
        assert STATUS_FAILED == "failed"
        assert STATUS_ABORTED == "aborted"

    def test_default_sessions_dir(self):
        """Test: Default-Verzeichnis ist definiert."""
        from src.experiments.live_session_registry import DEFAULT_LIVE_SESSION_DIR

        assert DEFAULT_LIVE_SESSION_DIR == Path("reports/experiments/live_sessions")


# =============================================================================
# Tests: Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests für Helper-Funktionen."""

    def test_generate_session_run_id(self):
        """Test: generate_session_run_id() erzeugt eindeutige IDs."""
        from src.experiments.live_session_registry import generate_session_run_id

        id1 = generate_session_run_id("shadow")
        id2 = generate_session_run_id("shadow")

        assert id1 != id2
        assert "shadow" in id1
        assert "session_" in id1

    def test_generate_session_run_id_modes(self):
        """Test: generate_session_run_id() mit verschiedenen Modes."""
        from src.experiments.live_session_registry import generate_session_run_id

        shadow_id = generate_session_run_id("shadow")
        testnet_id = generate_session_run_id("testnet")

        assert "shadow" in shadow_id
        assert "testnet" in testnet_id

    def test_load_session_record(self, sample_record, temp_sessions_dir):
        """Test: load_session_record() lädt JSON korrekt."""
        from src.experiments.live_session_registry import (
            register_live_session_run,
            load_session_record,
        )

        # Speichere Record
        path = register_live_session_run(sample_record, base_dir=temp_sessions_dir)

        # Lade Record
        loaded = load_session_record(path)

        assert loaded.session_id == sample_record.session_id
        assert loaded.run_type == sample_record.run_type
        assert loaded.symbol == sample_record.symbol


# =============================================================================
# Tests: Export from __init__.py
# =============================================================================


class TestExports:
    """Tests für Exports aus dem experiments Package."""

    def test_exports_from_experiments_package(self):
        """Test: Alle Phase-81-Komponenten werden exportiert."""
        from src.experiments import (
            LiveSessionRecord,
            register_live_session_run,
            load_session_record,
            list_session_records,
            get_session_summary,
            generate_session_run_id,
            DEFAULT_LIVE_SESSION_DIR,
            RUN_TYPE_LIVE_SESSION,
            RUN_TYPE_LIVE_SESSION_SHADOW,
            RUN_TYPE_LIVE_SESSION_TESTNET,
        )

        # Alle Imports sollten funktionieren
        assert LiveSessionRecord is not None
        assert register_live_session_run is not None
        assert list_session_records is not None
        assert get_session_summary is not None
        assert DEFAULT_LIVE_SESSION_DIR is not None


# =============================================================================
# Tests: Strategy Tier Support
# =============================================================================


class TestStrategyTierSupport:
    """Tests für Strategy-Tier-Unterstützung in LiveSessionRecord."""

    def test_strategy_tier_field_exists(self):
        """Test: strategy_tier Feld existiert in LiveSessionRecord."""
        from src.experiments.live_session_registry import LiveSessionRecord

        record = LiveSessionRecord(
            session_id="tier_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            strategy_tier="core",
        )

        assert record.strategy_tier == "core"

    def test_strategy_tier_default_is_none(self):
        """Test: strategy_tier ist standardmäßig None."""
        from src.experiments.live_session_registry import LiveSessionRecord

        record = LiveSessionRecord(
            session_id="tier_default_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
        )

        assert record.strategy_tier is None

    def test_strategy_tier_r_and_d(self):
        """Test: R&D-Tier wird korrekt gespeichert."""
        from src.experiments.live_session_registry import LiveSessionRecord

        record = LiveSessionRecord(
            session_id="rnd_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            config={"strategy_name": "armstrong_cycle"},
            strategy_tier="r_and_d",
        )

        assert record.strategy_tier == "r_and_d"

    def test_strategy_tier_roundtrip(self):
        """Test: strategy_tier wird bei to_dict/from_dict erhalten."""
        from src.experiments.live_session_registry import LiveSessionRecord

        record = LiveSessionRecord(
            session_id="tier_roundtrip",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            strategy_tier="r_and_d",
        )

        data = record.to_dict()
        assert data["strategy_tier"] == "r_and_d"

        restored = LiveSessionRecord.from_dict(data)
        assert restored.strategy_tier == "r_and_d"

    def test_strategy_tier_in_json(self, temp_sessions_dir):
        """Test: strategy_tier wird in JSON-Datei gespeichert."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
        )

        record = LiveSessionRecord(
            session_id="tier_json_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            strategy_tier="aux",
        )

        path = register_live_session_run(record, base_dir=temp_sessions_dir)

        with path.open("r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["strategy_tier"] == "aux"

    def test_summary_includes_by_tier(self, temp_sessions_dir):
        """Test: get_session_summary() enthält by_tier."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            get_session_summary,
        )

        # Core-Session
        record1 = LiveSessionRecord(
            session_id="core_session",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime(2024, 12, 8, 10, 0, 0),
            strategy_tier="core",
            metrics={"realized_pnl": 100.0},
        )
        register_live_session_run(record1, base_dir=temp_sessions_dir)

        # R&D-Session
        record2 = LiveSessionRecord(
            session_id="rnd_session",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime(2024, 12, 8, 11, 0, 0),
            strategy_tier="r_and_d",
            config={"strategy_name": "armstrong_cycle"},
            metrics={"realized_pnl": 50.0},
        )
        register_live_session_run(record2, base_dir=temp_sessions_dir)

        summary = get_session_summary(base_dir=temp_sessions_dir)

        assert "by_tier" in summary
        assert summary["by_tier"]["core"] == 1
        assert summary["by_tier"]["r_and_d"] == 1

    def test_summary_includes_r_and_d_summary(self, temp_sessions_dir):
        """Test: get_session_summary() enthält r_and_d_summary wenn R&D-Sessions vorhanden."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            get_session_summary,
        )

        # R&D-Sessions erstellen
        for i in range(2):
            record = LiveSessionRecord(
                session_id=f"rnd_session_{i}",
                run_id=None,
                run_type="live_session_shadow",
                mode="shadow",
                env_name="test",
                symbol="BTC/USD",
                status="completed",
                started_at=datetime(2024, 12, 8, 10 + i, 0, 0),
                strategy_tier="r_and_d",
                config={"strategy_name": f"research_strategy_{i}"},
                metrics={"realized_pnl": 100.0 * (i + 1)},
            )
            register_live_session_run(record, base_dir=temp_sessions_dir)

        summary = get_session_summary(base_dir=temp_sessions_dir)

        assert "r_and_d_summary" in summary
        assert summary["r_and_d_summary"]["num_sessions"] == 2
        assert summary["r_and_d_summary"]["total_realized_pnl"] == 300.0  # 100 + 200
        assert "notice" in summary["r_and_d_summary"]

    def test_render_markdown_includes_tier(self):
        """Test: render_session_markdown() zeigt Tier-Information."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            render_session_markdown,
        )

        record = LiveSessionRecord(
            session_id="markdown_tier_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            strategy_tier="core",
        )

        md = render_session_markdown(record)
        assert "Strategy Tier" in md
        assert "Core" in md

    def test_render_markdown_r_and_d_warning(self):
        """Test: render_session_markdown() zeigt R&D-Warnung."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            render_session_markdown,
        )

        record = LiveSessionRecord(
            session_id="rnd_markdown_test",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="test",
            symbol="BTC/USD",
            status="completed",
            started_at=datetime.utcnow(),
            strategy_tier="r_and_d",
        )

        md = render_session_markdown(record)
        assert "R&D / Research" in md
        assert "R&D-Strategie" in md or "Research" in md


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integrationstests für den kompletten Workflow."""

    def test_full_workflow(self, temp_sessions_dir):
        """Test: Kompletter Workflow - Registrieren, Laden, Abfragen, Summary."""
        from src.experiments.live_session_registry import (
            LiveSessionRecord,
            register_live_session_run,
            load_session_record,
            list_session_records,
            get_session_summary,
            render_session_markdown,
        )

        # 1. Records erstellen und registrieren
        records = []
        for i in range(3):
            record = LiveSessionRecord(
                session_id=f"integration_session_{i}",
                run_id=f"run_{i}",
                run_type="live_session_shadow",
                mode="shadow",
                env_name="test_env",
                symbol="BTC/USD",
                status="completed" if i < 2 else "failed",
                started_at=datetime(2024, 12, 8, 10 + i, 0, 0),
                finished_at=datetime(2024, 12, 8, 11 + i, 0, 0),
                config={"strategy_name": "ma_crossover", "timeframe": "1m"},
                metrics={
                    "realized_pnl": 100.0 * (i + 1),
                    "max_drawdown": 0.01 * (i + 1),
                },
                cli_args=["python", "run.py", f"--session={i}"],
            )
            path = register_live_session_run(record, base_dir=temp_sessions_dir)
            records.append((record, path))

        # 2. Records laden
        for record, path in records:
            loaded = load_session_record(path)
            assert loaded.session_id == record.session_id

        # 3. Records auflisten
        all_records = list_session_records(base_dir=temp_sessions_dir)
        assert len(all_records) == 3

        completed = list_session_records(base_dir=temp_sessions_dir, status="completed")
        assert len(completed) == 2

        # 4. Summary abrufen
        summary = get_session_summary(base_dir=temp_sessions_dir)
        assert summary["num_sessions"] == 3
        assert summary["total_realized_pnl"] == 600.0  # 100 + 200 + 300
        assert summary["by_status"]["completed"] == 2
        assert summary["by_status"]["failed"] == 1

        # 5. Markdown rendern
        md = render_session_markdown(all_records[0])
        assert "# Live-Session" in md
        assert "integration_session" in md
