# tests/test_research_golden_paths.py
"""
Tests für Phase 81: Research Golden Paths

Testet:
- Golden-Path-Skript ist ausführbar
- Golden-Path-Dokumentation existiert und ist vollständig
- Helper-Funktionen funktionieren korrekt
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_DIR = PROJECT_ROOT / "docs"


class TestGoldenPathScript:
    """Tests für das Golden-Path-Runner-Skript."""

    def test_script_exists(self):
        """Golden-Path-Skript existiert."""
        script = SCRIPTS_DIR / "run_research_golden_path.py"
        assert script.exists(), f"Script not found: {script}"

    def test_script_help_runs(self):
        """Skript --help funktioniert."""
        script = SCRIPTS_DIR / "run_research_golden_path.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Help failed: {result.stderr}"
        assert "Golden Path" in result.stdout or "golden_path" in result.stdout

    def test_new_strategy_help(self):
        """new_strategy subcommand help funktioniert."""
        script = SCRIPTS_DIR / "run_research_golden_path.py"
        result = subprocess.run(
            [sys.executable, str(script), "new_strategy", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--strategy-id" in result.stdout
        assert "--sweep-name" in result.stdout

    def test_optimize_help(self):
        """optimize subcommand help funktioniert."""
        script = SCRIPTS_DIR / "run_research_golden_path.py"
        result = subprocess.run(
            [sys.executable, str(script), "optimize", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--sweep-name" in result.stdout

    def test_portfolio_help(self):
        """portfolio subcommand help funktioniert."""
        script = SCRIPTS_DIR / "run_research_golden_path.py"
        result = subprocess.run(
            [sys.executable, str(script), "portfolio", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--preset" in result.stdout


class TestGoldenPathDocumentation:
    """Tests für die Golden-Path-Dokumentation."""

    def test_documentation_exists(self):
        """Golden-Paths-Dokumentation existiert."""
        doc = DOCS_DIR / "PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md"
        assert doc.exists(), f"Documentation not found: {doc}"

    def test_documentation_has_golden_paths(self):
        """Dokumentation enthält mindestens 3 Golden Paths."""
        doc = DOCS_DIR / "PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md"
        content = doc.read_text()

        # Prüfe auf Golden Path Sektionen
        assert "Golden Path 1" in content
        assert "Golden Path 2" in content
        assert "Golden Path 3" in content

    def test_documentation_has_cli_examples(self):
        """Dokumentation enthält CLI-Beispiele."""
        doc = DOCS_DIR / "PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md"
        content = doc.read_text()

        # Prüfe auf CLI-Befehle
        assert "research_cli.py" in content
        assert "python scripts/" in content or "python scripts" in content.lower()

    def test_documentation_references_tiering(self):
        """Dokumentation referenziert das Tiering-System."""
        doc = DOCS_DIR / "PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md"
        content = doc.read_text()

        assert "tier" in content.lower()
        assert "core" in content
        assert "aux" in content

    def test_documentation_has_quick_reference(self):
        """Dokumentation enthält Schnellreferenz."""
        doc = DOCS_DIR / "PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md"
        content = doc.read_text()

        assert "Schnellreferenz" in content or "Quick" in content or "CLI-Befehle" in content


class TestGoldenPathLinkage:
    """Tests für die Verlinkung der Golden-Paths-Doku."""

    def test_first_7_days_links_to_golden_paths(self):
        """PEAK_TRADE_FIRST_7_DAYS.md verlinkt zu Golden Paths."""
        doc = DOCS_DIR / "PEAK_TRADE_FIRST_7_DAYS.md"
        if not doc.exists():
            pytest.skip("PEAK_TRADE_FIRST_7_DAYS.md not found")

        content = doc.read_text()
        assert "PEAK_TRADE_RESEARCH_GOLDEN_PATHS" in content

    def test_overview_links_to_golden_paths(self):
        """PEAK_TRADE_V1_OVERVIEW_FULL.md verlinkt zu Golden Paths."""
        doc = DOCS_DIR / "PEAK_TRADE_V1_OVERVIEW_FULL.md"
        if not doc.exists():
            pytest.skip("PEAK_TRADE_V1_OVERVIEW_FULL.md not found")

        content = doc.read_text()
        assert "PEAK_TRADE_RESEARCH_GOLDEN_PATHS" in content


class TestGoldenPathIntegration:
    """Integration Tests für Golden Paths."""

    def test_tiering_functions_available(self):
        """Tiering-Funktionen sind importierbar."""
        from src.experiments.portfolio_presets import (
            get_strategies_by_tier,
            get_tiering_aware_strategies,
            get_all_tiered_strategies,
            validate_preset_tiering_compliance,
        )

        # Basic smoke test
        all_tiered = get_all_tiered_strategies()
        assert "core" in all_tiered
        assert "aux" in all_tiered
        assert "legacy" in all_tiered

    def test_portfolio_presets_exist(self):
        """Portfolio-Presets für Golden Paths existieren."""
        presets_dir = PROJECT_ROOT / "config" / "portfolio_presets"
        assert presets_dir.exists()

        # Mindestens 3 Presets
        presets = list(presets_dir.glob("*.toml"))
        assert len(presets) >= 3, f"Expected at least 3 presets, found {len(presets)}"

    def test_research_cli_exists(self):
        """research_cli.py existiert."""
        cli = SCRIPTS_DIR / "research_cli.py"
        assert cli.exists(), f"research_cli.py not found: {cli}"

    def test_profile_script_exists(self):
        """profile_research_and_portfolio.py existiert."""
        script = SCRIPTS_DIR / "profile_research_and_portfolio.py"
        assert script.exists(), f"profile script not found: {script}"
