#!/usr/bin/env python3
"""
Docs Graph Snapshot Generator

Generates a deterministic snapshot of the documentation link graph.

Usage:
    uv run python scripts/ops/docs_graph_snapshot.py \\
        --roots docs/WORKFLOW_FRONTDOOR.md WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md \\
        --out docs/_generated/docs_graph_snapshot.json

Exit Codes:
    0 = Success (or no broken links if --fail-on-broken)
    1 = Error or broken links found (if --fail-on-broken)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from _docs_graph import build_graph, find_orphans


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate docs graph snapshot (JSON only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=[
            "docs/WORKFLOW_FRONTDOOR.md",
            "WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md",
            "docs/ops/README.md",
            "docs/INSTALLATION_QUICKSTART.md",
        ],
        help="Root source files for graph traversal",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON file path (required)",
    )
    parser.add_argument(
        "--include-archives",
        action="store_true",
        default=False,
        help="Include docs/ops/_archive/** in analysis (default: False)",
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="docs",
        help="Docs directory to scan (default: docs)",
    )
    parser.add_argument(
        "--fail-on-broken",
        action="store_true",
        default=False,
        help="Exit with code 1 if broken targets/anchors found (default: False)",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=None,
        help="Optional safety cap on number of nodes (default: none)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: current directory)",
    )

    args = parser.parse_args()

    # Determine repo root
    repo_root = args.repo_root if args.repo_root else Path.cwd()
    if not repo_root.exists():
        print(f"Error: Repository root not found: {repo_root}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Build graph (with timing)
    start_time = time.time()
    print(f"Building docs graph from {repo_root}...", file=sys.stderr)
    nodes_dict, edges_list, broken_targets_list, broken_anchors_list = build_graph(
        repo_root=repo_root,
        roots=args.roots,
        include_archives=args.include_archives,
        docs_dir=args.docs_dir,
    )

    # Check max_nodes safety cap
    if args.max_nodes and len(nodes_dict) > args.max_nodes:
        print(
            f"Error: Node count {len(nodes_dict)} exceeds safety cap {args.max_nodes}",
            file=sys.stderr,
        )
        return 1

    # Find orphans
    orphans_list = find_orphans(nodes=nodes_dict, roots=args.roots)

    runtime_seconds = time.time() - start_time

    # Convert to JSON-serializable format (schema v1.0.0)
    roots_set = set(args.roots)
    nodes_json = [
        {
            "path": path,
            "is_root": path in roots_set,
        }
        for path in sorted(nodes_dict.keys())
    ]

    edges_json = [
        {
            "src": e.src,
            "dst": e.dst,
            "kind": "md",
            "anchor": e.anchor,
            "raw": e.raw if hasattr(e, "raw") else None,
        }
        for e in edges_list
    ]

    broken_targets_json = [
        {
            "src": b.src,
            "raw": b.target,
            "resolved": b.target,
            "reason": b.reason if hasattr(b, "reason") else "file not found",
        }
        for b in broken_targets_list
    ]

    broken_anchors_json = [
        {
            "src": b.src,
            "dst": b.target,
            "anchor": b.anchor,
            "reason": f"anchor not found: #{b.anchor}",
        }
        for b in broken_anchors_list
    ]

    orphans_json = [{"path": path} for path in orphans_list]

    # Build output (schema v1.0.0)
    output_data = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "roots": args.roots,
        "config": {
            "include_archives": args.include_archives,
            "docs_dir": args.docs_dir,
        },
        "stats": {
            "nodes": len(nodes_dict),
            "edges": len(edges_list),
            "broken_targets": len(broken_targets_list),
            "broken_anchors": len(broken_anchors_list),
            "orphaned_pages": len(orphans_list),
            "runtime_seconds": round(runtime_seconds, 3),
        },
        "nodes": nodes_json,
        "edges": edges_json,
        "broken_targets": broken_targets_json,
        "broken_anchors": broken_anchors_json,
        "orphans": orphans_json,
    }

    # Write JSON output
    args.out.write_text(json.dumps(output_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"✅ JSON snapshot written to: {args.out}", file=sys.stderr)

    # Print summary
    print("\n📊 Summary:", file=sys.stderr)
    print(f"  Nodes: {len(nodes_dict)}", file=sys.stderr)
    print(f"  Edges: {len(edges_list)}", file=sys.stderr)
    print(f"  Broken targets: {len(broken_targets_list)}", file=sys.stderr)
    print(f"  Broken anchors: {len(broken_anchors_list)}", file=sys.stderr)
    print(f"  Orphaned pages: {len(orphans_list)}", file=sys.stderr)
    print(f"  Runtime: {runtime_seconds:.3f}s", file=sys.stderr)

    # Fail on broken if requested
    if args.fail_on_broken and (broken_targets_list or broken_anchors_list):
        print(
            f"\n❌ Found {len(broken_targets_list) + len(broken_anchors_list)} broken link(s)",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
