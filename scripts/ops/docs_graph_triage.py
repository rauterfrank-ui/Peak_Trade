#!/usr/bin/env python3
"""
Docs Graph Triage Tool

Analyzes a docs graph snapshot and generates triage reports for broken targets and orphans.

Usage:
    uv run python scripts/ops/docs_graph_triage.py \\
        --snapshot docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json \\
        --out-dir docs/ops/graphs/snapshots/2026-01-13

Exit Codes:
    0 = Success (always, even with broken links - this is triage, not a gate)

Token Policy:
    All inline-code paths containing "/" are escaped as "&#47;" to comply with
    Peak_Trade token policy (no illustrative path-like strings in docs).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def safe_escape_path(path: str) -> str:
    """
    Escape "/" in paths for inline-code markdown contexts per Token Policy.

    Example: "docs/ops/README.md" → "docs&#47;ops&#47;README.md"
    """
    return path.replace("/", "&#47;")


def categorize_broken_targets(broken_targets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group broken targets by reason (root cause class).

    Returns dict: {reason: [broken_target_dicts]}
    """
    categorized: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bt in broken_targets:
        reason = bt.get("reason", "unknown")
        categorized[reason].append(bt)
    return dict(categorized)


def categorize_orphans(orphans: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group orphans by doc area (directory prefix).

    Returns dict: {area: [orphan_dicts]}
    """
    categorized: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for orphan in orphans:
        path = orphan.get("path", "")
        # Determine area
        if path.startswith("docs/ops/runbooks/"):
            area = "docs/ops/runbooks"
        elif path.startswith("docs/ops/"):
            area = "docs/ops"
        elif path.startswith("docs/"):
            area = "docs"
        elif path.startswith("src/"):
            area = "src"
        elif path.startswith("tests/"):
            area = "tests"
        else:
            area = "root"
        categorized[area].append(orphan)
    return dict(categorized)


def generate_broken_targets_md(
    broken_targets: list[dict[str, Any]],
    out_path: Path,
    snapshot_path: str,
) -> None:
    """Generate broken_targets.md report."""
    categorized = categorize_broken_targets(broken_targets)

    # Sort categories by count (descending), then alphabetically
    sorted_categories = sorted(
        categorized.items(),
        key=lambda x: (-len(x[1]), x[0])
    )

    lines = [
        "# Broken Targets Report",
        "",
        f"**Snapshot:** `{safe_escape_path(snapshot_path)}`  ",
        f"**Total Broken Targets:** {len(broken_targets)}",
        "",
        "## Summary by Reason",
        "",
    ]

    for reason, items in sorted_categories:
        lines.append(f"- **{reason}:** {len(items)}")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Breakdown",
        "",
    ])

    for reason, items in sorted_categories:
        lines.append(f"### {reason.title()} ({len(items)})")
        lines.append("")

        # Sort items by src, then raw
        sorted_items = sorted(items, key=lambda x: (x.get("src", ""), x.get("raw", "")))

        for item in sorted_items:
            src = safe_escape_path(item.get("src", "unknown"))
            raw = safe_escape_path(item.get("raw", "unknown"))
            resolved = safe_escape_path(item.get("resolved", "unknown"))

            lines.append(f"- **Source:** `{src}`")
            lines.append(f"  - **Raw target:** `{raw}`")
            if resolved != raw:
                lines.append(f"  - **Resolved:** `{resolved}`")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def generate_orphans_md(
    orphans: list[dict[str, Any]],
    out_path: Path,
    snapshot_path: str,
) -> None:
    """Generate orphans.md report."""
    categorized = categorize_orphans(orphans)

    # Sort categories by count (descending), then alphabetically
    sorted_categories = sorted(
        categorized.items(),
        key=lambda x: (-len(x[1]), x[0])
    )

    lines = [
        "# Orphaned Pages Report",
        "",
        f"**Snapshot:** `{safe_escape_path(snapshot_path)}`  ",
        f"**Total Orphans:** {len(orphans)}",
        "",
        "## Summary by Area",
        "",
    ]

    for area, items in sorted_categories:
        lines.append(f"- **{area}:** {len(items)}")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Breakdown",
        "",
    ])

    for area, items in sorted_categories:
        lines.append(f"### {area} ({len(items)})")
        lines.append("")

        # Sort items alphabetically by path
        sorted_items = sorted(items, key=lambda x: x.get("path", ""))

        for item in sorted_items:
            path = safe_escape_path(item.get("path", "unknown"))
            lines.append(f"- `{path}`")

        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Docs graph triage tool - analyze snapshot for broken targets and orphans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help="Path to docs_graph_snapshot.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for triage reports",
    )

    args = parser.parse_args()

    # Validate snapshot file
    if not args.snapshot.exists():
        print(f"Error: Snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1

    # Load snapshot
    try:
        with open(args.snapshot, encoding="utf-8") as f:
            snapshot = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: Failed to load snapshot: {e}", file=sys.stderr)
        return 1

    # Extract data
    broken_targets = snapshot.get("broken_targets", [])
    broken_anchors = snapshot.get("broken_anchors", [])
    orphans = snapshot.get("orphans", [])
    metadata = snapshot.get("metadata", {})

    # Create output directory
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Generate reports
    broken_targets_path = args.out_dir / "broken_targets.md"
    orphans_path = args.out_dir / "orphans.md"

    generate_broken_targets_md(
        broken_targets=broken_targets,
        out_path=broken_targets_path,
        snapshot_path=str(args.snapshot),
    )

    generate_orphans_md(
        orphans=orphans,
        out_path=orphans_path,
        snapshot_path=str(args.snapshot),
    )

    # Print summary to stdout
    print("=" * 60)
    print("DOCS GRAPH TRIAGE SUMMARY")
    print("=" * 60)
    print(f"Snapshot: {args.snapshot}")
    print(f"Output:   {args.out_dir}")
    print()
    print(f"Broken targets:  {len(broken_targets)}")
    print(f"Broken anchors:  {len(broken_anchors)}")
    print(f"Orphaned pages:  {len(orphans)}")
    print()
    print(f"Reports generated:")
    print(f"  - {broken_targets_path}")
    print(f"  - {orphans_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
