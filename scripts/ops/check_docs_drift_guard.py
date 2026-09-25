#!/usr/bin/env python3
"""
Docs Drift Guard — Slice A (deterministic, PR-local).

Compares changed files against a base ref (default: origin/main). If a sensitive
path changed but none of the mapped required_docs changed, exit 1.

Exit codes:
  0 — OK (no violation, or no sensitive changes)
  1 — Drift: sensitive change without required doc update
  2 — Configuration or git error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from ops.truth import (  # noqa: E402
    TruthStatus,
    evaluate_docs_drift,
    git_changed_files_three_dot,
    load_docs_truth_map,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Docs drift guard: sensitive changes require canonical doc updates.",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git base ref for three-dot diff (default: origin/main).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root (default: auto).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_REPO_ROOT / "config" / "ops" / "docs_truth_map.yaml",
        help="Path to docs_truth_map.yaml.",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    cfg_path = args.config.resolve()

    if not cfg_path.is_file():
        print(f"ERR: config not found: {cfg_path}", file=sys.stderr)
        return 2

    try:
        mapping = load_docs_truth_map(cfg_path)
    except Exception as e:
        print(f"ERR: failed to load mapping: {e}", file=sys.stderr)
        return 2

    try:
        changed = git_changed_files_three_dot(repo_root, args.base)
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        print(
            "Hint: ensure the base ref exists (e.g. git fetch origin).",
            file=sys.stderr,
        )
        return 2

    result = evaluate_docs_drift(changed, mapping)

    if result.status is TruthStatus.PASS:
        print("docs_drift_guard: OK (no sensitive changes without required doc updates).")
        print(f"  base={args.base!r}  changed_files={len(changed)}")
        return 0

    print(
        "docs_drift_guard: FAIL — sensitive area changed but no required canonical doc in diff.\n",
        file=sys.stderr,
    )
    for v in result.violations:
        print(f"  Rule: {v.rule_id}", file=sys.stderr)
        print("  Sensitive paths touched:", file=sys.stderr)
        for t in v.triggered_paths:
            print(f"    - {t}", file=sys.stderr)
        print(
            "  At least one of these docs should have been updated in the same diff:",
            file=sys.stderr,
        )
        for r in v.required_docs:
            print(f"    - {r}", file=sys.stderr)
        print(file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
