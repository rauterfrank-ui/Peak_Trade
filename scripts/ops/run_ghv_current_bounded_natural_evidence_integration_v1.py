#!/usr/bin/env python3
"""WP: GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_INTEGRATION_V1.

Orchestrates bounded CURRENT Natural Evidence observation (optional, Owner-GO gated)
and offline GHV forensic analysis on canonical evidence. GHV is reference-only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EVIDENCE_FAMILY = "evidence/ops/ghv_current_bounded_natural_evidence_integration_v1"
BOUNDED_LAUNCHER = (
    REPO_ROOT
    / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)
PARENT_OUTER_WATCHDOG_MARGIN_SECONDS = 60.0


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_origin_main_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "origin/main"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _invoke_bounded_current_run_v1(
    *,
    evidence_root: Path,
    lane_state_root: Path,
    productivity_root: Path,
    max_cycles: int,
    max_run_duration_seconds: float,
) -> dict[str, object]:
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_bounded_natural_evidence_forensic_adapter_v1 import (
        build_bounded_natural_evidence_launcher_argv_v1,
    )
    from scripts.ops.run_current_productive_ghv_input_readiness_and_convergence_v1 import (
        compute_bounded_child_outer_watchdog_seconds_v1,
    )

    cmd = build_bounded_natural_evidence_launcher_argv_v1(
        repo_root=REPO_ROOT,
        launcher_script=BOUNDED_LAUNCHER,
        evidence_root=evidence_root,
        lane_state_root=lane_state_root,
        productivity_root=productivity_root,
        max_cycles=max_cycles,
        max_run_duration_seconds=max_run_duration_seconds,
        enable_ghv_forensic_capture=True,
    )
    outer_timeout = compute_bounded_child_outer_watchdog_seconds_v1(
        inner_max_run_duration_seconds=max_run_duration_seconds,
        margin_seconds=PARENT_OUTER_WATCHDOG_MARGIN_SECONDS,
    )
    t0 = time.monotonic()
    runtime_started = True
    runtime_completed = False
    child_return_code: int | None = None
    parent_timeout = False
    stdout = ""
    stderr = ""
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=outer_timeout,
        )
        child_return_code = int(proc.returncode)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        runtime_completed = True
    except subprocess.TimeoutExpired as exc:
        parent_timeout = True
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        child_proc = getattr(exc, "process", None)
        if child_proc is not None:
            try:
                child_proc.kill()
                child_proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired, OSError):
                pass

    (evidence_root / "bounded_current_run_stdout_v1.txt").write_text(stdout, encoding="utf-8")
    (evidence_root / "bounded_current_run_stderr_v1.txt").write_text(stderr, encoding="utf-8")
    return {
        "RUNTIME_STARTED": runtime_started,
        "RUNTIME_COMPLETED": runtime_completed and not parent_timeout,
        "CHILD_RETURN_CODE": child_return_code,
        "PARENT_TIMEOUT": parent_timeout,
        "DURATION_SECONDS": round(time.monotonic() - t0, 3),
        "LAUNCHER_ARGV": cmd,
    }


def _main() -> int:
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_bounded_natural_evidence_forensic_adapter_v1 import (
        BOUNDED_DEFAULT_MAX_CYCLES,
        BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS,
        COMBINED_REPORT_FILENAME,
        WORK_PACKAGE_ID,
        build_combined_bounded_natural_evidence_report_v1,
        load_current_pre_external_report_v1,
        materialize_ghv_forensic_artifacts_v1,
        persist_combined_report_v1,
    )

    parser = argparse.ArgumentParser(
        description="GHV + bounded CURRENT Natural Evidence integration WP"
    )
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument(
        "--execute-bounded-current-run",
        action="store_true",
        help=(
            "Invoke productive bounded observation launcher (requires --productivity-root, "
            "--lane-state-root, and --owner-run-go-acknowledged)"
        ),
    )
    parser.add_argument("--productivity-root", type=Path, default=None)
    parser.add_argument("--lane-state-root", type=Path, default=None)
    parser.add_argument(
        "--owner-run-go-acknowledged",
        action="store_true",
        help="Explicit operator acknowledgment of fresh OWNER_RUN_GO for this session",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=BOUNDED_DEFAULT_MAX_CYCLES,
        help=f"Bounded S6 cycles when executing CURRENT run (default {BOUNDED_DEFAULT_MAX_CYCLES})",
    )
    parser.add_argument(
        "--max-run-duration-seconds",
        type=float,
        default=BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS,
        help=(
            "S6 sequencer duration cap when executing CURRENT run "
            f"(default {BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS})"
        ),
    )
    parser.add_argument(
        "--skip-ghv-continuation-harness",
        action="store_true",
        help="Materialize flight-record GHV artifacts only (no offline continuation replay)",
    )
    args = parser.parse_args()

    evidence_root = args.evidence_root
    if evidence_root is None:
        evidence_root = REPO_ROOT / EVIDENCE_FAMILY / _utc_stamp()
    evidence_root = Path(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    runtime_meta: dict[str, object] = {
        "RUNTIME_STARTED": False,
        "RUNTIME_COMPLETED": False,
    }

    if args.execute_bounded_current_run:
        if not args.owner_run_go_acknowledged:
            out = {
                "status": "FAIL",
                "blocker": "OWNER_RUN_GO_ACKNOWLEDGMENT_REQUIRED",
                "work_package": WORK_PACKAGE_ID,
            }
            print(json.dumps(out, sort_keys=True))
            return 2
        if args.productivity_root is None or args.lane_state_root is None:
            out = {
                "status": "FAIL",
                "blocker": "PRODUCTIVITY_AND_LANE_STATE_ROOT_REQUIRED",
                "work_package": WORK_PACKAGE_ID,
            }
            print(json.dumps(out, sort_keys=True))
            return 2
        runtime_meta = _invoke_bounded_current_run_v1(
            evidence_root=evidence_root,
            lane_state_root=Path(args.lane_state_root),
            productivity_root=Path(args.productivity_root),
            max_cycles=int(args.max_cycles),
            max_run_duration_seconds=float(args.max_run_duration_seconds),
        )
        if not (evidence_root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").is_file():
            out = {
                "status": "FAIL",
                "blocker": "MISSING_PRE_EXTERNAL_CONVERGENCE_REPORT_AFTER_RUN",
                "work_package": WORK_PACKAGE_ID,
                **runtime_meta,
            }
            print(json.dumps(out, sort_keys=True))
            return 2

    try:
        current_report = load_current_pre_external_report_v1(evidence_root)
    except FileNotFoundError:
        out = {
            "status": "FAIL",
            "blocker": "MISSING_CANONICAL_CURRENT_EVIDENCE",
            "work_package": WORK_PACKAGE_ID,
            "evidence_root": str(evidence_root),
            "hint": "Pass --evidence-root with PRE_EXTERNAL_CONVERGENCE_REPORT.json or execute run",
        }
        print(json.dumps(out, sort_keys=True))
        return 2

    ghv = materialize_ghv_forensic_artifacts_v1(
        evidence_root=evidence_root,
        skip_continuation_harness=bool(args.skip_ghv_continuation_harness),
    )
    combined = build_combined_bounded_natural_evidence_report_v1(
        evidence_root=evidence_root,
        repo_root=REPO_ROOT,
        runtime_started=bool(runtime_meta.get("RUNTIME_STARTED")),
        runtime_completed=bool(runtime_meta.get("RUNTIME_COMPLETED")),
        ghv=ghv,
        current_report=current_report,
    )
    combined["INTEGRATION_RUN"] = {
        **runtime_meta,
        "GHV_MATERIALIZATION": {
            "attempted": ghv.attempted,
            "status": ghv.status,
            "blocker": ghv.blocker,
        },
    }
    report_path = persist_combined_report_v1(evidence_root=evidence_root, report=combined)

    summary = {
        "status": "PASS",
        "work_package": WORK_PACKAGE_ID,
        "CURRENT_MAIN_SHA": _git_origin_main_sha(),
        "GHV_INTEGRATION_STATUS": combined.get("GHV_CAUSAL_CHAIN_STATUS"),
        "COMBINED_REPORT": str(report_path.relative_to(REPO_ROOT)),
        "COMBINED_REPORT_FILENAME": COMBINED_REPORT_FILENAME,
        "EVIDENCE_ROOT": str(evidence_root),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
