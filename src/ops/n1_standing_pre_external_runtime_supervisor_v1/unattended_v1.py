"""Durable technical restart control for the existing bounded N1 supervisor.

The request factory binds existing runtime ports and governance. This owner
never grants trading authority, renews a spent cycle budget, or resubmits orders.
An interrupted S5 needs its own proven recovery; absence of POST is insufficient.
"""

from dataclasses import asdict, dataclass, replace
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time
import uuid

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _dead_owner_wait_checkpoint_proven_v1,
    LEDGER_FILENAME,
    LOCK_NAME,
    ABSOLUTE_MAX_CYCLES_PER_RUN,
    ABSOLUTE_MAX_RUN_DURATION_SECONDS,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    bounded_retry_policy_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    record_runtime_notice_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEFAULT_BOUNDED_RETRY_LIMIT,
)
from .supervisor_v1 import run_n1_standing_pre_external_supervisor_v1


@dataclass(frozen=True)
class UnattendedHostBoundsV1:
    host_id: str
    repository_sha: str
    runtime_config_digest: str
    expires_at_unix: float
    max_total_cycles: int
    max_total_seconds: float
    wait_interval_seconds: float

    def validate_v1(self):
        if not all(
            isinstance(v, str) and v and v == v.strip()
            for v in (self.host_id, self.repository_sha, self.runtime_config_digest)
        ):
            raise ValueError("HOST_RESTART_BINDING_INVALID")
        if (
            type(self.max_total_cycles) is not int
            or not 0 < self.max_total_cycles <= ABSOLUTE_MAX_CYCLES_PER_RUN
            or not all(
                type(v) in {int, float} and math.isfinite(v) and v > 0
                for v in (self.expires_at_unix, self.max_total_seconds, self.wait_interval_seconds)
            )
            or self.max_total_seconds > ABSOLUTE_MAX_RUN_DURATION_SECONDS
            or self.wait_interval_seconds > 60
        ):
            raise ValueError("HOST_RESTART_BOUNDS_INVALID")


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".writing." + uuid.uuid4().hex)
    try:
        with temp.open("x") as stream:
            os.chmod(temp, 0o600)
            json.dump(value, stream, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


def unattended_request_digest_v1(request):
    """Bind stable host configuration and the actual checkout's Python source."""
    config = asdict(request["config"])
    config.pop("evidence_root")
    if config.get("lock_root") is None:
        raise ValueError("HOST_RESTART_STABLE_LOCK_ROOT_REQUIRED")
    authorization = asdict(request["authorization"])
    for key in ("expected_cursor_floor", "max_cycles_per_run", "max_run_duration_seconds"):
        authorization.pop(key, None)
    repo = Path(request.get("repo_root") or Path(__file__).resolve().parents[3]).resolve()
    source = sha256()
    for path in sorted((repo / "src").rglob("*.py")):
        source.update(str(path.relative_to(repo)).encode())
        source.update(path.read_bytes())
    value = {
        "config": config,
        "authorization": authorization,
        "bound": request["bound"].to_dict(),
        "source_digest": source.hexdigest(),
        "origin_main_sha": request["origin_main_sha"],
    }
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def run_unattended_n1_host_v1(
    *,
    bounds: UnattendedHostBoundsV1,
    state_root: Path,
    request_factory,
    clock=time.time,
    sleeper=time.sleep,
):
    """Call the actual supervisor with fresh ports and the remaining original bounds.

    request_factory(attempt_index, evidence_root) returns its normal kwargs.
    No factory is synthesized from fixtures and no network credential is loaded
    here. The factory and normal N1/F1-M9/governance gates retain their authority.
    A process manager may call this again after death; its durable allowance is
    shared across those invocations. A stop marker is authoritative.
    """
    bounds.validate_v1()
    root = Path(state_root).resolve()
    existing_root = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    binding = sha256(json.dumps(bounds.__dict__, sort_keys=True).encode()).hexdigest()
    receipt = root / "host_restart_state_v1.json"
    if existing_root and not receipt.is_file():
        raise ValueError("HOST_RESTART_REGISTERED_STATE_MISSING")
    with (root / "host_controller.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if receipt.exists():
            state = json.loads(receipt.read_text())
            if (
                state.get("binding") != binding
                or type(state.get("attempts")) is not int
                or not 0 <= state["attempts"] <= 1 + DEFAULT_BOUNDED_RETRY_LIMIT
                or type(state.get("cycles_used")) is not int
                or not 0 <= state["cycles_used"] <= bounds.max_total_cycles
                or type(state.get("started_at")) not in {int, float}
                or not math.isfinite(state["started_at"])
                or state.get("status")
                not in {
                    "READY",
                    "RUNNING",
                    "RECOVERY_CHECKPOINT_REQUIRED",
                    "COMPLETED",
                    "STOPPED",
                    "BOUNDS_EXHAUSTED",
                    "RETRY_EXHAUSTED",
                    "GOVERNED_RUNTIME_STOPPED",
                }
            ):
                raise ValueError("HOST_RESTART_RECEIPT_UNPROVEN")
        else:
            state = {
                "binding": binding,
                "attempts": 0,
                "cycles_used": 0,
                "started_at": clock(),
                "status": "READY",
                "previous": None,
            }
            _write(receipt, state)

        def stop(reason):
            state["status"] = reason
            _write(receipt, state)
            return dict(state)

        if state["status"] in {
            "COMPLETED",
            "STOPPED",
            "BOUNDS_EXHAUSTED",
            "RETRY_EXHAUSTED",
            "GOVERNED_RUNTIME_STOPPED",
        }:
            return dict(state)
        while True:
            if (root / "STOP").exists():
                return stop("STOPPED")
            now = clock()
            remaining_seconds = min(
                bounds.expires_at_unix - now, bounds.max_total_seconds - (now - state["started_at"])
            )
            if now < state["started_at"] or remaining_seconds <= 0:
                return stop("BOUNDS_EXHAUSTED")
            prior = state.get("previous")
            if prior is not None:
                if not state.get("incident_id"):
                    fault = record_runtime_notice_v1(
                        evidence_root=root,
                        component="N1_HOST_RESTART",
                        run_id=bounds.host_id,
                        reason_code="HOST_PROCESS_INTERRUPTED",
                        action="Automatic checkpoint verification is in progress; no order is resent.",
                        owner_action_required=False,
                        notification_kind="FAULT",
                    )
                    state["incident_id"] = fault["event_id"]
                    _write(receipt, state)
                # Reuse the exact existing S6 proof, rather than treating process
                # death or an empty order list as a safe restart checkpoint.
                ledger_path = Path(prior["evidence_root"]) / LEDGER_FILENAME
                lock_path = Path(prior["lock_root"]) / LOCK_NAME
                try:
                    ledger = json.loads(ledger_path.read_text())
                    receipt_value = json.loads(lock_path.read_text())
                    proven = _dead_owner_wait_checkpoint_proven_v1(
                        receipt_value,
                        cursor_store_root=Path(prior["cursor_root"]),
                        native_id=prior["native_id"],
                    )
                except (OSError, ValueError, KeyError):
                    proven = False
                if not proven:
                    return stop("RECOVERY_CHECKPOINT_REQUIRED")
                consumed = ledger["s5_invoke_count"]
                if not 0 <= consumed <= prior["max_cycles"]:
                    return stop("RECOVERY_CHECKPOINT_REQUIRED")
                state["cycles_used"] = prior["cycles_before"] + consumed
            remaining_cycles = bounds.max_total_cycles - state["cycles_used"]
            if remaining_cycles <= 0:
                return stop("BOUNDS_EXHAUSTED")
            if (
                state["attempts"]
                and not bounded_retry_policy_v1(
                    attempt=state["attempts"] - 1,
                    automatic_recovery_allowed=True,
                )["retry_allowed"]
            ):
                return stop("RETRY_EXHAUSTED")
            from src.governance.current_continuous_run_policy_v1 import (
                standing_continuous_run_authorized_v1,
            )
            from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
                validate_bounded_continuous_run_owner_go_decision_v1,
            )

            repo = Path(__file__).resolve().parents[3]
            valid_go, _ = validate_bounded_continuous_run_owner_go_decision_v1(
                repo_root=repo,
                baseline_origin_main_sha=bounds.repository_sha,
            )
            if not valid_go or not standing_continuous_run_authorized_v1(repo_root=repo):
                return stop("GOVERNED_RUNTIME_STOPPED")
            evidence = root / "attempts" / str(state["attempts"] + 1)
            request = request_factory(state["attempts"] + 1, evidence)
            config, authorization = request["config"], request["authorization"]
            if (
                request["origin_main_sha"] != bounds.repository_sha
                or Path(config.evidence_root).resolve() != evidence
                or request.get("skip_owner_go_validation") is True
                or unattended_request_digest_v1(request) != bounds.runtime_config_digest
            ):
                raise ValueError("HOST_RESTART_REQUEST_BINDING_MISMATCH")
            # Account/lane/private roots must not follow the new evidence folder.
            roots = {
                key: str(Path(getattr(config, key)).resolve())
                for key in ("private_store_root", "public_store_root", "lane_state_root")
            }
            if state.get("roots") not in (None, roots):
                raise ValueError("HOST_RESTART_STATE_ROOT_CHANGED")
            state["roots"] = roots
            request["authorization"] = replace(
                authorization,
                max_cycles_per_run=min(authorization.max_cycles_per_run, remaining_cycles),
                max_run_duration_seconds=min(
                    authorization.max_run_duration_seconds, remaining_seconds
                ),
            )
            original_cancel = request.get("cancel_requested")
            request["cancel_requested"] = lambda: (
                (root / "STOP").exists() or (original_cancel is not None and original_cancel())
            )
            from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
                build_s8_occupied_lane_pairs_v1,
            )

            pairs = build_s8_occupied_lane_pairs_v1(
                lane_state_root=config.lane_state_root, bound=request["bound"]
            )
            cursor = Path(pairs["LANE_1"][0].lane_state_root)
            shared_lock = config.lock_root or (config.evidence_root / "continuous_lock")
            if state.get("shared_lock") not in (None, str(Path(shared_lock).resolve())):
                raise ValueError("HOST_RESTART_SHARED_LOCK_CHANGED")
            state["shared_lock"] = str(Path(shared_lock).resolve())
            state["attempts"] += 1
            state["status"] = "RUNNING"
            state["previous"] = {
                "evidence_root": str(evidence),
                "cursor_root": str(cursor.resolve()),
                "lock_root": state["shared_lock"],
                "native_id": authorization.native_id,
                "cycles_before": state["cycles_used"],
                "max_cycles": request["authorization"].max_cycles_per_run,
            }
            _write(receipt, state)
            try:
                result = run_n1_standing_pre_external_supervisor_v1(**request)
            except (TimeoutError, ConnectionError):
                record_runtime_notice_v1(
                    evidence_root=root,
                    component="N1_HOST_RESTART",
                    run_id=bounds.host_id,
                    reason_code="HOST_TRANSPORT_RECOVERY_PENDING",
                    action="Recheck the durable S6 checkpoint before automatic technical restart.",
                    owner_action_required=False,
                    notification_kind="FAULT",
                )
                sleeper(min(bounds.wait_interval_seconds, max(0, remaining_seconds)))
                continue
            state["cycles_used"] += result.trace.governed_cycle_count
            state["previous"] = None
            state["last_disposition"] = result.trace.terminal_disposition
            if (root / "STOP").exists():
                return stop("STOPPED")
            if result.ok:
                # Successful PRE_EXTERNAL is a deliberate terminal, not a crash.
                if state["attempts"] > 1:
                    record_runtime_notice_v1(
                        evidence_root=root,
                        component="N1_HOST_RESTART",
                        run_id=bounds.host_id,
                        reason_code="HOST_TECHNICAL_RECOVERY_VERIFIED",
                        action="A fresh governed N1 cycle completed after technical restart.",
                        owner_action_required=False,
                        notification_kind="RECOVERED",
                        extra={
                            "incident_id": state["incident_id"],
                            "recovery_scope": "N1_GOVERNED_PRE_EXTERNAL_PROCESSING",
                            "cycles_used": state["cycles_used"],
                        },
                    )
                return stop("COMPLETED")
            return stop("GOVERNED_RUNTIME_STOPPED")


