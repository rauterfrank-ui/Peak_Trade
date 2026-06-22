#!/usr/bin/env python3
"""Shadow bounded observation retention adapter v0 (plan-only default, Stage-3 gated execute).

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10.

Non-authorizing ops tooling. Does not clear HOLD, preflight BLOCKED, or GLB blockers.
Does not grant Live/broker/exchange approval. Does not override scheduler, preflight, or operator approval boundaries.
Default mode emits a command plan only; no wrapper or Shadow runtime subprocess.
"""

from __future__ import annotations

import argparse
import json
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

from scripts.ops import bounded_daemon_paper_shadow_24h_approval_v0 as contract_24h
from scripts.ops.shadow_247_futures_start_wrapper_skeleton_v0 import (
    BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES,
    BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP,
    EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0,
    _read_git_sha_prefix,
)
from scripts.ops.primary_evidence_retention_v0 import (
    verify_manifest_sha256,
    write_manifest_sha256 as _write_manifest_sha256,
)
from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import (
    DurableCloseoutInvoker,
    FINAL_MACHINE_LINES_FILENAME,
    _write_final_machine_lines_artifact,
    add_bounded_adapter_durable_closeout_cli_args,
    maybe_invoke_durable_closeout_after_archive,
    validate_durable_closeout_invoke_cli_args,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    emit_universe_selection_closeout_machine_lines,
    maybe_write_missing_truth_after_bounded_closeout,
)

BOUNDED_ADAPTER_LANE_SHADOW = "shadow_bounded_observation_v0"

ADAPTER_VERSION = "cli_adapter_wrapper_composition_v0"
WRAPPER_SCRIPT = "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
REVIEW_SCRIPT = "scripts/ops/review_shadow_bounded_observation_evidence_v0.py"
OPS_CONFIG = "config/ops/shadow_247_futures_wrapper_skeleton.toml"
JOBS_CONFIG = "config/scheduler/jobs.toml"
WRAPPER_CONFIRM_TOKEN = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
)
WRAPPER_EVIDENCE_DIR = "wrapper_evidence"
COMMAND_TRANSCRIPT_FILENAME = "COMMAND_TRANSCRIPT.log"
PROCESS_INVENTORY_BEFORE_FILENAME = "PROCESS_INVENTORY_BEFORE.txt"
PROCESS_INVENTORY_AFTER_FILENAME = "PROCESS_INVENTORY_AFTER.txt"
DEFAULT_DURATION_MINUTES = 10
DEFAULT_MAX_STEPS = 120
DEFAULT_STEP_INTERVAL_SECONDS = 0.0
MAX_DURATION_MINUTES = 10
MAX_STEPS_CAP = 600
CANDIDATE_24H_MAX_STEPS_CAP = 86400
CANDIDATE_24H_BOUNDED_SHADOW_CONFIRM_TOKEN_V0 = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_CANDIDATE_24H_BOUNDED_SHADOW_TIER_V0"
)

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "START_SHADOW_NOW",
        "START_TESTNET_NOW",
        "START_SUPERVISOR_NOW",
        "LIVE_ALLOWED",
        "START_RUNTIME_NOW",
        "START_PAPER_NOW",
        "START_LIVE_NOW",
        "BROKER_EXCHANGE_ALLOWED",
        "BLOCKER_CLEARANCE_GRANTED",
        "GLB_014_CLEARED",
        "GLB_015_CLEARED",
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
    "run_shadow_loop",
    "online_readiness_supervisor",
    "run_bounded_pilot_session",
    "testnet",
    "bounded_pilot",
    "run_scheduler.py",
)

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW": "true",
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
    wrapper_script: str
    wrapper_mode: str
    commands: dict[str, list[str]]
    retention_steps: list[str]
    expected_artifacts: list[str]
    contract_profile: str = ""
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


