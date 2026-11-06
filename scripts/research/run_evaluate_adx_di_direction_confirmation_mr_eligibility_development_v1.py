#!/usr/bin/env python3
"""Run exactly one preregistered DEVELOPMENT evaluation (baseline vs ADX DI direction-confirmation gate).

Research-only. No holdout. No runtime / orders / productive authority mutation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1.panel_runner_v1 import (  # noqa: E402
    run_development_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate ADX DI direction-confirmation MR eligibility (DEVELOPMENT, one run)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT
        / "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed DEVELOPMENT panel archive root override.",
    )
    args = parser.parse_args()
    summary = run_development_evaluation(
        output_dir=args.output_dir,
        archive_root=args.archive_root,
    )
    print(f"RESULT_CLASS={summary.get('result_class')}")
    print(f"REASON={summary.get('decision', {}).get('reason')}")
    print(f"EVALUATION_RUN_COUNT={summary.get('evaluation_run_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
