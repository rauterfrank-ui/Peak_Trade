#!/usr/bin/env python3
"""Run Multi-Future GHV Counterfactual Distance Lab V3 (research-only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.multi_future_ghv_counterfactual_distance_lab_v3.runner_v3 import run_lab_v3  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--smoke", action="store_true", help="Bounded smoke flight matrix")
    args = parser.parse_args()
    result = run_lab_v3(repo_root=args.repo_root, smoke=args.smoke)
    print(result.get("evidence_dir", result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
