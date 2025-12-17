# tests/test_operator_dashboard.py
"""
Tests für Phase 84: Operator Dashboard CLI

Testet:
- Dashboard-Skript ist ausführbar
- Alle Views funktionieren
- JSON-Output ist valide
- Alerts werden korrekt generiert
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class TestOperatorDashboardCLI:
    """Tests für das Operator-Dashboard CLI."""

    def test_script_exists(self):
        """Dashboard-Skript existiert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        assert script.exists(), f"Script not found: {script}"

    def test_help_runs(self):
        """--help funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Help failed: {result.stderr}"
        assert "operator" in result.stdout.lower() or "dashboard" in result.stdout.lower()

    def test_default_view_runs(self):
        """Default-View (all) funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Kann mit Exit-Code 1 beenden wenn Alerts vorhanden
        assert result.returncode in [0, 1], f"Dashboard failed: {result.stderr}"
        assert "DASHBOARD" in result.stdout or "SUMMARY" in result.stdout

    def test_strategies_view(self):
        """--view strategies funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--view", "strategies"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0, 1]
        assert "STRATEGIES" in result.stdout or "Strategy" in result.stdout

    def test_portfolios_view(self):
        """--view portfolios funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--view", "portfolios"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0, 1]
        assert "PORTFOLIOS" in result.stdout or "Portfolio" in result.stdout

    def test_alerts_view(self):
        """--view alerts funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--view", "alerts"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0, 1]
        assert "ALERTS" in result.stdout or "No alerts" in result.stdout

    def test_summary_view(self):
        """--view summary funktioniert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--view", "summary"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0, 1]
        assert "SUMMARY" in result.stdout or "Total" in result.stdout


class TestOperatorDashboardJSONOutput:
    """Tests für JSON-Output."""

    def test_json_format(self):
        """--format json gibt valides JSON aus."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0, 1]

        # Parse JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.stdout[:500]}")

        # Struktur prüfen
        assert "timestamp" in data
        assert "summary" in data
        assert "strategies" in data
        assert "portfolios" in data
        assert "alerts" in data

    def test_json_has_strategies(self):
        """JSON enthält Strategien."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)
        assert isinstance(data["strategies"], list)
        assert len(data["strategies"]) > 0, "Should have at least one strategy"

        # Strategie-Struktur prüfen
        strategy = data["strategies"][0]
        assert "strategy_id" in strategy
        assert "tier" in strategy
        assert "is_eligible" in strategy

    def test_json_summary_has_counts(self):
        """JSON Summary enthält Zählungen."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)
        summary = data["summary"]

        assert "total_strategies" in summary
        assert "strategies_eligible" in summary
        assert "total_portfolios" in summary
        assert "alerts_error" in summary
        assert "alerts_warning" in summary


class TestOperatorDashboardContent:
    """Tests für Dashboard-Inhalt."""

    def test_shows_core_strategies(self):
        """Dashboard zeigt Core-Strategien."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)
        core_strategies = [s for s in data["strategies"] if s["tier"] == "core"]

        assert len(core_strategies) >= 1, "Should have at least one core strategy"

        # Bekannte Core-Strategien
        core_ids = [s["strategy_id"] for s in core_strategies]
        assert "rsi_reversion" in core_ids or "ma_crossover" in core_ids

    def test_shows_portfolio_presets(self):
        """Dashboard zeigt Portfolio-Presets."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)
        portfolios = data["portfolios"]

        assert len(portfolios) >= 1, "Should have at least one portfolio"

        # Prüfe core_balanced
        portfolio_ids = [p["portfolio_id"] for p in portfolios]
        assert "core_balanced" in portfolio_ids

    def test_core_strategies_are_eligible(self):
        """Core-Strategien sind im Dashboard als eligible markiert."""
        script = SCRIPTS_DIR / "operator_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        data = json.loads(result.stdout)
        core_strategies = [s for s in data["strategies"] if s["tier"] == "core"]

        for s in core_strategies:
            assert s["is_eligible"], f"Core strategy {s['strategy_id']} should be eligible"


class TestOperatorDashboardIntegration:
    """Integration Tests für Dashboard."""

    def test_dashboard_imports_work(self):
        """Dashboard-Imports funktionieren."""
        # Importiere Dashboard-Module
        from src.experiments.portfolio_presets import get_all_tiered_strategies
        from src.live.live_gates import get_eligibility_summary

        summary = get_eligibility_summary()
        assert summary is not None

        tiered = get_all_tiered_strategies()
        assert "core" in tiered

    def test_dashboard_data_collection(self):
        """Datensammlung funktioniert."""
        # Importiere und teste collect-Funktionen
        sys.path.insert(0, str(SCRIPTS_DIR))

        from operator_dashboard import (
            collect_dashboard_data,
            collect_portfolio_statuses,
            collect_strategy_statuses,
        )

        strategies = collect_strategy_statuses()
        assert len(strategies) > 0

        portfolios = collect_portfolio_statuses()
        # Kann 0 sein wenn keine Presets

        data = collect_dashboard_data()
        assert data.timestamp is not None
        assert len(data.strategies) > 0
