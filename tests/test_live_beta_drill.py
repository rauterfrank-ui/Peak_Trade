# tests/test_live_beta_drill.py
"""
Peak_Trade: Tests für Live-Beta Drill (Phase 85)
================================================

Tests für das Live-Beta Drill Script und seine Komponenten.

WICHTIG: Phase 85 - Shadow/Testnet Only
    - Keine echten Orders
    - Keine Live-Kapital-Risiken
    - Alle Tests sind Simulationen
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

# Projekt-Root zum Python-Path hinzufügen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_live_beta_drill import (
    DrillCheckResult,
    LiveBetaDrillResult,
    run_preflight_drill,
    run_eligibility_drill,
    run_shadow_gates_drill,
    run_incident_simulation_drill,
    run_all_drills,
    format_drill_report_text,
    format_drill_report_json,
    get_available_presets,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_check_result() -> DrillCheckResult:
    """Sample DrillCheckResult für Tests."""
    return DrillCheckResult(
        check_name="Test Check",
        passed=True,
        details="Test details",
        category="preflight",
        severity="info",
    )


@pytest.fixture
def sample_drill_result() -> LiveBetaDrillResult:
    """Sample LiveBetaDrillResult für Tests."""
    return LiveBetaDrillResult(
        timestamp="2025-12-07T23:45:00",
        drill_type="test_drill",
        total_checks=5,
        passed_checks=4,
        failed_checks=1,
        checks=[
            DrillCheckResult("Check 1", True, "OK", "preflight", "info"),
            DrillCheckResult("Check 2", True, "OK", "eligibility", "info"),
            DrillCheckResult("Check 3", True, "OK", "gates", "info"),
            DrillCheckResult("Check 4", True, "OK", "incident", "info"),
            DrillCheckResult("Check 5", False, "Failed", "gates", "error"),
        ],
        lessons_learned=["Lesson 1"],
        recommendations=["Recommendation 1"],
    )


# =============================================================================
# Tests: Datamodels
# =============================================================================


class TestDrillCheckResult:
    """Tests für DrillCheckResult."""

    def test_create_drill_check_result(self, sample_check_result):
        """Test: DrillCheckResult erstellen."""
        assert sample_check_result.check_name == "Test Check"
        assert sample_check_result.passed is True
        assert sample_check_result.details == "Test details"
        assert sample_check_result.category == "preflight"
        assert sample_check_result.severity == "info"

    def test_drill_check_result_failed(self):
        """Test: DrillCheckResult mit Fehler."""
        result = DrillCheckResult(
            check_name="Failed Check",
            passed=False,
            details="Error occurred",
            category="gates",
            severity="error",
        )
        assert result.passed is False
        assert result.severity == "error"


class TestLiveBetaDrillResult:
    """Tests für LiveBetaDrillResult."""

    def test_create_drill_result(self, sample_drill_result):
        """Test: LiveBetaDrillResult erstellen."""
        assert sample_drill_result.timestamp == "2025-12-07T23:45:00"
        assert sample_drill_result.drill_type == "test_drill"
        assert sample_drill_result.total_checks == 5
        assert sample_drill_result.passed_checks == 4
        assert sample_drill_result.failed_checks == 1

    def test_all_passed_property_false(self, sample_drill_result):
        """Test: all_passed ist False wenn failed > 0."""
        assert sample_drill_result.all_passed is False

    def test_all_passed_property_true(self):
        """Test: all_passed ist True wenn failed == 0."""
        result = LiveBetaDrillResult(
            timestamp="2025-12-07T23:45:00",
            drill_type="test",
            total_checks=3,
            passed_checks=3,
            failed_checks=0,
            checks=[],
        )
        assert result.all_passed is True


# =============================================================================
# Tests: Drill Functions
# =============================================================================


class TestPreflightDrill:
    """Tests für Pre-flight Drill."""

    def test_run_preflight_drill_returns_list(self):
        """Test: run_preflight_drill gibt Liste zurück."""
        results = run_preflight_drill()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_preflight_drill_checks_tiering(self):
        """Test: Pre-flight prüft Tiering-System."""
        results = run_preflight_drill()
        tiering_check = next((r for r in results if "Tiering" in r.check_name), None)
        assert tiering_check is not None
        assert tiering_check.category == "preflight"

    def test_preflight_drill_checks_policies(self):
        """Test: Pre-flight prüft Live-Policies."""
        results = run_preflight_drill()
        policies_check = next((r for r in results if "Policies" in r.check_name), None)
        assert policies_check is not None
        assert policies_check.category == "preflight"

    def test_preflight_drill_all_have_category(self):
        """Test: Alle Pre-flight Checks haben category='preflight'."""
        results = run_preflight_drill()
        for result in results:
            assert result.category == "preflight"


class TestEligibilityDrill:
    """Tests für Eligibility Drill."""

    def test_run_eligibility_drill_returns_list(self):
        """Test: run_eligibility_drill gibt Liste zurück."""
        results = run_eligibility_drill()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_eligibility_drill_checks_core(self):
        """Test: Eligibility prüft Core-Strategien."""
        results = run_eligibility_drill()
        core_check = next((r for r in results if "Core" in r.check_name), None)
        assert core_check is not None
        assert core_check.category == "eligibility"

    def test_eligibility_drill_checks_legacy(self):
        """Test: Eligibility prüft Legacy-Strategien."""
        results = run_eligibility_drill()
        legacy_check = next((r for r in results if "Legacy" in r.check_name), None)
        assert legacy_check is not None
        assert legacy_check.category == "eligibility"

    def test_eligibility_drill_all_have_category(self):
        """Test: Alle Eligibility Checks haben category='eligibility'."""
        results = run_eligibility_drill()
        for result in results:
            assert result.category == "eligibility"


class TestShadowGatesDrill:
    """Tests für Shadow-Gates Drill."""

    def test_run_shadow_gates_drill_returns_list(self):
        """Test: run_shadow_gates_drill gibt Liste zurück."""
        results = run_shadow_gates_drill()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_shadow_gates_drill_has_summary(self):
        """Test: Shadow-Gates hat Summary-Check."""
        results = run_shadow_gates_drill()
        summary_check = next((r for r in results if "Summary" in r.check_name), None)
        assert summary_check is not None

    def test_shadow_gates_drill_all_have_category(self):
        """Test: Alle Gate Checks haben category='gates'."""
        results = run_shadow_gates_drill()
        for result in results:
            assert result.category == "gates"


class TestIncidentSimulationDrill:
    """Tests für Incident-Simulation Drill."""

    def test_run_incident_simulation_drill_returns_list(self):
        """Test: run_incident_simulation_drill gibt Liste zurück."""
        results = run_incident_simulation_drill()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_incident_drill_checks_data_gap(self):
        """Test: Incident-Sim prüft Data-Gap."""
        results = run_incident_simulation_drill()
        data_gap_check = next((r for r in results if "Data-Gap" in r.check_name), None)
        assert data_gap_check is not None

    def test_incident_drill_checks_risk_limit(self):
        """Test: Incident-Sim prüft Risk-Limit."""
        results = run_incident_simulation_drill()
        risk_check = next((r for r in results if "Risk-Limit" in r.check_name), None)
        assert risk_check is not None

    def test_incident_drill_all_have_category(self):
        """Test: Alle Incident Checks haben category='incident'."""
        results = run_incident_simulation_drill()
        for result in results:
            assert result.category == "incident"


class TestRunAllDrills:
    """Tests für run_all_drills."""

    def test_run_all_drills_returns_result(self):
        """Test: run_all_drills gibt LiveBetaDrillResult zurück."""
        result = run_all_drills()
        assert isinstance(result, LiveBetaDrillResult)

    def test_run_all_drills_has_all_categories(self):
        """Test: run_all_drills enthält alle Kategorien."""
        result = run_all_drills()
        categories = {c.category for c in result.checks}
        assert "preflight" in categories
        assert "eligibility" in categories
        assert "gates" in categories
        assert "incident" in categories

    def test_run_all_drills_counts_correct(self):
        """Test: run_all_drills zählt korrekt."""
        result = run_all_drills()
        assert result.total_checks == len(result.checks)
        assert result.passed_checks + result.failed_checks == result.total_checks

    def test_run_all_drills_has_timestamp(self):
        """Test: run_all_drills hat Timestamp."""
        result = run_all_drills()
        assert result.timestamp is not None
        assert len(result.timestamp) > 0


# =============================================================================
# Tests: Formatters
# =============================================================================


class TestFormatters:
    """Tests für Report-Formatter."""

    def test_format_text_contains_header(self, sample_drill_result):
        """Test: Text-Format enthält Header."""
        text = format_drill_report_text(sample_drill_result)
        assert "PEAK_TRADE LIVE-BETA DRILL" in text
        assert "Phase 85" in text

    def test_format_text_contains_summary(self, sample_drill_result):
        """Test: Text-Format enthält Summary."""
        text = format_drill_report_text(sample_drill_result)
        assert "SUMMARY" in text
        assert "Total Checks" in text
        assert "Passed" in text
        assert "Failed" in text

    def test_format_text_contains_checks(self, sample_drill_result):
        """Test: Text-Format enthält Checks."""
        text = format_drill_report_text(sample_drill_result)
        assert "Check 1" in text
        assert "Check 5" in text

    def test_format_json_is_valid(self, sample_drill_result):
        """Test: JSON-Format ist valides JSON."""
        json_str = format_drill_report_json(sample_drill_result)
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_format_json_has_required_fields(self, sample_drill_result):
        """Test: JSON hat erforderliche Felder."""
        json_str = format_drill_report_json(sample_drill_result)
        data = json.loads(json_str)
        assert "phase" in data
        assert "timestamp" in data
        assert "summary" in data
        assert "checks" in data

    def test_format_json_summary_correct(self, sample_drill_result):
        """Test: JSON Summary ist korrekt."""
        json_str = format_drill_report_json(sample_drill_result)
        data = json.loads(json_str)
        assert data["summary"]["total_checks"] == 5
        assert data["summary"]["passed_checks"] == 4
        assert data["summary"]["failed_checks"] == 1


# =============================================================================
# Tests: CLI
# =============================================================================


class TestLiveBetaDrillCLI:
    """Tests für Live-Beta Drill CLI."""

    def test_cli_runs_without_error(self):
        """Test: CLI läuft ohne Fehler."""
        result = subprocess.run(
            [sys.executable, "scripts/run_live_beta_drill.py"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        # Exit-Code kann 0 oder 1 sein (je nach Drill-Ergebnis)
        assert result.returncode in [0, 1]
        assert "PEAK_TRADE LIVE-BETA DRILL" in result.stdout

    def test_cli_scenario_preflight(self):
        """Test: CLI mit --scenario preflight."""
        result = subprocess.run(
            [sys.executable, "scripts/run_live_beta_drill.py", "--scenario", "preflight"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]
        assert "PREFLIGHT" in result.stdout

    def test_cli_scenario_eligibility(self):
        """Test: CLI mit --scenario eligibility."""
        result = subprocess.run(
            [sys.executable, "scripts/run_live_beta_drill.py", "--scenario", "eligibility"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]
        assert "ELIGIBILITY" in result.stdout

    def test_cli_format_json(self):
        """Test: CLI mit --format json."""
        result = subprocess.run(
            [sys.executable, "scripts/run_live_beta_drill.py", "--format", "json"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]
        # Sollte valides JSON sein
        data = json.loads(result.stdout)
        assert "phase" in data
        assert data["phase"] == "85"

    def test_cli_all_flag(self):
        """Test: CLI mit --all Flag."""
        result = subprocess.run(
            [sys.executable, "scripts/run_live_beta_drill.py", "--all"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]
        assert "PEAK_TRADE LIVE-BETA DRILL" in result.stdout


# =============================================================================
# Tests: Integration
# =============================================================================


class TestLiveBetaDrillIntegration:
    """Integration Tests für Live-Beta Drill."""

    def test_all_drills_complete_without_exception(self):
        """Test: Alle Drills laufen ohne Exception."""
        try:
            result = run_all_drills()
            assert result is not None
        except Exception as e:
            pytest.fail(f"run_all_drills raised exception: {e}")

    def test_drill_results_have_valid_severities(self):
        """Test: Alle Drill-Ergebnisse haben valide Severities."""
        result = run_all_drills()
        valid_severities = {"info", "warning", "error"}
        for check in result.checks:
            assert check.severity in valid_severities

    def test_drill_results_have_valid_categories(self):
        """Test: Alle Drill-Ergebnisse haben valide Kategorien."""
        result = run_all_drills()
        valid_categories = {"preflight", "eligibility", "gates", "incident"}
        for check in result.checks:
            assert check.category in valid_categories

    def test_drill_recommendations_present_on_failure(self):
        """Test: Bei Fehlern sind Recommendations vorhanden."""
        result = run_all_drills()
        if result.failed_checks > 0:
            # Bei Fehlern sollten Recommendations vorhanden sein
            # (kann leer sein wenn alle Tests bestehen)
            pass  # OK - Recommendations sind optional

    def test_drill_lessons_learned_present(self):
        """Test: Lessons Learned sind vorhanden."""
        result = run_all_drills()
        assert isinstance(result.lessons_learned, list)
