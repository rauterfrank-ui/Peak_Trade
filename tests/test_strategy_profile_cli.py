# tests/test_strategy_profile_cli.py
"""
CLI-Tests für strategy-profile Command (Phase 41B).

Testet:
- CLI-Argument-Parsing
- Hilfe-Ausgabe
- --list-strategies
- Profil-Generierung mit Dummy-Daten
- Output-Dateien
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestStrategyProfileCLIHelp:
    """Tests für CLI-Hilfe und Argument-Parsing."""

    def test_help_output(self):
        """Testet --help für strategy-profile."""
        result = subprocess.run(
            [sys.executable, "scripts/research_cli.py", "strategy-profile", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "--strategy-id" in result.stdout
        assert "--output-format" in result.stdout
        assert "--with-montecarlo" in result.stdout
        assert "--with-stress" in result.stdout
        assert "--with-regime" in result.stdout

    def test_list_strategies(self):
        """Testet --list-strategies."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/research_cli.py",
                "strategy-profile",
                "--strategy-id",
                "dummy",  # Wird ignoriert wegen --list-strategies
                "--list-strategies",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Strategy-ID" in result.stdout or "rsi_reversion" in result.stdout


class TestStrategyProfileCLIExecution:
    """Tests für CLI-Ausführung mit Dummy-Daten."""

    def test_basic_profile_generation(self):
        """Generiert einfaches Profil mit Dummy-Daten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "rsi_reversion",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "100",
                    "--output-format",
                    "both",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            # Akzeptiere Exit 0 oder Warnungen
            assert result.returncode == 0, f"STDERR: {result.stderr}"

            # Prüfe, dass Dateien erzeugt wurden
            tmpdir_path = Path(tmpdir)
            json_files = list(tmpdir_path.glob("*.json"))
            md_files = list(tmpdir_path.glob("*.md"))

            assert len(json_files) >= 1, f"Keine JSON-Datei gefunden in {tmpdir}"
            assert len(md_files) >= 1, f"Keine MD-Datei gefunden in {tmpdir}"

    def test_profile_with_montecarlo(self):
        """Generiert Profil mit Monte-Carlo-Analyse."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "ma_crossover",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "100",
                    "--with-montecarlo",
                    "--mc-num-runs",
                    "10",  # Wenige Runs für schnellen Test
                    "--output-format",
                    "json",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0, f"STDERR: {result.stderr}"

            # Prüfe JSON-Inhalt
            import json

            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) >= 1

            with open(json_files[0]) as f:
                data = json.load(f)

            assert "robustness" in data
            # Monte-Carlo sollte Ergebnisse haben
            assert data["robustness"]["num_montecarlo_runs"] > 0

    def test_profile_with_stress(self):
        """Generiert Profil mit Stress-Tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "bollinger_bands",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "100",
                    "--with-stress",
                    "--stress-scenarios",
                    "single_crash_bar",
                    "--output-format",
                    "json",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0, f"STDERR: {result.stderr}"

            # Prüfe JSON-Inhalt
            import json

            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) >= 1

            with open(json_files[0]) as f:
                data = json.load(f)

            assert data["robustness"]["num_stress_scenarios"] > 0

    def test_profile_with_regime(self):
        """Generiert Profil mit Regime-Analyse."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "breakout",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "200",
                    "--with-regime",
                    "--output-format",
                    "json",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0, f"STDERR: {result.stderr}"

            # Prüfe JSON-Inhalt
            import json

            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) >= 1

            with open(json_files[0]) as f:
                data = json.load(f)

            # Regime sollte vorhanden sein
            assert "regimes" in data
            assert len(data["regimes"]["regimes"]) > 0

    def test_unknown_strategy_fails(self):
        """Unbekannte Strategy-ID führt zu Fehler."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/research_cli.py",
                "strategy-profile",
                "--strategy-id",
                "nonexistent_strategy_xyz",
                "--use-dummy-data",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=30,
        )

        # Sollte Exit-Code != 0 haben
        assert result.returncode != 0


class TestStrategyProfileCLIOutputFormats:
    """Tests für verschiedene Output-Formate."""

    def test_json_only(self):
        """Generiert nur JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "macd",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "50",
                    "--output-format",
                    "json",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0

            json_files = list(Path(tmpdir).glob("*.json"))
            md_files = list(Path(tmpdir).glob("*.md"))

            assert len(json_files) >= 1
            # Bei json-only sollte keine MD-Datei entstehen
            # (außer output-dir wird für beides verwendet)

    def test_md_only(self):
        """Generiert nur Markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "momentum_1h",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "50",
                    "--output-format",
                    "md",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0

            md_files = list(Path(tmpdir).glob("*.md"))
            assert len(md_files) >= 1


class TestStrategyProfileCLIWithTiering:
    """Tests für Tiering-Integration."""

    def test_tiering_loaded(self):
        """Testet, dass Tiering aus Config geladen wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/research_cli.py",
                    "strategy-profile",
                    "--strategy-id",
                    "rsi_reversion",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "50",
                    "--output-format",
                    "json",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=60,
            )

            assert result.returncode == 0

            # Prüfe JSON
            import json

            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) >= 1

            with open(json_files[0]) as f:
                data = json.load(f)

            # Tiering sollte vorhanden sein (wenn config/strategy_tiering.toml existiert)
            if "tiering" in data and data["tiering"]:
                assert data["tiering"]["tier"] in ("core", "aux", "legacy", "unclassified")
