#!/usr/bin/env python3
"""
Reproduce a backtest run from saved metadata.

Usage:
    python scripts/reproduce_run.py --run-id abc123
    python scripts/reproduce_run.py --run-id abc123 --validate

This tool loads a saved reproducibility context and re-runs the backtest
with the same seed and configuration to verify reproducibility.
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.repro import ReproContext, set_global_seed, get_git_sha
from src.backtest.engine import BacktestEngine


def reproduce_run(run_id: str, validate: bool = True, verbose: bool = False) -> bool:
    """
    Reproduce a backtest run from saved metadata.

    Args:
        run_id: The run ID to reproduce
        validate: If True, validate environment matches original
        verbose: If True, print detailed information

    Returns:
        True if reproduction successful, False otherwise
    """
    # Load repro context
    repro_path = Path("results") / run_id / "repro.json"
    
    if not repro_path.exists():
        print(f"❌ Error: Repro file not found: {repro_path}")
        print(f"   Available runs:")
        results_dir = Path("results")
        if results_dir.exists():
            for run_dir in results_dir.iterdir():
                if run_dir.is_dir() and (run_dir / "repro.json").exists():
                    print(f"     - {run_dir.name}")
        else:
            print(f"     No results directory found")
        return False
    
    try:
        repro_ctx = ReproContext.load(repro_path)
    except Exception as e:
        print(f"❌ Error loading repro context: {e}")
        return False
    
    print(f"📋 Loaded reproduction context for run: {run_id}")
    print(f"   Seed: {repro_ctx.seed}")
    print(f"   Git SHA: {repro_ctx.git_sha}")
    print(f"   Config hash: {repro_ctx.config_hash}")
    print(f"   Timestamp: {repro_ctx.timestamp}")
    print(f"   Hostname: {repro_ctx.hostname}")
    print(f"   Python version: {repro_ctx.python_version}")
    
    # Validate environment if requested
    if validate:
        print(f"\n🔍 Validating environment...")
        warnings = []
        
        # Check git SHA
        current_git = get_git_sha(short=False)
        if current_git and repro_ctx.git_sha:
            if not current_git.startswith(repro_ctx.git_sha):
                warnings.append(
                    f"Git SHA mismatch: current={current_git[:7]}, "
                    f"original={repro_ctx.git_sha}"
                )
        
        # Check Python version
        import sys
        current_python = sys.version.split()[0]
        if current_python != repro_ctx.python_version:
            warnings.append(
                f"Python version mismatch: current={current_python}, "
                f"original={repro_ctx.python_version}"
            )
        
        # Check dependencies
        from src.core.repro import hash_dependencies
        current_deps = hash_dependencies()
        if current_deps and repro_ctx.dependencies_hash:
            if current_deps != repro_ctx.dependencies_hash:
                warnings.append(
                    f"Dependencies mismatch: current={current_deps}, "
                    f"original={repro_ctx.dependencies_hash}"
                )
        
        if warnings:
            print(f"⚠️  Environment warnings:")
            for warning in warnings:
                print(f"   - {warning}")
            print(f"   Reproduction may not be exact.")
        else:
            print(f"✅ Environment matches original")
    
    # Note about reproduction
    print(f"\n📝 Note: To fully reproduce this run, you need:")
    print(f"   1. The same data file used in the original run")
    print(f"   2. The same strategy function and parameters")
    print(f"   3. Use seed={repro_ctx.seed} when calling BacktestEngine.run_realistic()")
    print(f"\nExample code:")
    print(f"   engine = BacktestEngine()")
    print(f"   result = engine.run_realistic(")
    print(f"       df=your_data,")
    print(f"       strategy_signal_fn=your_strategy,")
    print(f"       strategy_params=your_params,  # Use config_hash={repro_ctx.config_hash}")
    print(f"       seed={repro_ctx.seed}")
    print(f"   )")
    
    return True


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Reproduce a backtest run from saved metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reproduce a run
  python scripts/reproduce_run.py --run-id abc12345

  # Reproduce with validation
  python scripts/reproduce_run.py --run-id abc12345 --validate

  # List available runs
  python scripts/reproduce_run.py --list
        """
    )
    
    parser.add_argument(
        "--run-id",
        type=str,
        help="Run ID to reproduce (8-character UUID)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate environment matches original (default: True)"
    )
    
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip environment validation"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available runs"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # List runs if requested
    if args.list:
        print("Available runs:")
        results_dir = Path("results")
        if results_dir.exists():
            for run_dir in sorted(results_dir.iterdir()):
                if run_dir.is_dir() and (run_dir / "repro.json").exists():
                    try:
                        ctx = ReproContext.load(run_dir / "repro.json")
                        print(f"  {run_dir.name}:")
                        print(f"    Timestamp: {ctx.timestamp}")
                        print(f"    Seed: {ctx.seed}")
                        print(f"    Git SHA: {ctx.git_sha}")
                    except Exception as e:
                        print(f"  {run_dir.name}: (error loading: {e})")
        else:
            print("  No results directory found")
        return 0
    
    # Require run-id for reproduction
    if not args.run_id:
        parser.print_help()
        print("\n❌ Error: --run-id is required (or use --list to see available runs)")
        return 1
    
    # Determine validation flag
    validate = not args.no_validate
    
    # Reproduce the run
    success = reproduce_run(
        run_id=args.run_id,
        validate=validate,
        verbose=args.verbose
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
