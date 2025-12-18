"""
Tests für scripts/profile_research_and_portfolio.py (Phase 61)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DummyCompletedProcess:
    """Mock für subprocess.CompletedProcess."""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def fake_subprocess_run(
    command: list[str], check: bool = False, capture_output: bool = False, cwd: Path | None = None
) -> DummyCompletedProcess:
    """
    Mock für subprocess.run.

    Prüft, dass der Command sinnvoll aussieht (z.B. enthält "scripts/research_cli.py").
    """
    # Prüfe, dass es ein Python-Command ist
    assert command[0] == sys.executable or command[0].endswith("python") or command[0].endswith("python3")
    # Prüfe, dass ein Script-Pfad enthalten ist
    assert any("scripts/" in str(arg) or "research_cli.py" in str(arg) or "run_portfolio_robustness.py" in str(arg) for arg in command)

    return DummyCompletedProcess(returncode=0)


def test_profile_script_list_scenarios():
    """Test: Script kann Szenarien auflisten."""
    result = subprocess.run(
        [sys.executable, "scripts/profile_research_and_portfolio.py", "--list"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    assert result.returncode == 0
    assert "portfolio_multi_style_moderate" in result.stdout
    assert "pipeline_rsi_reversion_basic" in result.stdout
    assert "portfolio_robustness_multi_style_moderate" in result.stdout


@patch("subprocess.run")
def test_profile_script_runs_scenarios(mock_run: MagicMock):
    """Test: Script führt Szenarien aus (mit gemocktem subprocess)."""
    # Mock subprocess.run
    mock_run.return_value = DummyCompletedProcess(returncode=0)

    # Importiere und führe main() aus
    from scripts.profile_research_and_portfolio import main

    # Simuliere --scenario Argument
    with patch("sys.argv", ["profile_research_and_portfolio.py", "--scenario", "portfolio_multi_style_moderate"]):
        result = main()

    # Prüfe, dass subprocess.run aufgerufen wurde
    assert mock_run.called
    # Prüfe, dass der Command sinnvoll aussieht
    call_args = mock_run.call_args
    assert call_args is not None
    command = call_args[0][0]
    assert "research_cli.py" in str(command) or "run_portfolio_robustness.py" in str(command)

    # main() sollte erfolgreich sein (0)
    assert result == 0


@patch("subprocess.run")
def test_profile_script_handles_failure(mock_run: MagicMock):
    """Test: Script behandelt Fehler korrekt."""
    # Mock subprocess.run mit Fehler
    mock_run.return_value = DummyCompletedProcess(returncode=1)

    from scripts.profile_research_and_portfolio import main

    # Simuliere --scenario Argument
    with patch("sys.argv", ["profile_research_and_portfolio.py", "--scenario", "portfolio_multi_style_moderate"]):
        # subprocess.run sollte check=True haben, daher wird CalledProcessError geworfen
        mock_run.side_effect = subprocess.CalledProcessError(1, ["python", "scripts/research_cli.py"])

        result = main()

    # main() sollte Fehler zurückgeben (1)
    assert result == 1


def test_profile_script_invalid_scenario():
    """Test: Script behandelt ungültige Szenario-Namen korrekt."""
    result = subprocess.run(
        [sys.executable, "scripts/profile_research_and_portfolio.py", "--scenario", "invalid_scenario"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Script sollte Fehler zurückgeben
    assert result.returncode == 1
    assert "Keine Szenarien gefunden" in result.stdout or "invalid_scenario" in result.stdout


@patch("subprocess.run")
def test_profile_script_output_format(mock_run: MagicMock, capsys):
    """Test: Script erzeugt sinnvolle Ausgabe."""
    mock_run.return_value = DummyCompletedProcess(returncode=0)

    from scripts.profile_research_and_portfolio import format_table

    results = [
        ("scenario_1", 42.3),
        ("scenario_2", 95.8),
    ]

    # Text-Format
    output = format_table(results, markdown=False)
    assert "scenario_1" in output
    assert "42.30" in output or "42.3" in output

    # Markdown-Format
    output_md = format_table(results, markdown=True)
    assert "| Scenario |" in output_md
    assert "scenario_1" in output_md





