#!/usr/bin/env python3
"""Offline CLI for forensic whole-system crosswalk (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import json
import subprocess
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
    parser.add_argument(
        "--declared-current-sha",
        default=None,
        help="Owner-declared CURRENT main SHA for forensic proof eligibility (not inferred from HEAD)",
    )
    parser.add_argument(
        "--test-execution-sha",
        default=None,
        help="Git SHA of the tree used to execute this crosswalk (fail-closed for CURRENT proof)",
    )
    parser.add_argument(
        "--workspace-read-declared-pin",
        action="store_true",
        help="Caller attestation: filesystem reads used unpinned workspace despite declared pin",
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

    from scripts.ops.ghv_forensic_source_provenance_v1.reporting_v1 import (
        build_forensic_source_provenance_report_v1,
        write_forensic_source_provenance_report_v1,
    )

    impl_sha = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    provenance_report = build_forensic_source_provenance_report_v1(
        repo_root=repo_root,
        output_dir=output_dir,
        declared_current_sha=args.declared_current_sha,
        test_execution_sha=args.test_execution_sha,
        coverage=dict(result.coverage),
        crosswalk_ok=result.ok,
        evidence_root=args.evidence_root.resolve() if args.evidence_root else None,
        workspace_read_declared_pin=args.workspace_read_declared_pin,
        implementation_source_sha=impl_sha,
    )
    write_forensic_source_provenance_report_v1(
        repo_root=repo_root,
        output_dir=output_dir,
        report=provenance_report,
    )
    proof_eligibility = provenance_report["record"]["PROOF_ELIGIBILITY"]
    print(
        json.dumps(
            {
                "status": "PASS" if result.ok else "FAIL",
                "crosswalk_cli_ok": result.ok,
                "proof_eligibility": proof_eligibility,
                "proof_eligibility_reasons": provenance_report["record"][
                    "PROOF_ELIGIBILITY_REASONS"
                ],
                "output_dir": str(output_dir),
                "forensic_source_provenance_report": str(
                    output_dir / "forensic_source_provenance_report.v1.json"
                ),
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
