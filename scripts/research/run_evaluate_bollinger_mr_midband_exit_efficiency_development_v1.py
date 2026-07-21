#!/usr/bin/env python3
"""Run exactly one preregistered DEVELOPMENT midband exit-efficiency evaluation.

Research-only. No holdout. No runtime / orders / productive authority mutation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.panel_runner_v1 import (  # noqa: E402
    run_development_evaluation,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (  # noqa: E402
    DEV_PANEL_SUBDIR,
)


def _default_archive_root() -> Path | None:
    env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
    if not env:
        return None
    return Path(env).expanduser().resolve() / DEV_PANEL_SUBDIR


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Bollinger/MR midband exit-efficiency (DEVELOPMENT, one run)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT
        / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v1",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed DEVELOPMENT panel archive root override.",
    )
    args = parser.parse_args()
    archive = args.archive_root
    if archive is None:
        archive = _default_archive_root()
        if archive is None:
            raise SystemExit("PEAK_TRADE_DATA_ARCHIVE_ROOT_UNSET")
    summary = run_development_evaluation(output_dir=args.output_dir, archive_root=archive)
    print(f"RESULT_CLASS={summary.get('result_class')}")
    print(f"REASON={summary.get('decision', {}).get('reason')}")
    print(f"EVALUATION_RUN_COUNT={summary.get('evaluation_run_count')}")
    print(f"HOLDOUT_DATA_ACCESSED={summary.get('holdout_data_accessed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
