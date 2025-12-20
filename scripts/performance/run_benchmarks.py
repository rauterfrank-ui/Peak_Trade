#!/usr/bin/env python3
"""
Run Performance Benchmarks
===========================

CLI tool to run performance benchmarks and generate reports.

Usage:
    python scripts/performance/run_benchmarks.py [--all] [--stress] [--report]
"""

import sys
import argparse
import subprocess
from pathlib import Path


def run_benchmarks(test_path: str = "tests/performance/", verbose: bool = True):
    """
    Run performance benchmarks.
    
    Args:
        test_path: Path to tests
        verbose: Verbose output
    """
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v" if verbose else "-q"
    ]
    
    print(f"Running benchmarks: {test_path}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode


def run_stress_tests(verbose: bool = True):
    """Run stress tests."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/performance/test_stress.py",
        "-v" if verbose else "-q",
        "-m", "slow"
    ]
    
    print("Running stress tests...")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode


def generate_report():
    """Generate benchmark report."""
    print("\n" + "="*70)
    print("Performance Benchmark Summary")
    print("="*70)
    
    # Run benchmarks with JSON output
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/performance/",
        "--tb=no",
        "-q"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print("\n✅ All benchmarks passed!")
    else:
        print("\n❌ Some benchmarks failed")
    
    print("="*70)
    print("\nFor detailed results, see: docs/performance_benchmarks.md")
    print("For optimization tips, see: docs/performance_guide.md")
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Peak Trade performance benchmarks"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all benchmarks including stress tests"
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        help="Run only stress tests"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate benchmark report"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet output"
    )
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    exit_code = 0
    
    if args.stress or args.all:
        exit_code = run_stress_tests(verbose)
        if exit_code != 0:
            return exit_code
    
    if not args.stress:
        exit_code = run_benchmarks(verbose=verbose)
        if exit_code != 0:
            return exit_code
    
    if args.report or args.all:
        exit_code = generate_report()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
