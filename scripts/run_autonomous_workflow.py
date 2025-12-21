#!/usr/bin/env python3
"""
Peak_Trade Autonomous Workflow Orchestrator
============================================

Orchestrates autonomous AI-driven workflows for automated trading research,
monitoring, and decision-making.

Features:
- Automated workflow execution based on market conditions
- AI-enhanced decision making
- Integration with scheduler and research pipeline
- Comprehensive monitoring and alerting

Usage:
    # Run autonomous orchestrator once
    python scripts/run_autonomous_workflow.py --config config/config.toml --once

    # Run in continuous mode (daemon)
    python scripts/run_autonomous_workflow.py --config config/config.toml --continuous

    # Dry-run mode
    python scripts/run_autonomous_workflow.py --config config/config.toml --once --dry-run

    # Specific workflow type
    python scripts/run_autonomous_workflow.py --workflow-type signal_analysis --symbol BTC/EUR
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.autonomous import (
    WorkflowEngine,
    DecisionEngine,
    MarketMonitor,
    SignalMonitor,
    PerformanceMonitor,
)

# Optional imports
try:
    from src.notifications import Alert, ConsoleNotifier, FileNotifier, CombinedNotifier

    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

try:
    from src.core.experiments import log_autonomous_workflow_run

    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False


# Global shutdown flag
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _shutdown_requested
    print("\n[AUTONOMOUS] Shutdown requested...")
    _shutdown_requested = True


def parse_args(argv=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Autonomous Workflow Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once with decision-making
  python scripts/run_autonomous_workflow.py --config config/config.toml --once

  # Continuous monitoring mode
  python scripts/run_autonomous_workflow.py --config config/config.toml --continuous

  # Specific workflow
  python scripts/run_autonomous_workflow.py --workflow-type signal_analysis --symbol BTC/EUR
        """,
    )

    parser.add_argument(
        "--config", type=str, default="config/config.toml", help="Path to config file"
    )

    parser.add_argument(
        "--workflow-type",
        type=str,
        choices=["signal_analysis", "risk_check", "market_scan", "portfolio_analysis", "auto"],
        default="auto",
        help="Type of workflow to execute (default: auto - decides automatically)",
    )

    parser.add_argument("--symbol", type=str, default="BTC/EUR", help="Trading symbol for analysis")

    parser.add_argument("--strategy", type=str, default="ma_crossover", help="Strategy to use")

    parser.add_argument("--once", action="store_true", help="Run once and exit")

    parser.add_argument("--continuous", action="store_true", help="Run continuously (daemon mode)")

    parser.add_argument(
        "--poll-interval", type=int, default=300, help="Polling interval in seconds (default: 300)"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate execution without running workflows"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--no-alerts", action="store_true", help="Disable alerts")

    parser.add_argument(
        "--alert-log", type=str, default="logs/autonomous_alerts.log", help="Path to alert log file"
    )

    return parser.parse_args(argv)


