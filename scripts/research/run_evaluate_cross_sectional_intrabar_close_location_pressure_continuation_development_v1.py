#!/usr/bin/env python3
"""Canonical DEVELOPMENT evaluation entry point for CS intrabar CLV pressure continuation v1.

Modes:
  - preflight (default): bind digests/guards/evidence schema; no panel; no run.
  - dry-validate: prove executable-path contracts without runner start or counters.
  - evaluate: requires machine-checkable authorization; fail-closed while
    development_evaluation_authorized=false on HEAD.

Generic LIVE/SHADOW/TESTNET/SCHEDULER flags cannot authorize this runner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.constants_v1 import (  # noqa: E402
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.entry_point_v1 import (  # noqa: E402
    run_dry_validate,
    run_evaluate_fail_closed,
    run_preflight_only,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.guards_v1 import (  # noqa: E402
    GuardError,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CS intrabar CLV pressure continuation v1 DEVELOPMENT evaluation entry point "
            "(default: preflight; evaluate remains unauthorized on HEAD)."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("preflight", "dry-validate", "evaluate"),
        default="preflight",
        help="preflight (default), dry-validate, or evaluate (auth fail-closed on HEAD).",
    )
    parser.add_argument(
        "--authorize-single-development-evaluation",
        default="",
        help=(
            f"Must equal {HYPOTHESIS_ID}; still fail-closed while "
            "development_evaluation_authorized=false on HEAD."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for preflight report / evaluate evidence.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Rejected: cannot authorize this research entry point.",
    )
    parser.add_argument(
        "--shadow",
        action="store_true",
        help="Rejected: cannot authorize this research entry point.",
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Rejected: cannot authorize this research entry point.",
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Rejected: cannot authorize this research entry point.",
    )
    args = parser.parse_args(argv)

    if args.live or args.shadow or args.testnet or args.scheduler:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "reason": "RUNTIME_FLAG_REJECTED",
                    "runner_started": False,
                    "evaluation_executed": False,
                },
                sort_keys=True,
            )
        )
        return 2

    try:
        if args.mode == "preflight":
            report = run_preflight_only(REPO_ROOT, output_dir=args.output_dir)
            print(json.dumps(report, sort_keys=True, default=str))
            return 0

        if args.mode == "dry-validate":
            report = run_dry_validate(REPO_ROOT)
            print(json.dumps(report, sort_keys=True, default=str))
            return 0

        output_dir = args.output_dir or (REPO_ROOT / EVIDENCE_REL_PATH)
        report = run_evaluate_fail_closed(
            REPO_ROOT,
            authorize_token=args.authorize_single_development_evaluation,
            output_dir=Path(output_dir),
        )
        print(json.dumps(report, sort_keys=True, default=str))
        return 0
    except GuardError as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "reason": str(exc),
                    "runner_started": False,
                    "evaluation_executed": False,
                    "holdout_accessed": False,
                },
                sort_keys=True,
            )
        )
        return 2
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "reason": f"UNEXPECTED:{type(exc).__name__}:{exc}",
                    "runner_started": False,
                    "evaluation_executed": False,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
