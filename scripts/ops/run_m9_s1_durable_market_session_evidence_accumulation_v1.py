#!/usr/bin/env python3
"""CLI: M9-S1 offline counterfactual replay + owner review accumulation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from research.m9_s1_durable_market_session_evidence_accumulation_v1.runner_v1 import (  # noqa: E402
    run_offline_replay_and_owner_review_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="M9-S1 durable market session evidence offline replay (no threshold selection)."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--join-ledger-path", type=Path, default=None)
    parser.add_argument("--observation-ledger-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository-sha", type=str, default=None)
    args = parser.parse_args(argv)

    sha = args.repository_sha
    if not sha:
        import subprocess

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(args.repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        sha = proc.stdout.strip() if proc.returncode == 0 else "unknown"

    package = run_offline_replay_and_owner_review_v1(
        repo_root=args.repo_root.resolve(),
        join_ledger_path=None if args.join_ledger_path is None else args.join_ledger_path.resolve(),
        m9_s1_observation_ledger_path=(
            None if args.observation_ledger_path is None else args.observation_ledger_path.resolve()
        ),
        output_dir=args.output_dir.resolve(),
        repository_sha=sha,
    )
    print(json.dumps(package, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
