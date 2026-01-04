#!/usr/bin/env python3
"""
Christoffersen Tests Demo CLI
==============================

Phase 8B: Demonstration of LR-IND and LR-CC tests.

Usage:
    python scripts/risk/run_christoffersen_demo.py --pattern scattered
    python scripts/risk/run_christoffersen_demo.py --pattern clustered
    python scripts/risk/run_christoffersen_demo.py --pattern alternating
    python scripts/risk/run_christoffersen_demo.py --custom "FFFFFTTTTTFFFFF"

Examples:
    # Test scattered violations (should pass)
    python scripts/risk/run_christoffersen_demo.py --pattern scattered

    # Test clustered violations (should fail IND)
    python scripts/risk/run_christoffersen_demo.py --pattern clustered

    # Custom pattern
    python scripts/risk/run_christoffersen_demo.py --custom "FFTFFTFF"
"""

from __future__ import annotations

import argparse
import sys


def main():
    """Main entry point for Christoffersen demo CLI."""
    parser = argparse.ArgumentParser(
        description="Christoffersen Tests Demo (LR-IND, LR-CC)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Pattern selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pattern",
        type=str,
        choices=["scattered", "clustered", "alternating", "perfect"],
        help="Predefined violation pattern",
    )
    group.add_argument(
        "--custom",
        type=str,
        help='Custom pattern (e.g., "FFTFFTFF" where F=False, T=True)',
    )

    # Test parameters
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Expected exceedance rate (default: 0.05 for 95%% VaR)",
    )
    parser.add_argument(
        "--p-threshold",
        type=float,
        default=0.05,
        help="Significance level for tests (default: 0.05)",
    )

    # Output options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed transition matrix",
    )

    args = parser.parse_args()

    # Import here to avoid slow startup for --help
    try:
        from src.risk_layer.var_backtest.christoffersen_tests import (
            christoffersen_lr_cc,
            christoffersen_lr_ind,
        )
        from src.risk_layer.var_backtest.kupiec_pof import kupiec_lr_uc
    except ImportError as e:
        print(f"ERROR: Failed to import test functions: {e}", file=sys.stderr)
        sys.exit(3)

    # Generate exceedances pattern
    if args.pattern:
        exceedances = _generate_pattern(args.pattern)
        pattern_name = args.pattern.upper()
    else:
        exceedances = _parse_custom_pattern(args.custom)
        pattern_name = "CUSTOM"

    n = len(exceedances)
    x = sum(exceedances)

    # Run tests
    print("=" * 60)
    print("CHRISTOFFERSEN TESTS DEMO")
    print("=" * 60)
    print(f"Pattern:      {pattern_name}")
    print(f"Observations: {n}")
    print(f"Exceedances:  {x} ({x / n:.1%})")
    print(f"Alpha:        {args.alpha:.2%} (expected rate)")
    print(f"p-threshold:  {args.p_threshold:.2%}")
    print()

    # 1. Kupiec POF (Unconditional Coverage)
    print("-" * 60)
    print("1. KUPIEC POF TEST (Unconditional Coverage)")
    print("-" * 60)
    uc_result = kupiec_lr_uc(n=n, x=x, alpha=args.alpha, p_threshold=args.p_threshold)
    print(f"LR-UC:     {uc_result.lr_uc:.4f}")
    print(f"p-value:   {uc_result.p_value:.4f}")
    print(f"Verdict:   {uc_result.verdict}")
    print(f"Notes:     {uc_result.notes}")
    print()

    # 2. Christoffersen Independence Test
    print("-" * 60)
    print("2. CHRISTOFFERSEN INDEPENDENCE TEST")
    print("-" * 60)
    ind_result = christoffersen_lr_ind(exceedances, p_threshold=args.p_threshold)
    print(f"LR-IND:    {ind_result.lr_ind:.4f}")
    print(f"p-value:   {ind_result.p_value:.4f}")
    print(f"Verdict:   {ind_result.verdict}")
    print(f"Notes:     {ind_result.notes}")

    if args.verbose:
        print()
        print("Transition Matrix:")
        print(f"  n00 (F→F): {ind_result.n00}")
        print(f"  n01 (F→T): {ind_result.n01}")
        print(f"  n10 (T→F): {ind_result.n10}")
        print(f"  n11 (T→T): {ind_result.n11}")
        print()
        print("Transition Probabilities:")
        print(f"  π₀₁ (P(T|F)): {ind_result.pi_01:.4f}")
        print(f"  π₁₁ (P(T|T)): {ind_result.pi_11:.4f}")
    print()

    # 3. Christoffersen Conditional Coverage Test
    print("-" * 60)
    print("3. CHRISTOFFERSEN CONDITIONAL COVERAGE TEST")
    print("-" * 60)
    cc_result = christoffersen_lr_cc(
        exceedances,
        alpha=args.alpha,
        p_threshold=args.p_threshold,
    )
    print(f"LR-UC:     {cc_result.lr_uc:.4f}")
    print(f"LR-IND:    {cc_result.lr_ind:.4f}")
    print(f"LR-CC:     {cc_result.lr_cc:.4f} (= LR-UC + LR-IND)")
    print(f"p-value:   {cc_result.p_value:.4f}")
    print(f"Verdict:   {cc_result.verdict}")
    print(f"Notes:     {cc_result.notes}")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = (
        uc_result.verdict == "PASS" and ind_result.verdict == "PASS" and cc_result.verdict == "PASS"
    )

    if all_pass:
        print("✅ ALL TESTS PASSED")
        print("Model has correct coverage and independent violations.")
        exit_code = 0
    else:
        print("❌ SOME TESTS FAILED")
        if uc_result.verdict == "FAIL":
            print("  - Unconditional Coverage: FAIL (wrong violation rate)")
        if ind_result.verdict == "FAIL":
            print("  - Independence: FAIL (violations are clustered)")
        if cc_result.verdict == "FAIL":
            print("  - Conditional Coverage: FAIL (combined test)")
        exit_code = 1

    print("=" * 60)
    sys.exit(exit_code)


def _generate_pattern(pattern_type: str) -> list[bool]:
    """Generate predefined violation pattern."""
    if pattern_type == "scattered":
        # 5% violations, scattered evenly
        exceedances = [False] * 100
        for i in [10, 30, 50, 70, 90]:
            exceedances[i] = True
        return exceedances

    elif pattern_type == "clustered":
        # 5% violations, all clustered together
        return [False] * 95 + [True] * 5

    elif pattern_type == "alternating":
        # 50% violations, alternating pattern
        return [False, True] * 50

    elif pattern_type == "perfect":
        # Perfect calibration (5%) with perfect independence
        # Violations at positions that maximize independence
        exceedances = [False] * 100
        for i in [0, 20, 40, 60, 80]:
            exceedances[i] = True
        return exceedances

    else:
        raise ValueError(f"Unknown pattern: {pattern_type}")


def _parse_custom_pattern(pattern_str: str) -> list[bool]:
    """Parse custom pattern string."""
    pattern_str = pattern_str.upper().strip()
    exceedances = []

    for char in pattern_str:
        if char == "F":
            exceedances.append(False)
        elif char == "T":
            exceedances.append(True)
        else:
            raise ValueError(f"Invalid character in pattern: {char} (use F or T)")

    if len(exceedances) < 2:
        raise ValueError("Pattern must have at least 2 observations")

    return exceedances


if __name__ == "__main__":
    main()
