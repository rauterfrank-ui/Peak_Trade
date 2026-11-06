#!/usr/bin/env python3
"""Classify PR diffs for Current Law Impact Map. LAW_IMPACT_MAP_AUTHORITY=NONE."""

from __future__ import annotations

import argparse
import sys
import json
import subprocess
from pathlib import Path
from runpy import run_path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.current_law_impact_map_v1 import _load_json, SOURCE_PATH  # noqa: E402
from scripts.ops.law_map_v1.impact_v1 import (  # noqa: E402
    LAW_IMPACT_REVIEW_REQUIRED,
    evaluate_changed_paths,
    git_changed_paths,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Law impact checker (non-authoritative).")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--advisory-only",
        action="store_true",
        help="Exit 0 even when REVIEW_REQUIRED (default for bootstrap maturity).",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    doc = _load_json(repo_root / SOURCE_PATH.relative_to(_REPO_ROOT))
    candidates_path = (
        repo_root / "config/governance/current_law_impact_map_v1/impact_candidates_v1.json"
    )
    candidates = _load_json(candidates_path)
    if doc.get("policy_inventory"):
        tracked = subprocess.check_output(
            ["git", "diff", "--name-only", doc["baseline_sha"], "--"], cwd=repo_root, text=True
        ).splitlines()
        extras = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_root, text=True
        ).splitlines()
        changed = sorted(set(tracked + extras))
        projection = run_path(str(repo_root / "docs/system_atlas/policy_projection.py"))
        policy_impact = projection["policy_impact_for_paths"](doc, changed, repo_root)
        print("LAW_COMPARISON=FROZEN_SOURCE")
        print(
            json.dumps(
                {
                    "indexed_policy_hits": len(policy_impact["policies"]),
                    "source_reference_paths": len(policy_impact["source_references"]),
                    "test_reference_paths": len(policy_impact["test_references"]),
                    "runtime_effect_inferred": False,
                }
            )
        )
    else:
        changed = git_changed_paths(repo_root, args.base)
    report = evaluate_changed_paths(
        doc, changed, candidate_surfaces=list(candidates.get("surfaces", []))
    )
    sys.stdout.write(report.marker_block())
    if report.unclassified_surfaces:
        print("LAW_UNCLASSIFIED_SURFACES=true", file=sys.stderr)
        for path in report.unclassified_surfaces:
            print(f"  - {path}", file=sys.stderr)
    if report.impact == LAW_IMPACT_REVIEW_REQUIRED:
        print("LAW_IMPACT_REVIEW_REQUIRED=true", file=sys.stderr)
        if args.advisory_only:
            print("LAW_IMPACT_ADVISORY_ONLY=true")
            return 0
        return 1
    print("LAW_IMPACT_REVIEW_REQUIRED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
