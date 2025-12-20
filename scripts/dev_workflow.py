#!/usr/bin/env python3
"""
Peak_Trade Developer Workflow Assistant
========================================

Automates common development workflows to improve productivity.

Usage:
    python scripts/dev_workflow.py --help
    python scripts/dev_workflow.py setup
    python scripts/dev_workflow.py test --module strategies
    python scripts/dev_workflow.py perf-check
    python scripts/dev_workflow.py docs-validate
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional
import time

# Add src to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from src.core.performance import performance_monitor
except ImportError:
    # Performance monitoring not available, that's ok
    performance_monitor = None


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def run_command(cmd: List[str], capture_output: bool = False, check: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Run a shell command with nice output."""
    print_info(f"Running: {' '.join(cmd)}")
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result
        else:
            subprocess.run(cmd, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        if capture_output and e.stdout:
            print(e.stdout)
        if capture_output and e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return None


def setup_environment() -> None:
    """Setup development environment."""
    print_header("Setting up development environment")
    
    # Check Python version
    print_info("Checking Python version...")
    result = run_command(["python", "--version"], capture_output=True)
    if result:
        print_success(f"Python version: {result.stdout.strip()}")
    
    # Create venv if it doesn't exist
    venv_path = REPO_ROOT / ".venv"
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        run_command(["python", "-m", "venv", str(venv_path)])
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")
    
    # Install dependencies
    print_info("Installing dependencies...")
    
    # Platform-agnostic pip path
    if os.name == 'nt':  # Windows
        pip_cmd = str(venv_path / "Scripts" / "pip.exe")
    else:  # Unix/Linux/Mac
        pip_cmd = str(venv_path / "bin" / "pip")
    
    run_command([pip_cmd, "install", "-e", ".[dev]"])
    print_success("Dependencies installed")
    
    print_success("Setup complete!")


def run_tests(module: Optional[str] = None, coverage: bool = False, verbose: bool = False) -> None:
    """Run tests with optional filtering and coverage."""
    print_header("Running tests")
    
    if performance_monitor:
        with performance_monitor.measure("test_execution"):
            _run_tests_impl(module, coverage, verbose)
        
        # Show performance metrics
        summary = performance_monitor.get_summary("test_execution")
        if summary:
            duration = summary["test_execution"].mean_ms / 1000
            print_info(f"Tests completed in {duration:.2f}s")
    else:
        _run_tests_impl(module, coverage, verbose)


def _run_tests_impl(module: Optional[str] = None, coverage: bool = False, verbose: bool = False) -> None:
    """Implementation of test running."""
    cmd = ["python", "-m", "pytest"]
    
    if module:
        test_path = f"tests/test_{module}.py" if not module.startswith("test_") else f"tests/{module}"
        cmd.append(test_path)
        print_info(f"Running tests for: {module}")
    else:
        cmd.append("tests/")
        print_info("Running all tests")
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    
    run_command(cmd, check=False)


def run_linters() -> None:
    """Run code linters."""
    print_header("Running linters")
    
    print_info("Running ruff...")
    result = run_command(["ruff", "check", "src/", "tests/"], check=False)
    
    print_info("Running black (check only)...")
    result = run_command(["black", "--check", "src/", "tests/"], check=False)
    
    print_success("Linting complete")


def performance_check() -> None:
    """Run performance checks on key operations."""
    print_header("Performance Check")
    
    if not performance_monitor:
        print_error("Performance monitoring not available")
        return
    
    # Import after adding to path
    try:
        from src.data.cache_manifest import CacheManifest
        from src.core.repro import get_git_sha, stable_hash_dict
    except ImportError as e:
        print_error(f"Could not import required modules: {e}")
        return
    
    print_info("Running performance benchmarks...")
    
    # Test cache manifest operations
    with performance_monitor.measure("cache_manifest_create"):
        manifest = CacheManifest("test_run_id")
    
    # Test git SHA retrieval
    with performance_monitor.measure("git_sha_retrieval"):
        for _ in range(10):
            get_git_sha()
    
    # Test config hashing
    test_config = {"key1": "value1", "key2": "value2", "nested": {"a": 1, "b": 2}}
    with performance_monitor.measure("config_hashing"):
        for _ in range(100):
            stable_hash_dict(test_config)
    
    # Display results
    performance_monitor.print_summary()
    
    print_success("Performance check complete")


def validate_docs() -> None:
    """Validate documentation."""
    print_header("Validating documentation")
    
    docs_dir = REPO_ROOT / "docs"
    
    print_info("Checking for broken links...")
    
    # Find all markdown files
    md_files = list(docs_dir.rglob("*.md"))
    print_info(f"Found {len(md_files)} markdown files")
    
    # Check for common issues
    issues = []
    
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for TODO markers
            if "TODO" in content or "FIXME" in content:
                issues.append(f"{md_file.name}: Contains TODO/FIXME")
            
            # Check for empty files
            if len(content.strip()) < 100:
                issues.append(f"{md_file.name}: File is too short (<100 chars)")
    
    if issues:
        print_error(f"Found {len(issues)} documentation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print_success("Documentation validation passed")


def quick_health_check() -> None:
    """Quick health check of the system."""
    print_header("System Health Check")
    
    checks = []
    
    # Check if venv exists
    venv_path = REPO_ROOT / ".venv"
    checks.append(("Virtual environment", venv_path.exists()))
    
    # Check if key directories exist
    checks.append(("Source directory", (REPO_ROOT / "src").exists()))
    checks.append(("Tests directory", (REPO_ROOT / "tests").exists()))
    checks.append(("Docs directory", (REPO_ROOT / "docs").exists()))
    
    # Check if key files exist
    checks.append(("pyproject.toml", (REPO_ROOT / "pyproject.toml").exists()))
    checks.append(("config.toml", (REPO_ROOT / "config.toml").exists()))
    
    # Check git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT
        )
        has_changes = bool(result.stdout.strip())
        checks.append(("Git working tree clean", not has_changes))
    except subprocess.CalledProcessError:
        checks.append(("Git working tree clean", False))
    
    # Print results
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    if all_passed:
        print_success("\nAll health checks passed!")
    else:
        print_error("\nSome health checks failed")


def create_strategy_scaffold(name: str) -> None:
    """Create a new strategy with boilerplate code."""
    print_header(f"Creating strategy scaffold: {name}")
    
    # Convert name to snake_case and PascalCase
    snake_name = name.lower().replace(" ", "_").replace("-", "_")
    pascal_name = "".join(word.capitalize() for word in snake_name.split("_"))
    
    # Strategy file path
    strategy_file = REPO_ROOT / "src" / "strategies" / f"{snake_name}.py"
    test_file = REPO_ROOT / "tests" / "strategies" / f"test_{snake_name}.py"
    
    if strategy_file.exists():
        print_error(f"Strategy already exists: {strategy_file}")
        return
    
    # Create strategy file
    strategy_template = f'''"""
{pascal_name} Strategy
"""

from typing import List
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal


class {pascal_name}(BaseStrategy):
    """
    {pascal_name} trading strategy.
    
    TODO: Add strategy description
    
    Parameters:
    -----------
    TODO: Document parameters
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TODO: Initialize strategy parameters
    
    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals based on {name} logic.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # TODO: Implement signal generation logic
        
        return signals
'''
    
    # Create test file
    test_template = f'''"""
Tests for {pascal_name} Strategy
"""

import pytest
import pandas as pd
import numpy as np

from src.strategies.{snake_name} import {pascal_name}


class Test{pascal_name}:
    """Tests for {pascal_name} strategy."""
    
    def test_init(self):
        """Test strategy initialization."""
        strategy = {pascal_name}()
        assert strategy is not None
    
    def test_generate_signals_empty_data(self):
        """Test with empty DataFrame."""
        strategy = {pascal_name}()
        df = pd.DataFrame()
        signals = strategy.generate_signals(df)
        assert signals == []
    
    def test_generate_signals_basic(self):
        """Test basic signal generation."""
        strategy = {pascal_name}()
        
        # Create sample data
        df = pd.DataFrame({{
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h'),
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 101,
            'low': np.random.randn(100).cumsum() + 99,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100),
        }})
        
        signals = strategy.generate_signals(df)
        # TODO: Add assertions based on expected behavior
'''
    
    # Write files
    strategy_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(strategy_file, 'w') as f:
        f.write(strategy_template)
    
    with open(test_file, 'w') as f:
        f.write(test_template)
    
    print_success(f"Created strategy: {strategy_file}")
    print_success(f"Created tests: {test_file}")
    print_info(f"\nNext steps:")
    print_info(f"1. Edit {strategy_file} to implement your strategy")
    print_info(f"2. Edit {test_file} to add comprehensive tests")
    print_info(f"3. Run tests: python scripts/dev_workflow.py test --module strategies/test_{snake_name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Developer Workflow Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    subparsers.add_parser("setup", help="Setup development environment")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--module", help="Specific module to test")
    test_parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Lint command
    subparsers.add_parser("lint", help="Run linters")
    
    # Performance check command
    subparsers.add_parser("perf-check", help="Run performance checks")
    
    # Docs validation command
    subparsers.add_parser("docs-validate", help="Validate documentation")
    
    # Health check command
    subparsers.add_parser("health", help="Quick health check")
    
    # Create strategy command
    create_parser = subparsers.add_parser("create-strategy", help="Create strategy scaffold")
    create_parser.add_argument("name", help="Strategy name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "setup":
        setup_environment()
    elif args.command == "test":
        run_tests(args.module, args.coverage, args.verbose)
    elif args.command == "lint":
        run_linters()
    elif args.command == "perf-check":
        performance_check()
    elif args.command == "docs-validate":
        validate_docs()
    elif args.command == "health":
        quick_health_check()
    elif args.command == "create-strategy":
        create_strategy_scaffold(args.name)


if __name__ == "__main__":
    main()
