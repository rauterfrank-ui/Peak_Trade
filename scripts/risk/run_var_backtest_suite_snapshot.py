#!/usr/bin/env python3
"""
Peak_Trade VaR Backtest Suite Snapshot Runner
==============================================

Single operator command that:
- Runs full VaR backtest suite (Kupiec POF + Christoffersen IND/CC + Basel Traffic Light)
- Optionally runs Phase 9A Duration Diagnostic
- Optionally runs Phase 9B Rolling Evaluation
- Writes deterministic markdown snapshot report
- Prints compact console summary
- Does NOT touch live modes (backtest/research only)

Usage:
    # Basic suite (Kupiec + Christoffersen + Basel)
    python scripts/risk/run_var_backtest_suite_snapshot.py \\
        --returns-file data/portfolio_returns.csv \\
        --var-file data/var_estimates.csv \\
        --confidence 0.99

    # With Phase 9A Duration Diagnostic
    python scripts/risk/run_var_backtest_suite_snapshot.py \\
        --returns-file data/portfolio_returns.csv \\
        --var-file data/var_estimates.csv \\
        --confidence 0.99 \\
        --enable-duration-diagnostic

    # With Phase 9B Rolling Evaluation
    python scripts/risk/run_var_backtest_suite_snapshot.py \\
        --returns-file data/portfolio_returns.csv \\
        --var-file data/var_estimates.csv \\
        --confidence 0.99 \\
        --enable-rolling \\
        --rolling-window-size 250 \\
        --rolling-step-size 50

    # Full diagnostics (Duration + Rolling)
    python scripts/risk/run_var_backtest_suite_snapshot.py \\
        --returns-file data/portfolio_returns.csv \\
        --var-file data/var_estimates.csv \\
        --confidence 0.99 \\
        --enable-duration-diagnostic \\
        --enable-rolling \\
        --rolling-window-size 250

    # Synthetic data demo
    python scripts/risk/run_var_backtest_suite_snapshot.py \\
        --use-synthetic \\
        --n-observations 500 \\
        --confidence 0.99

Output:
    - Console: Compact summary
    - File: reports/var_backtest/var_backtest_suite_snapshot_YYYYMMDD_HHMMSS.md

Phase 10 Implementation: Operator convenience pack for VaR backtest suite
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
    basel_traffic_light,
    traffic_light_recommendation,
    duration_independence_diagnostic,  # Phase 9A
    rolling_evaluation,  # Phase 9B
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="VaR Backtest Suite Snapshot Runner (Phase 10)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Data input
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        "--returns-file",
        type=str,
        help="Path to portfolio returns CSV file",
    )
    data_group.add_argument(
        "--use-synthetic",
        action="store_true",
        help="Use synthetic data for demo",
    )

    parser.add_argument(
        "--var-file",
        type=str,
        help="Path to VaR estimates CSV file (required if --returns-file)",
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="PORTFOLIO",
        help="Symbol/Portfolio name (default: PORTFOLIO)",
    )

    # VaR parameters
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.99,
        help="VaR confidence level (default: 0.99 for 99%% VaR)",
    )

    parser.add_argument(
        "--test-alpha",
        type=float,
        default=0.05,
        help="Significance level for hypothesis tests (default: 0.05)",
    )

    # Synthetic data options
    parser.add_argument(
        "--n-observations",
        type=int,
        default=500,
        help="Number of observations for synthetic data (default: 500)",
    )

    # Phase 9A: Duration Diagnostic
    parser.add_argument(
        "--enable-duration-diagnostic",
        action="store_true",
        help="Enable Phase 9A duration-based independence diagnostic",
    )

    # Phase 9B: Rolling Evaluation
    parser.add_argument(
        "--enable-rolling",
        action="store_true",
        help="Enable Phase 9B rolling-window evaluation",
    )

    parser.add_argument(
        "--rolling-window-size",
        type=int,
        default=250,
        help="Window size for rolling evaluation (default: 250)",
    )

    parser.add_argument(
        "--rolling-step-size",
        type=int,
        default=None,
        help="Step size for rolling evaluation (default: window_size, non-overlapping)",
    )

    # Output
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/var_backtest",
        help="Output directory for snapshot reports (default: reports/var_backtest)",
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing markdown report (console output only)",
    )

    # Debug
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    # Validation
    if args.returns_file and not args.var_file:
        parser.error("--var-file is required when using --returns-file")

    return args


def load_data(args: argparse.Namespace) -> tuple[pd.Series, pd.Series]:
    """
    Load returns and VaR estimates from files or generate synthetic data.

    Args:
        args: Parsed CLI arguments

    Returns:
        (returns, var_estimates) tuple of pd.Series
    """
    if args.use_synthetic:
        logger.info("Generating synthetic data...")
        return generate_synthetic_data(
            n_observations=args.n_observations,
            confidence_level=args.confidence,
        )
    else:
        logger.info(f"Loading returns from: {args.returns_file}")
        returns = pd.read_csv(args.returns_file, index_col=0, parse_dates=True, squeeze=True)
        if not isinstance(returns, pd.Series):
            returns = returns.iloc[:, 0]  # Take first column if DataFrame

        logger.info(f"Loading VaR estimates from: {args.var_file}")
        var_estimates = pd.read_csv(args.var_file, index_col=0, parse_dates=True, squeeze=True)
        if not isinstance(var_estimates, pd.Series):
            var_estimates = var_estimates.iloc[:, 0]

        logger.info(f"Loaded {len(returns)} returns and {len(var_estimates)} VaR estimates")
        return returns, var_estimates


def generate_synthetic_data(
    n_observations: int = 500,
    confidence_level: float = 0.99,
) -> tuple[pd.Series, pd.Series]:
    """
    Generate synthetic returns and VaR estimates for demo.

    Args:
        n_observations: Number of observations
        confidence_level: VaR confidence level

    Returns:
        (returns, var_estimates) tuple
    """
    expected_rate = 1 - confidence_level
    n_violations = int(n_observations * expected_rate)

    # Generate returns (mostly small losses, some large violations)
    returns_list = [-0.01] * (n_observations - n_violations) + [-0.03] * n_violations

    # Use fixed seed for deterministic output in tests
    rng = np.random.default_rng(42)
    rng.shuffle(returns_list)

    # Generate VaR estimates (constant)
    var_estimates_list = [-0.02] * n_observations

    dates = pd.date_range("2024-01-01", periods=n_observations, freq="D")
    returns = pd.Series(returns_list, index=dates)
    var_estimates = pd.Series(var_estimates_list, index=dates)

    return returns, var_estimates


def run_suite(
    returns: pd.Series,
    var_estimates: pd.Series,
    confidence_level: float,
    test_alpha: float,
    symbol: str,
    enable_duration: bool,
    enable_rolling: bool,
    rolling_window_size: int,
    rolling_step_size: Optional[int],
) -> dict:
    """
    Run full VaR backtest suite.

    Returns:
        Dictionary with all results
    """
    logger.info("=" * 70)
    logger.info("Running VaR Backtest Suite...")
    logger.info("=" * 70)

    # 1. Run VaRBacktestRunner (Kupiec POF)
    logger.info("Step 1/6: Kupiec POF Test...")
    runner = VaRBacktestRunner(
        confidence_level=confidence_level,
        significance_level=test_alpha,
    )
    backtest_result = runner.run(returns, var_estimates, symbol=symbol)
    logger.info(f"  Kupiec POF: {'PASS' if backtest_result.kupiec.is_valid else 'FAIL'}")

    # Extract violations
    violations = backtest_result.violations.violations.tolist()
    n_violations = backtest_result.violations.n_violations

    # 2. Christoffersen Independence Test
    logger.info("Step 2/6: Christoffersen Independence Test...")
    independence_result = christoffersen_independence_test(violations, alpha=test_alpha)
    logger.info(f"  Independence: {'PASS' if independence_result.passed else 'FAIL'}")

    # 3. Christoffersen Conditional Coverage Test
    logger.info("Step 3/6: Christoffersen Conditional Coverage Test...")
    var_alpha = 1 - confidence_level
    cc_result = christoffersen_conditional_coverage_test(
        violations, alpha=test_alpha, var_alpha=var_alpha
    )
    logger.info(f"  Conditional Coverage: {'PASS' if cc_result.passed else 'FAIL'}")

    # 4. Basel Traffic Light
    logger.info("Step 4/6: Basel Traffic Light Test...")
    traffic_light_result = basel_traffic_light(
        n_violations,
        backtest_result.violations.n_observations,
        confidence_level,
    )
    logger.info(f"  Basel Zone: {traffic_light_result.zone.value.upper()}")

    # 5. Phase 9A: Duration Diagnostic (optional)
    duration_result = None
    if enable_duration:
        logger.info("Step 5/6: Duration Independence Diagnostic (Phase 9A)...")
        duration_result = duration_independence_diagnostic(
            violations,
            expected_rate=var_alpha,
            timestamps=backtest_result.violations.dates,
        )
        logger.info(f"  Duration Ratio: {duration_result.duration_ratio:.4f}")
        logger.info(f"  Clustering: {'YES' if duration_result.is_suspicious() else 'NO'}")
    else:
        logger.info("Step 5/6: Duration Diagnostic skipped (not enabled)")

    # 6. Phase 9B: Rolling Evaluation (optional)
    rolling_result = None
    if enable_rolling:
        logger.info("Step 6/6: Rolling-Window Evaluation (Phase 9B)...")
        rolling_result = rolling_evaluation(
            violations,
            window_size=rolling_window_size,
            step_size=rolling_step_size,
            var_alpha=var_alpha,
            test_alpha=test_alpha,
            timestamps=backtest_result.violations.dates,
        )
        logger.info(f"  Windows: {rolling_result.summary.n_windows}")
        logger.info(f"  Pass-Rate: {rolling_result.summary.all_pass_rate:.1%}")
        logger.info(f"  Stability: {rolling_result.summary.verdict_stability:.1%}")
    else:
        logger.info("Step 6/6: Rolling Evaluation skipped (not enabled)")

    logger.info("=" * 70)

    return {
        "backtest": backtest_result,
        "independence": independence_result,
        "conditional_coverage": cc_result,
        "traffic_light": traffic_light_result,
        "duration": duration_result,
        "rolling": rolling_result,
    }


def format_console_summary(results: dict, symbol: str, confidence_level: float) -> str:
    """
    Format compact console summary.

    Args:
        results: Results dictionary from run_suite()
        symbol: Symbol name
        confidence_level: VaR confidence level

    Returns:
        Formatted string for console output
    """
    backtest = results["backtest"]
    independence = results["independence"]
    cc = results["conditional_coverage"]
    traffic_light = results["traffic_light"]
    duration = results.get("duration")
    rolling = results.get("rolling")

    lines = [
        "",
        "=" * 70,
        f"VAR BACKTEST SUITE SUMMARY - {symbol}",
        "=" * 70,
        f"VaR Confidence Level:  {confidence_level:.1%}",
        f"Observations:          {backtest.violations.n_observations}",
        f"Violations:            {backtest.violations.n_violations}",
        f"Violation Rate:        {backtest.violations.violation_rate:.2%}",
        "",
        "Core Tests:",
        f"  Kupiec POF:          {'✓ PASS' if backtest.kupiec.is_valid else '✗ FAIL'}  (p={backtest.kupiec.p_value:.4f})",
        f"  Independence:        {'✓ PASS' if independence.passed else '✗ FAIL'}  (p={independence.p_value:.4f})",
        f"  Cond. Coverage:      {'✓ PASS' if cc.passed else '✗ FAIL'}  (p={cc.p_value:.4f})",
        f"  Basel Traffic Light: {traffic_light.zone.value.upper()}",
        "",
    ]

    # Phase 9A: Duration Diagnostic
    if duration:
        lines.extend(
            [
                "Phase 9A: Duration Diagnostic (optional)",
                f"  Duration Ratio:      {duration.duration_ratio:.4f}",
                f"  Clustering:          {'⚠️  YES' if duration.is_suspicious() else '✓ NO'}",
                "",
            ]
        )

    # Phase 9B: Rolling Evaluation
    if rolling:
        lines.extend(
            [
                "Phase 9B: Rolling Evaluation (optional)",
                f"  Windows Evaluated:   {rolling.summary.n_windows}",
                f"  All-Pass Rate:       {rolling.summary.all_pass_rate:.1%}",
                f"  Verdict Stability:   {rolling.summary.verdict_stability:.1%}",
                f"  Assessment:          {rolling.summary.notes[:50]}...",
                "",
            ]
        )

    # Overall Verdict
    all_core_passed = backtest.kupiec.is_valid and independence.passed and cc.passed

    lines.extend(
        [
            "Overall Verdict:",
            f"  Core Tests:          {'✅ ALL PASSED' if all_core_passed else '❌ SOME FAILED'}",
            "=" * 70,
            "",
        ]
    )

    return "\n".join(lines)


def generate_markdown_report(
    results: dict,
    symbol: str,
    confidence_level: float,
    test_alpha: float,
    timestamp: datetime,
) -> str:
    """
    Generate deterministic markdown snapshot report.

    Args:
        results: Results dictionary from run_suite()
        symbol: Symbol name
        confidence_level: VaR confidence level
        test_alpha: Significance level
        timestamp: Report timestamp

    Returns:
        Markdown string
    """
    backtest = results["backtest"]
    independence = results["independence"]
    cc = results["conditional_coverage"]
    traffic_light = results["traffic_light"]
    duration = results.get("duration")
    rolling = results.get("rolling")

    lines = [
        f"# VaR Backtest Suite Snapshot",
        "",
        f"**Generated:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Symbol:** {symbol}  ",
        f"**VaR Confidence:** {confidence_level:.1%}  ",
        f"**Test Significance:** {test_alpha:.2%}  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Observations:** {backtest.violations.n_observations}",
        f"- **Violations:** {backtest.violations.n_violations}",
        f"- **Violation Rate:** {backtest.violations.violation_rate:.2%}",
        f"- **Expected Rate:** {1 - confidence_level:.2%}",
        "",
        "---",
        "",
        "## Core Tests",
        "",
        "### Kupiec Proportion of Failures (POF)",
        "",
        f"- **Result:** {'✓ PASS' if backtest.kupiec.is_valid else '✗ FAIL'}",
        f"- **LR Statistic:** {backtest.kupiec.lr_statistic:.4f}",
        f"- **p-value:** {backtest.kupiec.p_value:.4f}",
        f"- **Critical Value:** {backtest.kupiec.critical_value:.4f}",
        "",
        "### Christoffersen Independence Test",
        "",
        f"- **Result:** {'✓ PASS' if independence.passed else '✗ FAIL'}",
        f"- **LR Statistic:** {independence.lr_statistic:.4f}",
        f"- **p-value:** {independence.p_value:.4f}",
        f"- **Critical Value:** {independence.critical_value:.4f}",
        "",
        "### Christoffersen Conditional Coverage Test",
        "",
        f"- **Result:** {'✓ PASS' if cc.passed else '✗ FAIL'}",
        f"- **LR Statistic:** {cc.lr_statistic:.4f}",
        f"- **p-value:** {cc.p_value:.4f}",
        f"- **Critical Value:** {cc.critical_value:.4f}",
        "",
        "### Basel Traffic Light",
        "",
        f"- **Zone:** {traffic_light.zone.value.upper()}",
        f"- **Recommendation:** {traffic_light_recommendation(traffic_light)}",
        "",
    ]

    # Phase 9A: Duration Diagnostic
    if duration:
        lines.extend(
            [
                "---",
                "",
                "## Phase 9A: Duration Diagnostic (Optional)",
                "",
                f"- **Mean Duration:** {duration.mean_duration:.2f}",
                f"- **Expected Duration:** {duration.expected_duration:.2f}",
                f"- **Duration Ratio:** {duration.duration_ratio:.4f}",
                f"- **Clustering Score:** {duration.clustering_score:.4f}",
                f"- **Suspicious Clustering:** {'⚠️  YES' if duration.is_suspicious() else '✓ NO'}",
                "",
                f"**Notes:** {duration.notes}",
                "",
            ]
        )

    # Phase 9B: Rolling Evaluation
    if rolling:
        lines.extend(
            [
                "---",
                "",
                "## Phase 9B: Rolling Evaluation (Optional)",
                "",
                f"- **Windows Evaluated:** {rolling.summary.n_windows}",
                f"- **Window Size:** {rolling.window_size}",
                f"- **Step Size:** {rolling.step_size}",
                "",
                "### Pass Rates",
                "",
                f"- **Kupiec POF:** {rolling.summary.kupiec_pass_rate:.1%}",
                f"- **Independence:** {rolling.summary.independence_pass_rate:.1%}",
                f"- **Conditional Coverage:** {rolling.summary.cc_pass_rate:.1%}",
                f"- **ALL Tests:** {rolling.summary.all_pass_rate:.1%}",
                "",
                "### Worst p-values",
                "",
                f"- **Kupiec POF:** {rolling.summary.worst_kupiec_p_value:.4f}",
                f"- **Independence:** {rolling.summary.worst_independence_p_value:.4f}",
                f"- **Conditional Coverage:** {rolling.summary.worst_cc_p_value:.4f}",
                "",
                f"**Verdict Stability:** {rolling.summary.verdict_stability:.1%}",
                "",
                f"**Assessment:** {rolling.summary.notes}",
                "",
                "### Window Details",
                "",
                "| Win | Start | End | N | Viol | UC | IND | CC | All |",
                "|-----|-------|-----|---|------|----|-----|----|----|",
            ]
        )

        # Add window rows
        for w in rolling.windows:
            uc_status = "✓" if w.kupiec.is_valid else "✗"
            ind_status = "✓" if w.independence.passed else "✗"
            cc_status = "✓" if w.conditional_coverage.passed else "✗"
            all_status = "✓" if w.all_passed else "✗"

            lines.append(
                f"| {w.window_id} | {w.start_idx} | {w.end_idx} | {w.n_observations} | "
                f"{w.n_violations} | {uc_status} | {ind_status} | {cc_status} | {all_status} |"
            )

        lines.append("")

    # Overall Verdict
    all_core_passed = backtest.kupiec.is_valid and independence.passed and cc.passed

    lines.extend(
        [
            "---",
            "",
            "## Overall Verdict",
            "",
            f"**Core Tests:** {'✅ ALL PASSED' if all_core_passed else '❌ SOME FAILED'}",
            "",
        ]
    )

    if all_core_passed:
        lines.append(
            "The VaR model passes all core validation tests (Kupiec POF + Christoffersen IND/CC)."
        )
    else:
        lines.append("⚠️  The VaR model fails at least one core validation test. Review required.")

    lines.extend(
        [
            "",
            "---",
            "",
            "*This report was generated by Phase 10: VaR Backtest Suite Snapshot Runner*  ",
            "*Backtest/Research only - NOT for live trading*",
        ]
    )

    return "\n".join(lines)


def write_report(report_content: str, output_dir: str, timestamp: datetime) -> Path:
    """
    Write markdown report to file.

    Args:
        report_content: Markdown content
        output_dir: Output directory
        timestamp: Report timestamp

    Returns:
        Path to written file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"var_backtest_suite_snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = output_path / filename

    with open(filepath, "w") as f:
        f.write(report_content)

    logger.info(f"Report written to: {filepath}")
    return filepath


def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    try:
        # Load data
        returns, var_estimates = load_data(args)

        # Run suite
        results = run_suite(
            returns=returns,
            var_estimates=var_estimates,
            confidence_level=args.confidence,
            test_alpha=args.test_alpha,
            symbol=args.symbol,
            enable_duration=args.enable_duration_diagnostic,
            enable_rolling=args.enable_rolling,
            rolling_window_size=args.rolling_window_size,
            rolling_step_size=args.rolling_step_size,
        )

        # Print console summary
        summary = format_console_summary(results, args.symbol, args.confidence)
        print(summary)

        # Write markdown report
        if not args.no_report:
            timestamp = datetime.now()
            report = generate_markdown_report(
                results,
                args.symbol,
                args.confidence,
                args.test_alpha,
                timestamp,
            )
            report_path = write_report(report, args.output_dir, timestamp)
            print(f"\n📄 Report saved to: {report_path}")

        # Exit code: 0 if all core tests passed, 1 otherwise
        all_core_passed = (
            results["backtest"].kupiec.is_valid
            and results["independence"].passed
            and results["conditional_coverage"].passed
        )

        sys.exit(0 if all_core_passed else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(2)


if __name__ == "__main__":
    main()
