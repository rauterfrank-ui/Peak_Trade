#!/usr/bin/env python3
# scripts/run_research_golden_path.py
"""
Peak_Trade Research Golden Path Runner (Phase 81)
==================================================

Non-authority research-operator wrapper. Invoke via the canonical launcher:

    ./scripts/pt scripts/run_research_golden_path.py --help

Does not grant trading, selection, runtime, execution, promotion, learning,
or live authority. Child processes use scripts/pt + scripts/research_cli.py.

Supported Golden Paths:
1. new_strategy: Neue Strategie validieren (Sweep → Profile → Tiering)
2. optimize: Bestehende Strategie optimieren (Full Pipeline)
3. portfolio: Portfolio-Robustness testen
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"
CANONICAL_LAUNCHER = PROJECT_ROOT / "scripts" / "pt"
RESEARCH_CLI = PROJECT_ROOT / "scripts" / "research_cli.py"

AUTHORITY_CLASS = "NON_AUTHORITY_RESEARCH_OPERATOR"
AUTHORITY_EFFECT = "NONE"
GOLDEN_PATH_ROLE = "NON_AUTHORITY_RESEARCH_OPERATOR"

GOLDEN_PATH_RESEARCH_CLI_SUBCOMMANDS = (
    "sweep",
    "report",
    "walkforward",
    "montecarlo",
    "strategy-profile",
    "pipeline",
    "portfolio",
)


def canonical_research_cli_argv(*cli_args: str) -> list[str]:
    """Build a research_cli argv bound to scripts/pt. Fail closed if launcher missing."""
    if not CANONICAL_LAUNCHER.is_file():
        raise FileNotFoundError(
            f"PT_RUNTIME_FAIL: canonical launcher missing: {CANONICAL_LAUNCHER}"
        )
    if not RESEARCH_CLI.is_file():
        raise FileNotFoundError(f"research_cli missing: {RESEARCH_CLI}")
    if not cli_args:
        raise ValueError("research_cli subcommand required")
    return [str(CANONICAL_LAUNCHER), str(RESEARCH_CLI), *cli_args]


def run_command(cmd: list[str], description: str) -> bool:
    """Führt einen Befehl aus und gibt Erfolg zurück."""
    logger.info(">>> %s", description)
    logger.info("    Command: %s", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        logger.info("    ✅ %s completed", description)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("    ❌ %s failed: %s", description, e)
        return False


def new_strategy_commands(args: argparse.Namespace) -> list[tuple[list[str], str]]:
    """Deterministic command list for Golden Path 1 (offline dummy research)."""
    return [
        (
            canonical_research_cli_argv(
                "sweep",
                "--sweep-name",
                args.sweep_name,
                "--config",
                str(CONFIG_PATH),
            ),
            "Step 1/5: Running parameter sweep",
        ),
        (
            canonical_research_cli_argv(
                "report",
                "--sweep-name",
                args.sweep_name,
                "--format",
                "both",
                "--with-plots",
            ),
            "Step 2/5: Generating sweep report",
        ),
        (
            canonical_research_cli_argv(
                "walkforward",
                "--sweep-name",
                args.sweep_name,
                "--top-n",
                str(args.top_n),
                "--train-window",
                args.train_window,
                "--test-window",
                args.test_window,
                "--use-dummy-data",
            ),
            "Step 3/5: Walk-forward testing",
        ),
        (
            canonical_research_cli_argv(
                "montecarlo",
                "--sweep-name",
                args.sweep_name,
                "--config",
                str(CONFIG_PATH),
                "--top-n",
                str(args.top_n),
                "--num-runs",
                str(args.mc_runs),
                "--use-dummy-data",
            ),
            "Step 4/5: Monte-Carlo analysis",
        ),
        (
            canonical_research_cli_argv(
                "strategy-profile",
                "--strategy-id",
                args.strategy_id,
                "--config",
                str(CONFIG_PATH),
                "--with-regime",
                "--with-montecarlo",
                "--mc-num-runs",
                str(args.mc_runs),
                "--with-stress",
                "--stress-scenarios",
                "single_crash_bar",
                "vol_spike",
                "--output-format",
                "both",
                "--use-dummy-data",
            ),
            "Step 5/5: Generating strategy profile",
        ),
    ]


def optimize_command(args: argparse.Namespace) -> list[str]:
    """Deterministic command list for Golden Path 2 pipeline (offline dummy research)."""
    cmd = canonical_research_cli_argv(
        "pipeline",
        "--sweep-name",
        args.sweep_name,
        "--config",
        str(CONFIG_PATH),
        "--format",
        "both",
        "--with-plots",
        "--top-n",
        str(args.top_n),
    )
    if args.run_walkforward:
        cmd.extend(
            [
                "--run-walkforward",
                "--walkforward-train-window",
                args.train_window,
                "--walkforward-test-window",
                args.test_window,
                "--walkforward-use-dummy-data",
            ]
        )
    if args.run_montecarlo:
        cmd.extend(
            [
                "--run-montecarlo",
                "--mc-num-runs",
                str(args.mc_runs),
                "--mc-use-dummy-data",
            ]
        )
    if args.run_stress:
        cmd.extend(
            [
                "--run-stress-tests",
                "--stress-scenarios",
                "single_crash_bar",
                "vol_spike",
                "drawdown_extension",
                "gap_down_open",
                "--stress-use-dummy-data",
            ]
        )
    return cmd


def portfolio_command(args: argparse.Namespace) -> list[str]:
    """Deterministic command list for Golden Path 3 (offline dummy research)."""
    cmd = canonical_research_cli_argv(
        "portfolio",
        "--config",
        str(CONFIG_PATH),
        "--portfolio-preset",
        args.preset,
        "--format",
        "both",
        "--use-dummy-data",
    )
    if args.with_plots:
        cmd.append("--with-plots")
    return cmd


def golden_path_new_strategy(args: argparse.Namespace) -> int:
    """
    Golden Path 1: Neue Strategie validieren.

    Schritte:
    1. Sweep ausführen
    2. Report generieren
    3. Walk-Forward Testing
    4. Monte-Carlo Analyse
    5. StrategyProfile generieren
    """
    logger.info("=" * 60)
    logger.info("GOLDEN PATH 1: Neue Strategie validieren")
    logger.info("Strategy: %s", args.strategy_id)
    logger.info("Sweep: %s", args.sweep_name)
    logger.info("Authority: %s effect=%s", GOLDEN_PATH_ROLE, AUTHORITY_EFFECT)
    logger.info("=" * 60)

    steps = new_strategy_commands(args)
    success_count = 0
    for cmd, desc in steps:
        if run_command(cmd, desc):
            success_count += 1
        elif not args.continue_on_error:
            logger.error("Stopping due to error. Use --continue-on-error to proceed.")
            break

    logger.info("")
    logger.info("=" * 60)
    logger.info("Golden Path 1 completed: %s/%s steps successful", success_count, len(steps))
    logger.info("=" * 60)

    if success_count == len(steps):
        logger.info("")
        logger.info("Next steps:")
        logger.info(
            "  1. Review profile: reports/strategy_profiles/%s_profile_v1.json",
            args.strategy_id,
        )
        logger.info("  2. Add tiering entry to config/strategy_tiering.toml")
        logger.info(
            "  3. Run: ./scripts/pt -c "
            '"from src.experiments.portfolio_presets import get_strategy_tier; '
            "print(get_strategy_tier('%s'))\"",
            args.strategy_id,
        )

    return 0 if success_count == len(steps) else 1


def golden_path_optimize(args: argparse.Namespace) -> int:
    """
    Golden Path 2: Strategie optimieren.

    Nutzt die research_cli pipeline für einen vollständigen Durchlauf.
    """
    logger.info("=" * 60)
    logger.info("GOLDEN PATH 2: Strategie optimieren")
    logger.info("Sweep: %s", args.sweep_name)
    logger.info("Top-N: %s", args.top_n)
    logger.info("Authority: %s effect=%s", GOLDEN_PATH_ROLE, AUTHORITY_EFFECT)
    logger.info("=" * 60)

    cmd = optimize_command(args)
    success = run_command(cmd, "Running full optimization pipeline")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Golden Path 2 completed" if success else "Golden Path 2 failed")
    logger.info("=" * 60)

    if success:
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Review report: reports/sweeps/%s/report.html", args.sweep_name)
        logger.info("  2. Update strategy profile if metrics improved")
        logger.info("  3. Update tiering in config/strategy_tiering.toml if needed")

    return 0 if success else 1


def golden_path_portfolio(args: argparse.Namespace) -> int:
    """
    Golden Path 3: Portfolio-Robustness testen.

    Schritte:
    1. Tiering-Compliance validieren
    2. Portfolio-Robustness ausführen
    """
    logger.info("=" * 60)
    logger.info("GOLDEN PATH 3: Portfolio-Robustness")
    logger.info("Preset: %s", args.preset)
    logger.info("Authority: %s effect=%s", GOLDEN_PATH_ROLE, AUTHORITY_EFFECT)
    logger.info("=" * 60)

    logger.info(">>> Step 1/2: Validating tiering compliance")
    try:
        from src.experiments.portfolio_presets import (
            load_tiered_preset,
            validate_preset_tiering_compliance,
        )

        presets_dir = PROJECT_ROOT / "config" / "portfolio_presets"
        preset_file = presets_dir / f"{args.preset}.toml"

        if preset_file.exists():
            recipe = load_tiered_preset(
                args.preset, presets_dir=presets_dir, enforce_compliance=False
            )

            if args.preset.startswith("core_plus_aux") or args.preset.startswith("core_aux"):
                allowed_tiers = ["core", "aux"]
            elif args.preset.startswith("core_"):
                allowed_tiers = ["core"]
            else:
                allowed_tiers = ["core", "aux"]

            result = validate_preset_tiering_compliance(
                args.preset,
                allowed_tiers=allowed_tiers,
                recipe=recipe,
            )

            if result.is_compliant:
                logger.info("    ✅ Tiering compliance: PASSED")
            else:
                logger.warning("    ⚠️ Tiering compliance: FAILED")
                logger.warning("    Violations: %s", result.violations)
                if not args.continue_on_error:
                    return 1
        else:
            logger.warning("    ⚠️ Preset file not found: %s", preset_file)
            logger.info("    Will try to load from portfolio_recipes.toml")

    except Exception as e:
        logger.error("    ❌ Tiering validation failed: %s", e)
        if not args.continue_on_error:
            return 1

    cmd = portfolio_command(args)
    success = run_command(cmd, "Step 2/2: Running portfolio robustness")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Golden Path 3 completed" if success else "Golden Path 3 failed")
    logger.info("=" * 60)

    if success:
        logger.info("")
        logger.info("Next steps:")
        logger.info(
            "  1. Review report: reports/portfolio_robustness/%s/portfolio_robustness_report.html",
            args.preset,
        )
        logger.info("  2. Check Go/No-Go criteria (Sharpe, MC p5, Stress Min)")
        logger.info("  3. Shadow/Testnet/Live remain unauthorized; this path does not grant them")

    return 0 if success else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Peak_Trade Research Golden Path Runner (non-authority research operator)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./scripts/pt scripts/run_research_golden_path.py new_strategy \\
      --strategy-id my_new_strategy --sweep-name my_new_strategy_basic

  ./scripts/pt scripts/run_research_golden_path.py optimize \\
      --sweep-name rsi_reversion_tuning_v2 --top-n 5

  ./scripts/pt scripts/run_research_golden_path.py portfolio \\
      --preset core_balanced
        """,
    )

    subparsers = parser.add_subparsers(dest="golden_path", help="Golden Path to execute")

    p1 = subparsers.add_parser("new_strategy", help="Validate a new strategy")
    p1.add_argument("--strategy-id", required=True, help="Strategy ID")
    p1.add_argument("--sweep-name", required=True, help="Sweep name to use")
    p1.add_argument("--top-n", type=int, default=5, help="Top N configs to test (default: 5)")
    p1.add_argument(
        "--train-window", default="90d", help="Walk-forward train window (default: 90d)"
    )
    p1.add_argument("--test-window", default="30d", help="Walk-forward test window (default: 30d)")
    p1.add_argument("--mc-runs", type=int, default=500, help="Monte-Carlo runs (default: 500)")
    p1.add_argument(
        "--continue-on-error", action="store_true", help="Continue even if a step fails"
    )

    p2 = subparsers.add_parser("optimize", help="Optimize an existing strategy")
    p2.add_argument("--sweep-name", required=True, help="Sweep name to use")
    p2.add_argument("--top-n", type=int, default=5, help="Top N configs to test (default: 5)")
    p2.add_argument(
        "--train-window", default="90d", help="Walk-forward train window (default: 90d)"
    )
    p2.add_argument("--test-window", default="30d", help="Walk-forward test window (default: 30d)")
    p2.add_argument("--mc-runs", type=int, default=500, help="Monte-Carlo runs (default: 500)")
    p2.add_argument(
        "--run-walkforward", action="store_true", default=True, help="Run walk-forward testing"
    )
    p2.add_argument(
        "--run-montecarlo", action="store_true", default=True, help="Run Monte-Carlo analysis"
    )
    p2.add_argument("--run-stress", action="store_true", default=True, help="Run stress tests")
    p2.add_argument(
        "--continue-on-error", action="store_true", help="Continue even if a step fails"
    )

    p3 = subparsers.add_parser("portfolio", help="Test portfolio robustness")
    p3.add_argument("--preset", required=True, help="Portfolio preset name")
    p3.add_argument("--with-plots", action="store_true", default=True, help="Generate plots")
    p3.add_argument(
        "--continue-on-error", action="store_true", help="Continue even if a step fails"
    )

    args = parser.parse_args()

    if args.golden_path is None:
        parser.print_help()
        return 1

    if args.golden_path == "new_strategy":
        return golden_path_new_strategy(args)
    if args.golden_path == "optimize":
        return golden_path_optimize(args)
    if args.golden_path == "portfolio":
        return golden_path_portfolio(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