SubprocessRunner = Callable[[Sequence[str], Optional[Path], Optional[Path], Optional[Path]], int]
RepoCleanChecker = Callable[[Path], tuple[bool, str]]


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_machine_lines(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("```"):
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


def normalize_profile(profile: str | None) -> str:
    return (profile or "").strip()


def validate_profile_name(profile: str) -> list[str]:
    if profile and profile != contract_24h.CONTRACT_PROFILE:
        return [f"unknown profile: {profile!r}"]
    return []


def validate_approval_record(
    fields: Mapping[str, str],
    *,
    profile: str = "",
    approved_run_id: str = "",
) -> list[str]:
    issues: list[str] = []
    if profile == contract_24h.CONTRACT_PROFILE:
        issues.extend(
            contract_24h.validate_approval_record(fields, approved_run_id=approved_run_id)
        )
        for key in FORBIDDEN_APPROVAL_TRUE:
            if fields.get(key, "false").lower() == "true":
                issues.append(f"approval record forbids {key}=true")
        return issues
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
    output = proc.stdout.strip()
    if output:
        return False, "repository working tree is not clean"
    return True, ""


def _python_cmd(repo_root: Path, script_rel: str) -> list[str]:
    script = (repo_root / script_rel).resolve()
    return [sys.executable, str(script)]


def _default_max_steps(duration_minutes: int, max_steps: int | None) -> int:
    if max_steps is not None:
        return max_steps
    return min(DEFAULT_MAX_STEPS, max(1, duration_minutes * 12))


def extended_tier_active(duration_minutes: int) -> bool:
    return duration_minutes > MAX_DURATION_MINUTES


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
    contract_profile: str = "",
    extended_tier: bool = False,
) -> AdapterPlan:
    wrapper_evidence = staging_root / WRAPPER_EVIDENCE_DIR
    review_out = staging_root / "review" / "REVIEW_RESULT.json"

    wrapper_cmd = _python_cmd(repo_root, WRAPPER_SCRIPT) + [
        "--bounded-shadow-dry-run",
        "--evidence-root",
        str(wrapper_evidence.resolve()),
        "--duration-minutes",
        str(duration_minutes),
        "--max-steps",
        str(max_steps),
        "--step-interval-seconds",
        str(step_interval_seconds),
        "--confirm-token",
        WRAPPER_CONFIRM_TOKEN,
        "--config",
        OPS_CONFIG,
        "--jobs-config",
        JOBS_CONFIG,
    ]
    if contract_profile == contract_24h.CONTRACT_PROFILE:
        wrapper_cmd.extend(
            [
                "--candidate-24h-bounded-shadow-validation",
                "--candidate-24h-confirm-token",
                CANDIDATE_24H_BOUNDED_SHADOW_CONFIRM_TOKEN_V0,
            ]
        )
    elif extended_tier:
        wrapper_cmd.extend(
            [
                "--extended-bounded-shadow-validation",
                "--extended-confirm-token",
                EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0,
            ]
        )
    review_cmd = _python_cmd(repo_root, REVIEW_SCRIPT) + [
        "--staging-root",
        str(staging_root.resolve()),
        "--out",
        str(review_out.resolve()),
        "--json",
    ]

    archive_dest = archive_root / "runs" / "shadow" / run_id
    retention_steps = [
        f"run wrapper bounded dry-run under {wrapper_evidence}",
        f"review PASS required at {review_out.parent}",
        f"write {COMMAND_TRANSCRIPT_FILENAME} under {staging_root}",
        f"write {PROCESS_INVENTORY_BEFORE_FILENAME} and {PROCESS_INVENTORY_AFTER_FILENAME} under {staging_root}",
        f"generate MANIFEST.sha256 under {staging_root}",
        f"copy staging bundle to {archive_dest}",
        f"verify checksums on archive copy at {archive_dest}",
        f"write ARCHIVE_POINTER.md under {staging_root}",
    ]
    expected_artifacts = [
        "wrapper_evidence/SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md",
        "wrapper_evidence/steps.jsonl",
        "wrapper_evidence/manifest.json",
        "logs/wrapper_stdout.log",
        "logs/wrapper_stderr.log",
        "review/REVIEW_RESULT.json",
        COMMAND_TRANSCRIPT_FILENAME,
        PROCESS_INVENTORY_BEFORE_FILENAME,
        PROCESS_INVENTORY_AFTER_FILENAME,
        "MANIFEST.sha256",
        "CLOSEOUT.md",
        "POSTRUN_ANALYSIS.md",
        "RUN_METADATA.json",
        FINAL_MACHINE_LINES_FILENAME,
    ]

    commands = {
        "wrapper_bounded_dry_run": wrapper_cmd,
        "review": review_cmd,
        "archive_copy": [
            "copytree",
            str(staging_root),
            str(archive_dest),
        ],
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
        wrapper_script=WRAPPER_SCRIPT,
        wrapper_mode="bounded-shadow-dry-run",
        commands=commands,
        retention_steps=retention_steps,
        expected_artifacts=expected_artifacts,
        contract_profile=contract_profile,
        forbidden_paths_absent=forbidden_absent,
    )


