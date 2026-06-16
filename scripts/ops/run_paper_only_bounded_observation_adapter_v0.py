#!/usr/bin/env python3
"""Paper-only bounded observation adapter v0 (plan-only default, Stage-3 gated execute).

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10.

Non-authorizing ops tooling. Does not clear HOLD, preflight BLOCKED, or GLB blockers.
Does not grant Live/broker/exchange approval. Does not override scheduler, preflight, or operator approval boundaries.
Default mode emits a command plan only; no scheduler or paper runtime subprocess.
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
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import bounded_daemon_paper_shadow_24h_approval_v0 as contract_24h
from scripts.ops import gap4_req_a_paper_hold_binding_approval_v0 as contract_gap4
from scripts.ops import paper_l2_120min_hold_binding_approval_v0 as contract_l2_120min
from scripts.ops.durable_closeout_copy_verify_v0 import (
    _dest_has_content,
    _validate_source_dest_distinct,
)
from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    emit_universe_selection_closeout_machine_lines,
    maybe_write_missing_truth_after_bounded_closeout,
)

ADAPTER_VERSION = "cli_adapter_scheduler_composition_v0"
ALLOWED_JOB = "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"
INCLUDE_TAGS = "paper_runtime"
DEFAULT_DURATION_SECONDS = 7200
DEFAULT_POLL_INTERVAL_SECONDS = 30

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "START_SHADOW_NOW",
        "START_TESTNET_NOW",
        "START_SUPERVISOR_NOW",
        "LIVE_ALLOWED",
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
    "shadow_247_futures",
    "run_shadow_loop",
    "online_readiness_supervisor",
    "run_bounded_pilot_session",
    "testnet",
    "bounded_pilot",
)

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW": "true",
    "START_PAPER_NOW": "true",
}

USAGE_EXIT = 2
VALIDATION_EXIT = 1
TIMEOUT_EXIT = 124
START_RETURN_CODE_ARTIFACT = "start_return_code.txt"
FINAL_MACHINE_LINES_FILENAME = "FINAL_MACHINE_LINES.txt"
BOUNDED_ADAPTER_LANE_PAPER = "paper_only_bounded_observation_v0"
DURABLE_CLOSEOUT_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "durable_closeout_copy_verify_v0.py"

DurableCloseoutInvoker = Callable[[Sequence[str]], int]


@dataclass(frozen=True)
class AdapterPlan:
    adapter_version: str
    mode: str
    staging_root: str
    archive_root: str
    duration_seconds: int
    poll_interval_seconds: int
    job_name: str
    include_tags: str
    run_id: str
    repo_root: str
    source_jobs_toml: str
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
    runtime_out: Path
    logs_dir: Path
    plan_dir: Path
    review_dir: Path
    temp_jobs: Path
    run_id: str
    approval_fields: Mapping[str, str] = field(default_factory=dict)


class SubprocessRunner(Protocol):
    def __call__(
        self,
        argv: Sequence[str],
        cwd: Path | None,
        stdout_path: Path | None,
        stderr_path: Path | None,
        *,
        extra_env: Mapping[str, str] | None = None,
    ) -> int: ...


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
    known = {
        contract_24h.CONTRACT_PROFILE,
        contract_gap4.CONTRACT_PROFILE,
        contract_l2_120min.CONTRACT_PROFILE,
    }
    if profile and profile not in known:
        return [f"unknown profile: {profile!r}"]
    return []


def _profiles_with_hold_runtime_env_bridge() -> frozenset[str]:
    return frozenset(
        {
            contract_24h.CONTRACT_PROFILE,
            contract_gap4.CONTRACT_PROFILE,
            contract_l2_120min.CONTRACT_PROFILE,
        }
    )


def resolve_scheduler_hold_runtime_binding_target(
    *,
    profile: str,
    approval_record: Path,
    approval_fields: Mapping[str, str],
    run_id: str,
) -> tuple[Path | None, str, list[str]]:
    """Resolve OUTROOT + RUN_ID for scheduler HOLD env bridge (non-authorizing)."""
    if profile == contract_24h.CONTRACT_PROFILE:
        return approval_record.resolve().parent.parent, run_id, []
    if profile == contract_gap4.CONTRACT_PROFILE:
        outroot, issues = contract_gap4.resolve_hold_binding_outroot(approval_fields)
        expected = approval_fields.get("APPROVED_RUN_ID", "").strip() or run_id
        if outroot is None:
            return None, expected, issues
        if expected != run_id:
            return (
                None,
                expected,
                [f"APPROVED_RUN_ID mismatch: expected {run_id!r}, got {expected!r}"],
            )
        return outroot, expected, []
    if profile == contract_l2_120min.CONTRACT_PROFILE:
        outroot, issues = contract_l2_120min.resolve_hold_binding_outroot(approval_fields)
        expected = approval_fields.get("APPROVED_RUN_ID", "").strip() or run_id
        if outroot is None:
            return None, expected, issues
        if expected != run_id:
            return (
                None,
                expected,
                [f"APPROVED_RUN_ID mismatch: expected {run_id!r}, got {expected!r}"],
            )
        return outroot, expected, []
    return None, run_id, []


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
    if profile == contract_gap4.CONTRACT_PROFILE:
        issues.extend(
            contract_gap4.validate_approval_record(fields, approved_run_id=approved_run_id)
        )
        return issues
    if profile == contract_l2_120min.CONTRACT_PROFILE:
        issues.extend(
            contract_l2_120min.validate_approval_record(fields, approved_run_id=approved_run_id)
        )
        return issues
    for key, expected in REQUIRED_APPROVAL.items():
        if fields.get(key, "").lower() != expected:
            issues.append(f"approval record missing or invalid: {key}={expected}")
    for key in FORBIDDEN_APPROVAL_TRUE:
        if fields.get(key, "false").lower() == "true":
            issues.append(f"approval record forbids {key}=true")
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


def _plan_paths(staging_root: Path, run_id: str) -> dict[str, Path]:
    return {
        "staging_root": staging_root,
        "runtime_out": staging_root / "runtime_out",
        "logs_dir": staging_root / "logs",
        "plan_dir": staging_root / "plan",
        "review_dir": staging_root / "review",
        "temp_jobs": staging_root / "plan" / "temp_jobs.toml",
        "run_id": Path(run_id),
    }


def build_plan(
    *,
    mode: str,
    staging_root: Path,
    archive_root: Path,
    repo_root: Path,
    source_jobs_toml: Path,
    duration_seconds: int,
    poll_interval_seconds: int,
    run_id: str,
    contract_profile: str = "",
) -> AdapterPlan:
    paths = _plan_paths(staging_root, run_id)
    runtime_out = paths["runtime_out"]
    logs_dir = paths["logs_dir"]
    temp_jobs = paths["temp_jobs"]

    make_scheduler = _python_cmd(repo_root, "scripts/ops/make_scheduler_temp_config.py") + [
        "--source",
        str(source_jobs_toml.resolve()),
        "--job",
        ALLOWED_JOB,
        "--outdir",
        str(runtime_out.resolve()),
        "--output",
        str(temp_jobs.resolve()),
        "--force",
    ]
    scheduler_inner = _python_cmd(repo_root, "scripts/run_scheduler.py") + [
        "--config",
        str(temp_jobs.resolve()),
        "--poll-interval",
        str(poll_interval_seconds),
        "--include-tags",
        INCLUDE_TAGS,
        "--no-registry",
        "--no-alerts",
        "--heartbeat-file",
        str((runtime_out / "scheduler_heartbeat_freshness_v0.json").resolve()),
    ]
    run_with_timeout = _python_cmd(repo_root, "scripts/ops/run_with_timeout.py") + [
        "--timeout-seconds",
        str(duration_seconds),
        "--",
        *scheduler_inner,
    ]
    review = _python_cmd(repo_root, "scripts/ops/review_scheduler_paper_runtime_evidence.py") + [
        "--outroot",
        str(runtime_out.resolve()),
        "--logroot",
        str(logs_dir.resolve()),
        "--expected-timeout-seconds",
        str(float(duration_seconds)),
        "--json",
    ]

    archive_dest = archive_root / "runs" / "paper" / run_id
    retention_steps = [
        f"generate MANIFEST.sha256 under {staging_root}",
        f"rsync staging bundle to {archive_dest}",
        f"verify checksums on archive copy at {archive_dest}",
        f"write ARCHIVE_POINTER.md under {staging_root}",
    ]
    expected_artifacts = [
        "runtime_out/account.json",
        "runtime_out/fills.json",
        "runtime_out/evidence_manifest.json",
        "logs/scheduler_stdout.log",
        "logs/scheduler_stderr.log",
        "review/REVIEW_RESULT.json",
        "RUN_METADATA.json",
        "MANIFEST.sha256",
        "CLOSEOUT.md",
        "POSTRUN_ANALYSIS.md",
        FINAL_MACHINE_LINES_FILENAME,
    ]

    commands = {
        "temp_config": make_scheduler,
        "scheduler_bounded": run_with_timeout,
        "review": review,
        "archive_copy": [
            "rsync",
            "-a",
            "--checksum",
            f"{staging_root}/",
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
        duration_seconds=duration_seconds,
        poll_interval_seconds=poll_interval_seconds,
        job_name=ALLOWED_JOB,
        include_tags=INCLUDE_TAGS,
        run_id=run_id,
        repo_root=str(repo_root.resolve()),
        source_jobs_toml=str(source_jobs_toml.resolve()),
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
        f"JOB_NAME={plan.job_name}",
        f"INCLUDE_TAGS={plan.include_tags}",
        f"DURATION_SECONDS={plan.duration_seconds}",
        f"POLL_INTERVAL_SECONDS={plan.poll_interval_seconds}",
        f"STAGING_ROOT={plan.staging_root}",
        f"ARCHIVE_ROOT={plan.archive_root}",
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
            if profile == contract_gap4.CONTRACT_PROFILE:
                outroot, expected_run_id, resolve_issues = (
                    resolve_scheduler_hold_runtime_binding_target(
                        profile=profile,
                        approval_record=ctx.args.approval_record,
                        approval_fields=fields,
                        run_id=ctx.run_id,
                    )
                )
                issues.extend(resolve_issues)
                if outroot is not None:
                    issues.extend(
                        contract_gap4.validate_scheduler_hold_runtime_binding_outroot(
                            outroot,
                            expected_run_id=expected_run_id,
                        )
                    )
            if profile == contract_l2_120min.CONTRACT_PROFILE:
                outroot, expected_run_id, resolve_issues = (
                    resolve_scheduler_hold_runtime_binding_target(
                        profile=profile,
                        approval_record=ctx.args.approval_record,
                        approval_fields=fields,
                        run_id=ctx.run_id,
                    )
                )
                issues.extend(resolve_issues)
                if outroot is not None:
                    issues.extend(
                        contract_l2_120min.validate_scheduler_hold_runtime_binding_outroot(
                            outroot,
                            expected_run_id=expected_run_id,
                        )
                    )
    if not ctx.archive_root.is_dir():
        issues.append(f"archive root must exist: {ctx.archive_root}")
    elif not os.access(ctx.archive_root, os.W_OK):
        issues.append(f"archive root is not writable: {ctx.archive_root}")
    staging_str = str(ctx.staging_root)
    if "/tmp/" not in staging_str and not staging_str.startswith("/tmp"):
        issues.append("staging root must be under /tmp")
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


def validate_durable_closeout_invoke_cli_args(args: argparse.Namespace) -> list[str]:
    """Validate durable closeout invocation flags (default-off; fail-closed when enabled)."""
    issues: list[str] = []
    chain_requested = bool(getattr(args, "run_local_post_closeout_chain_v0", False))
    invoke_requested = bool(getattr(args, "invoke_durable_closeout_v0", False))
    pointer_required = bool(getattr(args, "require_durable_pointer_evidence", False))
    pointer_patterns = resolve_bounded_adapter_durable_pointer_patterns(args)
    if chain_requested and not invoke_requested:
        issues.append("--run-local-post-closeout-chain-v0 requires --invoke-durable-closeout-v0")
    if pointer_required and not invoke_requested:
        issues.append("--require-durable-pointer-evidence requires --invoke-durable-closeout-v0")
    if pointer_patterns and not invoke_requested:
        issues.append("--durable-pointer-pattern requires --invoke-durable-closeout-v0")
    if chain_requested:
        chain_archive = getattr(args, "chain_archive_root", None)
        if chain_archive is None:
            issues.append(
                "--chain-archive-root is required with --run-local-post-closeout-chain-v0"
            )
        else:
            chain_archive_path = Path(chain_archive).expanduser().resolve()
            if is_under_tmp(chain_archive_path):
                issues.append(
                    "chain archive root must be outside /tmp when "
                    "--run-local-post-closeout-chain-v0 is set"
                )
    if not invoke_requested:
        return issues
    dest = getattr(args, "durable_closeout_dest_dir", None)
    if dest is None:
        issues.append("--durable-closeout-dest-dir is required with --invoke-durable-closeout-v0")
    else:
        dest_path = Path(dest).expanduser().resolve()
        if is_under_tmp(dest_path):
            issues.append("durable closeout destination must be outside /tmp")
    return issues


def validate_durable_closeout_invoke_paths(
    source_dir: Path,
    dest_dir: Path,
    *,
    force: bool = False,
) -> tuple[bool, str, str]:
    """Validate adapter closeout paths before helper invoke (reuses helper guards)."""
    ok, msg = _validate_source_dest_distinct(source_dir, dest_dir)
    if not ok:
        return False, msg, "durable_closeout_identical_source_dest"
    if _dest_has_content(dest_dir) and not force:
        return (
            False,
            "destination exists and is non-empty "
            "(use --durable-closeout-force only when source and dest differ, "
            "or copy from a separate snapshot source directory)",
            "durable_closeout_dest_non_empty_without_force",
        )
    return True, "", ""


ARCHIVE_POINTER_FILENAME = "ARCHIVE_POINTER.md"


def resolve_bounded_adapter_durable_pointer_patterns(
    args: argparse.Namespace,
) -> tuple[str, ...]:
    raw = getattr(args, "durable_pointer_pattern", None)
    if not raw:
        return ()
    if isinstance(raw, str):
        return (raw,)
    return tuple(pattern for pattern in raw if pattern)


def ensure_archive_pointer_in_archive_dest(
    staging_root: Path,
    archive_dest: Path,
) -> tuple[bool, str]:
    """Copy existing ARCHIVE_POINTER.md into archive_dest when needed for durable helper source."""
    archive_pointer = archive_dest / ARCHIVE_POINTER_FILENAME
    if archive_pointer.is_file():
        return True, ""
    staging_pointer = staging_root / ARCHIVE_POINTER_FILENAME
    if staging_pointer.is_file():
        shutil.copy2(staging_pointer, archive_pointer)
        return True, ""
    return False, f"{ARCHIVE_POINTER_FILENAME} missing in staging and archive_dest"


def resolve_bounded_adapter_chain_run_id(
    args: argparse.Namespace,
    *,
    adapter_run_id: str,
) -> str | None:
    """Resolve chain run_id: explicit CLI wins; else adapter run_id when chain is requested."""
    explicit = (getattr(args, "chain_run_id", None) or "").strip()
    if explicit:
        return explicit
    if getattr(args, "run_local_post_closeout_chain_v0", False):
        run_id = adapter_run_id.strip()
        if run_id:
            return run_id
    return None


def _default_durable_closeout_invoker(argv: Sequence[str]) -> int:
    proc = subprocess.run(
        list(argv),
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return int(proc.returncode)


def build_durable_closeout_invoke_argv(
    *,
    source_dir: Path,
    dest_dir: Path,
    run_local_post_closeout_chain_v0: bool = False,
    chain_archive_root: Path | None = None,
    chain_run_id: str | None = None,
    require_durable_pointer_evidence: bool = False,
    durable_pointer_patterns: Sequence[str] = (),
    force: bool = False,
) -> list[str]:
    argv = [
        sys.executable,
        str(DURABLE_CLOSEOUT_SCRIPT),
        "--source-dir",
        str(source_dir.resolve()),
        "--dest-dir",
        str(dest_dir.resolve()),
    ]
    if is_under_tmp(source_dir):
        argv.append("--allow-tmp-source")
    if force:
        argv.append("--force")
    if run_local_post_closeout_chain_v0:
        if chain_archive_root is None:
            raise ValueError("chain_archive_root is required when run_local_post_closeout_chain_v0")
        argv.append("--run-local-post-closeout-chain-v0")
        argv.extend(["--chain-archive-root", str(chain_archive_root.resolve())])
        if chain_run_id:
            argv.extend(["--chain-run-id", chain_run_id])
    if require_durable_pointer_evidence:
        argv.append("--require-durable-pointer-evidence")
    for pattern in durable_pointer_patterns:
        argv.extend(["--durable-pointer-pattern", pattern])
    return argv


def invoke_durable_closeout_after_archive(
    *,
    source_dir: Path,
    dest_dir: Path,
    args: argparse.Namespace | None = None,
    adapter_run_id: str = "",
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
) -> int:
    """Invoke canonical durable closeout helper after adapter archive success."""
    chain_requested = bool(args and getattr(args, "run_local_post_closeout_chain_v0", False))
    chain_archive_root: Path | None = None
    if chain_requested and args is not None:
        chain_archive_root = Path(args.chain_archive_root).expanduser().resolve()
    chain_run_id = (
        resolve_bounded_adapter_chain_run_id(args, adapter_run_id=adapter_run_id)
        if args is not None
        else None
    )
    pointer_required = bool(args and getattr(args, "require_durable_pointer_evidence", False))
    pointer_patterns = (
        resolve_bounded_adapter_durable_pointer_patterns(args) if args is not None else ()
    )
    force = bool(args and getattr(args, "durable_closeout_force", False))
    ok, msg, _blocker = validate_durable_closeout_invoke_paths(
        source_dir,
        dest_dir,
        force=force,
    )
    if not ok:
        print(msg, file=sys.stderr)
        return 1
    invoker = durable_closeout_invoker or _default_durable_closeout_invoker
    return invoker(
        build_durable_closeout_invoke_argv(
            source_dir=source_dir,
            dest_dir=dest_dir,
            run_local_post_closeout_chain_v0=chain_requested,
            chain_archive_root=chain_archive_root,
            chain_run_id=chain_run_id,
            require_durable_pointer_evidence=pointer_required,
            durable_pointer_patterns=pointer_patterns,
            force=force,
        )
    )


def emit_bounded_adapter_durable_closeout_machine_lines(
    *,
    invoked: bool,
    rc: int,
    source_dir: Path,
    dest_dir: Path | None,
    validation_blocked: bool = False,
    blocker_hint: str = "",
) -> None:
    print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_INVOKED={'true' if invoked else 'false'}")
    print(
        "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_VALIDATION_BLOCKED="
        f"{'true' if validation_blocked else 'false'}"
    )
    if blocker_hint:
        print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_BLOCKER_HINT={blocker_hint}")
    print("BOUNDED_ADAPTER_OBSERVATION_CLOSEOUT_DECOUPLED=true")
    if not invoked and not validation_blocked:
        return
    if validation_blocked:
        print("BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS=blocked")
        print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_SOURCE_DIR={source_dir.resolve()}")
        if dest_dir is not None:
            print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_DEST_DIR={dest_dir.resolve()}")
        print("BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC=not_run")
        print("BOUNDED_ADAPTER_DURABLE_CLOSEOUT_NON_AUTHORIZING=true")
        return
    status = "pass" if rc == 0 else "failed"
    print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS={status}")
    print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_SOURCE_DIR={source_dir.resolve()}")
    if dest_dir is not None:
        print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_DEST_DIR={dest_dir.resolve()}")
    print(f"BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC={rc}")
    print("BOUNDED_ADAPTER_DURABLE_CLOSEOUT_NON_AUTHORIZING=true")
    print("REMOTE_AWS_TOUCHED=false")
    print("RUNTIME_STARTED=false")
    print("SCHEDULER_STARTED=false")
    print("PAPER_SHADOW_TESTNET_LIVE_STARTED=false")
    print("LIVE_AUTHORITY_CHANGED=false")
    print("DUPLICATE_SURFACE_CREATED=false")


def emit_bounded_adapter_local_post_closeout_chain_machine_lines(
    *,
    requested: bool,
    passthrough: bool,
    chain_archive_root: Path | None = None,
    chain_run_id: str | None = None,
) -> None:
    print(f"BOUNDED_ADAPTER_LOCAL_POST_CLOSEOUT_CHAIN_REQUESTED={'true' if requested else 'false'}")
    print(
        "BOUNDED_ADAPTER_LOCAL_POST_CLOSEOUT_CHAIN_PASSTHROUGH="
        f"{'true' if passthrough else 'false'}"
    )
    if chain_archive_root is not None:
        print(f"BOUNDED_ADAPTER_CHAIN_ARCHIVE_ROOT={chain_archive_root.resolve()}")
    else:
        print("BOUNDED_ADAPTER_CHAIN_ARCHIVE_ROOT=")
    if chain_run_id:
        print(f"BOUNDED_ADAPTER_CHAIN_RUN_ID={chain_run_id}")
    else:
        print("BOUNDED_ADAPTER_CHAIN_RUN_ID=")


def emit_bounded_adapter_durable_pointer_machine_lines(
    *,
    required: bool,
    pattern_count: int,
    archive_pointer_handoff: bool,
) -> None:
    print(f"BOUNDED_ADAPTER_DURABLE_POINTER_EVIDENCE_REQUIRED={'true' if required else 'false'}")
    print(f"BOUNDED_ADAPTER_DURABLE_POINTER_PATTERN_COUNT={pattern_count}")
    print(
        f"BOUNDED_ADAPTER_ARCHIVE_POINTER_HANDOFF={'true' if archive_pointer_handoff else 'false'}"
    )


def maybe_invoke_durable_closeout_after_archive(
    ctx: ExecuteContext,
    archive_dest: Path,
    *,
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
) -> int:
    """Return adapter exit code after optional durable closeout invocation."""
    chain_requested = bool(getattr(ctx.args, "run_local_post_closeout_chain_v0", False))
    chain_archive_root: Path | None = None
    if chain_requested:
        chain_archive_root = Path(ctx.args.chain_archive_root).expanduser().resolve()
    chain_run_id = resolve_bounded_adapter_chain_run_id(ctx.args, adapter_run_id=ctx.run_id)
    invoke_requested = bool(getattr(ctx.args, "invoke_durable_closeout_v0", False))
    chain_passthrough = chain_requested and invoke_requested
    pointer_required = bool(getattr(ctx.args, "require_durable_pointer_evidence", False))
    pointer_patterns = resolve_bounded_adapter_durable_pointer_patterns(ctx.args)
    pointer_pattern_count = len(pointer_patterns)

    if not invoke_requested:
        emit_bounded_adapter_durable_closeout_machine_lines(
            invoked=False,
            rc=0,
            source_dir=archive_dest,
            dest_dir=None,
        )
        emit_bounded_adapter_local_post_closeout_chain_machine_lines(
            requested=chain_requested,
            passthrough=False,
            chain_archive_root=chain_archive_root,
            chain_run_id=chain_run_id,
        )
        emit_bounded_adapter_durable_pointer_machine_lines(
            required=pointer_required,
            pattern_count=pointer_pattern_count,
            archive_pointer_handoff=False,
        )
        return 0
    archive_pointer_handoff = False
    if pointer_required:
        handoff_ok, handoff_msg = ensure_archive_pointer_in_archive_dest(
            ctx.staging_root,
            archive_dest,
        )
        archive_pointer_handoff = handoff_ok
        if not handoff_ok:
            emit_bounded_adapter_durable_closeout_machine_lines(
                invoked=False,
                rc=0,
                source_dir=archive_dest,
                dest_dir=None,
            )
            emit_bounded_adapter_local_post_closeout_chain_machine_lines(
                requested=chain_requested,
                passthrough=False,
                chain_archive_root=chain_archive_root,
                chain_run_id=chain_run_id,
            )
            emit_bounded_adapter_durable_pointer_machine_lines(
                required=True,
                pattern_count=pointer_pattern_count,
                archive_pointer_handoff=False,
            )
            print(handoff_msg, file=sys.stderr)
            return VALIDATION_EXIT
    dest_dir = Path(ctx.args.durable_closeout_dest_dir).expanduser().resolve()
    force = bool(getattr(ctx.args, "durable_closeout_force", False))
    ok, validation_msg, blocker_hint = validate_durable_closeout_invoke_paths(
        archive_dest,
        dest_dir,
        force=force,
    )
    if not ok:
        emit_bounded_adapter_durable_closeout_machine_lines(
            invoked=False,
            rc=0,
            source_dir=archive_dest,
            dest_dir=dest_dir,
            validation_blocked=True,
            blocker_hint=blocker_hint,
        )
        emit_bounded_adapter_local_post_closeout_chain_machine_lines(
            requested=chain_requested,
            passthrough=False,
            chain_archive_root=chain_archive_root,
            chain_run_id=chain_run_id,
        )
        emit_bounded_adapter_durable_pointer_machine_lines(
            required=pointer_required,
            pattern_count=pointer_pattern_count,
            archive_pointer_handoff=archive_pointer_handoff,
        )
        print(validation_msg, file=sys.stderr)
        return VALIDATION_EXIT
    rc = invoke_durable_closeout_after_archive(
        source_dir=archive_dest,
        dest_dir=dest_dir,
        args=ctx.args,
        adapter_run_id=ctx.run_id,
        durable_closeout_invoker=durable_closeout_invoker,
    )
    emit_bounded_adapter_durable_closeout_machine_lines(
        invoked=True,
        rc=rc,
        source_dir=archive_dest,
        dest_dir=dest_dir,
    )
    emit_bounded_adapter_local_post_closeout_chain_machine_lines(
        requested=chain_requested,
        passthrough=chain_passthrough,
        chain_archive_root=chain_archive_root,
        chain_run_id=chain_run_id,
    )
    emit_bounded_adapter_durable_pointer_machine_lines(
        required=pointer_required,
        pattern_count=pointer_pattern_count,
        archive_pointer_handoff=archive_pointer_handoff,
    )
    return 0 if rc == 0 else VALIDATION_EXIT


def _default_subprocess_runner(
    argv: Sequence[str],
    cwd: Path | None,
    stdout_path: Path | None,
    stderr_path: Path | None,
    *,
    extra_env: Mapping[str, str] | None = None,
) -> int:
    stdout = stderr = subprocess.DEVNULL
    if stdout_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout = stdout_path.open("w", encoding="utf-8")
    if stderr_path is not None:
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stderr = stderr_path.open("w", encoding="utf-8")
    env = None
    if extra_env:
        env = {**os.environ, **dict(extra_env)}
    try:
        proc = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd else None,
            check=False,
            stdout=stdout,
            stderr=stderr,
            env=env,
        )
    finally:
        if stdout not in (None, subprocess.DEVNULL):
            stdout.close()
        if stderr not in (None, subprocess.DEVNULL):
            stderr.close()
    return int(proc.returncode or 0)


def build_bounded_adapter_final_machine_lines_v0(
    *,
    run_id: str,
    adapter_lane: str,
    execution_performed: bool,
    review_verdict: str | None = None,
    closeout_succeeded: bool = True,
) -> dict[str, str]:
    """Deterministic non-authorizing FINAL_MACHINE_LINES payload for bounded adapters."""
    from scripts.ops.build_post_closeout_projection_payload_v0 import (
        REQUIRED_MACHINE_LINE_KEYS,
    )

    lines = {key: "false" for key in REQUIRED_MACHINE_LINE_KEYS}
    if execution_performed:
        lines["RUNTIME_COMMANDS_CALLED"] = "true"
    lines.update(
        {
            "ADAPTER_EXECUTED": "true" if execution_performed else "false",
            "ADAPTER_LANE": adapter_lane,
            "RUN_ID": run_id,
            "REMOTE_AWS_TOUCHED": "false",
            "RUNTIME_STARTED": "false",
            "SCHEDULER_STARTED": "false",
            "PAPER_SHADOW_TESTNET_LIVE_STARTED": "false",
            "LIVE_AUTHORITY_CHANGED": "false",
            "PREFLIGHT_BLOCKED": "true",
            "CLOSEOUT_ARTIFACT_EMIT_V0": "true",
            "CLOSEOUT_SUCCEEDED": "true" if closeout_succeeded else "false",
            "REVIEW_VERDICT": str(review_verdict or "UNKNOWN"),
            "BOUNDED_OBSERVATION_ONLY": "true",
            "NOTION_WRITE_CALLED": "false",
            "S3_AWS_RCLONE_CALLED": "false",
            "WORKFLOW_DISPATCH_CALLED": "false",
            "BROKER_EXCHANGE_CALLED": "false",
            "LIVE_AUTHORITY": "false",
            "TESTNET_AUTHORITY": "false",
        }
    )
    return lines


def _write_final_machine_lines_artifact(
    staging_root: Path,
    *,
    run_id: str,
    adapter_lane: str,
    execution_performed: bool,
    review_verdict: str | None,
    closeout_succeeded: bool = True,
) -> None:
    lines = build_bounded_adapter_final_machine_lines_v0(
        run_id=run_id,
        adapter_lane=adapter_lane,
        execution_performed=execution_performed,
        review_verdict=review_verdict,
        closeout_succeeded=closeout_succeeded,
    )
    staging_root.mkdir(parents=True, exist_ok=True)
    ordered = sorted(lines.items())
    (staging_root / FINAL_MACHINE_LINES_FILENAME).write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_closeout_artifacts(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    archive_dest: Path,
    review_payload: Mapping[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_metadata = {
        "run_id": ctx.run_id,
        "adapter_version": plan.adapter_version,
        "staging_root": str(ctx.staging_root),
        "archive_path": str(archive_dest),
        "duration_seconds": plan.duration_seconds,
        "poll_interval_seconds": plan.poll_interval_seconds,
        "review_verdict": review_payload.get("verdict"),
        "live_authority": False,
        "testnet_authority": False,
        "broker_authority": False,
        "utc": now,
    }
    (ctx.staging_root / "RUN_METADATA.json").write_text(
        json.dumps(run_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    closeout_lines = [
        "# Paper Bounded Observation Adapter Closeout",
        "",
        f"RUN_ID={ctx.run_id}",
        f"STAGING_PATH={ctx.staging_root}",
        f"ARCHIVE_PATH={archive_dest}",
        f"REVIEW_VERDICT={review_payload.get('verdict')}",
        "EXECUTION_PERFORMED=true",
        "PAPER_RUNTIME_APPROVAL_GRANTED=false",
        "SHADOW_STARTED=false",
        "TESTNET_STARTED=false",
        "LIVE_ALLOWED=false",
        "live_authority=false",
        "testnet_authority=false",
        "broker_authority=false",
        "PREFLIGHT_BLOCKED=true",
        "NOTION_WRITES=false",
        "PRIMARY_EVIDENCE_TIER=achieved",
        "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true",
    ]
    (ctx.staging_root / "CLOSEOUT.md").write_text(
        "\n".join(closeout_lines) + "\n",
        encoding="utf-8",
    )
    postrun_lines = [
        "# Paper Bounded Observation Postrun Analysis",
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
        adapter_lane=BOUNDED_ADAPTER_LANE_PAPER,
        execution_performed=True,
        review_verdict=str(review_payload.get("verdict") or "UNKNOWN"),
        closeout_succeeded=True,
    )


def _write_start_return_code_artifact(
    staging_root: Path,
    rc: int,
    *,
    blocker_hint: str = "",
) -> None:
    """Persist execute return code for external orchestrators."""
    staging_root.mkdir(parents=True, exist_ok=True)
    lines = [f"START_RC={int(rc)}"]
    if blocker_hint:
        lines.append(f"BLOCKER_HINT={blocker_hint}")
    (staging_root / START_RETURN_CODE_ARTIFACT).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def execute_plan(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    *,
    subprocess_runner: SubprocessRunner,
    durable_closeout_invoker: DurableCloseoutInvoker | None = None,
) -> int:
    ctx.staging_root.mkdir(parents=True, exist_ok=True)
    ctx.runtime_out.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    ctx.plan_dir.mkdir(parents=True, exist_ok=True)
    ctx.review_dir.mkdir(parents=True, exist_ok=True)

    rc = subprocess_runner(plan.commands["temp_config"], ctx.repo_root, None, None)
    if rc != 0:
        return rc

    stdout_log = ctx.logs_dir / "scheduler_stdout.log"
    stderr_log = ctx.logs_dir / "scheduler_stderr.log"
    scheduler_extra_env: dict[str, str] | None = None
    profile = normalize_profile(ctx.args.profile)
    if profile in _profiles_with_hold_runtime_env_bridge() and ctx.args.approval_record is not None:
        outroot, binding_run_id, bridge_issues = resolve_scheduler_hold_runtime_binding_target(
            profile=profile,
            approval_record=ctx.args.approval_record,
            approval_fields=ctx.approval_fields,
            run_id=ctx.run_id,
        )
        if bridge_issues:
            return VALIDATION_EXIT
        if outroot is not None:
            from scripts.ops.scheduler_start_boundary_guard_v0 import (
                SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV,
                SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV,
            )

            scheduler_extra_env = {
                SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV: str(outroot),
                SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV: binding_run_id,
            }

    rc = subprocess_runner(
        plan.commands["scheduler_bounded"],
        ctx.repo_root,
        stdout_log,
        stderr_log,
        extra_env=scheduler_extra_env,
    )
    if rc not in (0, TIMEOUT_EXIT):
        return rc

    review_out = ctx.review_dir / "REVIEW_RESULT.json"
    review_rc = subprocess_runner(
        plan.commands["review"],
        ctx.repo_root,
        review_out,
        None,
    )
    if review_rc != 0:
        return review_rc
    try:
        review_payload = json.loads(review_out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return VALIDATION_EXIT
    if review_payload.get("verdict") != "PASS":
        return VALIDATION_EXIT

    archive_dest = ctx.archive_root / "runs" / "paper" / ctx.run_id
    _write_closeout_artifacts(ctx, plan, archive_dest, review_payload)
    _write_manifest_sha256(ctx.staging_root)
    archive_dest.mkdir(parents=True, exist_ok=True)
    for item in ctx.staging_root.iterdir():
        dest = archive_dest / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    ok, reason = verify_manifest_sha256(archive_dest)
    if not ok:
        print(reason, file=sys.stderr)
        return VALIDATION_EXIT

    pointer = ctx.staging_root / "ARCHIVE_POINTER.md"
    pointer.write_text(
        "\n".join(
            [
                f"STAGING_PATH={ctx.staging_root}",
                f"ARCHIVE_PATH={archive_dest}",
                f"COPY_UTC={datetime.now(timezone.utc).isoformat()}",
                "ARCHIVE_COPY_COMPLETE=true",
                "MANIFEST_VERIFY_RC=0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    hook_result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=ctx.archive_root,
        run_bundle_path=archive_dest,
        source_run_id=ctx.run_id,
        source_stage="paper",
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
            "Paper-only bounded observation adapter v0. "
            "Default plan-only mode emits commands without executing runtime."
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
        help="Execute bounded observation (requires --approval-record).",
    )
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--source-jobs-toml", type=Path, default=None)
    parser.add_argument("--approval-record", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument(
        "--profile",
        type=str,
        default="",
        help=(
            "Optional approval contract profile. "
            f"Supported: {contract_24h.CONTRACT_PROFILE!r}, "
            f"{contract_gap4.CONTRACT_PROFILE!r}, "
            f"{contract_l2_120min.CONTRACT_PROFILE!r} "
            "(default empty: 120min paper-only without hold-binding bridge)."
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


def add_bounded_adapter_durable_closeout_cli_args(parser: argparse.ArgumentParser) -> None:
    """Register default-off durable closeout + local post-closeout chain CLI flags."""
    parser.add_argument(
        "--invoke-durable-closeout-v0",
        action="store_true",
        help=(
            "After successful archive copy, invoke durable_closeout_copy_verify_v0.py "
            "(requires --durable-closeout-dest-dir outside /tmp)."
        ),
    )
    parser.add_argument(
        "--durable-closeout-dest-dir",
        type=Path,
        default=None,
        help="Durable material closeout destination (required with --invoke-durable-closeout-v0).",
    )
    parser.add_argument(
        "--durable-closeout-force",
        action="store_true",
        help=(
            "Pass --force to durable_closeout_copy_verify_v0.py when source and dest differ "
            "and destination is pre-populated."
        ),
    )
    parser.add_argument(
        "--run-local-post-closeout-chain-v0",
        action="store_true",
        help=(
            "Pass through to durable_closeout_copy_verify_v0.py local post-closeout chain "
            "(requires --invoke-durable-closeout-v0 and --chain-archive-root outside /tmp)."
        ),
    )
    parser.add_argument(
        "--chain-archive-root",
        type=Path,
        default=None,
        help="Evidence archive root for Registry v1 (required with --run-local-post-closeout-chain-v0).",
    )
    parser.add_argument(
        "--chain-run-id",
        type=str,
        default="",
        help=(
            "Optional run_id for projection payload builder; defaults to adapter --run-id "
            "when --run-local-post-closeout-chain-v0 is set."
        ),
    )
    parser.add_argument(
        "--require-durable-pointer-evidence",
        action="store_true",
        help=(
            "Pass through to durable_closeout_copy_verify_v0.py pointer enforcement "
            "(requires --invoke-durable-closeout-v0)."
        ),
    )
    parser.add_argument(
        "--durable-pointer-pattern",
        action="append",
        default=None,
        help=(
            "Repeatable durable pointer/index glob for durable helper "
            "(requires --invoke-durable-closeout-v0)."
        ),
    )


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
        if args.duration_seconds is None:
            args.duration_seconds = contract_24h.DAEMON_PAPER_SHADOW_24H_DURATION_SECONDS
        duration_issues = contract_24h.validate_paper_duration_seconds(args.duration_seconds)
        if duration_issues:
            for issue in duration_issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
    elif profile == contract_gap4.CONTRACT_PROFILE:
        if not args.run_id.strip():
            print(
                f"--run-id is required for {contract_gap4.CONTRACT_PROFILE} profile",
                file=sys.stderr,
            )
            return USAGE_EXIT
        if args.duration_seconds is None:
            args.duration_seconds = contract_gap4.GAP4_DEFAULT_DURATION_SECONDS
        duration_issues = contract_gap4.validate_paper_duration_seconds(args.duration_seconds)
        if duration_issues:
            for issue in duration_issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
    elif profile == contract_l2_120min.CONTRACT_PROFILE:
        if not args.run_id.strip():
            print(
                f"--run-id is required for {contract_l2_120min.CONTRACT_PROFILE} profile",
                file=sys.stderr,
            )
            return USAGE_EXIT
        if args.duration_seconds is None:
            args.duration_seconds = contract_l2_120min.L2_DURATION_SECONDS
        duration_issues = contract_l2_120min.validate_paper_duration_seconds(args.duration_seconds)
        if duration_issues:
            for issue in duration_issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
    elif args.duration_seconds is None:
        args.duration_seconds = DEFAULT_DURATION_SECONDS

    if args.duration_seconds <= 0 or args.poll_interval <= 0:
        print("duration and poll interval must be > 0", file=sys.stderr)
        return USAGE_EXIT

    repo_root = (args.repo_root or repo_root_from_script()).resolve()
    source_jobs = (args.source_jobs_toml or (repo_root / "config/scheduler/jobs.toml")).resolve()
    staging_root = args.staging_root.expanduser().resolve()
    archive_root = args.archive_root.expanduser().resolve()
    run_id = (
        args.run_id.strip()
        or f"paper_only_bounded_observation_120min_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    mode = "execute" if args.execute else "plan-only"
    plan = build_plan(
        mode=mode,
        staging_root=staging_root,
        archive_root=archive_root,
        repo_root=repo_root,
        source_jobs_toml=source_jobs,
        duration_seconds=args.duration_seconds,
        poll_interval_seconds=args.poll_interval,
        run_id=run_id,
        contract_profile=profile,
    )

    if args.execute:
        ctx = ExecuteContext(
            args=args,
            repo_root=repo_root,
            staging_root=staging_root,
            archive_root=archive_root,
            runtime_out=staging_root / "runtime_out",
            logs_dir=staging_root / "logs",
            plan_dir=staging_root / "plan",
            review_dir=staging_root / "review",
            temp_jobs=staging_root / "plan" / "temp_jobs.toml",
            run_id=run_id,
        )
        issues = validate_execute_preconditions(
            ctx,
            repo_clean_checker=repo_clean_checker or default_repo_clean_checker,
            environ=environ,
        )
        if issues:
            blocker_hint = ";".join(issues)
            _write_start_return_code_artifact(
                staging_root,
                VALIDATION_EXIT,
                blocker_hint=blocker_hint,
            )
            for issue in issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
        runner = subprocess_runner or _default_subprocess_runner
        rc = execute_plan(
            ctx,
            plan,
            subprocess_runner=runner,
            durable_closeout_invoker=durable_closeout_invoker,
        )
        _write_start_return_code_artifact(
            staging_root,
            rc,
            blocker_hint="" if rc == 0 else "execute_plan_nonzero",
        )
        return rc

    print(render_plan(plan, args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
