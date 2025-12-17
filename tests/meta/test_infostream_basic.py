"""
InfoStream v1 – Smoke-Tests.

Testet die grundlegende Funktionalität des InfoStream-Systems:
- Models (IntelEvent, IntelEval, LearningSnippet)
- Collector (build_event_from_test_health_report, save_intel_event)
- Evaluator (render_event_as_infopacket, parse_eval_package, parse_learning_snippet)
- Router (append_learnings_to_log)
- Run-Cycle (run_infostream_cycle mit Mock-Client)

Verwendung:
    pytest tests/meta/test_infostream_basic.py -v
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.meta.infostream.collector import (
    build_event_from_test_health_report,
    load_intel_event,
    save_intel_event,
)
from src.meta.infostream.evaluator import (
    call_ai_for_event,
    parse_eval_package,
    parse_learning_snippet,
    render_event_as_infopacket,
)
from src.meta.infostream.models import IntelEval, IntelEvent, LearningSnippet
from src.meta.infostream.router import append_learnings_to_log, get_learning_log_stats
from src.meta.infostream.run_cycle import discover_test_health_runs, run_infostream_cycle

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_summary_json() -> dict[str, Any]:
    """Minimal-JSON für summary.json (TestHealthSummary-Struktur)."""
    return {
        "profile_name": "daily_quick",
        "health_score": 85.0,
        "passed_checks": 8,
        "failed_checks": 2,
        "skipped_checks": 0,
        "started_at": "2025-12-11T14:39:20",
        "finished_at": "2025-12-11T14:40:00",
        "trigger_violations": [
            {
                "severity": "warning",
                "trigger_name": "min_total_runs",
                "message": "Zu wenige Runs",
            }
        ],
        "strategy_coverage": {"enabled": True, "is_healthy": True},
        "switch_sanity": {"enabled": True, "is_ok": True},
    }


@pytest.fixture
def sample_test_health_dir(tmp_path: Path, sample_summary_json: dict[str, Any]) -> Path:
    """Erstellt ein Dummy-TestHealth-Report-Verzeichnis."""
    run_dir = tmp_path / "reports" / "test_health" / "20251211_143920_daily_quick"
    run_dir.mkdir(parents=True)

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(sample_summary_json), encoding="utf-8")

    return run_dir


@pytest.fixture
def mock_ai_response_text() -> str:
    """Mock-KI-Antwort mit EVAL_PACKAGE und LEARNING_SNIPPET."""
    return """
Hier ist meine Analyse des INFO_PACKETs:

=== EVAL_PACKAGE ===
event_id: INF-20251211_143920_daily_quick
short_eval:
  Health-Score im grünen Bereich (85/100), aber 2 Checks fehlgeschlagen. Ursachenanalyse empfohlen.
key_findings:
  - Guter Gesamt-Health-Score von 85/100
  - 2 fehlgeschlagene Checks erfordern Aufmerksamkeit
  - 1 Trigger-Violation (min_total_runs)
recommendations:
  - Fehlgeschlagene Checks analysieren und dokumentieren
  - Ursache für Trigger-Violation prüfen
  - Bei wiederkehrenden Failures Backlog-Item erstellen
risk_assessment:
  level: low
  notes: Keine kritischen Probleme, aber Monitoring empfohlen.
tags_out:
  - test_health
  - monitoring_needed
  - daily_check
=== /EVAL_PACKAGE ===

