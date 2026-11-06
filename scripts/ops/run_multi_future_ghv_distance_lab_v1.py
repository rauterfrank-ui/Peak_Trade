#!/usr/bin/env python3
"""Run isolated Multi-Future GHV counterfactual distance lab (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.multi_future_ghv_counterfactual_distance_lab_v1.runner_v1 import (  # noqa: E402
    run_experiment_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--smoke", action="store_true", help="Small deterministic smoke matrix")
    parser.add_argument(
        "--max-runtime-hours",
        type=float,
        default=10.0,
        help="Wall-clock budget (default 10h)",
    )
    args = parser.parse_args()
    result = run_experiment_v1(
        repo_root=args.repo_root,
        evidence_root=args.evidence_root,
        smoke=args.smoke,
        max_runtime_seconds=args.max_runtime_hours * 3600.0,
    )
    print(result["evidence_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
