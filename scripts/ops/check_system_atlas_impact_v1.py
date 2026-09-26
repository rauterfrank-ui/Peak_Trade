#!/usr/bin/env python3
"""Classify Peak_Trade diffs for System Atlas impact. ATLAS_AUTHORITY=NONE. Offline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.system_atlas_v1.impact_v1 import (  # noqa: E402
    ATLAS_IMPACT_REVIEW_REQUIRED,
    evaluate_working_tree_v1,
    render_impact_markdown,
)
from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed Atlas impact checker. Does not confer canonical authority.",
    )
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--changed-file",
        action="append",
        default=None,
        help="Override git diff with an explicit path (repeatable; tests).",
    )
    parser.add_argument(
        "--atlas-yaml-diff-file",
        type=Path,
        default=None,
        help="Override git atlas YAML diff with a file (tests).",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    atlas = load_atlas_v1(repo_root=repo_root)
    yaml_diff = None
    if args.atlas_yaml_diff_file is not None:
        yaml_diff = args.atlas_yaml_diff_file.read_text(encoding="utf-8")
    report = evaluate_working_tree_v1(
        atlas=atlas,
        repo_root=repo_root,
        changed_files=args.changed_file,
        atlas_yaml_diff=yaml_diff if args.atlas_yaml_diff_file is not None else None,
        base=args.base,
    )
    sys.stdout.write(
        render_impact_markdown(
            report, impact_state=atlas["records"].get("provenance/impact_state.yaml") or {}
        )
    )
    if report.impact == ATLAS_IMPACT_REVIEW_REQUIRED or report.drift_detected:
        print("SYSTEM_ATLAS_DRIFT_DETECTED=true", file=sys.stderr)
        return 1
    print("SYSTEM_ATLAS_DRIFT_DETECTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