=== LEARNING_SNIPPET ===
- Regelmäßige Health-Checks helfen, Probleme frühzeitig zu erkennen.
- Bei 85/100 Health-Score ist das System grundsätzlich gesund, aber 2 fehlgeschlagene Checks sollten nicht ignoriert werden.
- Trigger-Violations sind wertvolle Frühindikatoren für Process-Improvements.
=== /LEARNING_SNIPPET ===
"""


@pytest.fixture
def mock_client(mock_ai_response_text: str) -> MagicMock:
    """Mock-Client für KI-Aufrufe."""
    client = MagicMock()

    # Mock-Response-Struktur wie OpenAI
    mock_choice = MagicMock()
    mock_choice.message.content = mock_ai_response_text

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    client.chat.completions.create.return_value = mock_response

    return client


# =============================================================================
# Model Tests
# =============================================================================

class TestIntelEvent:
    """Tests für IntelEvent-Dataclass."""

    def test_create_default(self):
        """Test: Event mit Default-Werten erstellen."""
        event = IntelEvent()

        assert event.event_id.startswith("INF_")
        assert event.source == "unknown"
        assert event.severity == "info"
        assert event.status == "new"
        assert isinstance(event.created_at, datetime)

    def test_create_with_values(self):
        """Test: Event mit spezifischen Werten erstellen."""
        event = IntelEvent(
            event_id="INF-test123",
            source="test_health_automation",
            category="test_automation",
            severity="warning",
            summary="Test-Summary",
            details=["Detail 1", "Detail 2"],
            links=["path/to/report"],
            tags=["test_health", "nightly"],
        )

        assert event.event_id == "INF-test123"
        assert event.source == "test_health_automation"
        assert event.severity == "warning"
        assert len(event.details) == 2
        assert "test_health" in event.tags

    def test_to_dict_and_from_dict(self):
        """Test: Serialisierung und Deserialisierung."""
        event = IntelEvent(
            event_id="INF-test",
            source="test",
            summary="Test summary",
            tags=["tag1"],
        )

        data = event.to_dict()
        assert isinstance(data, dict)
        assert data["event_id"] == "INF-test"
        assert isinstance(data["created_at"], str)  # ISO-String

        # Rückwärts
        restored = IntelEvent.from_dict(data)
        assert restored.event_id == event.event_id
        assert restored.source == event.source


class TestIntelEval:
    """Tests für IntelEval-Dataclass."""

    def test_create_default(self):
        """Test: Eval mit Default-Werten erstellen."""
        eval_obj = IntelEval()

        assert eval_obj.event_id == ""
        assert eval_obj.risk_level == "none"
        assert eval_obj.key_findings == []

    def test_create_with_values(self):
        """Test: Eval mit spezifischen Werten erstellen."""
        eval_obj = IntelEval(
            event_id="INF-test",
            short_eval="Test-Bewertung",
            key_findings=["Finding 1", "Finding 2"],
            recommendations=["Rec 1"],
            risk_level="low",
            risk_notes="Keine kritischen Probleme",
            tags_out=["tag1"],
        )

        assert eval_obj.event_id == "INF-test"
        assert len(eval_obj.key_findings) == 2
        assert eval_obj.risk_level == "low"


class TestLearningSnippet:
    """Tests für LearningSnippet-Dataclass."""

    def test_create_default(self):
        """Test: Snippet mit Default-Werten erstellen."""
        snippet = LearningSnippet()

        assert snippet.event_id == ""
        assert snippet.lines == []
        assert snippet.snippet_id.startswith("learn_")

    def test_to_markdown_block(self):
        """Test: Markdown-Block-Generierung."""
        snippet = LearningSnippet(
            event_id="INF-test123",
            lines=["Erstes Learning", "Zweites Learning"],
        )

        markdown = snippet.to_markdown_block()

        assert "### INF-test123" in markdown
        assert "- Erstes Learning" in markdown
        assert "- Zweites Learning" in markdown

    def test_to_markdown_block_empty_lines(self):
        """Test: Markdown-Block ohne Learnings."""
        snippet = LearningSnippet(event_id="INF-empty")

        markdown = snippet.to_markdown_block()

        assert "### INF-empty" in markdown
        assert "- (keine Learnings)" in markdown


# =============================================================================
# Collector Tests
# =============================================================================

class TestCollector:
    """Tests für den Collector."""

    def test_build_event_from_test_health_report(self, sample_test_health_dir: Path):
        """Test: Event aus TestHealth-Report erstellen."""
        event = build_event_from_test_health_report(sample_test_health_dir)

        assert event.event_id == "INF-20251211_143920_daily_quick"
        assert event.source == "test_health_automation"
        assert event.category == "test_automation"
        assert "daily_quick" in event.summary
        assert "85" in event.summary or "85.0" in event.summary
        assert "test_health" in event.tags
        # Severity sollte warning sein wegen failed_checks > 0
        assert event.severity in ("warning", "info")

    def test_build_event_missing_summary(self, tmp_path: Path):
        """Test: Fehler wenn summary.json fehlt."""
        run_dir = tmp_path / "empty_run"
        run_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            build_event_from_test_health_report(run_dir)

    def test_save_and_load_intel_event(self, tmp_path: Path):
        """Test: Event speichern und laden."""
        event = IntelEvent(
            event_id="INF-save_test",
            source="test",
            summary="Test event",
        )

        events_dir = tmp_path / "events"
        saved_path = save_intel_event(event, events_dir)

        assert saved_path.exists()
        assert saved_path.name == "INF-save_test.json"

        # Laden
        loaded = load_intel_event(saved_path)
        assert loaded.event_id == event.event_id
        assert loaded.source == event.source


# =============================================================================
# Evaluator Tests
# =============================================================================

class TestEvaluator:
    """Tests für den Evaluator."""

    def test_render_event_as_infopacket(self):
        """Test: Event als INFO_PACKET rendern."""
        event = IntelEvent(
            event_id="INF-render_test",
            source="test_source",
            category="test_category",
            severity="info",
            summary="Test summary",
            details=["Detail 1", "Detail 2"],
            links=["link1", "link2"],
            tags=["tag1", "tag2"],
        )

        packet = render_event_as_infopacket(event)

        assert "=== INFO_PACKET ===" in packet
        assert "=== /INFO_PACKET ===" in packet
        assert "source: test_source" in packet
        assert "event_id: INF-render_test" in packet
        assert "category: test_category" in packet
        assert "severity: info" in packet
        assert "Test summary" in packet
        assert "- Detail 1" in packet
        assert "- tag1" in packet

    def test_parse_eval_package(self, mock_ai_response_text: str):
        """Test: EVAL_PACKAGE parsen."""
        result = parse_eval_package(mock_ai_response_text)

        assert result["event_id"] == "INF-20251211_143920_daily_quick"
        assert "85/100" in result["short_eval"] or "85" in result["short_eval"]
        assert len(result["key_findings"]) >= 2
        assert len(result["recommendations"]) >= 2
        assert result["risk_level"] == "low"
        assert len(result["tags_out"]) >= 1

    def test_parse_eval_package_missing_block(self):
        """Test: Leeres Ergebnis wenn Block fehlt."""
        result = parse_eval_package("No eval package here")

        assert result["event_id"] == ""
        assert result["key_findings"] == []

    def test_parse_learning_snippet(self, mock_ai_response_text: str):
        """Test: LEARNING_SNIPPET parsen."""
        lines = parse_learning_snippet(mock_ai_response_text)

        assert len(lines) == 3
        assert "Health-Checks" in lines[0] or "Regelmäßige" in lines[0]

    def test_parse_learning_snippet_missing_block(self):
        """Test: Leere Liste wenn Block fehlt."""
        lines = parse_learning_snippet("No learning snippet here")

        assert lines == []

    def test_call_ai_for_event(self, mock_client: MagicMock):
        """Test: KI-Aufruf mit Mock-Client."""
        event = IntelEvent(
            event_id="INF-ai_test",
            source="test",
            summary="Test event for AI",
        )

        intel_eval, learning = call_ai_for_event(event, mock_client, model="gpt-4o-mini")

        # Prüfe, dass Client aufgerufen wurde
        mock_client.chat.completions.create.assert_called_once()

        # Prüfe Ergebnisse - event_id kommt vom Input-Event, nicht aus der Response
        assert intel_eval.event_id == "INF-ai_test"  # Vom Input-Event übernommen
        assert len(intel_eval.key_findings) >= 2
        assert len(learning.lines) >= 1
        assert learning.event_id == "INF-ai_test"  # Ebenfalls vom Input-Event


# =============================================================================
# Router Tests
# =============================================================================

class TestRouter:
    """Tests für den Router."""

    def test_append_learnings_to_new_log(self, tmp_path: Path):
        """Test: Learnings in neues Log schreiben."""
        log_path = tmp_path / "LEARNING_LOG.md"

        snippets = [
            LearningSnippet(
                event_id="INF-test1",
                lines=["Erstes Learning", "Zweites Learning"],
            ),
            LearningSnippet(
                event_id="INF-test2",
                lines=["Drittes Learning"],
            ),
        ]

        append_learnings_to_log(snippets, log_path)

        assert log_path.exists()
        content = log_path.read_text()

        assert "# InfoStream Learning Log" in content
        assert "### INF-test1" in content
        assert "### INF-test2" in content
        assert "- Erstes Learning" in content
        assert "- Drittes Learning" in content

    def test_append_learnings_dedupe(self, tmp_path: Path):
        """Test: Duplikate werden übersprungen."""
        log_path = tmp_path / "LEARNING_LOG.md"

        # Erste Runde
        snippets1 = [LearningSnippet(event_id="INF-dupe", lines=["Learning 1"])]
        append_learnings_to_log(snippets1, log_path)

        # Zweite Runde mit gleichem Event
        snippets2 = [LearningSnippet(event_id="INF-dupe", lines=["Learning 2"])]
        append_learnings_to_log(snippets2, log_path)

        content = log_path.read_text()

        # Sollte nur einmal vorkommen
        assert content.count("### INF-dupe") == 1
        assert "Learning 1" in content
        assert "Learning 2" not in content  # Duplikat wurde übersprungen

    def test_get_learning_log_stats(self, tmp_path: Path):
        """Test: Statistiken aus Log extrahieren."""
        log_path = tmp_path / "LEARNING_LOG.md"

        snippets = [
            LearningSnippet(event_id="INF-stat1", lines=["L1"]),
            LearningSnippet(event_id="INF-stat2", lines=["L2"]),
        ]
        append_learnings_to_log(snippets, log_path)

        stats = get_learning_log_stats(log_path)

        assert stats["total_entries"] == 2
        assert "INF-stat1" in stats["event_ids"]
        assert "INF-stat2" in stats["event_ids"]


# =============================================================================
# Run-Cycle Tests
# =============================================================================

class TestRunCycle:
    """Tests für den Run-Cycle."""

    def test_discover_test_health_runs(self, tmp_path: Path, sample_summary_json: dict[str, Any]):
        """Test: TestHealth-Runs entdecken."""
        # Setup: Zwei Runs erstellen
        th_root = tmp_path / "reports" / "test_health"

        run1 = th_root / "20251211_143920_daily_quick"
        run1.mkdir(parents=True)
        (run1 / "summary.json").write_text(json.dumps(sample_summary_json))

        run2 = th_root / "20251211_150000_weekly_core"
        run2.mkdir(parents=True)
        (run2 / "summary.json").write_text(json.dumps(sample_summary_json))

        # Events-Dir (noch leer)
        events_dir = tmp_path / "reports" / "infostream" / "events"
        events_dir.mkdir(parents=True)

        # Discovery
        runs = discover_test_health_runs(tmp_path)

        assert len(runs) == 2
        run_names = [r.name for r in runs]
        assert "20251211_143920_daily_quick" in run_names
        assert "20251211_150000_weekly_core" in run_names

    def test_discover_skips_processed(self, tmp_path: Path, sample_summary_json: dict[str, Any]):
        """Test: Bereits verarbeitete Runs werden übersprungen."""
        # Setup
        th_root = tmp_path / "reports" / "test_health"
        run1 = th_root / "20251211_143920_daily_quick"
        run1.mkdir(parents=True)
        (run1 / "summary.json").write_text(json.dumps(sample_summary_json))

        # Event bereits vorhanden
        events_dir = tmp_path / "reports" / "infostream" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "INF-20251211_143920_daily_quick.json").write_text("{}")

        # Discovery
        runs = discover_test_health_runs(tmp_path)

        assert len(runs) == 0  # Bereits verarbeitet

    def test_run_infostream_cycle_dry_run(self, tmp_path: Path, sample_summary_json: dict[str, Any]):
        """Test: Vollständiger Zyklus im Dry-Run-Modus."""
        # Setup
        th_root = tmp_path / "reports" / "test_health"
        run1 = th_root / "20251211_143920_daily_quick"
        run1.mkdir(parents=True)
        (run1 / "summary.json").write_text(json.dumps(sample_summary_json))

        # Cycle ausführen (dry-run, skip-ai)
        result = run_infostream_cycle(
            project_root=tmp_path,
            dry_run=True,
            skip_ai=True,
        )

        assert result["discovered_runs"] == 1
        assert result["events_created"] == 1
        assert result["errors"] == []

        # Im Dry-Run sollten keine Dateien geschrieben werden
        events_dir = tmp_path / "reports" / "infostream" / "events"
        assert not events_dir.exists() or len(list(events_dir.glob("*.json"))) == 0

    @patch("src.meta.infostream.run_cycle.create_ai_client")
    def test_run_infostream_cycle_with_mock_ai(
        self,
        mock_create_client: MagicMock,
        tmp_path: Path,
        sample_summary_json: dict[str, Any],
        mock_client: MagicMock,
    ):
        """Test: Vollständiger Zyklus mit Mock-KI."""
        # Setup
        th_root = tmp_path / "reports" / "test_health"
        run1 = th_root / "20251211_143920_daily_quick"
        run1.mkdir(parents=True)
        (run1 / "summary.json").write_text(json.dumps(sample_summary_json))

        # Learning-Log Verzeichnis erstellen
        log_dir = tmp_path / "docs" / "mindmap"
        log_dir.mkdir(parents=True)

        # Mock-Client zurückgeben
        mock_create_client.return_value = mock_client

        # Cycle ausführen
        result = run_infostream_cycle(
            project_root=tmp_path,
            dry_run=False,
            skip_ai=False,
        )

        assert result["discovered_runs"] == 1
        assert result["events_created"] == 1
        assert result["evals_created"] == 1
        assert result["learnings_added"] >= 1

        # Prüfe, dass Dateien erstellt wurden
        events_dir = tmp_path / "reports" / "infostream" / "events"
        assert events_dir.exists()
        assert len(list(events_dir.glob("*.json"))) == 1

        evals_dir = tmp_path / "reports" / "infostream" / "evals"
        assert evals_dir.exists()
        assert len(list(evals_dir.glob("*.json"))) == 1

        log_path = tmp_path / "docs" / "mindmap" / "INFOSTREAM_LEARNING_LOG.md"
        assert log_path.exists()
        content = log_path.read_text()
        assert "INF-" in content


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """End-to-End Integration Tests."""

    @patch("src.meta.infostream.run_cycle.create_ai_client")
    def test_full_pipeline(
        self,
        mock_create_client: MagicMock,
        tmp_path: Path,
        mock_client: MagicMock,
    ):
        """Test: Vollständige Pipeline von Report zu Learning-Log."""
        # 1. Setup: Simuliere TestHealth-Report
        th_root = tmp_path / "reports" / "test_health"
        run_dir = th_root / "20251211_143920_integration_test"
        run_dir.mkdir(parents=True)

        summary = {
            "profile_name": "integration_test",
            "health_score": 92.0,
            "passed_checks": 10,
            "failed_checks": 0,
            "skipped_checks": 0,
            "started_at": "2025-12-11T14:39:20",
            "finished_at": "2025-12-11T14:40:00",
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))

        # Docs-Verzeichnis erstellen
        (tmp_path / "docs" / "mindmap").mkdir(parents=True)

        # Mock-Client
        mock_create_client.return_value = mock_client

        # 2. Zyklus ausführen
        result = run_infostream_cycle(
            project_root=tmp_path,
            dry_run=False,
            skip_ai=False,
        )

        # 3. Assertions
        assert result["errors"] == []
        assert result["discovered_runs"] == 1
        assert result["events_created"] == 1
        assert result["evals_created"] == 1
        assert result["learnings_added"] >= 1

        # Prüfe Event
        event_file = tmp_path / "reports" / "infostream" / "events" / "INF-20251211_143920_integration_test.json"
        assert event_file.exists()

        event_data = json.loads(event_file.read_text())
        assert event_data["source"] == "test_health_automation"
        assert "92" in event_data["summary"] or "92.0" in event_data["summary"]

        # Prüfe Learning-Log
        log_path = tmp_path / "docs" / "mindmap" / "INFOSTREAM_LEARNING_LOG.md"
        assert log_path.exists()

        log_content = log_path.read_text()
        assert "# InfoStream Learning Log" in log_content
        assert "INF-" in log_content
