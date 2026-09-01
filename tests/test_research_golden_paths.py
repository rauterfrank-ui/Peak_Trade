# tests/test_research_golden_paths.py
"""
Tests für Phase 81: Research Golden Paths

Testet:
- Golden-Path-Skript ist ausführbar via scripts/pt
- Command builders bind research_cli subcommands and dummy-data flags
- Golden-Path-Dokumentation beschreibt den heutigen Research-Contract
- Helper-Funktionen funktionieren korrekt
- No trading/selection/execution ownership transfer
"""

import argparse
import ast
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_DIR = PROJECT_ROOT / "docs"
PT_LAUNCHER = SCRIPTS_DIR / "pt"
GOLDEN_PATH_SCRIPT = SCRIPTS_DIR / "run_research_golden_path.py"
RESEARCH_CLI = SCRIPTS_DIR / "research_cli.py"

FORBIDDEN_OWNERSHIP_MARKERS = (
    "trading.master_v2",
    "SimulatedExecutionPort",
    "canonical_order_intent",
    "governed_futures_universe_producer_v1",
    "single_selected_future_policy_v1",
    "src.autonomous",
    "src.learning",
    "src.ai",
    "src.data.kraken",
    "fetch_ohlcv_df",
    "submit_order",
)


def _pt_run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PT_LAUNCHER), *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


class TestGoldenPathScript:
    """Tests für das Golden-Path-Runner-Skript."""

    def test_script_exists(self):
        """Golden-Path-Skript existiert."""
        assert GOLDEN_PATH_SCRIPT.exists(), f"Script not found: {GOLDEN_PATH_SCRIPT}"

    def test_script_help_runs(self):
        """Skript --help funktioniert über scripts/pt."""
        result = _pt_run(str(GOLDEN_PATH_SCRIPT), "--help")
        assert result.returncode == 0, f"Help failed: {result.stderr}"
        assert "Golden Path" in result.stdout or "golden_path" in result.stdout

    def test_new_strategy_help(self):
        """new_strategy subcommand help funktioniert."""
        result = _pt_run(str(GOLDEN_PATH_SCRIPT), "new_strategy", "--help")
        assert result.returncode == 0
        assert "--strategy-id" in result.stdout
        assert "--sweep-name" in result.stdout

    def test_optimize_help(self):
        """optimize subcommand help funktioniert."""
        result = _pt_run(str(GOLDEN_PATH_SCRIPT), "optimize", "--help")
        assert result.returncode == 0
        assert "--sweep-name" in result.stdout

    def test_portfolio_help(self):
        """portfolio subcommand help funktioniert."""
        result = _pt_run(str(GOLDEN_PATH_SCRIPT), "portfolio", "--help")
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
        # Docs-Hygiene: CLI-Snippets müssen den kanonischen Launcher nutzen.
        assert "./scripts/pt scripts/" in content
        assert "python3 scripts/" not in content
        assert "python scripts/run_research_golden_path.py" not in content
        assert "--use-dummy-data" in content
        assert "NON_AUTHORITY_RESEARCH_OPERATOR" in content

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


class TestGoldenPathOperatorContract:
    """WP-01: launcher, dummy-data, subcommand, and authority-boundary proofs."""

    def test_canonical_argv_uses_scripts_pt(self) -> None:
        from scripts.run_research_golden_path import canonical_research_cli_argv

        argv = canonical_research_cli_argv("sweep", "--sweep-name", "demo")
        assert argv[0] == str(PT_LAUNCHER)
        assert argv[1] == str(RESEARCH_CLI)
        assert argv[2] == "sweep"
        assert "python" not in Path(argv[0]).name
        assert "python3" not in Path(argv[0]).name

    def test_new_strategy_commands_bind_dummy_and_existing_subcommands(self) -> None:
        from scripts.run_research_golden_path import (
            GOLDEN_PATH_RESEARCH_CLI_SUBCOMMANDS,
            new_strategy_commands,
        )

        args = argparse.Namespace(
            strategy_id="rsi_reversion",
            sweep_name="rsi_reversion_basic",
            top_n=5,
            train_window="90d",
            test_window="30d",
            mc_runs=50,
        )
        steps = new_strategy_commands(args)
        subcommands = [cmd[2] for cmd, _desc in steps]
        assert subcommands == [
            "sweep",
            "report",
            "walkforward",
            "montecarlo",
            "strategy-profile",
        ]
        for cmd, _desc in steps:
            assert cmd[0] == str(PT_LAUNCHER)
            assert cmd[1] == str(RESEARCH_CLI)
            assert cmd[2] in GOLDEN_PATH_RESEARCH_CLI_SUBCOMMANDS
        walkforward = steps[2][0]
        montecarlo = steps[3][0]
        profile = steps[4][0]
        assert "--use-dummy-data" in walkforward
        assert "--use-dummy-data" in montecarlo
        assert "--use-dummy-data" in profile

    def test_optimize_and_portfolio_commands_bind_dummy(self) -> None:
        from scripts.run_research_golden_path import optimize_command, portfolio_command

        opt = optimize_command(
            argparse.Namespace(
                sweep_name="rsi_reversion_tuning_v2",
                top_n=5,
                train_window="90d",
                test_window="30d",
                mc_runs=50,
                run_walkforward=True,
                run_montecarlo=True,
                run_stress=True,
            )
        )
        assert opt[2] == "pipeline"
        assert "--walkforward-use-dummy-data" in opt
        assert "--mc-use-dummy-data" in opt
        assert "--stress-use-dummy-data" in opt

        port = portfolio_command(argparse.Namespace(preset="core_balanced", with_plots=True))
        assert port[2] == "portfolio"
        assert "--use-dummy-data" in port

    def test_research_cli_exposes_all_golden_path_subcommands(self) -> None:
        import argparse

        import scripts.research_cli as research_cli
        from scripts.run_research_golden_path import GOLDEN_PATH_RESEARCH_CLI_SUBCOMMANDS

        parser = research_cli.build_parser()
        subparsers = [
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        ]
        assert subparsers, "research_cli parser has no subcommands"
        choices = set(subparsers[0].choices)
        missing = set(GOLDEN_PATH_RESEARCH_CLI_SUBCOMMANDS) - choices
        assert not missing, f"missing research_cli subcommands: {missing}"

    def test_wrapper_has_no_forbidden_ownership_imports(self) -> None:
        source = GOLDEN_PATH_SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        joined = " ".join(sorted(imported))
        for marker in FORBIDDEN_OWNERSHIP_MARKERS:
            assert marker not in source
            assert marker not in joined
        assert "AUTHORITY_EFFECT" in source
        assert "NON_AUTHORITY_RESEARCH_OPERATOR" in source

    def test_research_cli_does_not_restore_legacy_venue_ohlcv(self) -> None:
        source = RESEARCH_CLI.read_text(encoding="utf-8")
        assert "src.data.kraken" not in source
        assert "fetch_ohlcv_df" not in source
        assert "legacy_venue_ohlcv_removed" not in source
        assert "LEGACY_VENUE_OHLCV_NOT_OPERATIVE" in source
