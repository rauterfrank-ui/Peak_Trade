#!/usr/bin/env python3
"""
Demo: Generate sample recon audit events for testing show_recon_audit.py

Creates synthetic RECON_SUMMARY and RECON_DIFF events and exports to JSON.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.audit_log import AuditLog
from src.execution.contracts import ReconSummary, ReconDiff


def generate_demo_data() -> AuditLog:
    """Generate sample recon audit events"""
    audit_log = AuditLog()

    # Run 1: Minor position mismatch (WARN)
    diff1 = ReconDiff(
        diff_id="diff_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        client_order_id="order_btc_001",
        severity="WARN",
        diff_type="POSITION",
        description="Position mismatch: local=0.1 BTC, exchange=0.0995 BTC (0.5% drift)",
        details={"local_qty": 0.1, "exchange_qty": 0.0995, "drift_pct": 0.5},
    )

    summary1 = ReconSummary(
        run_id="run_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        session_id="session_paper_001",
        strategy_id="ma_crossover",
        total_diffs=1,
        counts_by_severity={"WARN": 1},
        counts_by_type={"POSITION": 1},
        top_diffs=[diff1],
        has_critical=False,
        has_fail=False,
        max_severity="WARN",
    )

    audit_log.append_recon_summary(summary1)

    # Run 2: Multiple diffs including FAIL
    diff2a = ReconDiff(
        diff_id="diff_002a",
        timestamp=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        client_order_id="order_eth_002",
        severity="FAIL",
        diff_type="CASH",
        description="Cash balance divergence: local=1000.0 EUR, exchange=950.0 EUR",
        details={"local_balance": 1000.0, "exchange_balance": 950.0, "delta": -50.0},
    )

    diff2b = ReconDiff(
        diff_id="diff_002b",
        timestamp=datetime(2026, 1, 1, 11, 0, 1, tzinfo=timezone.utc),
        client_order_id="order_eth_003",
        severity="INFO",
        diff_type="POSITION",
        description="Minor position drift: 0.01% (within tolerance)",
        details={"drift_pct": 0.01},
    )

    summary2 = ReconSummary(
        run_id="run_002",
        timestamp=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        session_id="session_paper_001",
        strategy_id="ma_crossover",
        total_diffs=2,
        counts_by_severity={"FAIL": 1, "INFO": 1},
        counts_by_type={"CASH": 1, "POSITION": 1},
        top_diffs=[diff2a, diff2b],
        has_critical=False,
        has_fail=True,
        max_severity="FAIL",
    )

    audit_log.append_recon_summary(summary2)

    # Run 3: Clean run (no diffs)
    summary3 = ReconSummary(
        run_id="run_003",
        timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        session_id="session_paper_002",
        strategy_id="breakout",
        total_diffs=0,
        counts_by_severity={},
        counts_by_type={},
        top_diffs=[],
        has_critical=False,
        has_fail=False,
        max_severity="INFO",
    )

    audit_log.append_recon_summary(summary3)

    return audit_log


def main():
    """Generate demo data and export"""
    print("Generating demo recon audit events...")
    audit_log = generate_demo_data()

    # Export to JSON
    output_path = Path(__file__).parent.parent.parent / "demo_recon_audit.json"
    audit_log.export_to_file(str(output_path))

    print(f"✓ Exported {audit_log.get_entry_count()} entries to {output_path}")
    print()
    print("Try these commands:")
    print(f"  python scripts/execution/show_recon_audit.py summary --json {output_path}")
    print(f"  python scripts/execution/show_recon_audit.py diffs --json {output_path}")
    print(
        f"  python scripts/execution/show_recon_audit.py detailed --run-id run_002 --json {output_path}"
    )


if __name__ == "__main__":
    main()
