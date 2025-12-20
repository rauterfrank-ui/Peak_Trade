#!/usr/bin/env python3
"""
Automated code review script.

Runs all quality checks:
- Linting (Ruff)
- Type checking (MyPy)
- Security scanning (Bandit)
- Test coverage
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run command and return success status."""
    print(f"\n🔍 {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} passed")
        return True
    else:
        print(f"❌ {description} failed:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False


def main():
    """Run all code review checks."""
    print("=" * 60)
    print("  Automated Code Review")
    print("=" * 60)

    checks = [
        (["ruff", "check", "."], "Ruff linting"),
        (["ruff", "format", "--check", "."], "Ruff format check"),
        (["mypy", "src/", "--ignore-missing-imports"], "MyPy type checking"),
        (["bandit", "-r", "src/", "-ll"], "Bandit security scan"),
        (["pytest", "--cov=src", "--cov-report=term-missing", "-q"], "Test coverage"),
    ]

    failed = []
    for cmd, description in checks:
        if not run_command(cmd, description):
            failed.append(description)

    print("\n" + "=" * 60)
    if failed:
        print(f"❌ {len(failed)} check(s) failed:")
        for check in failed:
            print(f"  - {check}")
        print("\nRun individual checks to see details:")
        print("  ruff check .")
        print("  mypy src/")
        print("  bandit -r src/ -ll")
        print("  pytest --cov=src")
        sys.exit(1)
    else:
        print("✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