def load_host_service_manifest_v1(path: Path):
    """A deployment must explicitly register its governed real source factory."""
    import re

    value = json.loads(Path(path).read_text())
    if set(value) != {
        "schema",
        "bounds",
        "state_root",
        "repository_root",
        "runtime_factory",
        "runtime_request_config",
    }:
        raise ValueError("HOST_SERVICE_MANIFEST_SHAPE_INVALID")
    if value["schema"] != "n1_unattended_host_service.v1":
        raise ValueError("HOST_SERVICE_MANIFEST_SCHEMA_INVALID")
    factory = value["runtime_factory"]
    if (
        not isinstance(factory, str)
        or re.fullmatch(r"src\.ops\.[a-zA-Z0-9_.]+:[a-zA-Z_][a-zA-Z0-9_]*", factory) is None
    ):
        raise ValueError("HOST_SERVICE_GOVERNED_SOURCE_FACTORY_REQUIRED")
    repo = Path(value["repository_root"]).resolve()
    if repo != Path(__file__).resolve().parents[3]:
        raise ValueError("HOST_SERVICE_CHECKOUT_MISMATCH")
    module, symbol = factory.split(":")
    source = repo.joinpath(*module.split(".")).with_suffix(".py")
    if not source.is_file() or not source.resolve().is_relative_to(repo / "src/ops"):
        raise ValueError("HOST_SERVICE_SOURCE_FACTORY_MISSING")
    state = Path(value["state_root"])
    if not state.is_absolute() or not (repo / "scripts/pt").is_file():
        raise ValueError("HOST_SERVICE_CANONICAL_PATH_REQUIRED")
    bounds = UnattendedHostBoundsV1(**value["bounds"])
    bounds.validate_v1()
    return value, bounds


