#!/usr/bin/env python3
"""
Repo Truth Claims — deterministic presence checks against repo_truth_claims.yaml.

Exit codes:
  0 — All claims PASS
  1 — At least one claim FAIL
  2 — Configuration/load error, or aggregate UNKNOWN (unsupported checks)
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
    evaluate_repo_truth_claims,
    load_repo_truth_claims,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify declarative repo truth claims (path existence, etc.).",
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
        default=_REPO_ROOT / "config" / "ops" / "repo_truth_claims.yaml",
        help="Path to repo_truth_claims.yaml.",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    cfg_path = args.config.resolve()

    if not cfg_path.is_file():
        print(f"ERR: config not found: {cfg_path}", file=sys.stderr)
        return 2

    try:
        claims_cfg = load_repo_truth_claims(cfg_path)
    except Exception as e:
        print(f"ERR: failed to load claims: {e}", file=sys.stderr)
        return 2

    result = evaluate_repo_truth_claims(repo_root, claims_cfg)

    for r in result.results:
        line = f"[{r.status.value}] {r.check_id}: {r.message}"
        if r.status is TruthStatus.PASS:
            print(line)
        else:
            print(line, file=sys.stderr)

    if result.status is TruthStatus.PASS:
        print(f"repo_truth_claims: OK ({len(result.results)} check(s)).")
        return 0
    if result.status is TruthStatus.FAIL:
        print("repo_truth_claims: FAIL — one or more claims did not hold.", file=sys.stderr)
        return 1

    print("repo_truth_claims: UNKNOWN — unsupported or ambiguous claim(s).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
