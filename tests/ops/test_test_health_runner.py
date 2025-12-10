"""
Tests für Test Health Runner
=============================

Testet die Core-Funktionen des Test-Health-Automation-Systems:
  - TOML-Profil-Parsing
  - Check-Ausführung
  - Health-Score-Aggregation
  - Report-Generierung (JSON/MD/HTML)

Stand: Dezember 2024
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.ops.test_health_runner import (
    TestCheckConfig,
    TestCheckResult,
    TestHealthSummary,
    aggregate_health,
    load_test_health_profile,
    run_single_check,
    run_test_health_profile,
    write_test_health_html,
    write_test_health_json,
    write_test_health_markdown,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Erstellt ein temporäres Config-Verzeichnis mit Test-TOML."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Minimal-TOML für Tests
    toml_content = """
version = "0.1"
default_profile = "test_profile"

[profiles.test_profile]
description = "Test Profile für Unit-Tests"
time_window_days = 1

[[profiles.test_profile.checks]]
id = "success_check"
name = "Success Check"
cmd = "python3 -c 'import sys; sys.exit(0)'"
weight = 3
category = "tests"

[[profiles.test_profile.checks]]
id = "fail_check"
name = "Fail Check"
cmd = "python3 -c 'import sys; sys.exit(1)'"
weight = 2
category = "tests"
"""

    config_path = config_dir / "test_health_profiles.toml"
    config_path.write_text(toml_content)

    return config_dir


@pytest.fixture
def temp_report_dir(tmp_path):
    """Erstellt ein temporäres Report-Verzeichnis."""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return report_dir


class TestLoadTestHealthProfile:
    """Tests für load_test_health_profile()"""

    def test_load_valid_profile(self, temp_config_dir):
        """Test: Korrektes Laden eines validen Profils."""
        config_path = temp_config_dir / "test_health_profiles.toml"
        checks = load_test_health_profile(config_path, "test_profile")

        assert len(checks) == 2
        assert checks[0].id == "success_check"
        assert checks[0].name == "Success Check"
        assert checks[0].weight == 3
        assert checks[1].id == "fail_check"
        assert checks[1].weight == 2

    def test_load_nonexistent_profile(self, temp_config_dir):
        """Test: ValueError bei nicht existierendem Profil."""
        config_path = temp_config_dir / "test_health_profiles.toml"

        with pytest.raises(ValueError, match="Profil 'nonexistent' nicht gefunden"):
            load_test_health_profile(config_path, "nonexistent")

    def test_load_nonexistent_config(self, tmp_path):
        """Test: FileNotFoundError bei nicht existierender Config-Datei."""
        config_path = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            load_test_health_profile(config_path, "test_profile")


class TestRunSingleCheck:
    """Tests für run_single_check()"""

    def test_success_check(self):
        """Test: Check mit Exit-Code 0 → Status PASS."""
        check = TestCheckConfig(
            id="test_pass",
            name="Test Pass",
            cmd="python3 -c 'import sys; sys.exit(0)'",
            weight=1,
            category="tests",
        )

        result = run_single_check(check)

        assert result.status == "PASS"
        assert result.return_code == 0
        assert result.error_message is None
        assert result.duration_seconds >= 0

    def test_fail_check(self):
        """Test: Check mit Exit-Code 1 → Status FAIL."""
        check = TestCheckConfig(
            id="test_fail",
            name="Test Fail",
            cmd="python3 -c 'import sys; sys.exit(1)'",
            weight=1,
            category="tests",
        )

        result = run_single_check(check)

        assert result.status == "FAIL"
        assert result.return_code == 1
        assert result.error_message is not None
        assert "exited with code 1" in result.error_message

    def test_invalid_command(self):
        """Test: Ungültiger Command → Status FAIL."""
        check = TestCheckConfig(
            id="test_invalid",
            name="Test Invalid",
            cmd="this_command_does_not_exist_12345",
            weight=1,
            category="tests",
        )

        result = run_single_check(check)

        assert result.status == "FAIL"

    def test_stdout_stderr_capture(self):
        """Test P2: Stdout/Stderr werden erfasst."""
        check = TestCheckConfig(
            id="test_output",
            name="Test Output Capture",
            cmd='python3 -c "import sys; print(\'STDOUT_TEST\'); print(\'STDERR_TEST\', file=sys.stderr); sys.exit(1)"',
            weight=1,
            category="tests",
        )

        result = run_single_check(check)

        assert result.status == "FAIL"
        assert result.return_code == 1
        # Prüfe ob stdout/stderr erfasst wurden
        assert result.stdout is not None
        assert "STDOUT_TEST" in result.stdout
        assert result.stderr is not None
        assert "STDERR_TEST" in result.stderr
        # Exit-Code kann variieren (127 auf Unix, andere auf Windows)
        assert result.return_code != 0
        assert result.error_message is not None


class TestAggregateHealth:
    """Tests für aggregate_health()"""

    def test_all_pass(self):
        """Test: Alle Checks erfolgreich → Health-Score 100."""
        import datetime as dt
        
        results = [
            TestCheckResult(
                id="check1",
                name="Check 1",
                category="tests",
                cmd="cmd1",
                status="PASS",
                weight=3,
                started_at=dt.datetime.utcnow(),
                finished_at=dt.datetime.utcnow(),
                duration_seconds=1.0,
            ),
            TestCheckResult(
                id="check2",
                name="Check 2",
                category="tests",
                cmd="cmd2",
                status="PASS",
                weight=2,
                started_at=dt.datetime.utcnow(),
                finished_at=dt.datetime.utcnow(),
                duration_seconds=1.0,
            ),
        ]

        summary = aggregate_health("test_profile", results)

        assert summary.health_score == 100.0
        assert summary.passed_checks == 2
        assert summary.failed_checks == 0
        assert summary.total_weight == 5
        assert summary.passed_weight == 5

    def test_mixed_results(self):
        """Test: Gemischte Ergebnisse → Health-Score korrekt berechnet."""
        import datetime as dt
        
        results = [
            TestCheckResult(
                id="check1",
                name="Check 1",
                category="tests",
                cmd="cmd1",
                status="PASS",
                weight=3,
                started_at=dt.datetime.utcnow(),
                finished_at=dt.datetime.utcnow(),
                duration_seconds=1.0,
            ),
            TestCheckResult(
                id="check2",
                name="Check 2",
                category="tests",
                cmd="cmd2",
                status="FAIL",
                weight=2,
                started_at=dt.datetime.utcnow(),
                finished_at=dt.datetime.utcnow(),
                duration_seconds=1.0,
            ),
        ]

        summary = aggregate_health("test_profile", results)

        # passed_weight = 3, total_weight = 5 → 60%
        assert summary.health_score == 60.0
        assert summary.passed_checks == 1
        assert summary.failed_checks == 1
        assert summary.total_weight == 5
        assert summary.passed_weight == 3

    def test_empty_results(self):
        """Test: Keine Checks → Health-Score 0."""
        summary = aggregate_health("test_profile", [])

        assert summary.health_score == 0.0
        assert summary.passed_checks == 0
        assert summary.failed_checks == 0
        assert summary.total_weight == 0


class TestReportWriters:
    """Tests für Report-Writer-Funktionen."""

    def test_write_json(self, tmp_path):
        """Test: JSON-Report wird korrekt geschrieben."""
        import datetime as dt

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime(2025, 12, 10, 14, 0, 0),
            finished_at=dt.datetime(2025, 12, 10, 14, 5, 0),
            checks=[],
            health_score=85.0,
            passed_checks=3,
            failed_checks=1,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
        )

        json_path = tmp_path / "summary.json"
        write_test_health_json(summary, json_path)

        assert json_path.exists()

        # JSON validieren
        with open(json_path) as f:
            data = json.load(f)

        assert data["profile_name"] == "test_profile"
        assert data["health_score"] == 85.0
        assert data["passed_checks"] == 3
        assert data["failed_checks"] == 1

    def test_write_markdown(self, tmp_path):
        """Test: Markdown-Report wird korrekt geschrieben."""
        import datetime as dt

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime(2025, 12, 10, 14, 0, 0),
            finished_at=dt.datetime(2025, 12, 10, 14, 5, 0),
            checks=[],
            health_score=75.0,
            passed_checks=2,
            failed_checks=1,
            skipped_checks=0,
            total_weight=10,
            passed_weight=7,
        )

        md_path = tmp_path / "summary.md"
        write_test_health_markdown(summary, md_path)

        assert md_path.exists()

        # Markdown-Inhalt validieren
        content = md_path.read_text()
        assert "# Test Health Report: test_profile" in content
        assert "75.0 / 100.0" in content
        assert "Passed Checks**: 2" in content

    def test_write_markdown_with_failed_checks(self, tmp_path):
        """Test P2: Markdown-Report mit fehlgeschlagenen Checks + stdout/stderr."""
        import datetime as dt

        failed_check = TestCheckResult(
            id="test_fail",
            name="Failed Test",
            category="tests",
            cmd="pytest test_something.py",
            status="FAIL",
            weight=1,
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            duration_seconds=1.5,
            return_code=1,
            error_message="Test failed",
            stdout="STDOUT: Test output here\nFailed: 1 test",
            stderr="STDERR: Some error",
        )

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime(2025, 12, 10, 14, 0, 0),
            finished_at=dt.datetime(2025, 12, 10, 14, 5, 0),
            checks=[failed_check],
            health_score=50.0,
            passed_checks=0,
            failed_checks=1,
            skipped_checks=0,
            total_weight=1,
            passed_weight=0,
        )

        md_path = tmp_path / "summary_failed.md"
        write_test_health_markdown(summary, md_path)

        assert md_path.exists()
        content = md_path.read_text()
        
        # Prüfe ob fehlgeschlagener Check detailliert dargestellt wird
        assert "❌ Fehlgeschlagene Checks (Details)" in content
        assert "Failed Test" in content
        assert "Test output here" in content
        assert "Some error" in content

    def test_write_html(self, tmp_path):
        """Test: HTML-Report wird korrekt geschrieben."""
        import datetime as dt

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime(2025, 12, 10, 14, 0, 0),
            finished_at=dt.datetime(2025, 12, 10, 14, 5, 0),
            checks=[],
            health_score=45.0,
            passed_checks=1,
            failed_checks=2,
            skipped_checks=0,
            total_weight=10,
            passed_weight=4,
        )

        html_path = tmp_path / "summary.html"
        write_test_health_html(summary, html_path)

        assert html_path.exists()

        # HTML-Inhalt validieren
        content = html_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "test_profile" in content
        assert "45.0" in content


class TestRunTestHealthProfile:
    """Integration-Tests für run_test_health_profile()"""

    def test_full_run(self, temp_config_dir, temp_report_dir):
        """Test: Kompletter Profil-Lauf mit Report-Generierung."""
        config_path = temp_config_dir / "test_health_profiles.toml"

        summary, report_dir = run_test_health_profile(
            profile_name="test_profile",
            config_path=config_path,
            report_root=temp_report_dir,
        )

        # Summary validieren
        assert summary.profile_name == "test_profile"
        assert summary.passed_checks == 1  # success_check
        assert summary.failed_checks == 1  # fail_check
        assert summary.health_score == 60.0  # 3 / (3+2) = 60%

        # Report-Files validieren
        assert report_dir.exists()
        assert (report_dir / "summary.json").exists()
        assert (report_dir / "summary.md").exists()
        assert (report_dir / "summary.html").exists()

        # JSON-Inhalt validieren
        with open(report_dir / "summary.json") as f:
            data = json.load(f)
        assert data["health_score"] == 60.0
        assert len(data["checks"]) == 2


# ============================================================================
# Tests für Test Health History
# ============================================================================


class TestHealthHistory:
    """Tests für test_health_history.py"""

    def test_append_and_load_history(self, tmp_path):
        """Test: Historie anlegen und laden."""
        import datetime as dt
        from src.ops.test_health_history import (
            append_to_history,
            load_history,
            HealthHistoryEntry,
        )

        history_path = tmp_path / "history.json"

        # Erstelle eine Test-Summary
        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime(2025, 12, 10, 14, 0, 0),
            finished_at=dt.datetime(2025, 12, 10, 14, 5, 0),
            checks=[],
            health_score=85.0,
            passed_checks=3,
            failed_checks=1,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
        )

        # Füge zur Historie hinzu
        result_path = append_to_history(summary, tmp_path / "report", history_path)
        assert result_path == history_path
        assert history_path.exists()

        # Lade Historie
        entries = load_history(history_path, "test_profile")
        assert len(entries) == 1
        assert entries[0].profile_name == "test_profile"
        assert entries[0].health_score == 85.0
        assert entries[0].passed_checks == 3

    def test_get_history_stats(self, tmp_path):
        """Test: Historie-Statistiken berechnen."""
        import datetime as dt
        from src.ops.test_health_history import (
            append_to_history,
            get_history_stats,
        )

        history_path = tmp_path / "history.json"

        # Erstelle mehrere Einträge
        for i, score in enumerate([70.0, 75.0, 80.0, 85.0]):
            summary = TestHealthSummary(
                profile_name="test_profile",
                started_at=dt.datetime(2025, 12, 10, 14, i, 0),
                finished_at=dt.datetime(2025, 12, 10, 14, i, 30),
                checks=[],
                health_score=score,
                passed_checks=3,
                failed_checks=1,
                skipped_checks=0,
                total_weight=10,
                passed_weight=int(score / 10),
            )
            append_to_history(summary, history_path=history_path)

        # Hole Stats
        stats = get_history_stats("test_profile", days=14, history_path=history_path)

        assert stats["count"] == 4
        assert stats["avg_score"] == 77.5
        assert stats["min_score"] == 70.0
        assert stats["max_score"] == 85.0
        assert stats["latest_score"] == 85.0
        assert stats["trend"] == "improving"  # Steigender Trend

    def test_load_history_empty(self, tmp_path):
        """Test: Leere Historie laden."""
        from src.ops.test_health_history import load_history

        history_path = tmp_path / "nonexistent.json"
        entries = load_history(history_path, "test_profile")
        assert entries == []

    def test_history_filter_by_profile(self, tmp_path):
        """Test: Historie nach Profil filtern."""
        import datetime as dt
        from src.ops.test_health_history import (
            append_to_history,
            load_history,
        )

        history_path = tmp_path / "history.json"

        # Erstelle Einträge für verschiedene Profile
        for profile in ["profile_a", "profile_b", "profile_a"]:
            summary = TestHealthSummary(
                profile_name=profile,
                started_at=dt.datetime.utcnow(),
                finished_at=dt.datetime.utcnow(),
                checks=[],
                health_score=100.0,
                passed_checks=1,
                failed_checks=0,
                skipped_checks=0,
                total_weight=1,
                passed_weight=1,
            )
            append_to_history(summary, history_path=history_path)

        # Lade nur profile_a
        entries_a = load_history(history_path, "profile_a")
        assert len(entries_a) == 2

        # Lade nur profile_b
        entries_b = load_history(history_path, "profile_b")
        assert len(entries_b) == 1

        # Lade alle
        entries_all = load_history(history_path, None)
        assert len(entries_all) == 3


# ============================================================================
# Marker für Slow-Tests (falls gewünscht)
# ============================================================================

# pytestmark = pytest.mark.unit  # Deaktiviert, da Marker nicht in pytest.ini registriert
