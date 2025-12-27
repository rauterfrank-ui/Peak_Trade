#!/usr/bin/env python3
"""
Demo Script for Risk-Layer Multi-Channel Alerting
===================================================

Demonstrates the multi-channel alerting system with various scenarios.
"""

import os
import tempfile
from pathlib import Path

from src.risk_layer.alerting import (
    AlertDispatcher,
    AlertEvent,
    AlertSeverity,
    ConsoleChannel,
    FileChannel,
    EmailChannel,
    SlackChannel,
    TelegramChannel,
    WebhookChannel,
)


def demo_basic_alerting():
    """Demonstrate basic alerting with console output."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Console Alerting")
    print("=" * 80 + "\n")

    # Create console channel
    console = ConsoleChannel()

    # Create dispatcher with console only
    dispatcher = AlertDispatcher(channels=[console])

    # Send alerts of different severities
    alerts = [
        AlertEvent(
            source="risk_gate",
            severity=AlertSeverity.INFO,
            title="Position Check Passed",
            body="Portfolio within acceptable risk limits",
            labels={"portfolio": "main", "status": "healthy"},
        ),
        AlertEvent(
            source="var_gate",
            severity=AlertSeverity.WARN,
            title="VaR Approaching Threshold",
            body="Portfolio VaR at 90% of configured threshold",
            labels={"threshold_pct": "90"},
            metadata={"current_var": 0.045, "limit": 0.05},
        ),
        AlertEvent(
            source="kill_switch",
            severity=AlertSeverity.CRITICAL,
            title="Kill Switch Triggered",
            body="Emergency shutdown due to excessive drawdown",
            labels={"reason": "max_drawdown_exceeded"},
            metadata={"drawdown": 0.15, "limit": 0.10},
        ),
    ]

    for alert in alerts:
        results = dispatcher.dispatch(alert)
        print(f"Dispatch result: {results}\n")


def demo_file_channel():
    """Demonstrate file-based alerting with JSONL storage."""
    print("\n" + "=" * 80)
    print("DEMO 2: File-Based Alerting (JSONL)")
    print("=" * 80 + "\n")

    # Create temp file for alerts
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        temp_file = f.name

    try:
        # Create channels
        console = ConsoleChannel(color=False)
        file_channel = FileChannel(file_path=temp_file)

        # Create dispatcher
        dispatcher = AlertDispatcher(channels=[console, file_channel])

        # Send critical alert
        alert = AlertEvent(
            source="stress_gate",
            severity=AlertSeverity.CRITICAL,
            title="Stress Test Failure",
            body="Portfolio failed stress scenario: market_crash_2008",
            labels={"scenario": "market_crash_2008", "loss_pct": "35"},
        )

        results = dispatcher.dispatch(alert)
        print(f"\nDispatch results: {results}")

        # Read and display file contents
        print(f"\nFile contents ({temp_file}):")
        with open(temp_file) as f:
            print(f.read())

    finally:
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)


def demo_routing_matrix():
    """Demonstrate severity-based routing."""
    print("\n" + "=" * 80)
    print("DEMO 3: Severity-Based Routing Matrix")
    print("=" * 80 + "\n")

    # Create channels
    console = ConsoleChannel(color=False)

    # Note: Other channels are disabled by default (no config)
    email = EmailChannel()
    slack = SlackChannel()

    print("Channel Status:")
    print(f"  Console: {'enabled' if console.enabled else 'disabled'}")
    print(f"  Email:   {'enabled' if email.enabled else 'disabled'}")
    print(f"  Slack:   {'enabled' if slack.enabled else 'disabled'}")
    print()

    # Create dispatcher with custom routing
    custom_routing = {
        AlertSeverity.INFO: ["console"],
        AlertSeverity.WARN: ["console"],
        AlertSeverity.CRITICAL: ["console", "email", "slack"],  # Will try but skip disabled
    }

    dispatcher = AlertDispatcher(
        channels=[console, email, slack],
        routing_matrix=custom_routing,
    )

    # Show routing configuration
    print("Routing Matrix:")
    for severity in [AlertSeverity.INFO, AlertSeverity.WARN, AlertSeverity.CRITICAL]:
        routes = dispatcher.get_routing_for_severity(severity)
        print(f"  {severity.value.upper()}: {routes}")

    print("\nEnabled channels:", dispatcher.get_enabled_channels())


def demo_async_dispatch():
    """Demonstrate async dispatch for parallel channel delivery."""
    print("\n" + "=" * 80)
    print("DEMO 4: Async Dispatch (Parallel Delivery)")
    print("=" * 80 + "\n")

    # Create multiple channels
    console = ConsoleChannel(color=False)

    # Create temp files for multiple file channels
    files = []
    channels = [console]

    for i in range(3):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            files.append(f.name)
            channels.append(FileChannel(file_path=f.name))

    try:
        # Custom routing to use all channels
        routing = {
            AlertSeverity.CRITICAL: ["console", "file", "file", "file"],  # Note: duplicates will be deduplicated
        }

        dispatcher = AlertDispatcher(channels=channels, routing_matrix=routing)

        # Send critical alert using async dispatch
        alert = AlertEvent(
            source="liquidity_gate",
            severity=AlertSeverity.CRITICAL,
            title="Liquidity Crisis",
            body="Insufficient liquidity for required positions",
            labels={"required": "100000", "available": "50000"},
        )

        print("Dispatching alert to multiple channels in parallel...")
        results = dispatcher.dispatch_async(alert)

        print(f"\nAsync dispatch results: {results}")
        print(f"Channels used: {list(results.keys())}")

    finally:
        # Cleanup
        for file_path in files:
            Path(file_path).unlink(missing_ok=True)


def demo_failover():
    """Demonstrate failover behavior when channels fail."""
    print("\n" + "=" * 80)
    print("DEMO 5: Failover to Backup Channels")
    print("=" * 80 + "\n")

    # Create channels
    console = ConsoleChannel()

    # Slack/email/telegram are disabled (no config)
    slack = SlackChannel()
    email = EmailChannel()

    # Custom routing with disabled channels first
    routing = {
        AlertSeverity.CRITICAL: ["slack", "email"],  # Both disabled
    }

    dispatcher = AlertDispatcher(
        channels=[slack, email, console],
        routing_matrix=routing,
        enable_failover=True,
    )

    print("Primary channels (will be skipped - disabled):")
    print(f"  Slack: {slack.enabled}")
    print(f"  Email: {email.enabled}")
    print("\nFailover channel:")
    print(f"  Console: {console.enabled}")
    print()

    # Send critical alert
    alert = AlertEvent(
        source="risk_gate",
        severity=AlertSeverity.CRITICAL,
        title="Risk Limit Breach",
        body="Multiple risk limits exceeded",
    )

    results = dispatcher.dispatch(alert)
    print(f"\nDispatch results: {results}")
    print("\nNote: Disabled channels were skipped, console failover succeeded")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Risk-Layer Multi-Channel Alerting System - Demo")
    print("=" * 80)

    demo_basic_alerting()
    demo_file_channel()
    demo_routing_matrix()
    demo_async_dispatch()
    demo_failover()

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Multiple notification channels (console, file, email, slack, telegram, webhook)")
    print("  ✓ Severity-based routing matrix")
    print("  ✓ Async dispatch for parallel delivery")
    print("  ✓ Failover to backup channels")
    print("  ✓ Safe defaults (external channels disabled by default)")
    print()
