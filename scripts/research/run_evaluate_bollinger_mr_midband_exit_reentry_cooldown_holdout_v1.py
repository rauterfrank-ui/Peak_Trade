#!/usr/bin/env python3
"""Run the single preregistered, execution-gated Exit V8 HOLDOUT evaluation.

Fail-closed duplicate-run protection BEFORE any sealed holdout data access:
exclusive non-blocking flock on ``<output-dir>/.holdout_run.lock`` plus
``<output-dir>/.holdout_run_consumed`` marker.

Requires:
  PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_EXECUTION_GO=true
  plus bound AUTH_* env fields (HEAD SHA, contract digest, dataset, panel, successor).

This script does not set those values; the operator/environment must.
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

from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (  # noqa: E402
    CONSUMED_MARKER_FILENAME,
    EVIDENCE_REL_PATH,
    LOCK_FILENAME,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.panel_runner_v1 import (  # noqa: E402
    run_holdout_evaluation,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (  # noqa: E402
    HoldoutPreregistrationError,
)

BLOCKED_RESULT_CLASS = "BLOCKED_NO_RERUN"
DUPLICATE_RUN_REASON = "HOLDOUT_DUPLICATE_RUN_BLOCKED"


def _write_blocked_manifest(output_dir: Path, *, reason: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_run_manifest.v1",
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
        "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_run_manifest.v1",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the single preregistered, execution-gated Bollinger/MR midband "
            "reentry-cooldown HOLDOUT evaluation (control vs treatment, one run)."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / EVIDENCE_REL_PATH,
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed FINAL_AUDIT holdout panel archive root override.",
    )
    args = parser.parse_args(argv)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    consumed_marker = output_dir / CONSUMED_MARKER_FILENAME
    lock_path = output_dir / LOCK_FILENAME

    if consumed_marker.is_file():
        print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
        print(f"REASON={DUPLICATE_RUN_REASON}")
        print("HOLDOUT_RUN_COUNT=0")
        _write_blocked_manifest(output_dir, reason=DUPLICATE_RUN_REASON)
        return 2

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
        try:
            summary = run_holdout_evaluation(
                output_dir=output_dir,
                archive_root=args.archive_root,
            )
        except HoldoutPreregistrationError as exc:
            print(f"RESULT_CLASS={BLOCKED_RESULT_CLASS}")
            print(f"REASON={exc}")
            print("HOLDOUT_RUN_COUNT=0")
            _write_blocked_manifest(output_dir, reason=str(exc))
            return 2
        except Exception as exc:  # noqa: BLE001
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
