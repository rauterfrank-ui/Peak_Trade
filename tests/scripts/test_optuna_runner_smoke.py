"""
Smoke-Tests für Optuna Study Runner
====================================
Tests werden übersprungen wenn optuna nicht installiert ist.
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Check if optuna is available
try:
    import optuna

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

pytestmark = pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna nicht installiert")

# Script-Pfad
SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "run_optuna_study.py"


class TestOptunaRunnerSmoke:
    """Smoke-Tests für Optuna Runner."""

    def test_script_exists(self):
        """Script existiert."""
        assert SCRIPT_PATH.exists()

    def test_script_help(self):
        """Script --help funktioniert."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Optuna" in result.stdout or "strategy" in result.stdout

    @pytest.mark.skip(
        reason="Requires valid strategy with parameter_schema - defer to integration tests"
    )
    def test_script_invalid_strategy(self):
        """Script mit ungültiger Strategie: Exit != 0."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--strategy",
                "nonexistent_strategy",
                "--n-trials",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Sollte mit Error beenden
        assert result.returncode != 0

    @pytest.mark.skip(
        reason="Requires valid config, data, and strategy - defer to integration tests"
    )
    def test_script_single_trial(self):
        """Script mit 1 Trial: Funktioniert (langsam)."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--strategy",
                "ma_crossover",
                "--n-trials",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=60,  # Max 60s
        )

        # Sollte erfolgreich sein
        assert result.returncode == 0