def render_plan(plan: AdapterPlan, as_json: bool) -> str:
    if as_json:
        return json.dumps(plan.to_dict(), indent=2, sort_keys=True)
    lines = [
        f"ADAPTER_VERSION={plan.adapter_version}",
        f"MODE={plan.mode}",
        f"WRAPPER_SCRIPT={plan.wrapper_script}",
        f"WRAPPER_MODE={plan.wrapper_mode}",
        f"DURATION_MINUTES={plan.duration_minutes}",
        f"MAX_STEPS={plan.max_steps}",
        f"STEP_INTERVAL_SECONDS={plan.step_interval_seconds}",
        f"STAGING_ROOT={plan.staging_root}",
        f"ARCHIVE_ROOT={plan.archive_root}",
        f"RUN_ID={plan.run_id}",
    ]
    if plan.contract_profile:
        lines.append(f"CONTRACT_PROFILE={plan.contract_profile}")
    lines.append("COMMANDS:")
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
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    issues: list[str] = []
    if ctx.args.approval_record is None:
        issues.append("execute requires --approval-record")
    else:
        try:
            fields = load_approval_record(ctx.args.approval_record)
        except ValueError as exc:
            issues.append(str(exc))
        else:
            ctx.approval_fields = fields
            profile = normalize_profile(getattr(ctx.args, "profile", ""))
            issues.extend(
                validate_approval_record(
                    fields,
                    profile=profile,
                    approved_run_id=ctx.run_id,
                )
            )
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
    if ctx.args.strict_repo_clean:
        clean, reason = repo_clean_checker(ctx.repo_root)
        if not clean:
            issues.append(reason or "repository is not clean")
    issues.extend(validate_durable_closeout_invoke_cli_args(ctx.args))
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


def _sanitize_command_for_transcript(argv: Sequence[str]) -> str:
    joined = " ".join(argv)
    lowered = joined.lower()
    for forbidden in ("api_key", "apikey", "secret", "password", "bearer ", "token="):
        if forbidden in lowered:
            return "[REDACTED_BOUNDED_SHADOW_COMMAND]"
    return joined


