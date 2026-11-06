#!/usr/bin/env python3
"""Stage-2 proof-surface repair + bounded reproof (v2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.multi_future_ghv_counterfactual_distance_lab_v2.runner_v2 import run_lab_v2  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    result = run_lab_v2(repo_root=args.repo_root, smoke=args.smoke)
    print(result["evidence_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
