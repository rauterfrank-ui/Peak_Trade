#!/usr/bin/env python3
"""Run the single preregistered, execution-gated ADX DI direction-confirmation HOLDOUT evaluation.

Fail-closed duplicate-run protection (BEFORE any sealed holdout data access):
an exclusive, non-blocking ``fcntl.flock`` on ``<output-dir>/.holdout_run.lock``
plus a persisted ``<output-dir>/.holdout_run_consumed`` marker. Either
condition unconditionally blocks a second invocation with exit code ``2``
and no data access. Requires the separate explicit operator GO
(``PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO=true``); this script does not set
it, the operator/environment must.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2.panel_runner_v1 import (  # noqa: E402
    run_holdout_evaluation,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (  # noqa: E402
    HoldoutPreregistrationError,
    assert_execution_go_present,
)

LOCK_FILENAME = ".holdout_run.lock"
CONSUMED_MARKER_FILENAME = ".holdout_run_consumed"
BLOCKED_RESULT_CLASS = "BLOCKED_NO_RERUN"
DUPLICATE_RUN_REASON = "HOLDOUT_DUPLICATE_RUN_BLOCKED"


def _write_blocked_manifest(output_dir: Path, *, reason: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema_version": "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_run_manifest.v2",
        "result_class": BLOCKED_RESULT_CLASS,
        "reason": reason,
        "holdout_accessed": False,
        "sealed_holdout_content_inspected": False,
        "run_blocked_before_data_access": True,
        "exit_code": 2,
    }
    (output_dir / "run_manifest_blocked.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_failure_manifest(output_dir: Path, *, reason: str, exc: BaseException) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema_version": "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_run_manifest.v2",
        "result_class": "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN",
        "reason": reason,
        "error": f"{type(exc).__name__}:{exc}",
        "traceback": traceback.format_exc(),
        "holdout_accessed": True,
        "sealed_holdout_content_inspected": True,
        "holdout_run_count": 1,
        "no_retry": True,
        "exit_code": 1,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the single preregistered, execution-gated ADX DI direction-confirmation "
            "MR eligibility HOLDOUT evaluation (baseline vs treatment, one run)."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT
        / "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed FINAL_AUDIT holdout panel archive root override.",
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    consumed_marker = output_dir / CONSUMED_MARKER_FILENAME
    lock_path = output_dir / LOCK_FILENAME

    # Duplicate-run guard #1: a prior consumed marker unconditionally blocks,
    # BEFORE opening the lock file or touching any preregistration / data
    # access code path.
    if consumed_marker.is_file():
        print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
        print(f"REASON={DUPLICATE_RUN_REASON}")
        print("HOLDOUT_RUN_COUNT=0")
        _write_blocked_manifest(output_dir, reason=DUPLICATE_RUN_REASON)
        return 2

    # Duplicate-run guard #2: exclusive, non-blocking file lock. Held for the
    # lifetime of this process so a genuinely concurrent second invocation is
    # also blocked (not just a second invocation after this one exits).
    lock_fh = lock_path.open("a+")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_fh.close()
        print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
        print(f"REASON={DUPLICATE_RUN_REASON}")
        print("HOLDOUT_RUN_COUNT=0")
        _write_blocked_manifest(output_dir, reason=DUPLICATE_RUN_REASON)
        return 2

    try:
        # Gate: separate explicit operator GO required for execution, checked
        # BEFORE any preregistration contract loading or sealed data access.
        try:
            assert_execution_go_present()
        except HoldoutPreregistrationError as exc:
            print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
            print(f"REASON={exc}")
            print("HOLDOUT_RUN_COUNT=0")
            _write_blocked_manifest(output_dir, reason=str(exc))
            return 2

        try:
            summary = run_holdout_evaluation(
                output_dir=output_dir,
                archive_root=args.archive_root,
            )
        except HoldoutPreregistrationError as exc:
            # Preregistration-level gate block raised inside the runner
            # (digest drift, already-consumed run, dev-PASS binding
            # mismatch, etc.) — all of these fire BEFORE sealed holdout data
            # is read, so no run is consumed.
            print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
            print(f"REASON={exc}")
            print("HOLDOUT_RUN_COUNT=0")
            _write_blocked_manifest(output_dir, reason=str(exc))
            return 2
        except Exception as exc:  # noqa: BLE001
            # Unexpected failure once panel-open / backtest execution has
            # started: this consumes the single authorized holdout run (no
            # rerun) and is recorded as a technical
            # ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN / INCONCLUSIVE outcome,
            # never silently retried.
            reason = f"UNEXPECTED_FAILURE_AFTER_DATA_ACCESS:{type(exc).__name__}"
            print("RESULT_CLASS=ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN")
            print(f"REASON={reason}")
            print("HOLDOUT_RUN_COUNT=1")
            _write_failure_manifest(output_dir, reason=reason, exc=exc)
            consumed_marker.write_text("ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN\n", encoding="utf-8")
            return 1

        print(f"RESULT_CLASS={summary.get('result_class')}")
        print(f"REASON={summary.get('decision', {}).get('reason')}")
        print(f"HOLDOUT_RUN_COUNT={summary.get('holdout_run_count')}")
        consumed_marker.write_text(f"{summary.get('result_class')}\n", encoding="utf-8")
        return 0
    finally:
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        lock_fh.close()


if __name__ == "__main__":
    raise SystemExit(main())
