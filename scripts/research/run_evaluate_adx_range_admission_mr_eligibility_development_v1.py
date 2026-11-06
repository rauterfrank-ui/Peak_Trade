#!/usr/bin/env python3
"""Run exactly one preregistered DEVELOPMENT evaluation (baseline vs ADX range-admission gate).

Operator-GO scope: DEVELOPMENT evaluation only. No holdout. No runtime/orders.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
for p in (_REPO, _REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.research.adx_range_admission_mr_eligibility_development_evaluation_v1.panel_runner_v1 import (  # noqa: E402
    run_development_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_REPO / "docs/evidence/evaluate_adx_range_admission_mr_eligibility_development_v1",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional override for sealed DEVELOPMENT panel archive root",
    )
    args = parser.parse_args()
    summary = run_development_evaluation(
        output_dir=args.output_dir,
        archive_root=args.archive_root,
        repo_root=_REPO,
    )
    print(
        json.dumps(
            {"result_class": summary["result_class"], "decision": summary["decision"]}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
