#!/usr/bin/env python3
# scripts/run_research_golden_path.py
"""
Peak_Trade Research Golden Path Runner (Phase 81)
==================================================

Wrapper-Skript für die Ausführung von Research Golden Paths.

Unterstützte Golden Paths:
1. new_strategy: Neue Strategie validieren (Sweep → Profile → Tiering)
2. optimize: Bestehende Strategie optimieren (Full Pipeline)
3. portfolio: Portfolio-Robustness testen

Usage:
    # Golden Path 1: Neue Strategie validieren
    python scripts/run_research_golden_path.py new_strategy \\
        --strategy-id my_new_strategy \\
        --sweep-name my_new_strategy_basic

    # Golden Path 2: Strategie optimieren
    python scripts/run_research_golden_path.py optimize \\
        --sweep-name rsi_reversion_tuning_v2 \\
        --top-n 5

    # Golden Path 3: Portfolio-Robustness
    python scripts/run_research_golden_path.py portfolio \\
        --preset core_balanced

    # Hilfe
    python scripts/run_research_golden_path.py --help
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"
RESEARCH_CLI = PROJECT_ROOT / "scripts" / "research_cli.py"
PROFILE_CLI = PROJECT_ROOT / "scripts" / "profile_research_and_portfolio.py"


def run_command(cmd: list[str], description: str) -> bool:
    """Führt einen Befehl aus und gibt Erfolg zurück."""
    logger.info(f">>> {description}")
    logger.info(f"    Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        logger.info(f"    ✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"    ❌ {description} failed: {e}")
        return False


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
    logger.info(f"Strategy: {args.strategy_id}")
    logger.info(f"Sweep: {args.sweep_name}")
    logger.info("=" * 60)

    python = sys.executable
    steps = []

    # Step 1: Sweep
    steps.append((
        [python, str(RESEARCH_CLI), "sweep",
         "--sweep-name", args.sweep_name,
         "--config", str(CONFIG_PATH)],
        "Step 1/5: Running parameter sweep"
    ))

    # Step 2: Report
    steps.append((
        [python, str(RESEARCH_CLI), "report",
         "--sweep-name", args.sweep_name,
         "--format", "both",
         "--with-plots"],
        "Step 2/5: Generating sweep report"
    ))

    # Step 3: Walk-Forward
    steps.append((
        [python, str(RESEARCH_CLI), "walkforward",
         "--sweep-name", args.sweep_name,
         "--top-n", str(args.top_n),
         "--train-window", args.train_window,
         "--test-window", args.test_window],
        "Step 3/5: Walk-forward testing"
    ))

    # Step 4: Monte-Carlo
    steps.append((
        [python, str(RESEARCH_CLI), "montecarlo",
         "--sweep-name", args.sweep_name,
         "--config", str(CONFIG_PATH),
         "--top-n", str(args.top_n),
         "--num-runs", str(args.mc_runs)],
        "Step 4/5: Monte-Carlo analysis"
    ))

    # Step 5: Profile
    steps.append((
        [python, str(PROFILE_CLI),
         "--strategy-id", args.strategy_id,
         "--sweep-name", args.sweep_name,
         "--with-regime",
         "--with-montecarlo",
         "--output-format", "both"],
        "Step 5/5: Generating strategy profile"
    ))

    # Execute all steps
    success_count = 0
    for cmd, desc in steps:
        if run_command(cmd, desc):
            success_count += 1
        elif not args.continue_on_error:
            logger.error("Stopping due to error. Use --continue-on-error to proceed.")
            break

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Golden Path 1 completed: {success_count}/{len(steps)} steps successful")
    logger.info("=" * 60)

    if success_count == len(steps):
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. Review profile: reports/strategy_profiles/{args.strategy_id}_profile_v1.json")
        logger.info(f"  2. Add tiering entry to config/strategy_tiering.toml")
        logger.info(f"  3. Run: python -c \"from src.experiments.portfolio_presets import get_strategy_tier; print(get_strategy_tier('{args.strategy_id}'))\"")

    return 0 if success_count == len(steps) else 1


def golden_path_optimize(args: argparse.Namespace) -> int:
    """
    Golden Path 2: Strategie optimieren.

    Nutzt die research_cli pipeline für einen vollständigen Durchlauf.
    """
    logger.info("=" * 60)
    logger.info("GOLDEN PATH 2: Strategie optimieren")
    logger.info(f"Sweep: {args.sweep_name}")
    logger.info(f"Top-N: {args.top_n}")
    logger.info("=" * 60)

    python = sys.executable

    cmd = [
        python, str(RESEARCH_CLI), "pipeline",
        "--sweep-name", args.sweep_name,
        "--config", str(CONFIG_PATH),
        "--format", "both",
        "--with-plots",
        "--top-n", str(args.top_n),
    ]

    if args.run_walkforward:
        cmd.extend([
            "--run-walkforward",
            "--train-window", args.train_window,
            "--test-window", args.test_window,
        ])

    if args.run_montecarlo:
        cmd.extend([
            "--run-montecarlo",
            "--mc-num-runs", str(args.mc_runs),
        ])

    if args.run_stress:
        cmd.extend([
            "--run-stress-tests",
            "--stress-scenarios", "flash_crash", "high_volatility", "trend_reversal",
        ])

    success = run_command(cmd, "Running full optimization pipeline")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Golden Path 2 completed" if success else "Golden Path 2 failed")
    logger.info("=" * 60)

    if success:
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. Review report: reports/sweeps/{args.sweep_name}/report.html")
        logger.info(f"  2. Update strategy profile if metrics improved")
        logger.info(f"  3. Update tiering in config/strategy_tiering.toml if needed")

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
    logger.info(f"Preset: {args.preset}")
    logger.info("=" * 60)

    python = sys.executable

    # Step 1: Tiering-Compliance
    logger.info(">>> Step 1/2: Validating tiering compliance")
    try:
        from src.experiments.portfolio_presets import (
            validate_preset_tiering_compliance,
            load_tiered_preset,
        )
        from pathlib import Path

        presets_dir = PROJECT_ROOT / "config" / "portfolio_presets"
        preset_file = presets_dir / f"{args.preset}.toml"

        if preset_file.exists():
            recipe = load_tiered_preset(args.preset, presets_dir=presets_dir, enforce_compliance=False)

            # Determine allowed tiers based on preset name
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
                logger.info(f"    ✅ Tiering compliance: PASSED")
            else:
                logger.warning(f"    ⚠️ Tiering compliance: FAILED")
                logger.warning(f"    Violations: {result.violations}")
                if not args.continue_on_error:
                    return 1
        else:
            logger.warning(f"    ⚠️ Preset file not found: {preset_file}")
            logger.info(f"    Will try to load from portfolio_recipes.toml")

    except Exception as e:
        logger.error(f"    ❌ Tiering validation failed: {e}")
        if not args.continue_on_error:
            return 1

    # Step 2: Portfolio-Robustness
    cmd = [
        python, str(RESEARCH_CLI), "portfolio",
        "--config", str(CONFIG_PATH),
        "--portfolio-preset", args.preset,
        "--format", "both",
    ]

    if args.with_plots:
        cmd.append("--with-plots")

    success = run_command(cmd, "Step 2/2: Running portfolio robustness")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Golden Path 3 completed" if success else "Golden Path 3 failed")
    logger.info("=" * 60)

    if success:
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. Review report: reports/portfolio_robustness/{args.preset}_robustness.html")
        logger.info(f"  2. Check Go/No-Go criteria (Sharpe, MC p5, Stress Min)")
        logger.info(f"  3. If Go: Prepare for Shadow/Testnet")

    return 0 if success else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Peak_Trade Research Golden Path Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # New strategy validation
  python scripts/run_research_golden_path.py new_strategy \\
      --strategy-id my_new_strategy --sweep-name my_new_strategy_basic

  # Optimize existing strategy
  python scripts/run_research_golden_path.py optimize \\
      --sweep-name rsi_reversion_tuning_v2 --top-n 5

  # Portfolio robustness
  python scripts/run_research_golden_path.py portfolio \\
      --preset core_balanced
        """,
    )

    subparsers = parser.add_subparsers(dest="golden_path", help="Golden Path to execute")

    # Golden Path 1: new_strategy
    p1 = subparsers.add_parser("new_strategy", help="Validate a new strategy")
    p1.add_argument("--strategy-id", required=True, help="Strategy ID")
    p1.add_argument("--sweep-name", required=True, help="Sweep name to use")
    p1.add_argument("--top-n", type=int, default=5, help="Top N configs to test (default: 5)")
    p1.add_argument("--train-window", default="90d", help="Walk-forward train window (default: 90d)")
    p1.add_argument("--test-window", default="30d", help="Walk-forward test window (default: 30d)")
    p1.add_argument("--mc-runs", type=int, default=500, help="Monte-Carlo runs (default: 500)")
    p1.add_argument("--continue-on-error", action="store_true", help="Continue even if a step fails")

    # Golden Path 2: optimize
    p2 = subparsers.add_parser("optimize", help="Optimize an existing strategy")
    p2.add_argument("--sweep-name", required=True, help="Sweep name to use")
    p2.add_argument("--top-n", type=int, default=5, help="Top N configs to test (default: 5)")
    p2.add_argument("--train-window", default="90d", help="Walk-forward train window (default: 90d)")
    p2.add_argument("--test-window", default="30d", help="Walk-forward test window (default: 30d)")
    p2.add_argument("--mc-runs", type=int, default=500, help="Monte-Carlo runs (default: 500)")
    p2.add_argument("--run-walkforward", action="store_true", default=True, help="Run walk-forward testing")
    p2.add_argument("--run-montecarlo", action="store_true", default=True, help="Run Monte-Carlo analysis")
    p2.add_argument("--run-stress", action="store_true", default=True, help="Run stress tests")
    p2.add_argument("--continue-on-error", action="store_true", help="Continue even if a step fails")

    # Golden Path 3: portfolio
    p3 = subparsers.add_parser("portfolio", help="Test portfolio robustness")
    p3.add_argument("--preset", required=True, help="Portfolio preset name")
    p3.add_argument("--with-plots", action="store_true", default=True, help="Generate plots")
    p3.add_argument("--continue-on-error", action="store_true", help="Continue even if a step fails")

    args = parser.parse_args()

    if args.golden_path is None:
        parser.print_help()
        return 1

    if args.golden_path == "new_strategy":
        return golden_path_new_strategy(args)
    elif args.golden_path == "optimize":
        return golden_path_optimize(args)
    elif args.golden_path == "portfolio":
        return golden_path_portfolio(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
