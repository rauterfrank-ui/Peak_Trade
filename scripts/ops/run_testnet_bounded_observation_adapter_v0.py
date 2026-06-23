#!/usr/bin/env python3
"""Testnet bounded observation retention adapter v0 (plan-only default, Stage-3 gated execute).

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10.

Non-authorizing ops tooling. Does not clear HOLD, preflight BLOCKED, or GLB blockers.
Does not grant Live/broker/exchange approval. Does not override scheduler, preflight, or operator approval boundaries.
Default mode emits a command plan only; no Testnet runtime subprocess.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    verify_manifest_sha256,
    write_manifest_sha256 as _write_manifest_sha256,
)
from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import (
    DurableCloseoutInvoker,
    add_bounded_adapter_durable_closeout_cli_args,
    invoke_durable_closeout_after_archive,
    maybe_invoke_durable_closeout_after_archive,
    validate_durable_closeout_invoke_cli_args,
)
from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    TestnetCompletionPathMarketInputV0,
    build_testnet_bounded_adapter_completion_path_wiring_section,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
)
from src.ops.bounded_testnet_market_input_admission_wiring_v0 import (
    BoundedTestnetFuturesMarketObservationV0,
    resolve_testnet_completion_path_market_input,
)
from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
    CANONICAL_TESTNET_BASE_URL,
    BoundedTestnetRuntimeClock,
    PublicTestnetTickerFetcher,
    collect_bounded_testnet_runtime_market_observation_v0,
    default_public_testnet_ticker_fetcher,
)
from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    build_wallclock_evidence_from_manifest_fields,
    write_wallclock_evidence,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    emit_universe_selection_closeout_machine_lines,
    maybe_write_missing_truth_after_bounded_closeout,
)

TESTNET_BOUNDED_EVIDENCE_SOURCE = "testnet_bounded_dry_run"

ADAPTER_VERSION = "cli_testnet_evidence_flow_composition_v0"
STAGING_SCRIPT = "scripts/ops/run_testnet_bounded_evidence_staging_v0.sh"
REVIEW_SCRIPT = "scripts/ops/review_testnet_bounded_observation_evidence_v0.py"
PREREQ_SCRIPT = "scripts/ops/check_testnet_prerequisites_readonly.py"
WRAPPER_EVIDENCE_DIR = "wrapper_evidence"
DEFAULT_DURATION_MINUTES = 10
DEFAULT_MAX_STEPS = 120
DEFAULT_STEP_INTERVAL_SECONDS = 0.0
MAX_DURATION_MINUTES = 10
MAX_STEPS_CAP = 600

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "START_TESTNET_NOW",
        "START_SHADOW_NOW",
        "START_SUPERVISOR_NOW",
        "LIVE_ALLOWED",
        "START_RUNTIME_NOW",
        "START_PAPER_NOW",
        "START_LIVE_NOW",
        "BROKER_EXCHANGE_ALLOWED",
        "BLOCKER_CLEARANCE_GRANTED",
        "GLB_014_CLEARED",
        "GLB_015_CLEARED",
        "TESTNET_AUTHORIZED",
    }
)
FORBIDDEN_ENV_TRUTHY = frozenset(
    {
        "PT_LIVE_ENABLED",
        "PT_TESTNET_ENABLED",
        "PT_BROKER_ENABLED",
        "PT_ORDER_SUBMISSION_ENABLED",
        "LIVE_ALLOWED",
        "START_TESTNET_NOW",
        "START_SHADOW_NOW",
        "START_SUPERVISOR_NOW",
    }
)
FORBIDDEN_COMMAND_SUBSTRINGS = (
    "orchestrate_testnet_runs",
    "run_testnet_evidence_flow",
    "run_testnet_session.py",
    "run_shadow_loop",
    "online_readiness_supervisor",
    "run_bounded_pilot_session",
    "bounded_pilot",
    "run_scheduler.py",
)

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_TESTNET_BOUNDED_OBSERVATION_NOW": "true",
}

USAGE_EXIT = 2
VALIDATION_EXIT = 1


@dataclass(frozen=True)
class AdapterPlan:
    adapter_version: str
    mode: str
    staging_root: str
    archive_root: str
    duration_minutes: int
    max_steps: int
    step_interval_seconds: float
    run_id: str
    repo_root: str
    staging_script: str
    staging_mode: str
    commands: dict[str, list[str]]
    retention_steps: list[str]
    expected_artifacts: list[str]
    completion_path_wiring: dict[str, Any]
    forbidden_paths_absent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecuteContext:
    args: argparse.Namespace
    repo_root: Path
    staging_root: Path
    archive_root: Path
    wrapper_evidence: Path
    logs_dir: Path
    plan_dir: Path
    review_dir: Path
    run_id: str
    approval_fields: Mapping[str, str] = field(default_factory=dict)
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None = None


SubprocessRunner = Callable[[Sequence[str], Optional[Path], Optional[Path], Optional[Path]], int]
RepoCleanChecker = Callable[[Path], tuple[bool, str]]
PrerequisiteChecker = Callable[[Path], tuple[bool, str]]
StepSleeper = Callable[[float], None]


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_machine_lines(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def load_approval_record(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"approval record not found: {path}")
    return parse_machine_lines(path.read_text(encoding="utf-8"))


def validate_approval_record(fields: Mapping[str, str]) -> list[str]:
    issues: list[str] = []
    for key, expected in REQUIRED_APPROVAL.items():
        if fields.get(key, "").lower() != expected:
            issues.append(f"approval record missing or invalid: {key}={expected}")
    for key in FORBIDDEN_APPROVAL_TRUE:
        if fields.get(key, "false").lower() == "true":
            issues.append(f"approval record forbids {key}=true")
    if fields.get("NO_AUTOMATIC_24H_72H_RERUN_REQUIRED", "true").lower() != "true":
        issues.append("approval record must keep NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true")
    return issues


def validate_env_guardrails(environ: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    issues: list[str] = []
    for key in FORBIDDEN_ENV_TRUTHY:
        if env.get(key, "").strip().lower() in {"1", "true", "yes", "on"}:
            issues.append(f"environment forbids truthy {key}")
    return issues


def default_repo_clean_checker(repo_root: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return False, f"git status failed: {exc}"
    if proc.returncode != 0:
        return False, "git status returned nonzero"
    if proc.stdout.strip():
        return False, "repository working tree is not clean"
    return True, ""


def default_prerequisite_checker(repo_root: Path) -> tuple[bool, str]:
    script = (repo_root / PREREQ_SCRIPT).resolve()
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--json"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return False, f"prerequisite check failed: {exc}"
    if proc.returncode != 0:
        return False, "prerequisite checker returned nonzero"
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, "prerequisite checker output is not valid JSON"
    if payload.get("status") == "BLOCKED" or payload.get("missing_count", 0) > 0:
        missing = payload.get("missing") or []
        return False, f"testnet prerequisites BLOCKED; missing keys: {', '.join(missing)}"
    return True, ""


def _python_cmd(repo_root: Path, script_rel: str) -> list[str]:
    return [sys.executable, str((repo_root / script_rel).resolve())]


def _staging_cmd(
    repo_root: Path,
    staging_root: Path,
    run_id: str,
    duration_minutes: int,
    max_steps: int,
    step_interval_seconds: float,
) -> list[str]:
    script = (repo_root / STAGING_SCRIPT).resolve()
    return [
        "/bin/bash",
        str(script),
        "--staging-root",
        str(staging_root.resolve()),
        "--run-id",
        run_id,
        "--duration-minutes",
        str(duration_minutes),
        "--max-steps",
        str(max_steps),
        "--step-interval-seconds",
        str(step_interval_seconds),
    ]


def _default_max_steps(duration_minutes: int, max_steps: int | None) -> int:
    if max_steps is not None:
        return max_steps
    return min(DEFAULT_MAX_STEPS, max(1, duration_minutes * 12))


def collect_public_testnet_market_observation_for_execute(
    *,
    run_id: str,
    max_steps: int,
    step_interval_seconds: float,
    fetcher: PublicTestnetTickerFetcher,
    clock: BoundedTestnetRuntimeClock | None = None,
    step_sleep: StepSleeper | None = None,
    testnet_base_url: str = CANONICAL_TESTNET_BASE_URL,
) -> BoundedTestnetFuturesMarketObservationV0 | None:
    """Collect bounded public testnet ticker observations for execute closeout wiring."""
    observation, _failure_class, _failure_detail = (
        collect_bounded_testnet_runtime_market_observation_v0(
            testnet_base_url=testnet_base_url,
            source_run_id=run_id,
            max_steps=max_steps,
            fetcher=fetcher,
            clock=clock,
            step_sleep=step_sleep,
            step_interval_seconds=step_interval_seconds,
        )
    )
    return observation


def _resolve_adapter_completion_path_market_input(
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None,
) -> tuple[TestnetCompletionPathMarketInputV0 | None, tuple[str, ...]]:
    if market_observation is None:
        return None, ()
    admission = resolve_testnet_completion_path_market_input(market_observation)
    if admission is None:
        return None, ()
    return admission.market_input, admission.fail_reasons


def build_plan(
    *,
    mode: str,
    staging_root: Path,
    archive_root: Path,
    repo_root: Path,
    duration_minutes: int,
    max_steps: int,
    step_interval_seconds: float,
    run_id: str,
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None = None,
) -> AdapterPlan:
    review_out = staging_root / "review" / "REVIEW_RESULT.json"
    staging_cmd = _staging_cmd(
        repo_root,
        staging_root,
        run_id,
        duration_minutes,
        max_steps,
        step_interval_seconds,
    )
    review_cmd = _python_cmd(repo_root, REVIEW_SCRIPT) + [
        "--staging-root",
        str(staging_root.resolve()),
        "--out",
        str(review_out.resolve()),
        "--json",
    ]
    archive_dest = archive_root / "runs" / "testnet" / run_id
    market_input, producer_fail_reasons = _resolve_adapter_completion_path_market_input(
        market_observation
    )
    completion_path_wiring = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id=run_id,
        mode=mode,
        market_input=market_input,
        market_input_producer_fail_reasons=producer_fail_reasons,
    )
    retention_steps = [
        f"run bounded staging shell under {staging_root / WRAPPER_EVIDENCE_DIR}",
        (
            "evaluate Master-V2 completion path wiring admission "
            "(fail-closed without real testnet market input)"
        ),
        f"review PASS required at {review_out.parent}",
        f"generate MANIFEST.sha256 under {staging_root}",
        f"copy staging bundle to {archive_dest}",
        f"verify checksums on archive copy at {archive_dest}",
        f"write ARCHIVE_POINTER.md under {staging_root}",
    ]
    expected_artifacts = [
        "wrapper_evidence/TESTNET_BOUNDED_OBSERVATION.md",
        "wrapper_evidence/steps.jsonl",
        "wrapper_evidence/manifest.json",
        "logs/wrapper_stdout.log",
        "logs/wrapper_stderr.log",
        "review/REVIEW_RESULT.json",
        "MANIFEST.sha256",
        "CLOSEOUT.md",
        "POSTRUN_ANALYSIS.md",
        "RUN_METADATA.json",
        WALLCLOCK_EVIDENCE_FILENAME,
    ]
    commands = {
        "bounded_evidence_staging": staging_cmd,
        "review": review_cmd,
        "archive_copy": ["copytree", str(staging_root), str(archive_dest)],
    }
    forbidden_absent = all(
        forbidden not in " ".join(argv).lower()
        for forbidden in FORBIDDEN_COMMAND_SUBSTRINGS
        for argv in commands.values()
    )
    return AdapterPlan(
        adapter_version=ADAPTER_VERSION,
        mode=mode,
        staging_root=str(staging_root.resolve()),
        archive_root=str(archive_root.resolve()),
        duration_minutes=duration_minutes,
        max_steps=max_steps,
        step_interval_seconds=step_interval_seconds,
        run_id=run_id,
        repo_root=str(repo_root.resolve()),
        staging_script=STAGING_SCRIPT,
        staging_mode="bounded-testnet-evidence-staging",
        commands=commands,
        retention_steps=retention_steps,
        expected_artifacts=expected_artifacts,
        completion_path_wiring=completion_path_wiring,
        forbidden_paths_absent=forbidden_absent,
    )


def render_plan(plan: AdapterPlan, as_json: bool) -> str:
    if as_json:
        return json.dumps(plan.to_dict(), indent=2, sort_keys=True)
    lines = [
        f"ADAPTER_VERSION={plan.adapter_version}",
        f"MODE={plan.mode}",
        f"STAGING_SCRIPT={plan.staging_script}",
        f"STAGING_MODE={plan.staging_mode}",
        f"DURATION_MINUTES={plan.duration_minutes}",
        f"MAX_STEPS={plan.max_steps}",
        f"STAGING_ROOT={plan.staging_root}",
        f"ARCHIVE_ROOT={plan.archive_root}",
        f"RUN_ID={plan.run_id}",
        "COMMANDS:",
    ]
    for name, argv in plan.commands.items():
        lines.append(f"  {name}: {' '.join(argv)}")
    lines.append("RETENTION_STEPS:")
    for step in plan.retention_steps:
        lines.append(f"  - {step}")
    return "\n".join(lines)


def validate_execute_preconditions(
    ctx: ExecuteContext,
    *,
    repo_clean_checker: RepoCleanChecker,
    prerequisite_checker: PrerequisiteChecker,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    issues: list[str] = []
    if not ctx.run_id.strip():
        issues.append("execute requires non-empty --run-id")
    if ctx.args.approval_record is None:
        issues.append("execute requires --approval-record")
    else:
        try:
            fields = load_approval_record(ctx.args.approval_record)
        except ValueError as exc:
            issues.append(str(exc))
        else:
            ctx.approval_fields = fields
            issues.extend(validate_approval_record(fields))
    if not ctx.archive_root.is_dir():
        issues.append(f"archive root must exist: {ctx.archive_root}")
    elif not os.access(ctx.archive_root, os.W_OK):
        issues.append(f"archive root is not writable: {ctx.archive_root}")
    staging_str = str(ctx.staging_root)
    if "/tmp/" not in staging_str and not staging_str.startswith("/tmp"):
        issues.append("staging root must be under /tmp")
    if not staging_str.split("/tmp/", 1)[-1].split("/")[0].startswith("peak_trade"):
        issues.append("staging root must use /tmp/peak_trade_* convention")
    archive_resolved = str(ctx.archive_root.resolve())
    if archive_resolved.startswith(("/tmp", "/private/tmp")):
        issues.append("archive root must be outside /tmp")
    issues.extend(validate_env_guardrails(environ))
    ok, reason = prerequisite_checker(ctx.repo_root)
    if not ok:
        issues.append(reason or "testnet prerequisites not satisfied")
    if ctx.args.strict_repo_clean:
        clean, reason = repo_clean_checker(ctx.repo_root)
        if not clean:
            issues.append(reason or "repository is not clean")
    issues.extend(validate_durable_closeout_invoke_cli_args(ctx.args))
    if getattr(ctx.args, "collect_public_testnet_market_observation", False):
        if not ctx.args.execute:
            issues.append(
                "--collect-public-testnet-market-observation requires --execute "
                "(plan/staging-only remain network-disabled)"
            )
        if ctx.args.step_interval_seconds <= 0.0:
            issues.append(
                "--collect-public-testnet-market-observation requires --step-interval-seconds > 0"
            )
    return issues


def _default_subprocess_runner(
    argv: Sequence[str],
    cwd: Path | None,
    stdout_path: Path | None,
    stderr_path: Path | None,
) -> int:
    stdout = stderr = subprocess.DEVNULL
    if stdout_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout = stdout_path.open("w", encoding="utf-8")
    if stderr_path is not None:
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stderr = stderr_path.open("w", encoding="utf-8")
    try:
        proc = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd else None,
            check=False,
            stdout=stdout,
            stderr=stderr,
        )
    finally:
        if stdout not in (None, subprocess.DEVNULL):
            stdout.close()
        if stderr not in (None, subprocess.DEVNULL):
            stderr.close()
    return int(proc.returncode or 0)


def _load_wrapper_manifest(wrapper_evidence: Path) -> dict[str, Any]:
    manifest_path = wrapper_evidence / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"wrapper manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("wrapper manifest must be a JSON object")
    return payload


def _emit_wallclock_evidence_from_wrapper_manifest(
    staging_root: Path,
    wrapper_evidence: Path,
) -> tuple[bool, str, dict[str, Any] | None]:
    try:
        manifest = _load_wrapper_manifest(wrapper_evidence)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return False, f"wrapper manifest load failed: {exc}", None

    required_fields = (
        "utc_started",
        "utc_completed",
        "duration_minutes_requested",
        "start_monotonic_seconds",
        "end_monotonic_seconds",
    )
    missing = [field for field in required_fields if manifest.get(field) in (None, "")]
    if missing:
        return False, f"wrapper manifest missing wallclock fields: {', '.join(missing)}", None

    try:
        duration_minutes = int(manifest["duration_minutes_requested"])
        start_mono = float(manifest["start_monotonic_seconds"])
        end_mono = float(manifest["end_monotonic_seconds"])
    except (TypeError, ValueError) as exc:
        return False, f"wrapper manifest wallclock fields invalid: {exc}", None

    if not math.isfinite(start_mono) or not math.isfinite(end_mono):
        return False, "wrapper manifest monotonic fields must be finite", None

    if end_mono < start_mono:
        return False, "wrapper manifest negative elapsed monotonic duration", None

    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started=str(manifest["utc_started"]),
        utc_completed=str(manifest["utc_completed"]),
        duration_minutes=duration_minutes,
        start_monotonic_seconds=start_mono,
        end_monotonic_seconds=end_mono,
        evidence_source=TESTNET_BOUNDED_EVIDENCE_SOURCE,
        real_sleep_used=float(manifest.get("step_interval_seconds") or 0.0) > 0.0,
    )
    evidence_path = staging_root / WALLCLOCK_EVIDENCE_FILENAME
    try:
        write_wallclock_evidence(evidence_path, evidence)
    except OSError as exc:
        return False, f"wallclock evidence write failed: {exc}", None

    if not evidence.get("duration_evidence_valid"):
        reasons = evidence.get("wallclock_fail_reasons", [])
        return False, f"wallclock evidence invalid: {'; '.join(reasons)}", evidence
    return True, "", evidence


def _write_closeout_artifacts(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    archive_dest: Path,
    review_payload: Mapping[str, Any],
    *,
    wallclock_evidence: Mapping[str, Any] | None = None,
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_metadata: dict[str, Any] = {
        "run_id": ctx.run_id,
        "adapter_version": plan.adapter_version,
        "staging_root": str(ctx.staging_root),
        "archive_path": str(archive_dest),
        "duration_minutes": plan.duration_minutes,
        "max_steps": plan.max_steps,
        "review_verdict": review_payload.get("verdict"),
        "utc": now,
    }
    market_input, _producer_fail_reasons = _resolve_adapter_completion_path_market_input(
        market_observation
    )
    wiring_admission = evaluate_bounded_master_v2_testnet_completion_path_wiring(market_input)
    run_metadata["completion_path_wiring"] = wiring_admission.to_machine_lines()
    run_metadata["market_input_bound"] = market_input is not None
    if wallclock_evidence is not None:
        run_metadata["wallclock_evidence_filename"] = WALLCLOCK_EVIDENCE_FILENAME
        run_metadata["wallclock_duration_proven"] = wallclock_evidence.get("duration_proven")
        run_metadata["wallclock_duration_evidence_valid"] = wallclock_evidence.get(
            "duration_evidence_valid"
        )
    (ctx.staging_root / "RUN_METADATA.json").write_text(
        json.dumps(run_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    closeout_lines = [
        "# Testnet Bounded Observation Adapter Closeout",
        "",
        f"RUN_ID={ctx.run_id}",
        f"REVIEW_VERDICT={review_payload.get('verdict')}",
        "EXECUTION_PERFORMED=true",
        "TESTNET_AUTHORIZED=false",
        "START_TESTNET_NOW=false",
        "LIVE_ALLOWED=false",
        "NOTION_WRITES=false",
        "PRIMARY_EVIDENCE_TIER=achieved",
    ]
    for key, value in wiring_admission.to_machine_lines().items():
        closeout_lines.append(f"{key}={value}")
    if wallclock_evidence is not None:
        closeout_lines.append(f"WALLCLOCK_EVIDENCE_FILENAME={WALLCLOCK_EVIDENCE_FILENAME}")
        closeout_lines.append(
            f"WALLCLOCK_DURATION_PROVEN={wallclock_evidence.get('duration_proven', False)}"
        )
    (ctx.staging_root / "CLOSEOUT.md").write_text(
        "\n".join(closeout_lines) + "\n",
        encoding="utf-8",
    )
    (ctx.staging_root / "POSTRUN_ANALYSIS.md").write_text(
        f"# Postrun\n\nReview issues: {review_payload.get('issues', [])}\n",
        encoding="utf-8",
    )


def _copy_staging_to_archive(staging_root: Path, archive_dest: Path) -> None:
    archive_dest.mkdir(parents=True, exist_ok=True)
    for item in staging_root.iterdir():
        dest = archive_dest / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def execute_plan(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    *,
    subprocess_runner: SubprocessRunner,
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
) -> int:
    if ctx.staging_root.exists():
        shutil.rmtree(ctx.staging_root)
    ctx.staging_root.mkdir(parents=True, exist_ok=True)
    ctx.wrapper_evidence.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    ctx.review_dir.mkdir(parents=True, exist_ok=True)

    rc = subprocess_runner(
        plan.commands["bounded_evidence_staging"],
        ctx.repo_root,
        ctx.logs_dir / "wrapper_stdout.log",
        ctx.logs_dir / "wrapper_stderr.log",
    )
    if rc != 0:
        return rc

    review_out = ctx.review_dir / "REVIEW_RESULT.json"
    review_rc = subprocess_runner(plan.commands["review"], ctx.repo_root, review_out, None)
    if review_rc != 0:
        return review_rc
    try:
        review_payload = json.loads(review_out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return VALIDATION_EXIT
    if review_payload.get("verdict") != "PASS":
        return VALIDATION_EXIT

    wallclock_ok, wallclock_reason, wallclock_evidence = (
        _emit_wallclock_evidence_from_wrapper_manifest(
            ctx.staging_root,
            ctx.wrapper_evidence,
        )
    )
    if not wallclock_ok:
        print(wallclock_reason, file=sys.stderr)
        return VALIDATION_EXIT

    archive_dest = ctx.archive_root / "runs" / "testnet" / ctx.run_id
    _write_closeout_artifacts(
        ctx,
        plan,
        archive_dest,
        review_payload,
        wallclock_evidence=wallclock_evidence,
        market_observation=ctx.market_observation,
    )
    (ctx.staging_root / "ARCHIVE_POINTER.md").write_text(
        f"ARCHIVE_PATH={archive_dest}\nARCHIVE_COPY_COMPLETE=true\n",
        encoding="utf-8",
    )
    _write_manifest_sha256(ctx.staging_root)
    _copy_staging_to_archive(ctx.staging_root, archive_dest)
    ok, reason = verify_manifest_sha256(archive_dest)
    if not ok:
        print(reason, file=sys.stderr)
        return VALIDATION_EXIT
    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=ctx.archive_root,
        run_bundle_path=archive_dest,
        source_run_id=ctx.run_id,
        source_stage="testnet",
    )
    emit_universe_selection_closeout_machine_lines(hook_result)
    return maybe_invoke_durable_closeout_after_archive(
        ctx,
        archive_dest,
        durable_closeout_invoker=durable_closeout_invoker,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Testnet bounded observation retention adapter v0. "
            "Default plan-only; execute requires approval and prerequisite keys."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--duration-minutes", type=int, default=DEFAULT_DURATION_MINUTES)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument(
        "--step-interval-seconds", type=float, default=DEFAULT_STEP_INTERVAL_SECONDS
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--approval-record", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--strict-repo-clean", action="store_true", default=True)
    parser.add_argument("--no-strict-repo-clean", action="store_false", dest="strict_repo_clean")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--collect-public-testnet-market-observation",
        action="store_true",
        help=(
            "Execute-only: collect bounded public testnet PF_ETHUSD ticker observations "
            "via canonical runtime producer (default disabled; no automatic retry)."
        ),
    )
    add_bounded_adapter_durable_closeout_cli_args(parser)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    subprocess_runner: SubprocessRunner | None = None,
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
    repo_clean_checker: RepoCleanChecker | None = None,
    prerequisite_checker: PrerequisiteChecker | None = None,
    environ: Mapping[str, str] | None = None,
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None = None,
    public_ticker_fetcher: PublicTestnetTickerFetcher | None = None,
    runtime_market_clock: BoundedTestnetRuntimeClock | None = None,
    step_sleep: StepSleeper | None = None,
) -> int:
    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return USAGE_EXIT

    if args.duration_minutes <= 0 or args.duration_minutes > MAX_DURATION_MINUTES:
        print(f"duration-minutes must be 1..{MAX_DURATION_MINUTES}", file=sys.stderr)
        return USAGE_EXIT
    max_steps = _default_max_steps(args.duration_minutes, args.max_steps)
    if max_steps <= 0 or max_steps > MAX_STEPS_CAP:
        print(f"max-steps must be 1..{MAX_STEPS_CAP}", file=sys.stderr)
        return USAGE_EXIT
    if args.collect_public_testnet_market_observation and not args.execute:
        print(
            "--collect-public-testnet-market-observation requires --execute",
            file=sys.stderr,
        )
        return USAGE_EXIT

    repo_root = (args.repo_root or repo_root_from_script()).resolve()
    staging_root = args.staging_root.expanduser().resolve()
    archive_root = args.archive_root.expanduser().resolve()
    run_id = args.run_id.strip() or (
        f"testnet_bounded_observation_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    mode = "execute" if args.execute else "plan-only"

    if args.execute:
        ctx = ExecuteContext(
            args=args,
            repo_root=repo_root,
            staging_root=staging_root,
            archive_root=archive_root,
            wrapper_evidence=staging_root / WRAPPER_EVIDENCE_DIR,
            logs_dir=staging_root / "logs",
            plan_dir=staging_root / "plan",
            review_dir=staging_root / "review",
            run_id=run_id,
            market_observation=market_observation,
        )
        issues = validate_execute_preconditions(
            ctx,
            repo_clean_checker=repo_clean_checker or default_repo_clean_checker,
            prerequisite_checker=prerequisite_checker or default_prerequisite_checker,
            environ=environ,
        )
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
        resolved_market_observation = market_observation
        if args.collect_public_testnet_market_observation and resolved_market_observation is None:
            fetcher = public_ticker_fetcher or default_public_testnet_ticker_fetcher()
            resolved_market_observation = collect_public_testnet_market_observation_for_execute(
                run_id=run_id,
                max_steps=max_steps,
                step_interval_seconds=args.step_interval_seconds,
                fetcher=fetcher,
                clock=runtime_market_clock,
                step_sleep=step_sleep,
            )
        ctx.market_observation = resolved_market_observation
        plan = build_plan(
            mode=mode,
            staging_root=staging_root,
            archive_root=archive_root,
            repo_root=repo_root,
            duration_minutes=args.duration_minutes,
            max_steps=max_steps,
            step_interval_seconds=args.step_interval_seconds,
            run_id=run_id,
            market_observation=resolved_market_observation,
        )
        return execute_plan(
            ctx,
            plan,
            subprocess_runner=subprocess_runner or _default_subprocess_runner,
            durable_closeout_invoker=durable_closeout_invoker,
        )

    plan = build_plan(
        mode=mode,
        staging_root=staging_root,
        archive_root=archive_root,
        repo_root=repo_root,
        duration_minutes=args.duration_minutes,
        max_steps=max_steps,
        step_interval_seconds=args.step_interval_seconds,
        run_id=run_id,
        market_observation=market_observation,
    )
    print(render_plan(plan, args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