def host_service_v1(*, manifest_path: Path, action: str, output_path: Path | None = None):
    """Canonical CLI adapter. Preparing a plist never loads a macOS service."""
    import importlib
    import plistlib

    value, bounds = load_host_service_manifest_v1(manifest_path)
    if action == "validate":
        return {
            "ok": True,
            "manifest_valid": True,
            "runtime_ports_validated": False,
            "service_activated": False,
            "external_effect_authorized": False,
        }
    if action == "prepare":
        if output_path is None:
            raise ValueError("HOST_SERVICE_OUTPUT_PATH_REQUIRED")
        repo = Path(value["repository_root"])
        root = Path(value["state_root"])
        payload = {
            "Label": "de.peaktrade.n1-host.v1",
            "ProgramArguments": [
                str(repo / "scripts/pt"),
                str(repo / "scripts/ops/peak_trade_runtime.py"),
                "--repository-root",
                str(repo),
                "host-service",
                "run",
                "--manifest",
                str(Path(manifest_path).resolve()),
            ],
            "WorkingDirectory": str(repo),
            "RunAtLoad": True,
            "KeepAlive": {"SuccessfulExit": False},
            "ThrottleInterval": 60,
            "ProcessType": "Background",
            "Umask": 0o077,
            "StandardOutPath": str(root.parent / "host-service.stdout.log"),
            "StandardErrorPath": str(root.parent / "host-service.stderr.log"),
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(output_path).open("xb") as stream:
            plistlib.dump(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        Path(output_path).chmod(0o600)
        return {"ok": True, "plist_path": str(output_path), "service_activated": False}
    if action != "run":
        raise ValueError("HOST_SERVICE_ACTION_INVALID")

    # The real adapter supplies existing N1 kwargs; no fixture/default balance,
    # test profile, arbitrary shell command or new trading grant is synthesized.
    def request_factory(attempt, evidence):
        module, symbol = value["runtime_factory"].split(":")
        factory = getattr(importlib.import_module(module), symbol)
        return factory(
            attempt_index=attempt,
            evidence_root=evidence,
            runtime_config=value["runtime_request_config"],
        )

    result = run_unattended_n1_host_v1(
        bounds=bounds,
        state_root=Path(value["state_root"]),
        request_factory=request_factory,
    )
    return {
        "ok": result["status"]
        in {
            "COMPLETED",
            "STOPPED",
            "BOUNDS_EXHAUSTED",
            "RETRY_EXHAUSTED",
            "GOVERNED_RUNTIME_STOPPED",
        },
        "result": result,
        "service_activated": False,
        "external_effect_authorized": False,
    }
