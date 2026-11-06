#!/usr/bin/env python3
"""Offline CLI for forensic whole-system crosswalk (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> int:
    _ensure_repo_on_path()
    parser = argparse.ArgumentParser(description="GHV forensic whole-system crosswalk v1")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Peak_Trade repository root (must not be C1 overlay worktree for baseline graph)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Isolated forensic output directory (default: /tmp/ghv_forensic_crosswalk_<utc>)",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path(__file__).resolve().parent / "crosswalk_rules.v1.json",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=None,
        help="Optional GHV capture dir; ingested only if repository_sha matches HEAD",
    )
    parser.add_argument("--no-atlas", action="store_true", help="Skip atlas entities/relations")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--navigation-only",
        action="store_true",
        help="NAVIGATION_ONLY mode: tolerate snapshot drift; graph has no CURRENT verification authority",
    )
    mode.add_argument(
        "--skip-snapshot-binding",
        action="store_true",
        help="Alias for --navigation-only (explicit selector only; no silent fallback)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if "pl_c1_p510a_entry_exit_alignment" in str(repo_root):
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "blocker": "C1_WORKTREE_NOT_ALLOWED_FOR_CURRENT_BASELINE_GRAPH",
                }
            )
        )
        return 2

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path(f"/tmp/ghv_forensic_crosswalk_{ts}")

    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.compose_v1 import (
        run_forensic_crosswalk_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.graph_mode_v1 import (
        GraphMode,
        parse_graph_mode,
    )

    graph_mode = parse_graph_mode(
        navigation_only=args.navigation_only or args.skip_snapshot_binding
    )

    result = run_forensic_crosswalk_v1(
        repo_root=repo_root,
        output_dir=output_dir,
        rules_path=args.rules,
        evidence_root=args.evidence_root,
        include_atlas=not args.no_atlas,
        graph_mode=graph_mode,
    )
    print(
        json.dumps(
            {
                "status": "PASS" if result.ok else "FAIL",
                "output_dir": str(output_dir),
                "snapshot_id": result.snapshot_id,
                "node_count": len(result.nodes),
                "edge_count": len(result.edges),
                "graph_mode": result.coverage.get("GRAPH_MODE"),
                "graph_authority": result.coverage.get("GRAPH_AUTHORITY"),
                "coverage": result.coverage,
            },
            sort_keys=True,
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
