#!/usr/bin/env python3
"""WP: CURRENT productive GHV input readiness gap matrix + optional bounded convergence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_FIXTURE = (
    REPO_ROOT / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1"
)
EVIDENCE_FAMILY = "evidence/research/current_productive_ghv_input_readiness_and_convergence_v1"

PARENT_OUTER_WATCHDOG_MARGIN_SECONDS = 60.0
BOUNDED_CHILD_MAX_CYCLES = 1
BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS = 120.0
TERMINATION_PARENT_OUTER_WATCHDOG = "PARENT_OUTER_WATCHDOG"
TERMINATION_CHILD_COMPLETED = "CHILD_COMPLETED"


@dataclass(frozen=True)
class BoundedPreExternalChildResultV1:
    executed: bool
    duration_seconds: float
    parent_timeout: bool
    termination_reason: str
    child_return_code: int | None
    pre_external_reached: bool
    natural_enter_observed: bool
    post_count: int
    cycles_completed: int
    stdout: str
    stderr: str


def compute_bounded_child_outer_watchdog_seconds_v1(
    *,
    inner_max_run_duration_seconds: float,
    margin_seconds: float = PARENT_OUTER_WATCHDOG_MARGIN_SECONDS,
) -> float:
    inner = float(inner_max_run_duration_seconds)
    if inner <= 0:
        raise ValueError("INNER_MAX_RUN_DURATION_MUST_BE_POSITIVE")
    margin = float(margin_seconds)
    if margin <= 0:
        raise ValueError("OUTER_WATCHDOG_MARGIN_MUST_BE_POSITIVE")
    return inner + margin


def build_bounded_pre_external_launcher_argv_v1(
    *,
    repo_root: Path,
    launcher: Path,
    run_evidence: Path,
    run_lane: Path,
    run_prod: Path,
    max_cycles: int = BOUNDED_CHILD_MAX_CYCLES,
    max_run_duration_seconds: float = BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS,
) -> list[str]:
    return [
        str(repo_root / "scripts/pt"),
        str(launcher),
        "--evidence-root",
        str(run_evidence),
        "--lane-state-root",
        str(run_lane),
        "--productivity-root",
        str(run_prod),
        "--max-cycles",
        str(int(max_cycles)),
        "--max-run-duration-seconds",
        str(float(max_run_duration_seconds)),
        "--wp-branch-evidence-run",
    ]


def invoke_bounded_pre_external_child_v1(
    *,
    repo_root: Path,
    launcher: Path,
    run_evidence: Path,
    run_lane: Path,
    run_prod: Path,
    max_cycles: int = BOUNDED_CHILD_MAX_CYCLES,
    max_run_duration_seconds: float = BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS,
    margin_seconds: float = PARENT_OUTER_WATCHDOG_MARGIN_SECONDS,
) -> BoundedPreExternalChildResultV1:
    cmd = build_bounded_pre_external_launcher_argv_v1(
        repo_root=repo_root,
        launcher=launcher,
        run_evidence=run_evidence,
        run_lane=run_lane,
        run_prod=run_prod,
        max_cycles=max_cycles,
        max_run_duration_seconds=max_run_duration_seconds,
    )
    outer_timeout = compute_bounded_child_outer_watchdog_seconds_v1(
        inner_max_run_duration_seconds=max_run_duration_seconds,
        margin_seconds=margin_seconds,
    )
    t0 = time.monotonic()
    stdout = ""
    stderr = ""
    child_return_code: int | None = None
    parent_timeout = False
    termination = TERMINATION_CHILD_COMPLETED
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=outer_timeout,
        )
        child_return_code = int(proc.returncode)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        parent_timeout = True
        termination = TERMINATION_PARENT_OUTER_WATCHDOG
        child_return_code = None
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        child_proc = getattr(exc, "process", None)
        if child_proc is not None:
            try:
                child_proc.kill()
                child_proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired, OSError):
                pass

    pre_external_reached = False
    natural_enter_observed = False
    post_count = 0
    cycles_completed = 0
    rep_path = run_evidence / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    if rep_path.is_file():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        pre_external_reached = str(rep.get("PRE_EXTERNAL_REACHED")).lower() == "true"
        post_count = int(rep.get("POST_COUNT") or 0)
        natural_enter_observed = str(rep.get("NATURAL_ENTER_OBSERVED")).lower() == "true"
        summaries = rep.get("S5_CYCLE_SUMMARIES") or []
        cycles_completed = len(summaries)

    return BoundedPreExternalChildResultV1(
        executed=True,
        duration_seconds=round(time.monotonic() - t0, 3),
        parent_timeout=parent_timeout,
        termination_reason=termination,
        child_return_code=child_return_code,
        pre_external_reached=pre_external_reached,
        natural_enter_observed=natural_enter_observed,
        post_count=post_count,
        cycles_completed=cycles_completed,
        stdout=stdout,
        stderr=stderr,
    )


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="CURRENT productive GHV input readiness WP runner")
    parser.add_argument("--golden-vector-root", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--productivity-root", type=Path, default=None)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument(
        "--perform-live-observation",
        action="store_true",
        help="Use productive read-only GET transport (public MD only)",
    )
    parser.add_argument(
        "--bounded-convergence-run",
        action="store_true",
        help="If CURRENT_INPUT_READY, invoke bounded pre-external launcher (max 1 cycle)",
    )
    args = parser.parse_args()

    evidence_root = args.evidence_root
    if evidence_root is None:
        evidence_root = REPO_ROOT / EVIDENCE_FAMILY / _utc_stamp()
    evidence_root.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(
        (args.golden_vector_root / "golden_vector_manifest_v1.json").read_text(encoding="utf-8")
    )

    from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_current_input_observation_adapter_v1 import (
        SOURCE_LIVE_PRODUCTIVE_GET,
        build_fixture_vs_current_gap_matrix_v1,
        gap_matrix_to_json_v1,
        observe_current_productive_ghv_inputs_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_startability_evaluator_v1 import (
        evaluate_current_productive_golden_happy_vector_startability_v1,
        report_to_machine_json_v1,
    )

    observation = None
    offline_gap = build_fixture_vs_current_gap_matrix_v1(manifest=manifest, observation=None)
    (evidence_root / "01_offline_gap_matrix.json").write_text(
        json.dumps(gap_matrix_to_json_v1(offline_gap), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if args.perform_live_observation:
        if args.productivity_root is None:
            out = {"status": "FAIL", "blocker": "PRODUCTIVITY_ROOT_REQUIRED_FOR_LIVE_OBSERVATION"}
            print(json.dumps(out, sort_keys=True))
            return 2
        from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
            FullCoreProductiveReadOnlyGetTransportV1,
        )

        transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=8)
        observation = observe_current_productive_ghv_inputs_v1(
            productivity_root=Path(args.productivity_root),
            evidence_store_root=evidence_root / "g17_checkpoint_store",
            transport=transport,
            source_kind=SOURCE_LIVE_PRODUCTIVE_GET,
            expected_instrument_id=str(manifest.get("INSTRUMENT_ID") or ""),
            expected_native_id=str(manifest.get("NATIVE_ID") or ""),
        )
        (evidence_root / "02_live_gap_matrix.json").write_text(
            json.dumps(gap_matrix_to_json_v1(observation.gap_rows), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "03_live_observation_summary.json").write_text(
            json.dumps(
                {
                    "observation_ok": observation.observation_ok,
                    "current_input_blocker": observation.current_input_blocker,
                    "http_get_count": observation.http_get_count,
                    "source_kind": observation.source_kind,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    live_required = args.perform_live_observation
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO_ROOT,
        golden_vector_root=args.golden_vector_root,
        actual_head_sha=_git_head(),
        live_inputs_required=live_required,
        current_input_observation=observation,
    )
    payload = report_to_machine_json_v1(report)
    (evidence_root / "04_startability_evaluation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bounded: dict[str, object] = {
        "BOUNDED_CURRENT_RUN_EXECUTED": False,
        "BOUNDED_CURRENT_RUN_DURATION": 0.0,
        "BOUNDED_CURRENT_RUN_CYCLES": 0,
        "BOUNDED_CURRENT_RUN_PARENT_TIMEOUT": False,
        "BOUNDED_CURRENT_RUN_TERMINATION_REASON": "",
        "BOUNDED_CHILD_OUTER_WATCHDOG_SECONDS": compute_bounded_child_outer_watchdog_seconds_v1(
            inner_max_run_duration_seconds=BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS,
        ),
        "NATURAL_ENTER_OBSERVED": False,
        "PRE_EXTERNAL_REACHED": False,
        "POST_COUNT": 0,
    }
    if args.bounded_convergence_run and report.current_input_ready and args.productivity_root:
        launcher = (
            REPO_ROOT
            / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
        )
        run_evidence = evidence_root / "bounded_run"
        run_lane = evidence_root / "bounded_lane"
        run_prod = Path(args.productivity_root)
        child = invoke_bounded_pre_external_child_v1(
            repo_root=REPO_ROOT,
            launcher=launcher,
            run_evidence=run_evidence,
            run_lane=run_lane,
            run_prod=run_prod,
        )
        bounded["BOUNDED_CURRENT_RUN_EXECUTED"] = child.executed
        bounded["BOUNDED_CURRENT_RUN_DURATION"] = child.duration_seconds
        bounded["BOUNDED_CURRENT_RUN_PARENT_TIMEOUT"] = child.parent_timeout
        bounded["BOUNDED_CURRENT_RUN_TERMINATION_REASON"] = child.termination_reason
        bounded["BOUNDED_CHILD_RETURN_CODE"] = child.child_return_code
        bounded["PRE_EXTERNAL_REACHED"] = child.pre_external_reached
        bounded["POST_COUNT"] = child.post_count
        bounded["NATURAL_ENTER_OBSERVED"] = child.natural_enter_observed
        bounded["BOUNDED_CURRENT_RUN_CYCLES"] = child.cycles_completed
        (evidence_root / "05_bounded_run_stdout.txt").write_text(child.stdout, encoding="utf-8")
        (evidence_root / "05_bounded_run_stderr.txt").write_text(child.stderr, encoding="utf-8")

    (evidence_root / "06_bounded_run_summary.json").write_text(
        json.dumps(bounded, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "WP_ID": "CURRENT_PRODUCTIVE_GHV_INPUT_READINESS_AND_CONVERGENCE_V1",
        "BASELINE_SHA": _git_head(),
        "EVIDENCE_ROOT": str(evidence_root),
        "CURRENT_INPUT_READY": report.current_input_ready,
        "CURRENT_INPUT_BLOCKER": report.current_input_blocker,
        **bounded,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report.golden_vector_replay_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
