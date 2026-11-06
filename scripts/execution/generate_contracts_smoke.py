#!/usr/bin/env python3
"""
Generate contracts smoke report (WP0E Evidence)

This script generates a deterministic snapshot of all contract types
for evidence verification.
"""

import json
from pathlib import Path

from src.execution.contracts import serialize_contracts_snapshot


def main():
    """Generate contracts smoke snapshot"""
    # Generate snapshot
    snapshot = serialize_contracts_snapshot()

    # Add metadata
    report = {
        "phase": "WP0E - Contracts & Interfaces",
        "version": "1.0",
        "description": "Deterministic snapshot of execution contracts",
        "types": list(snapshot.keys()),
        "snapshot": snapshot,
    }

    # Write to reports/execution
    output_dir = Path(__file__).parent.parent.parent / "reports" / "execution"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "contracts_smoke.json"

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    print(f"✓ Contracts smoke report written to: {output_file}")
    print(f"  Types included: {', '.join(report['types'])}")

    return 0


if __name__ == "__main__":
    exit(main())