def _write_process_inventory_snapshot(
    staging_root: Path,
    *,
    phase: str,
    run_id: str,
) -> None:
    filename = (
        PROCESS_INVENTORY_BEFORE_FILENAME if phase == "before" else PROCESS_INVENTORY_AFTER_FILENAME
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header_lines = [
        f"CAPTURE_UTC={now}",
        f"CAPTURE_PHASE={phase}",
        f"RUN_ID={run_id}",
        f"STAGING_ROOT={staging_root.resolve()}",
        "BOUNDED_SHADOW_ADAPTER_EXECUTE=true",
        "",
    ]
    try:
        proc = subprocess.run(
            ["ps", "aux"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        body = proc.stdout or proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        body = f"PROCESS_INVENTORY_CAPTURE_ERROR={exc}\n"
    (staging_root / filename).write_text("".join(header_lines) + body, encoding="utf-8")


def _write_command_transcript(
    staging_root: Path,
    *,
    plan: AdapterPlan,
    run_id: str,
    archive_root: Path,
    wrapper_rc: int,
    review_rc: int | None,
    review_verdict: str | None,
    started_utc: str,
    ended_utc: str,
) -> None:
    lines = [
        f"=== SHADOW BOUNDED DRY-RUN START UTC={started_utc} ===",
        f"RUN_ID={run_id}",
        f"STAGING_ROOT={staging_root.resolve()}",
        f"ARCHIVE_ROOT={archive_root.resolve()}",
        f"ADAPTER_VERSION={plan.adapter_version}",
        "WRAPPER_MODE=bounded-shadow-dry-run",
        f"DURATION_MINUTES={plan.duration_minutes}",
        f"MAX_STEPS={plan.max_steps}",
        f"STEP_INTERVAL_SECONDS={plan.step_interval_seconds}",
        f"WRAPPER_COMMAND={_sanitize_command_for_transcript(plan.commands['wrapper_bounded_dry_run'])}",
        f"REVIEW_COMMAND={_sanitize_command_for_transcript(plan.commands['review'])}",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "SHADOW_RUNTIME_APPROVAL_GRANTED=false",
        "TESTNET_STARTED=false",
        "LIVE_ALLOWED=false",
        "",
        f"=== WRAPPER_RC={wrapper_rc} ===",
    ]
    if review_rc is not None:
        lines.append(f"=== REVIEW_RC={review_rc} REVIEW_VERDICT={review_verdict or 'UNKNOWN'} ===")
    lines.extend(
        [
            "",
            f"=== SHADOW BOUNDED DRY-RUN END UTC={ended_utc} ===",
        ]
    )
    (staging_root / COMMAND_TRANSCRIPT_FILENAME).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _write_closeout_artifacts(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    archive_dest: Path,
    review_payload: Mapping[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    repo_head_sha_prefix = _read_git_sha_prefix(Path(plan.repo_root))
    run_metadata = {
        "run_id": ctx.run_id,
        "adapter_version": plan.adapter_version,
        "staging_root": str(ctx.staging_root),
        "archive_path": str(archive_dest),
        "duration_minutes": plan.duration_minutes,
        "max_steps": plan.max_steps,
        "review_verdict": review_payload.get("verdict"),
        "repo_head_sha_prefix": repo_head_sha_prefix,
        "utc": now,
    }
    (ctx.staging_root / "RUN_METADATA.json").write_text(
        json.dumps(run_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    closeout_lines = [
        "# Shadow Bounded Observation Adapter Closeout",
        "",
        f"RUN_ID={ctx.run_id}",
        f"STAGING_PATH={ctx.staging_root}",
        f"ARCHIVE_PATH={archive_dest}",
        f"REVIEW_VERDICT={review_payload.get('verdict')}",
        "EXECUTION_PERFORMED=true",
        "SHADOW_RUNTIME_APPROVAL_GRANTED=false",
        "TESTNET_STARTED=false",
        "LIVE_ALLOWED=false",
        "PREFLIGHT_BLOCKED=true",
        "NOTION_WRITES=false",
        "PRIMARY_EVIDENCE_TIER=achieved",
        "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true",
    ]
    (ctx.staging_root / "CLOSEOUT.md").write_text(
        "\n".join(closeout_lines) + "\n", encoding="utf-8"
    )
    postrun_lines = [
        "# Shadow Bounded Observation Postrun Analysis",
        "",
        f"Generated UTC: {now}",
        f"Review issues: {review_payload.get('issues', [])}",
        "Non-authorizing adapter execute; no gate clearance claimed.",
    ]
    (ctx.staging_root / "POSTRUN_ANALYSIS.md").write_text(
        "\n".join(postrun_lines) + "\n",
        encoding="utf-8",
    )
    _write_final_machine_lines_artifact(
        ctx.staging_root,
        run_id=ctx.run_id,
        adapter_lane=BOUNDED_ADAPTER_LANE_SHADOW,
        execution_performed=True,
        review_verdict=str(review_payload.get("verdict") or "UNKNOWN"),
        closeout_succeeded=True,
        repo_head_sha_prefix=repo_head_sha_prefix,
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
    ctx.plan_dir.mkdir(parents=True, exist_ok=True)
    ctx.review_dir.mkdir(parents=True, exist_ok=True)

    started_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_process_inventory_snapshot(ctx.staging_root, phase="before", run_id=ctx.run_id)

    stdout_log = ctx.logs_dir / "wrapper_stdout.log"
    stderr_log = ctx.logs_dir / "wrapper_stderr.log"
    rc = subprocess_runner(
        plan.commands["wrapper_bounded_dry_run"],
        ctx.repo_root,
        stdout_log,
        stderr_log,
    )
    if rc != 0:
        ended_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_command_transcript(
            ctx.staging_root,
            plan=plan,
            run_id=ctx.run_id,
            archive_root=ctx.archive_root,
            wrapper_rc=rc,
            review_rc=None,
            review_verdict=None,
            started_utc=started_utc,
            ended_utc=ended_utc,
        )
        return rc

    review_out = ctx.review_dir / "REVIEW_RESULT.json"
    review_rc = subprocess_runner(plan.commands["review"], ctx.repo_root, review_out, None)
    review_payload: dict[str, Any] = {}
    if review_rc == 0:
        try:
            review_payload = json.loads(review_out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            review_payload = {}
    ended_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_command_transcript(
        ctx.staging_root,
        plan=plan,
        run_id=ctx.run_id,
        archive_root=ctx.archive_root,
        wrapper_rc=rc,
        review_rc=review_rc,
        review_verdict=str(review_payload.get("verdict") or "UNKNOWN"),
        started_utc=started_utc,
        ended_utc=ended_utc,
    )
    if review_rc != 0:
        return review_rc
    if review_payload.get("verdict") != "PASS":
        return VALIDATION_EXIT

    archive_dest = ctx.archive_root / "runs" / "shadow" / ctx.run_id
    _write_closeout_artifacts(ctx, plan, archive_dest, review_payload)
    _write_process_inventory_snapshot(ctx.staging_root, phase="after", run_id=ctx.run_id)

    pointer_text = (
        "\n".join(
            [
                f"STAGING_PATH={ctx.staging_root}",
                f"ARCHIVE_PATH={archive_dest}",
                f"COPY_UTC={datetime.now(timezone.utc).isoformat()}",
                "ARCHIVE_COPY_COMPLETE=true",
                "MANIFEST_VERIFY_RC=0",
            ]
        )
        + "\n"
    )
    (ctx.staging_root / "ARCHIVE_POINTER.md").write_text(pointer_text, encoding="utf-8")

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
        source_stage="shadow",
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
            "Shadow bounded observation retention adapter v0. "
            "Default plan-only mode emits commands without executing wrapper runtime."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan-only",
        action="store_true",
        help="Emit plan only (default when --execute is omitted).",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Execute bounded Shadow dry-run retention chain (requires --approval-record).",
    )
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--duration-minutes", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument(
        "--step-interval-seconds",
        type=float,
        default=DEFAULT_STEP_INTERVAL_SECONDS,
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--approval-record", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument(
        "--profile",
        type=str,
        default="",
        help=(
            "Optional approval contract profile. "
            f"Supported: {contract_24h.CONTRACT_PROFILE!r} (default: 10min bounded shadow)."
        ),
    )
    parser.add_argument(
        "--strict-repo-clean",
        action="store_true",
        default=True,
        help="Require clean git working tree before execute (default: true).",
    )
    parser.add_argument(
        "--no-strict-repo-clean",
        action="store_false",
        dest="strict_repo_clean",
        help="Do not require clean git working tree before execute.",
    )
    parser.add_argument("--json", action="store_true", help="Emit plan as JSON.")
    add_bounded_adapter_durable_closeout_cli_args(parser)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    subprocess_runner: SubprocessRunner | None = None,
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
    repo_clean_checker: RepoCleanChecker | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return USAGE_EXIT

    profile = normalize_profile(args.profile)
    profile_issues = validate_profile_name(profile)
    if profile_issues:
        for issue in profile_issues:
            print(issue, file=sys.stderr)
        return USAGE_EXIT

    if profile == contract_24h.CONTRACT_PROFILE:
        if not args.run_id.strip():
            print("--run-id is required for 24h profile", file=sys.stderr)
            return USAGE_EXIT
        if args.duration_minutes is None:
            args.duration_minutes = contract_24h.DAEMON_PAPER_SHADOW_24H_DURATION_MINUTES
        duration_issues = contract_24h.validate_shadow_duration_minutes(args.duration_minutes)
        if duration_issues:
            for issue in duration_issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
        max_steps_cap = CANDIDATE_24H_MAX_STEPS_CAP
    else:
        if args.duration_minutes is None:
            args.duration_minutes = DEFAULT_DURATION_MINUTES
        if args.duration_minutes <= 0:
            print("duration-minutes must be > 0", file=sys.stderr)
            return USAGE_EXIT
        if args.duration_minutes > BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES:
            print(
                "duration-minutes must be between 1 and "
                f"{BOUNDED_SHADOW_EXTENDED_DURATION_CAP_MINUTES} inclusive",
                file=sys.stderr,
            )
            return USAGE_EXIT
        max_steps_cap = (
            BOUNDED_SHADOW_EXTENDED_MAX_STEPS_CAP
            if extended_tier_active(args.duration_minutes)
            else MAX_STEPS_CAP
        )

    if args.duration_minutes <= 0:
        print("duration-minutes must be > 0", file=sys.stderr)
        return USAGE_EXIT

    extended_tier = profile != contract_24h.CONTRACT_PROFILE and extended_tier_active(
        args.duration_minutes
    )

    max_steps = _default_max_steps(args.duration_minutes, args.max_steps)
    if profile == contract_24h.CONTRACT_PROFILE and args.max_steps is None:
        max_steps = min(CANDIDATE_24H_MAX_STEPS_CAP, max(1, args.duration_minutes * 12))
    if max_steps <= 0 or max_steps > max_steps_cap:
        print(f"max-steps must be between 1 and {max_steps_cap} inclusive", file=sys.stderr)
        return USAGE_EXIT

    if args.step_interval_seconds < 0:
        print("step-interval-seconds must be >= 0", file=sys.stderr)
        return USAGE_EXIT

    repo_root = (args.repo_root or repo_root_from_script()).resolve()
    staging_root = args.staging_root.expanduser().resolve()
    archive_root = args.archive_root.expanduser().resolve()
    run_id = (
        args.run_id.strip()
        or f"shadow_bounded_dryrun_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    mode = "execute" if args.execute else "plan-only"
    plan = build_plan(
        mode=mode,
        staging_root=staging_root,
        archive_root=archive_root,
        repo_root=repo_root,
        duration_minutes=args.duration_minutes,
        max_steps=max_steps,
        step_interval_seconds=args.step_interval_seconds,
        run_id=run_id,
        contract_profile=profile,
        extended_tier=extended_tier,
    )

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
        )
        issues = validate_execute_preconditions(
            ctx,
            repo_clean_checker=repo_clean_checker or default_repo_clean_checker,
            environ=environ,
        )
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
        runner = subprocess_runner or _default_subprocess_runner
        return execute_plan(
            ctx,
            plan,
            subprocess_runner=runner,
            durable_closeout_invoker=durable_closeout_invoker,
        )

    print(render_plan(plan, args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
