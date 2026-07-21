#!/usr/bin/env python3
"""Materialize/apply V7 DEVELOPMENT evaluation authorization ratification.

Does not start the evaluation runner. Does not claim a run slot.

Requires released DEVELOPMENT panel and READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION.
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

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8 import (  # noqa: E402
    EvaluationAuthorizationRatificationError,
    apply_evaluation_authorization_transition,
    materialize_ratification_file,
    resolve_effective_evaluation_authorization,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authorize V7 DEVELOPMENT evaluation (no runner start)."
    )
    parser.add_argument(
        "--mode",
        choices=("materialize", "apply", "status"),
        default="status",
    )
    parser.add_argument("--archive-root", type=Path, default=None)
    args = parser.parse_args(argv)
    archive = args.archive_root
    if archive is None:
        env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
        archive = Path(env).expanduser() if env else None

    try:
        if args.mode == "materialize":
            payload = materialize_ratification_file(REPO_ROOT)
            print("MODE=materialize")
            print(f"RATIFICATION_DIGEST={payload.get('ratification_digest')}")
            print("RUNNER_STARTED=false")
            return 0
        if args.mode == "apply":
            result = apply_evaluation_authorization_transition(
                REPO_ROOT, archive_root=archive, write_evidence=True
            )
            print("MODE=apply")
            print(f"STATUS={result.get('status')}")
            print(f"EVALUATION_AUTHORIZED={result.get('evaluation_authorized')}")
            print(f"IDEMPOTENT={result.get('idempotent')}")
            print(f"AUTHORITY_DIGEST={result.get('authority_digest')}")
            print(f"EVALUATION_RUN_COUNT={result.get('evaluation_run_count')}")
            print(f"RUN_SLOT_CONSUMED={result.get('run_slot_consumed')}")
            print("RUNNER_STARTED=false")
            print("HOLDOUT_DATA_ACCESSED=false")
            return 0
        effective = resolve_effective_evaluation_authorization(REPO_ROOT, archive_root=archive)
        print("MODE=status")
        print(f"EVALUATION_AUTHORIZED={effective.get('evaluation_authorized')}")
        print(f"REASON={effective.get('reason')}")
        print(f"LIFECYCLE_STATUS={effective.get('lifecycle_status')}")
        print("RUNNER_STARTED=false")
        return 0 if effective.get("evaluation_authorized") else 1
    except EvaluationAuthorizationRatificationError as exc:
        print("RESULT=FAIL")
        print(f"REASON={exc}")
        print("RUNNER_STARTED=false")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