def create_notifier(args):
    """Create notification handler."""
    if not NOTIFICATIONS_AVAILABLE or args.no_alerts:
        return None

    notifiers = [ConsoleNotifier()]

    if args.alert_log:
        log_path = Path(args.alert_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        notifiers.append(FileNotifier(log_path))

    return CombinedNotifier(notifiers)


def send_alert(notifier, level: str, message: str, context: dict = None):
    """Send an alert."""
    if notifier is None:
        return

    alert = Alert(
        level=level,
        source="autonomous_workflow",
        message=message,
        timestamp=datetime.utcnow(),
        context=context or {},
    )
    notifier.send(alert)


def execute_autonomous_workflow(
    workflow_type: str,
    symbol: str,
    strategy: str,
    workflow_engine: WorkflowEngine,
    decision_engine: DecisionEngine,
    market_monitor: MarketMonitor,
    signal_monitor: SignalMonitor,
    performance_monitor: PerformanceMonitor,
    notifier,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Execute a single autonomous workflow cycle.

    Returns:
        Dictionary with execution results
    """
    print(f"\n{'=' * 70}")
    print(f"AUTONOMOUS WORKFLOW CYCLE")
    print(f"{'=' * 70}")
    print(f"Workflow Type: {workflow_type}")
    print(f"Symbol: {symbol}")
    print(f"Strategy: {strategy}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"{'=' * 70}\n")

    # Step 1: Monitor current conditions
    print("[1/4] Monitoring market conditions...")
    market_result = market_monitor.check_conditions(symbol)
    signal_result = signal_monitor.check_signal_quality(strategy, symbol)
    performance_result = performance_monitor.check_performance()

    if verbose:
        print(f"  Market Status: {market_result.status}")
        print(f"  Signal Status: {signal_result.status}")
        print(f"  Performance Status: {performance_result.status}")

    # Send alerts for critical conditions
    for result in [market_result, signal_result, performance_result]:
        if result.status == "critical" and result.alerts:
            for alert_msg in result.alerts:
                send_alert(notifier, "critical", alert_msg, {"monitor": result.monitor_name})

    # Step 2: Make decision
    print("[2/4] Making autonomous decision...")

    # Combine metrics from all monitors
    combined_metrics = {}
    combined_metrics.update(market_result.metrics)
    combined_metrics.update(signal_result.metrics)
    combined_metrics.update(performance_result.metrics)

    # Auto-determine workflow type if needed
    if workflow_type == "auto":
        # Simple logic: prioritize based on conditions
        if performance_result.status == "critical":
            workflow_type = "risk_check"
            print("  Auto-selected: risk_check (performance critical)")
        elif signal_result.metrics.get("signal_strength", 0) > 0.6:
            workflow_type = "signal_analysis"
            print("  Auto-selected: signal_analysis (strong signals)")
        else:
            workflow_type = "market_scan"
            print("  Auto-selected: market_scan (default)")

    # Make decision
    decision = decision_engine.make_decision(
        workflow_type=workflow_type,
        metrics=combined_metrics,
    )

    print(f"  Decision: {decision.action.value}")
    print(f"  Confidence: {decision.confidence:.2%}")
    print(f"  Reasoning: {decision.reasoning}")

    if verbose:
        print(f"  Criteria Results: {decision.criteria_results}")

    # Step 3: Execute workflow if decision permits
    workflow_result = None

    if decision.should_execute:
        print("[3/4] Executing workflow...")

        # Create workflow
        workflow_id = workflow_engine.create_workflow(
            name=f"autonomous_{workflow_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            workflow_type=workflow_type,
            parameters={
                "symbol": symbol,
                "strategy": strategy,
                "timeframe": "1h",
                "bars": 200,
                "tag": "autonomous",
            },
        )

        # Execute
        workflow_result = workflow_engine.execute_workflow(workflow_id, dry_run=dry_run)

        if workflow_result.success:
            print(f"  ✅ Workflow completed successfully")
            if verbose and workflow_result.output:
                print(f"  Output: {workflow_result.output}")
        else:
            print(f"  ❌ Workflow failed: {workflow_result.error}")
            send_alert(
                notifier,
                "critical",
                f"Autonomous workflow failed: {workflow_result.error}",
                {"workflow_type": workflow_type},
            )
    elif decision.should_alert:
        print("[3/4] Alerting (not executing)...")
        send_alert(
            notifier,
            "warning",
            f"Autonomous workflow alert: {decision.reasoning}",
            {"workflow_type": workflow_type, "decision": decision.action.value},
        )
    else:
        print("[3/4] Skipping workflow execution")
        print(f"  Reason: {decision.reasoning}")

    # Step 4: Summary
    print("[4/4] Cycle complete")

    return {
        "workflow_type": workflow_type,
        "decision": decision.action.value,
        "confidence": decision.confidence,
        "executed": workflow_result is not None,
        "success": workflow_result.success if workflow_result else False,
        "timestamp": datetime.utcnow().isoformat(),
    }


def run_autonomous_loop(
    args,
    workflow_engine: WorkflowEngine,
    decision_engine: DecisionEngine,
    market_monitor: MarketMonitor,
    signal_monitor: SignalMonitor,
    performance_monitor: PerformanceMonitor,
    notifier,
) -> int:
    """Run the autonomous workflow loop."""
    global _shutdown_requested

    iteration = 0
    total_executions = 0

    mode = "ONCE" if args.once else "CONTINUOUS"
    print(f"\n{'=' * 70}")
    print(f"AUTONOMOUS WORKFLOW ORCHESTRATOR")
    print(f"{'=' * 70}")
    print(f"Mode: {mode}")
    print(f"Workflow Type: {args.workflow_type}")
    print(f"Symbol: {args.symbol}")
    print(f"Strategy: {args.strategy}")
    if args.continuous:
        print(f"Poll Interval: {args.poll_interval}s")
    if args.dry_run:
        print("DRY-RUN: No actual execution")
    print(f"{'=' * 70}\n")

    while not _shutdown_requested:
        iteration += 1

        try:
            result = execute_autonomous_workflow(
                workflow_type=args.workflow_type,
                symbol=args.symbol,
                strategy=args.strategy,
                workflow_engine=workflow_engine,
                decision_engine=decision_engine,
                market_monitor=market_monitor,
                signal_monitor=signal_monitor,
                performance_monitor=performance_monitor,
                notifier=notifier,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )

            if result["executed"]:
                total_executions += 1

        except Exception as e:
            print(f"\n❌ Error in autonomous cycle: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()

            send_alert(
                notifier, "critical", f"Autonomous workflow error: {e}", {"iteration": iteration}
            )

        # Exit if once mode
        if args.once:
            break

        # Wait for next iteration
        if not _shutdown_requested and args.continuous:
            print(f"\nWaiting {args.poll_interval}s for next cycle...")
            time.sleep(args.poll_interval)

    # Summary
    print(f"\n{'=' * 70}")
    print("AUTONOMOUS ORCHESTRATOR STOPPED")
    print(f"{'=' * 70}")
    print(f"Total Iterations: {iteration}")
    print(f"Total Executions: {total_executions}")
    print(f"{'=' * 70}\n")

    return 0


def main(argv=None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create components
    workflow_engine = WorkflowEngine()
    decision_engine = DecisionEngine()
    market_monitor = MarketMonitor()
    signal_monitor = SignalMonitor()
    performance_monitor = PerformanceMonitor()
    notifier = create_notifier(args)

    # Run orchestrator
    return run_autonomous_loop(
        args=args,
        workflow_engine=workflow_engine,
        decision_engine=decision_engine,
        market_monitor=market_monitor,
        signal_monitor=signal_monitor,
        performance_monitor=performance_monitor,
        notifier=notifier,
    )


if __name__ == "__main__":
    sys.exit(main())
