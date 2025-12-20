#!/usr/bin/env python3
"""
Simplified Execution Pipeline Dry-Run Demo.

Demonstrates the simplified execution pipeline (src/execution_simple).
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.peak_config import load_config
from src.execution_simple import (
    ExecutionContext,
    ExecutionMode,
    build_execution_pipeline_from_config,
)


def main():
    """Run execution pipeline dry-run demo."""
    parser = argparse.ArgumentParser(description="Simplified Execution Pipeline Dry-Run")
    parser.add_argument("--config", type=str, default="config.toml", help="Config file path")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g., BTC-USD)")
    parser.add_argument(
        "--target", type=float, required=True, help="Target position in units"
    )
    parser.add_argument(
        "--current", type=float, required=True, help="Current position in units"
    )
    parser.add_argument("--price", type=float, required=True, help="Current market price")
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["backtest", "paper", "live"],
        help="Override execution mode",
    )
    parser.add_argument(
        "--tags", type=str, default="", help="Comma-separated tags (e.g., research_only,test)"
    )

    args = parser.parse_args()

    # Load config
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"❌ Config file not found: {args.config}")
        print("Using minimal default config...")
        # Create minimal config
        from types import SimpleNamespace

        cfg = SimpleNamespace()
        cfg.get = lambda key, default=None: default

    # Build pipeline
    print("=" * 70)
    print("🚀 SIMPLIFIED EXECUTION PIPELINE DRY-RUN")
    print("=" * 70)
    print()

    try:
        pipeline = build_execution_pipeline_from_config(cfg)
    except Exception as e:
        print(f"❌ Failed to build pipeline: {e}")
        return 1

    # Parse tags
    tags = set()
    if args.tags:
        tags = {tag.strip() for tag in args.tags.split(",")}

    # Determine mode
    if args.mode:
        mode = ExecutionMode(args.mode)
    else:
        mode_str = cfg.get("execution.mode", "paper")
        mode = ExecutionMode(mode_str)

    # Create context
    context = ExecutionContext(
        mode=mode,
        ts=datetime.now(),
        symbol=args.symbol,
        price=args.price,
        tags=tags,
    )

    # Print inputs
    print("📊 INPUT:")
    print(f"  Symbol:           {context.symbol}")
    print(f"  Mode:             {context.mode.value}")
    print(f"  Price:            ${context.price:,.2f}")
    print(f"  Target Position:  {args.target:.6f}")
    print(f"  Current Position: {args.current:.6f}")
    print(f"  Desired Delta:    {args.target - args.current:.6f}")
    if tags:
        print(f"  Tags:             {', '.join(sorted(tags))}")
    print()

    # Execute
    print("⚙️  EXECUTION:")
    print()

    result = pipeline.execute(
        target_position=args.target,
        current_position=args.current,
        context=context,
    )

    # Print gate decisions
    print("🔒 GATE DECISIONS:")
    for decision in result.gate_decisions:
        status = "✅ PASS" if decision.passed else "❌ BLOCK"
        print(f"  {decision.gate_name:20s} {status:10s} {decision.reason}")
        if decision.modified_qty is not None:
            print(f"    └─ Modified qty: {decision.modified_qty:.6f}")
    print()

    # Print result
    if result.blocked:
        print("❌ EXECUTION BLOCKED")
        print(f"   Reason: {result.block_reason}")
        print()
        return 1

    print("✅ EXECUTION ALLOWED")
    print()

    # Print orders
    if result.orders:
        print("📝 PLANNED ORDERS:")
        for i, order in enumerate(result.orders, 1):
            print(f"  Order {i}:")
            print(f"    Side:     {order.side.value.upper()}")
            print(f"    Quantity: {order.quantity:.6f}")
            print(f"    Price:    ${order.price:,.2f}")
            print(f"    Notional: ${order.notional:,.2f}")
            print(f"    Type:     {order.order_type.value}")
        print()

    # Print fills (if simulated)
    if result.fills:
        print("💰 SIMULATED FILLS:")
        for i, fill in enumerate(result.fills, 1):
            print(f"  Fill {i}:")
            print(f"    Side:     {fill.side.value.upper()}")
            print(f"    Quantity: {fill.quantity:.6f}")
            print(f"    Price:    ${fill.price:,.2f} (incl. slippage)")
            print(f"    Notional: ${fill.notional:,.2f}")
            print(f"    Fee:      ${fill.fee:.4f}")
        print()

        # Summary
        print("📊 SUMMARY:")
        print(f"  Total Filled:  {result.total_filled_qty:.6f}")
        print(f"  Total Notional: ${result.total_notional:,.2f}")
        print(f"  Total Fees:     ${result.total_fees:.4f}")
        print()

    print("=" * 70)
    print("✅ DRY-RUN COMPLETE")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
