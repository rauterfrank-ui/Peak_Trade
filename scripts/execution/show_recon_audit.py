#!/usr/bin/env python3
"""
Show Recon Audit Events

CLI helper for viewing RECON_SUMMARY and RECON_DIFF events from AuditLog.

Usage:
    python scripts/execution/show_recon_audit.py summary
    python scripts/execution/show_recon_audit.py diffs
    python scripts/execution/show_recon_audit.py detailed --run-id <run_id>

Design:
- SIM/PAPER only (no external APIs)
- Deterministic output (stable sorting)
- Reads from in-memory AuditLog or JSON export
- Phase 0: Demo mode with synthetic data
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.audit_log import AuditLog
from src.execution.contracts import LedgerEntry


@dataclass
class ReconAuditQuery:
    """Query parameters for recon audit events"""

    mode: str = "summary"  # summary, diffs, detailed
    run_id: Optional[str] = None
    session_id: Optional[str] = None
    severity: Optional[str] = None  # Filter by severity
    limit: int = 50  # Max results


def load_audit_log(json_path: Optional[str] = None) -> AuditLog:
    """
    Load audit log from JSON file or create demo data.

    Args:
        json_path: Path to JSON export (optional)

    Returns:
        AuditLog instance
    """
    audit_log = AuditLog()

    if json_path and Path(json_path).exists():
        # Load from JSON export
        with open(json_path) as f:
            entries_data = json.load(f)

        for entry_data in entries_data:
            # Reconstruct LedgerEntry
            entry = LedgerEntry(
                entry_id=entry_data["entry_id"],
                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                sequence=entry_data["sequence"],
                event_type=entry_data["event_type"],
                client_order_id=entry_data.get("client_order_id", ""),
                old_state=entry_data.get("old_state"),
                new_state=entry_data.get("new_state"),
                details=entry_data.get("details", {}),
            )
            # Bypass append() to preserve sequence from file
            audit_log._entries.append(entry)
            audit_log._sequence = max(audit_log._sequence, entry.sequence)

    return audit_log


def show_summary(audit_log: AuditLog, query: ReconAuditQuery) -> None:
    """
    Show reconciliation summary events.

    Output:
    - Run ID, timestamp, session, strategy
    - Total diffs, severity counts
    - Critical/fail flags
    """
    summaries = audit_log.get_entries_by_event_type("RECON_SUMMARY")

    # Filter by session if specified
    if query.session_id:
        summaries = [
            s for s in summaries if s.details.get("session_id") == query.session_id
        ]

    # Sort by timestamp (deterministic)
    summaries = sorted(summaries, key=lambda e: e.timestamp)

    # Apply limit
    summaries = summaries[: query.limit]

    if not summaries:
        print("No RECON_SUMMARY events found.")
        return

    print(f"Found {len(summaries)} RECON_SUMMARY event(s)\n")
    print("=" * 80)

    for entry in summaries:
        details = entry.details
        print(f"Run ID:      {details.get('run_id', 'N/A')}")
        print(f"Timestamp:   {entry.timestamp.isoformat()}")
        print(f"Session:     {details.get('session_id', 'N/A')}")
        print(f"Strategy:    {details.get('strategy_id', 'N/A')}")
        print(f"Total Diffs: {details.get('total_diffs', 0)}")
        print(
            f"Severity:    {json.dumps(details.get('counts_by_severity', {}), sort_keys=True)}"
        )
        print(f"Diff Types:  {json.dumps(details.get('counts_by_type', {}), sort_keys=True)}")
        print(f"Critical:    {details.get('has_critical', False)}")
        print(f"Fail:        {details.get('has_fail', False)}")
        print(f"Max Severity: {details.get('max_severity', 'INFO')}")
        print("=" * 80)


def show_diffs(audit_log: AuditLog, query: ReconAuditQuery) -> None:
    """
    Show reconciliation diff events.

    Output:
    - Diff ID, timestamp, run ID
    - Severity, type, description
    - Order ID, resolution status
    """
    diffs = audit_log.get_entries_by_event_type("RECON_DIFF")

    # Filter by run_id if specified
    if query.run_id:
        diffs = [d for d in diffs if d.details.get("run_id") == query.run_id]

    # Filter by severity if specified
    if query.severity:
        diffs = [d for d in diffs if d.details.get("severity") == query.severity]

    # Sort by timestamp (deterministic)
    diffs = sorted(diffs, key=lambda e: e.timestamp)

    # Apply limit
    diffs = diffs[: query.limit]

    if not diffs:
        print("No RECON_DIFF events found.")
        return

    print(f"Found {len(diffs)} RECON_DIFF event(s)\n")
    print("=" * 80)

    for entry in diffs:
        details = entry.details
        print(f"Diff ID:     {details.get('diff_id', 'N/A')}")
        print(f"Run ID:      {details.get('run_id', 'N/A')}")
        print(f"Timestamp:   {entry.timestamp.isoformat()}")
        print(f"Severity:    {details.get('severity', 'UNKNOWN')}")
        print(f"Type:        {details.get('diff_type', 'UNKNOWN')}")
        print(f"Order ID:    {entry.client_order_id or 'N/A'}")
        print(f"Description: {details.get('description', '')}")
        print(f"Resolved:    {details.get('resolved', False)}")

        # Show diff details if present
        diff_details = details.get("diff_details", {})
        if diff_details:
            print(f"Details:     {json.dumps(diff_details, sort_keys=True, indent=2)}")

        print("-" * 80)


def show_detailed(audit_log: AuditLog, query: ReconAuditQuery) -> None:
    """
    Show detailed view for a specific run.

    Output:
    - Summary + all diffs for that run
    """
    if not query.run_id:
        print("Error: --run-id required for detailed mode")
        sys.exit(1)

    # Get summary
    summaries = [
        e
        for e in audit_log.get_entries_by_event_type("RECON_SUMMARY")
        if e.details.get("run_id") == query.run_id
    ]

    if not summaries:
        print(f"No RECON_SUMMARY found for run_id={query.run_id}")
        return

    # Show summary
    print("SUMMARY")
    print("=" * 80)
    show_summary(audit_log, ReconAuditQuery(mode="summary", run_id=query.run_id))

    # Show all diffs for this run
    print("\nDIFFS")
    print("=" * 80)
    show_diffs(audit_log, ReconAuditQuery(mode="diffs", run_id=query.run_id, limit=1000))


def parse_args(args: List[str]) -> ReconAuditQuery:
    """
    Parse command line arguments.

    Args:
        args: Command line arguments (sys.argv[1:])

    Returns:
        ReconAuditQuery
    """
    if not args:
        print("Usage: show_recon_audit.py <mode> [options]")
        print()
        print("Modes:")
        print("  summary    Show reconciliation summary events")
        print("  diffs      Show reconciliation diff events")
        print("  detailed   Show detailed view for a specific run")
        print()
        print("Options:")
        print("  --run-id <id>      Filter by run ID")
        print("  --session-id <id>  Filter by session ID")
        print("  --severity <sev>   Filter by severity (INFO/WARN/FAIL/CRITICAL)")
        print("  --limit <n>        Max results (default: 50)")
        print("  --json <path>      Load from JSON export")
        sys.exit(1)

    mode = args[0]
    if mode not in ["summary", "diffs", "detailed"]:
        print(f"Error: Invalid mode '{mode}'")
        sys.exit(1)

    query = ReconAuditQuery(mode=mode)

    # Parse options
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--run-id" and i + 1 < len(args):
            query.run_id = args[i + 1]
            i += 2
        elif arg == "--session-id" and i + 1 < len(args):
            query.session_id = args[i + 1]
            i += 2
        elif arg == "--severity" and i + 1 < len(args):
            query.severity = args[i + 1].upper()
            i += 2
        elif arg == "--limit" and i + 1 < len(args):
            query.limit = int(args[i + 1])
            i += 2
        elif arg == "--json" and i + 1 < len(args):
            # Store path for later (not in query dataclass)
            i += 2
        else:
            print(f"Warning: Unknown option '{arg}'")
            i += 1

    return query


def main():
    """Main entry point"""
    args = sys.argv[1:]
    query = parse_args(args)

    # Load audit log (from JSON or demo data)
    json_path = None
    if "--json" in args:
        json_idx = args.index("--json")
        if json_idx + 1 < len(args):
            json_path = args[json_idx + 1]

    audit_log = load_audit_log(json_path)

    # Route to appropriate handler
    if query.mode == "summary":
        show_summary(audit_log, query)
    elif query.mode == "diffs":
        show_diffs(audit_log, query)
    elif query.mode == "detailed":
        show_detailed(audit_log, query)


if __name__ == "__main__":
    main()
