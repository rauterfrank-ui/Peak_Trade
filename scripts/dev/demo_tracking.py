#!/usr/bin/env python3
"""
Demo Script for Peak Trade Tracking
====================================

Demonstrates the full tracking workflow:
1. Create runs with PeakTradeRun
2. Compare runs with compare_runs.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from experiments.tracking import PeakTradeRun


def demo_basic_tracking():
    """Demonstrate basic tracking without MLflow."""
    print("=" * 60)
    print("Demo: Basic Tracking (Null Backend)")
    print("=" * 60)

    # Run 1: RSI strategy
    print("\n[1/3] Running RSI strategy...")
    with PeakTradeRun(
        experiment_name="demo_experiment",
        run_name="rsi_10_20",
        tags={"strategy": "rsi", "phase": "demo"},
    ) as run:
        # Log parameters
        run.log_params(
            {
                "fast_period": 10,
                "slow_period": 20,
                "threshold": 0.5,
            }
        )

        # Simulate backtest
        time.sleep(0.1)

        # Log metrics
        run.log_metrics(
            {
                "sharpe_ratio": 1.5,
                "total_return": 0.25,
                "max_drawdown": -0.12,
                "win_rate": 0.55,
            }
        )

    print(f"✓ Run completed: {run.run_id[:8]}")

    # Run 2: Different parameters
    print("\n[2/3] Running RSI with different params...")
    with PeakTradeRun(
        experiment_name="demo_experiment",
        run_name="rsi_15_30",
        tags={"strategy": "rsi", "phase": "demo"},
    ) as run:
        run.log_params(
            {
                "fast_period": 15,
                "slow_period": 30,
                "threshold": 0.6,
            }
        )

        time.sleep(0.1)

        run.log_metrics(
            {
                "sharpe_ratio": 1.7,
                "total_return": 0.30,
                "max_drawdown": -0.10,
                "win_rate": 0.58,
            }
        )

    print(f"✓ Run completed: {run.run_id[:8]}")

    # Run 3: Failed run
    print("\n[3/3] Simulating failed run...")
    try:
        with PeakTradeRun(
            experiment_name="demo_experiment",
            run_name="rsi_broken",
            tags={"strategy": "rsi", "phase": "demo"},
        ) as run:
            run.log_params(
                {
                    "fast_period": 5,
                    "slow_period": 10,
                }
            )

            # Simulate failure
            raise ValueError("Simulated backtest failure")

    except ValueError:
        print(f"✓ Failed run recorded: {run.run_id[:8]}")

    print("\n" + "=" * 60)
    print("✓ Demo complete! Run summaries saved to results/")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Compare runs:")
    print("     python scripts/dev/compare_runs.py --n 3")
    print("\n  2. View specific comparison:")
    print(f"     python scripts/dev/compare_runs.py \\")
    print(f"       --baseline {run.run_id[:8]} \\")
    print(f"       --candidate <other_run_id>")
    print("\n  3. Generate report:")
    print("     cd reports/quarto && quarto render backtest_report.qmd")


if __name__ == "__main__":
    demo_basic_tracking()
