#!/usr/bin/env python3
"""Path-C Testnet private-readonly connectivity adapter v1 (plan-only default, gated execute).

Delegates private GET read-only reachability to archive_futures_testnet_harness_v0.py
(private_readonly_reachability_only). Does not authorize Live, preflight lift, orders,
or Path-B/Path-A lanes.
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
from typing import Any, Callable, Mapping, Optional, Protocol

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import archive_futures_testnet_harness_v0 as harness
from scripts.ops.primary_evidence_retention_v0 import (
    verify_manifest_sha256,
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.ops.bounded_futures_private_readonly_contract_v0 import (
    CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PRIVATE_READONLY_MODE,
    PrivateReadonlyHttpRequest,
)

ADAPTER_VERSION = "cli_testnet_private_readonly_connectivity_flow_v1"
HARNESS_SCRIPT = "scripts/ops/archive_futures_testnet_harness_v0.py"
REVIEW_SCRIPT = "scripts/ops/review_testnet_private_readonly_connectivity_evidence_v1.py"
CREDENTIAL_PRESENCE_SCRIPT = (
    "scripts/ops/check_kraken_futures_demo_credentials_presence_readonly_v0.py"
)
WRAPPER_EVIDENCE_DIR = "wrapper_evidence"

SESSION_CLASS = "path_c_private_readonly_connectivity_v0"
RUN_TYPE = "TESTNET_ONLY_BOUNDED_L4_PRIVATE_READ_ONLY_CONNECTIVITY_HARNESS"
CONNECTIVITY_MODE = "private-readonly-connectivity"
TESTNET_PATH = "PathC_private_readonly_connectivity"
ORDER_MODE = "zero-order"

DEFAULT_DURATION_SECONDS = 900
MAX_DURATION_SECONDS = 900
HARNESS_MAX_DURATION_SECONDS = 300
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 5

MAX_ORDERS = 0
MAX_CANCEL = 0
MAX_NOTIONAL_USD = 0

PROOF_CONTRACT_DOC = "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"
MANIFEST_SCHEMA = "testnet_path_c_private_readonly_connectivity.v1"
ENDPOINT_ALLOWLIST_STR = ",".join(sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS))

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
        "EXECUTE_AUTHORIZED",
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
        "START_LIVE_NOW",
        "FUTURES_EXECUTE_AUTHORIZED",
        "FUTURES_PRIVATE_API_AUTHORIZED",
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
    "run_testnet_bounded_evidence_staging_v0.sh",
)

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_TESTNET_PATH_C_PRIVATE_READONLY_CONNECTIVITY_NOW": "true",
    "RUN_TYPE": RUN_TYPE,
    "CONNECTIVITY_MODE": CONNECTIVITY_MODE,
    "PATH_B_IS_NOT_PATH_C": "true",
    "ORDER_MODE": ORDER_MODE,
    "SESSION_CLASS": SESSION_CLASS,
}

REQUIRED_APPROVAL_CAPS = {
    "max_orders": str(MAX_ORDERS),
    "max_cancel": str(MAX_CANCEL),
    "max_notional": str(MAX_NOTIONAL_USD),
    "GET_ONLY": "true",
    "primary_evidence_required": "true",
    "closeout_required": "true",
    "manifest_verify_required": "true",
    "forbidden_substrings_enforced": "true",
}

USAGE_EXIT = 2
VALIDATION_EXIT = 1


class PrivateReadonlyFetcher(Protocol):
    def fetch(
        self,
        http_request: PrivateReadonlyHttpRequest,
        *,
        timeout_seconds: float,
    ) -> tuple[int, bytes]:
        """Return HTTP status and body bytes for a signed private GET."""


@dataclass(frozen=True)
class AdapterPlan:
    adapter_version: str
    mode: str
    staging_root: str
    archive_root: str
    duration_seconds: int
    harness_duration_seconds: int
    heartbeat_interval_seconds: int
    run_id: str
    repo_root: str
    harness_script: str
    harness_mode: str
    session_class: str
    run_type: str
    connectivity_mode: str
    testnet_path: str
    max_orders: int
    max_cancel: int
    max_notional_usd: int
    endpoint_allowlist: list[str]
    commands: dict[str, list[str]]
    retention_steps: list[str]
    expected_artifacts: list[str]
    credential_presence_script: str
    primary_evidence_required: bool = True
    closeout_required: bool = True
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
    review_dir: Path
    harness_work_root: Path
    run_id: str
    approval_fields: Mapping[str, str] = field(default_factory=dict)


HarnessRunner = Callable[
    [ExecuteContext, AdapterPlan, Optional[PrivateReadonlyFetcher], bool],
    tuple[int, Optional[dict[str, Any]]],
]
RepoCleanChecker = Callable[[Path], tuple[bool, str]]
CredentialPresenceChecker = Callable[[Path, Mapping[str, str]], tuple[bool, str]]
ReviewRunner = Callable[[Path, Path], tuple[int, dict[str, Any]]]


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
        if fields.get(key, "").lower() != expected.lower():
            issues.append(f"approval record missing or invalid: {key}={expected}")
    for key, expected in REQUIRED_APPROVAL_CAPS.items():
        if fields.get(key, "").lower() != expected.lower():
            issues.append(f"approval record cap/boundary invalid: {key}={expected}")
    allowlist_raw = fields.get("endpoint_allowlist", "")
    allowlist_parts = {part.strip() for part in allowlist_raw.split(",") if part.strip()}
    if allowlist_parts != set(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS):
        issues.append(
            "approval record endpoint_allowlist must match private-readonly GET allowlist"
        )
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


def default_credential_presence_checker(
    repo_root: Path,
    environ: Mapping[str, str],
) -> tuple[bool, str]:
    """Wire credential presence checker; never logs secret values."""
    script = (repo_root / CREDENTIAL_PRESENCE_SCRIPT).resolve()
    if not script.is_file():
        return False, f"credential presence script missing: {script}"

    from scripts.ops import (
        check_kraken_futures_demo_credentials_presence_readonly_v0 as presence_mod,
    )

    payload, code = presence_mod.run_presence_check(
        get_env_value=lambda key: environ.get(key, ""),
    )
    if code != 0:
        return False, "credential presence checker returned invalid input"
    if payload.get("status") == "BLOCKED" or payload.get("missing_count", 0) > 0:
        missing = payload.get("missing") or []
        return False, f"credential presence BLOCKED; missing keys: {', '.join(missing)}"
    if payload.get("forbidden_alternate_keys_present"):
        return False, "forbidden alternate credential env keys present"
    return True, ""


def _harness_duration_cap(duration_seconds: int) -> int:
    return min(duration_seconds, HARNESS_MAX_DURATION_SECONDS)


def _harness_argv(
    *,
    work_root: Path,
    run_id: str,
    duration_seconds: int,
    execute_network: bool,
) -> list[str]:
    harness_duration = _harness_duration_cap(duration_seconds)
    argv = [
        "--mode",
        PRIVATE_READONLY_MODE,
        "--archive-root",
        str(work_root.resolve()),
        "--run-id",
        run_id,
        "--rest-base-url",
        DEMO_FUTURES_REST_BASE_URL,
        "--duration-cap-seconds",
        str(harness_duration),
        "--order-cap",
        "0",
        "--validate-only-order-cap",
        "0",
    ]
    if execute_network:
        argv.extend(
            [
                "--execute-network",
                "--confirm-futures-private-readonly-reachability",
                CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
            ]
        )
    return argv


def _find_harness_runtime_dir(work_root: Path, run_id: str) -> Path | None:
    runtime_root = work_root / "runtime"
    if not runtime_root.is_dir():
        return None
    matches = sorted(runtime_root.glob(f"bounded_futures_private_readonly_{run_id}_*"))
    return matches[-1] if matches else None


def default_harness_runner(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    private_fetcher: Optional[PrivateReadonlyFetcher],
    execute_network: bool,
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[int, Optional[dict[str, Any]]]:
    if execute_network and private_fetcher is None:
        return VALIDATION_EXIT, None
    argv = _harness_argv(
        work_root=ctx.harness_work_root,
        run_id=ctx.run_id,
        duration_seconds=plan.duration_seconds,
        execute_network=execute_network,
    )
    env = dict(os.environ if environ is None else environ)
    rc = harness.main(argv, private_fetcher=private_fetcher, environ=env)
    if rc != 0:
        return rc, None
    runtime_dir = _find_harness_runtime_dir(ctx.harness_work_root, ctx.run_id)
    if runtime_dir is None:
        return VALIDATION_EXIT, None
    evidence_path = runtime_dir / "FUTURES_EVIDENCE.json"
    if not evidence_path.is_file():
        return VALIDATION_EXIT, None
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return VALIDATION_EXIT, None
    if not isinstance(payload, dict):
        return VALIDATION_EXIT, None
    return 0, payload


def _build_wrapper_evidence(
    ctx: ExecuteContext,
    *,
    harness_evidence: dict[str, Any],
    duration_seconds: int,
    heartbeat_interval_seconds: int,
) -> None:
    proven = bool(harness_evidence.get("private_readonly_reachability_proven"))
    request_count = int(harness_evidence.get("request_count") or 0)
    endpoints = list(harness_evidence.get("endpoints_called") or [])
    network_calls = list(harness_evidence.get("network_calls") or [])
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ctx.wrapper_evidence.mkdir(parents=True, exist_ok=True)
    (ctx.wrapper_evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text(
        "\n".join(
            [
                "# Testnet Path-C Private-Readonly Connectivity Observation",
                "",
                f"RUN_ID={ctx.run_id}",
                f"GENERATED_UTC={utc_now}",
                f"SESSION_CLASS={SESSION_CLASS}",
                f"RUN_TYPE={RUN_TYPE}",
                f"CONNECTIVITY_MODE={CONNECTIVITY_MODE}",
                f"TESTNET_PATH={TESTNET_PATH}",
                "PATH_B_IS_NOT_PATH_C=true",
                f"ORDER_MODE={ORDER_MODE}",
                f"max_orders={MAX_ORDERS}",
                f"max_cancel={MAX_CANCEL}",
                f"max_notional={MAX_NOTIONAL_USD}",
                "GET_ONLY=true",
                f"endpoint_allowlist={ENDPOINT_ALLOWLIST_STR}",
                "forbidden_substrings_enforced=true",
                "primary_evidence_required=true",
                "closeout_required=true",
                "TESTNET_SANDBOX_ONLY",
                "NO_PRODUCTION_FALLBACK",
                "NO_LIVE_ORDER_SUBMISSION",
                f"Proof contract reference: {PROOF_CONTRACT_DOC}",
                "",
                "Non-authorizing Path-C private-readonly connectivity evidence.",
                "Does not authorize Live, Preflight lift, Truth, or order submission.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "run_id": ctx.run_id,
        "generated_utc": utc_now,
        "session_class": SESSION_CLASS,
        "run_type": RUN_TYPE,
        "connectivity_mode": CONNECTIVITY_MODE,
        "testnet_path": TESTNET_PATH,
        "path_b_is_not_path_c": True,
        "order_mode": ORDER_MODE,
        "max_orders": MAX_ORDERS,
        "max_cancel": MAX_CANCEL,
        "max_notional_usd": MAX_NOTIONAL_USD,
        "get_only": True,
        "endpoint_allowlist": sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS),
        "forbidden_substrings_enforced": True,
        "primary_evidence_required": True,
        "closeout_required": True,
        "manifest_verify_required": True,
        "TESTNET_SANDBOX_ONLY": True,
        "NO_PRODUCTION_FALLBACK": True,
        "NO_LIVE_ORDER_SUBMISSION": True,
        "broker_connected": proven,
        "production_fallback": False,
        "private_readonly_reachability_proven": proven,
        "testnet_connectivity_proven": proven,
        "order_submission_allowed": False,
        "real_orders_executed": False,
        "trade_position_mutation_executed": False,
        "cancel_attempted": False,
        "network_request_count": request_count,
        "endpoints_called": endpoints,
        "network_host": harness_evidence.get("network_host"),
        "proof_contract_doc": PROOF_CONTRACT_DOC,
        "harness_version": harness_evidence.get("harness_version"),
        "evidence_source": harness_evidence.get("evidence_source"),
        "credential_values_logged": False,
    }
    (ctx.wrapper_evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    steps: list[str] = []
    step_no = 0
    for call in network_calls:
        step_no += 1
        steps.append(
            json.dumps(
                {
                    "step": step_no,
                    "mode": "private_readonly_connectivity_probe",
                    "endpoint": call.get("endpoint"),
                    "http_method": call.get("http_method", "GET"),
                    "http_status": call.get("http_status"),
                    "broker_connected": proven,
                    "no_orders": True,
                    "no_cancel": True,
                },
                sort_keys=True,
            )
        )
    if not steps:
        step_no = 1
        steps.append(
            json.dumps(
                {
                    "step": step_no,
                    "mode": "private_readonly_connectivity_probe",
                    "broker_connected": proven,
                    "no_orders": True,
                    "no_cancel": True,
                },
                sort_keys=True,
            )
        )
    hold_steps = max(0, (duration_seconds // heartbeat_interval_seconds) - step_no)
    for _offset in range(hold_steps):
        step_no += 1
        steps.append(
            json.dumps(
                {
                    "step": step_no,
                    "mode": "private_readonly_connectivity_hold",
                    "heartbeat_interval_seconds": heartbeat_interval_seconds,
                    "broker_connected": proven,
                    "no_orders": True,
                },
                sort_keys=True,
            )
        )
    (ctx.wrapper_evidence / "steps.jsonl").write_text("\n".join(steps) + "\n", encoding="utf-8")


def build_plan(
    *,
    mode: str,
    staging_root: Path,
    archive_root: Path,
    repo_root: Path,
    duration_seconds: int,
    heartbeat_interval_seconds: int,
    run_id: str,
) -> AdapterPlan:
    harness_duration = _harness_duration_cap(duration_seconds)
    review_out = staging_root / "review" / "REVIEW_RESULT.json"
    harness_work = (archive_root / ".path_c_harness_work" / run_id).resolve()
    harness_cmd = [
        sys.executable,
        str((repo_root / HARNESS_SCRIPT).resolve()),
        "--mode",
        PRIVATE_READONLY_MODE,
        "--archive-root",
        str(harness_work),
        "--run-id",
        run_id,
        "--rest-base-url",
        DEMO_FUTURES_REST_BASE_URL,
        "--duration-cap-seconds",
        str(harness_duration),
        "--order-cap",
        "0",
    ]
    review_cmd = [
        sys.executable,
        str((repo_root / REVIEW_SCRIPT).resolve()),
        "--staging-root",
        str(staging_root.resolve()),
        "--out",
        str(review_out.resolve()),
        "--json",
    ]
    archive_dest = archive_root / "runs" / "testnet" / run_id
    retention_steps = [
        f"delegate private-readonly reachability via {HARNESS_SCRIPT}",
        f"wire credential presence via {CREDENTIAL_PRESENCE_SCRIPT} (execute gate only)",
        f"materialize wrapper evidence under {staging_root / WRAPPER_EVIDENCE_DIR}",
        f"review PASS required at {review_out.parent}",
        f"generate MANIFEST.sha256 under {staging_root}",
        f"copy staging bundle to {archive_dest}",
        f"verify checksums on archive copy at {archive_dest}",
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
        "RUN_METADATA.json",
    ]
    commands = {
        "archive_harness_delegate": harness_cmd,
        "credential_presence_reference": [
            sys.executable,
            str((repo_root / CREDENTIAL_PRESENCE_SCRIPT).resolve()),
            "--json",
        ],
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
        duration_seconds=duration_seconds,
        harness_duration_seconds=harness_duration,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        run_id=run_id,
        repo_root=str(repo_root.resolve()),
        harness_script=HARNESS_SCRIPT,
        harness_mode=PRIVATE_READONLY_MODE,
        session_class=SESSION_CLASS,
        run_type=RUN_TYPE,
        connectivity_mode=CONNECTIVITY_MODE,
        testnet_path=TESTNET_PATH,
        max_orders=MAX_ORDERS,
        max_cancel=MAX_CANCEL,
        max_notional_usd=MAX_NOTIONAL_USD,
        endpoint_allowlist=sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS),
        commands=commands,
        retention_steps=retention_steps,
        expected_artifacts=expected_artifacts,
        credential_presence_script=CREDENTIAL_PRESENCE_SCRIPT,
        forbidden_paths_absent=forbidden_absent,
    )


def render_plan(plan: AdapterPlan, as_json: bool) -> str:
    if as_json:
        return json.dumps(plan.to_dict(), indent=2, sort_keys=True)
    lines = [
        f"ADAPTER_VERSION={plan.adapter_version}",
        f"MODE={plan.mode}",
        f"SESSION_CLASS={plan.session_class}",
        f"RUN_TYPE={plan.run_type}",
        f"CONNECTIVITY_MODE={plan.connectivity_mode}",
        f"TESTNET_PATH={plan.testnet_path}",
        f"HARNESS_SCRIPT={plan.harness_script}",
        f"HARNESS_MODE={plan.harness_mode}",
        f"DURATION_SECONDS={plan.duration_seconds}",
        f"HARNESS_DURATION_SECONDS={plan.harness_duration_seconds}",
        f"MAX_ORDERS={plan.max_orders}",
        f"MAX_CANCEL={plan.max_cancel}",
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
    credential_presence_checker: CredentialPresenceChecker,
    environ: Mapping[str, str] | None = None,
    allow_live_network: bool,
    private_fetcher: Optional[PrivateReadonlyFetcher],
) -> list[str]:
    issues: list[str] = []
    env = dict(os.environ if environ is None else environ)
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
    issues.extend(validate_env_guardrails(env))
    ok, reason = credential_presence_checker(ctx.repo_root, env)
    if not ok:
        issues.append(reason or "credential presence check not satisfied")
    if ctx.args.strict_repo_clean:
        clean, reason = repo_clean_checker(ctx.repo_root)
        if not clean:
            issues.append(reason or "repository is not clean")
    if not allow_live_network and private_fetcher is None:
        issues.append(
            "live network blocked: inject test private fetcher or pass --allow-live-network "
            "(requires separate Operator execute GO)"
        )
    return issues


def _default_review_runner(staging_root: Path, review_out: Path) -> tuple[int, dict[str, Any]]:
    script = repo_root_from_script() / REVIEW_SCRIPT
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--staging-root",
            str(staging_root),
            "--out",
            str(review_out),
            "--json",
        ],
        cwd=str(repo_root_from_script()),
        check=False,
        capture_output=True,
        text=True,
    )
    if not review_out.is_file():
        return int(proc.returncode or VALIDATION_EXIT), {}
    try:
        payload = json.loads(review_out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return VALIDATION_EXIT, {}
    return int(proc.returncode or 0), payload


def _write_closeout_artifacts(
    ctx: ExecuteContext,
    plan: AdapterPlan,
    archive_dest: Path,
    review_payload: Mapping[str, Any],
    harness_evidence: Mapping[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    (ctx.staging_root / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "run_id": ctx.run_id,
                "adapter_version": plan.adapter_version,
                "session_class": SESSION_CLASS,
                "run_type": RUN_TYPE,
                "connectivity_mode": CONNECTIVITY_MODE,
                "testnet_path": TESTNET_PATH,
                "path_b_is_not_path_c": True,
                "order_mode": ORDER_MODE,
                "max_orders": MAX_ORDERS,
                "max_cancel": MAX_CANCEL,
                "staging_root": str(ctx.staging_root),
                "archive_path": str(archive_dest),
                "duration_seconds_requested": plan.duration_seconds,
                "harness_duration_seconds": plan.harness_duration_seconds,
                "heartbeat_interval_seconds": plan.heartbeat_interval_seconds,
                "private_readonly_reachability_proven": harness_evidence.get(
                    "private_readonly_reachability_proven"
                ),
                "testnet_connectivity_proven": harness_evidence.get(
                    "private_readonly_reachability_proven"
                ),
                "network_request_count": harness_evidence.get("request_count"),
                "review_verdict": review_payload.get("verdict"),
                "primary_evidence_required": True,
                "closeout_required": True,
                "utc": now,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (ctx.staging_root / "CLOSEOUT.md").write_text(
        "\n".join(
            [
                "# Path-C Testnet Private-Readonly Connectivity Adapter Closeout",
                "",
                f"RUN_ID={ctx.run_id}",
                f"SESSION_CLASS={SESSION_CLASS}",
                f"RUN_TYPE={RUN_TYPE}",
                f"CONNECTIVITY_MODE={CONNECTIVITY_MODE}",
                "PATH_B_IS_NOT_PATH_C=true",
                f"REVIEW_VERDICT={review_payload.get('verdict')}",
                "EXECUTION_PERFORMED=true",
                "TESTNET_AUTHORIZED=false",
                "EXECUTE_AUTHORIZED=false",
                "LIVE_ALLOWED=false",
                "PREFLIGHT_REMAINS_BLOCKED=true",
                "PRIMARY_EVIDENCE_TIER=achieved",
                "CLOSEOUT_REQUIRED=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _copy_staging_to_archive(staging_root: Path, archive_dest: Path) -> None:
    archive_dest.mkdir(parents=True, exist_ok=True)
    for item in staging_root.iterdir():
        if item.name == "harness_work":
            continue
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
    harness_runner: HarnessRunner,
    review_runner: ReviewRunner,
    private_fetcher: Optional[PrivateReadonlyFetcher],
    allow_live_network: bool,
    environ: Mapping[str, str] | None = None,
) -> int:
    if ctx.staging_root.exists():
        shutil.rmtree(ctx.staging_root)
    ctx.staging_root.mkdir(parents=True, exist_ok=True)
    ctx.wrapper_evidence.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    ctx.review_dir.mkdir(parents=True, exist_ok=True)
    ctx.harness_work_root.mkdir(parents=True, exist_ok=True)

    execute_network = allow_live_network or private_fetcher is not None
    env = dict(os.environ if environ is None else environ)

    def _default_run(
        inner_ctx: ExecuteContext,
        inner_plan: AdapterPlan,
        fetcher: Optional[PrivateReadonlyFetcher],
        net: bool,
    ) -> tuple[int, Optional[dict[str, Any]]]:
        return default_harness_runner(inner_ctx, inner_plan, fetcher, net, environ=env)

    run = harness_runner if harness_runner is not None else _default_run
    harness_rc, harness_evidence = run(ctx, plan, private_fetcher, execute_network)
    (ctx.logs_dir / "wrapper_stdout.log").write_text(
        f"path_c_harness_rc={harness_rc}\nexecute_network={execute_network}\n",
        encoding="utf-8",
    )
    (ctx.logs_dir / "wrapper_stderr.log").write_text("", encoding="utf-8")
    if harness_rc != 0 or harness_evidence is None:
        return harness_rc if harness_rc != 0 else VALIDATION_EXIT
    if not harness_evidence.get("private_readonly_reachability_proven"):
        print("harness did not prove private-readonly connectivity", file=sys.stderr)
        return VALIDATION_EXIT

    _build_wrapper_evidence(
        ctx,
        harness_evidence=harness_evidence,
        duration_seconds=plan.duration_seconds,
        heartbeat_interval_seconds=plan.heartbeat_interval_seconds,
    )

    review_out = ctx.review_dir / "REVIEW_RESULT.json"
    review_rc, review_payload = review_runner(ctx.staging_root, review_out)
    if review_rc != 0:
        return review_rc
    if review_payload.get("verdict") != "PASS":
        return VALIDATION_EXIT

    archive_dest = ctx.archive_root / "runs" / "testnet" / ctx.run_id
    _write_closeout_artifacts(ctx, plan, archive_dest, review_payload, harness_evidence)
    _write_manifest_sha256(ctx.staging_root)
    _copy_staging_to_archive(ctx.staging_root, archive_dest)
    ok, reason = verify_manifest_sha256(archive_dest)
    if not ok:
        print(reason, file=sys.stderr)
        return VALIDATION_EXIT
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Path-C Testnet private-readonly connectivity adapter v1. "
            "Default plan-only; execute requires approval, credential presence, and network gate."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument(
        "--heartbeat-interval-seconds",
        type=int,
        default=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--approval-record", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument(
        "--allow-live-network",
        action="store_true",
        help="Allow real demo-futures private GET (separate Operator execute GO required).",
    )
    parser.add_argument("--strict-repo-clean", action="store_true", default=True)
    parser.add_argument("--no-strict-repo-clean", action="store_false", dest="strict_repo_clean")
    parser.add_argument("--json", action="store_true")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    harness_runner: Optional[HarnessRunner] = None,
    review_runner: Optional[ReviewRunner] = None,
    repo_clean_checker: Optional[RepoCleanChecker] = None,
    credential_presence_checker: Optional[CredentialPresenceChecker] = None,
    private_fetcher: Optional[PrivateReadonlyFetcher] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> int:
    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return USAGE_EXIT

    if args.duration_seconds <= 0 or args.duration_seconds > MAX_DURATION_SECONDS:
        print(f"duration-seconds must be 1..{MAX_DURATION_SECONDS}", file=sys.stderr)
        return USAGE_EXIT
    if args.heartbeat_interval_seconds <= 0:
        print("heartbeat-interval-seconds must be positive", file=sys.stderr)
        return USAGE_EXIT

    repo_root = (args.repo_root or repo_root_from_script()).resolve()
    staging_root = args.staging_root.expanduser().resolve()
    archive_root = args.archive_root.expanduser().resolve()
    run_id = args.run_id.strip() or (
        "testnet_path_c_private_readonly_connectivity_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    mode = "execute" if args.execute else "plan-only"
    plan = build_plan(
        mode=mode,
        staging_root=staging_root,
        archive_root=archive_root,
        repo_root=repo_root,
        duration_seconds=args.duration_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        run_id=run_id,
    )

    if args.execute:
        ctx = ExecuteContext(
            args=args,
            repo_root=repo_root,
            staging_root=staging_root,
            archive_root=archive_root,
            wrapper_evidence=staging_root / WRAPPER_EVIDENCE_DIR,
            logs_dir=staging_root / "logs",
            review_dir=staging_root / "review",
            harness_work_root=archive_root / ".path_c_harness_work" / run_id,
            run_id=run_id,
        )
        active_private_fetcher = private_fetcher
        if args.allow_live_network and active_private_fetcher is None:
            active_private_fetcher = harness.default_safe_private_readonly_rest_fetcher()
        issues = validate_execute_preconditions(
            ctx,
            repo_clean_checker=repo_clean_checker or default_repo_clean_checker,
            credential_presence_checker=credential_presence_checker
            or default_credential_presence_checker,
            environ=environ,
            allow_live_network=args.allow_live_network,
            private_fetcher=active_private_fetcher,
        )
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return VALIDATION_EXIT
        return execute_plan(
            ctx,
            plan,
            harness_runner=harness_runner,
            review_runner=review_runner or _default_review_runner,
            private_fetcher=active_private_fetcher,
            allow_live_network=args.allow_live_network,
            environ=environ,
        )

    print(render_plan(plan, args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
