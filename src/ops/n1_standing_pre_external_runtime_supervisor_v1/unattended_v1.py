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
import sqlite3
import time
import uuid

from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    capture_process_identity,
    read_local_boot_identity_v1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    ProcessIdentityMismatchError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    read_dead_owner_wait_ledger_v1,
    REASON_MANAGED_FILEGATE_ACTIVE_UNPROVEN,
    REASON_MANAGED_FILEGATE_REVISION_CHANGED,
    LEDGER_FILENAME,
    LOCK_AUTHORIZATION_ID,
    LOCK_NAME,
    ABSOLUTE_MAX_CYCLES_PER_RUN,
    ABSOLUTE_MAX_RUN_DURATION_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    cursor_last_accepted_c1_venue_event_time_v1,
    load_current_productive_c1_cursor_or_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.gates.risk_gate import (
    canonical_kill_switch_state_path,
    kill_switch_should_block_trading,
    kill_switch_state_path_from_env,
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
from .errors_v1 import StandingSupervisorError


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


def _proven_wait_checkpoint(root, state, *, boot_identity):
    prior = state["previous"]
    try:
        process = prior["process_identity"]
        pid = process["pid"]
        if (
            not boot_identity
            or not prior["boot_identity"]
            or type(pid) is not int
            or pid <= 0
            or type(process["pgid"]) is not int
            or process["pgid"] <= 0
            or not isinstance(process["process_start_identity"], str)
            or not process["process_start_identity"]
            or not isinstance(process["cmdline_fingerprint"], str)
            or len(process["cmdline_fingerprint"]) != 64
        ):
            return None, "HOST_RESTART_PROCESS_OR_BOOT_UNPROVEN"
        evidence = root / "attempts" / str(state["attempts"])
        cursor_root = Path(state["roots"]["lane_state_root"]) / "LANE_1"
        ledger_path = evidence / LEDGER_FILENAME
        lock_path = Path(state["shared_lock"]) / LOCK_NAME
        if any(path.resolve() != path for path in (ledger_path, lock_path, cursor_root)) or (
            prior["evidence_root"] != str(evidence)
            or prior["lock_root"] != str(lock_path.parent)
            or prior["cursor_root"] != str(cursor_root)
        ):
            return None, "HOST_RESTART_CHECKPOINT_SCOPE_CHANGED"
        retired = not lock_path.exists()
        if retired:
            from src.ops.managed_filegate_v1 import configured_filegate_writer_v1

            writer = configured_filegate_writer_v1(Path(prior["filegate_path"]))
            anchor = None if writer is None else writer.read_host_checkpoint_v1(lock_path=lock_path)
            if not isinstance(anchor, dict) or "retired_lock_receipt" not in anchor:
                return None, "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"
            lock = json.loads(anchor["retired_lock_receipt"])
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            except OSError:
                return None, "HOST_RESTART_PREVIOUS_OWNER_UNPROVEN"
            else:
                # A reused PID still requires explicit retirement of its claim.
                return None, "HOST_RESTART_PREVIOUS_PID_PRESENT"
            lock = json.loads(lock_path.read_bytes())
        context = lock["recovery_context"]
        owner = "current_productive_governed_continuous_cycle_orchestrator_v1"
        if (
            lock.get("pid") != pid
            or lock.get("owner") != owner
            or lock.get("writer_identity") != f"{owner}:{LOCK_AUTHORIZATION_ID}"
            or lock.get("authorization_id") != LOCK_AUTHORIZATION_ID
            or not lock.get("claim_id")
            or context.get("evidence_root") != str(evidence)
            or context.get("process_identity") != process
            or context.get("boot_identity") != prior["boot_identity"]
        ):
            blocker = (
                "HOST_RESTART_PROCESS_OR_BOOT_UNPROVEN"
                if prior["boot_identity"] != boot_identity
                else "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"
            )
            return None, blocker
        other_boot = prior["boot_identity"] != boot_identity
        ledger = read_dead_owner_wait_ledger_v1(
            lock,
            cursor_store_root=cursor_root,
            native_id=prior["native_id"],
            lock_path=lock_path,
            filegate_path=Path(prior["filegate_path"]),
            repository_sha=prior.get("repository_sha"),
            require_independent=other_boot,
            retired=retired,
        )
        if ledger is None:
            return None, (
                "HOST_RESTART_PROCESS_OR_BOOT_UNPROVEN"
                if other_boot
                else "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"
            )
        cursor, _ = load_current_productive_c1_cursor_or_reason_v1(cursor_root)
        floor = cursor_last_accepted_c1_venue_event_time_v1(cursor)
        consumed = ledger["s5_invoke_count"]
        if (
            not math.isfinite(floor)
            or cursor.get("venue_native_id") != prior["native_id"]
            or floor != ledger["last_accepted_c1"]
            or type(consumed) is not int
            or not 0 <= consumed <= prior["max_cycles"]
            or prior["cycles_before"] != state["cycles_used"]
        ):
            return None, "HOST_RESTART_CHECKPOINT_CYCLE_OR_CURSOR_CHANGED"
        return (consumed, floor), None
    except (AttributeError, OSError, OverflowError, TypeError, ValueError, KeyError, sqlite3.Error):
        return None, "HOST_RESTART_CHECKPOINT_UNREADABLE"


def _filegate_revision(expected_path):
    """Return the current admissible revision for one pre-external attempt."""
    try:
        path = Path(canonical_kill_switch_state_path()).resolve()
        if (
            path != expected_path
            or os.environ.get("PEAK_KILL_SWITCH") == "1"
            or kill_switch_should_block_trading(explicit_active=False)
        ):
            return None
        if kill_switch_state_path_from_env() is None and not path.exists():
            return "UNCONFIGURED"  # Legacy unconfigured, pre-external host.
        raw = path.read_bytes()
        evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
        if (
            evidence.evidence_status == "TRUSTED_PRESENT"
            and evidence.state_name == "ACTIVE"
            and evidence.blocked is False
            and evidence.boolean_reader_blocked is False
            and path.read_bytes() == raw
            and Path(canonical_kill_switch_state_path()).resolve() == expected_path
            and os.environ.get("PEAK_KILL_SWITCH") != "1"
        ):
            return sha256(raw).hexdigest()
    except (OSError, RuntimeError):
        pass
    return None


def attest_managed_n1_wait_checkpoint_v1(
    *, writer, stop, state_root, bounds, expires_at, key, cause=None
):
    """Sign the actual N1 takeover checkpoint only after the old writer is fenced."""
    from src.ops.filegate_recovery_authority_v1 import (
        FilegateAuthorityError,
        attest_filegate_owner_evidence_v1,
    )
    from src.ops.managed_filegate_v1 import ManagedFilegateV1

    if (
        type(writer) is not ManagedFilegateV1
        or (cause is not None and (cause != "R02" or cause not in stop["causes"]))
        or type(bounds) is not UnattendedHostBoundsV1
        or not state_root.is_absolute()
        or state_root.resolve() != state_root
        or writer.inspect_stop_v1() != stop
    ):
        raise FilegateAuthorityError("HOST_RECOVERY_SCOPE_UNPROVEN")
    bounds.validate_v1()
    path = state_root / "host_restart_state_v1.json"
    if path.resolve() != path or not path.is_file():
        raise FilegateAuthorityError("HOST_RECOVERY_SCOPE_UNPROVEN")
    raw = path.read_bytes()
    state = json.loads(raw)
    prior = state["previous"]
    if (
        not isinstance(prior, dict)
        or state["binding"]
        != sha256(json.dumps(bounds.__dict__, sort_keys=True).encode()).hexdigest()
        or prior["filegate_path"] != str(writer.state_path)
        or prior["native_id"] not in stop["scope"]["instruments"]
        or stop["scope"]["host"]
        != str(Path(state["roots"]["private_store_root"]) / "portfolio_budget_host_v1")
        or expires_at > bounds.expires_at_unix
    ):
        raise FilegateAuthorityError("HOST_RECOVERY_SCOPE_UNPROVEN")
    checkpoint, _ = _proven_wait_checkpoint(
        state_root, state, boot_identity=read_local_boot_identity_v1()
    )
    if checkpoint is None or writer.inspect_stop_v1() != stop or path.read_bytes() != raw:
        raise FilegateAuthorityError("HOST_RECOVERY_CHECKPOINT_UNPROVEN")
    digest = sha256(
        raw + json.dumps(checkpoint, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    return attest_filegate_owner_evidence_v1(
        role="HOST" if cause is None else "CAUSE",
        cause=cause,
        stop=stop,
        evidence_sha256=digest,
        observed_at=time.time(),
        expires_at=expires_at,
        key=key,
    )


class _FilegateObservationSource:
    def __init__(self, source, *, path, revision):
        self.source = source
        self.path = path
        self.revision = revision

    def poll(self):
        if _filegate_revision(self.path) != self.revision:
            return None
        observation = self.source.poll()
        return observation if _filegate_revision(self.path) == self.revision else None


class _FilegateRevisionChanged(RuntimeError):
    pass


def _filegate_cycle_evaluator(evaluator, *, path, revision):
    def evaluate(cycle_index):
        if _filegate_revision(path) != revision:
            raise _FilegateRevisionChanged("HOST_RESTART_FILEGATE_BLOCKED")
        result = evaluator(cycle_index)
        if _filegate_revision(path) != revision:
            raise _FilegateRevisionChanged("HOST_RESTART_FILEGATE_BLOCKED")
        return result

    return evaluate


def run_unattended_n1_host_v1(
    *,
    bounds: UnattendedHostBoundsV1,
    state_root: Path,
    request_factory,
    clock=time.time,
    sleeper=time.sleep,
    fault_recovery=None,
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
        boot_identity = read_local_boot_identity_v1()
        filegate = Path(canonical_kill_switch_state_path()).resolve()
        if fault_recovery is not None:
            from src.ops.managed_fault_recovery_v1 import ManagedFaultRecoveryV1
            from src.ops.managed_filegate_v1 import configured_filegate_writer_v1

            configured = configured_filegate_writer_v1(filegate)
            if (
                type(fault_recovery) is not ManagedFaultRecoveryV1
                or configured is None
                or fault_recovery.writer.state_path != filegate
                or fault_recovery.writer.root != configured.root
            ):
                raise ValueError("HOST_FAULT_RECOVERY_FILEGATE_SCOPE_UNPROVEN")
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
            if fault_recovery is not None and _filegate_revision(filegate) is None:
                state["last_fault_observation"] = fault_recovery.poll_v1()
                state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                stop("RECOVERY_CHECKPOINT_REQUIRED")
                if (root / "STOP").exists():
                    return stop("STOPPED")
                if _filegate_revision(filegate) is None:
                    sleeper(min(bounds.wait_interval_seconds, remaining_seconds))
                    continue
            prior = state.get("previous")
            cycles_used = state["cycles_used"]
            cursor_floor = None
            if state["attempts"] and not isinstance(prior, dict):
                state["checkpoint_blocker"] = "HOST_RESTART_PREVIOUS_ATTEMPT_UNPROVEN"
                return stop("RECOVERY_CHECKPOINT_REQUIRED")
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
                checkpoint, blocker = _proven_wait_checkpoint(
                    root, state, boot_identity=boot_identity
                )
                if checkpoint is None:
                    state["checkpoint_blocker"] = blocker
                    blocked = stop("RECOVERY_CHECKPOINT_REQUIRED")
                    if fault_recovery is None:
                        return blocked
                    sleeper(min(bounds.wait_interval_seconds, remaining_seconds))
                    continue
                if prior.get("filegate_path") != str(filegate):
                    state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_SCOPE_CHANGED"
                    return stop("RECOVERY_CHECKPOINT_REQUIRED")
                consumed, cursor_floor = checkpoint
                cycles_used = prior["cycles_before"] + consumed
            filegate_revision = _filegate_revision(filegate)
            if filegate_revision is None:
                state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                return stop("RECOVERY_CHECKPOINT_REQUIRED")
            remaining_cycles = bounds.max_total_cycles - cycles_used
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
            if cursor_floor is not None and (
                authorization.expected_cursor_floor != cursor_floor
                or authorization.native_id != prior["native_id"]
            ):
                state["checkpoint_blocker"] = "HOST_RESTART_REQUEST_CURSOR_CHANGED"
                return stop("RECOVERY_CHECKPOINT_REQUIRED")
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
                (root / "STOP").exists()
                or _filegate_revision(filegate) != filegate_revision
                or (original_cancel is not None and original_cancel())
            )
            if request.get("observation_source") is not None:
                request["observation_source"] = _FilegateObservationSource(
                    request["observation_source"], path=filegate, revision=filegate_revision
                )
            if request.get("f1_m9_cycle_evaluator") is not None:
                request["f1_m9_cycle_evaluator"] = _filegate_cycle_evaluator(
                    request["f1_m9_cycle_evaluator"], path=filegate, revision=filegate_revision
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
            if _filegate_revision(filegate) != filegate_revision:
                state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                return stop("RECOVERY_CHECKPOINT_REQUIRED")
            try:
                process = capture_process_identity(os.getpid()).to_dict()
            except ProcessIdentityMismatchError:
                process = None  # First run still follows the original admission.
            state["shared_lock"] = str(Path(shared_lock).resolve())
            state["attempts"] += 1
            state["cycles_used"] = cycles_used
            state["status"] = "RUNNING"
            state.pop("checkpoint_blocker", None)
            state["previous"] = {
                "evidence_root": str(evidence),
                "cursor_root": str(cursor.resolve()),
                "lock_root": state["shared_lock"],
                "native_id": authorization.native_id,
                "cycles_before": state["cycles_used"],
                "max_cycles": request["authorization"].max_cycles_per_run,
                "process_identity": process,
                "boot_identity": boot_identity,
                "filegate_path": str(filegate),
                "filegate_revision": filegate_revision,
                "repository_sha": bounds.repository_sha,
            }
            _write(receipt, state)
            try:
                result = run_n1_standing_pre_external_supervisor_v1(**request)
            except _FilegateRevisionChanged:
                state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                if fault_recovery is not None and _filegate_revision(filegate) is None:
                    stop("RECOVERY_CHECKPOINT_REQUIRED")
                    continue
                return stop("GOVERNED_RUNTIME_STOPPED")
            except StandingSupervisorError as exc:
                if fault_recovery is None:
                    raise
                if exc.reason_code in {
                    REASON_MANAGED_FILEGATE_ACTIVE_UNPROVEN,
                    REASON_MANAGED_FILEGATE_REVISION_CHANGED,
                }:
                    state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                elif (
                    exc.reason_code == "EXECUTION_GHOSV_SAFETY_HALT"
                    and _filegate_revision(filegate) is None
                ):
                    state["checkpoint_blocker"] = exc.reason_code
                else:
                    raise
                stop("RECOVERY_CHECKPOINT_REQUIRED")
                continue
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
            if fault_recovery is not None and _filegate_revision(filegate) is None:
                state["checkpoint_blocker"] = "HOST_RESTART_FILEGATE_BLOCKED"
                stop("RECOVERY_CHECKPOINT_REQUIRED")
                continue
            state["cycles_used"] += result.trace.governed_cycle_count
            state["previous"] = None
            state["last_disposition"] = result.trace.terminal_disposition
            if (root / "STOP").exists():
                return stop("STOPPED")
            if result.close_readback is not None:
                close = result.close_readback
                state["close_readback_status"] = close.status
                state["close_envelope_digest"] = close.envelope_digest
                state["close_booking_pending"] = (
                    "L10_CLOSE_NET_BOOKING_PENDING" in close.reason_codes
                )
                if close.net_booking is not None:
                    state["close_booking_digest"] = close.net_booking["booking_digest"]
                if result.counter_order_sizing is not None:
                    sizing = result.counter_order_sizing
                    state["counter_order_sizing"] = {
                        "status": sizing.status,
                        "first_blocker": sizing.first_blocker,
                        "venue_plan_authorized": sizing.venue_plan_authorized,
                    }
                return stop("GOVERNED_RUNTIME_STOPPED")
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
    required = {
        "schema",
        "bounds",
        "state_root",
        "repository_root",
        "runtime_factory",
        "runtime_request_config",
    }
    if set(value) not in (required, required | {"fault_recovery"}):
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
    recovery = value.get("fault_recovery")
    if "fault_recovery" in value:
        if (
            type(recovery) is not dict
            or set(recovery) != {"factory", "filegate_state_path", "authority_root", "config"}
            or type(recovery["config"]) is not dict
            or not isinstance(recovery["factory"], str)
            or re.fullmatch(r"src\.ops\.[a-zA-Z0-9_.]+:[a-zA-Z_][a-zA-Z0-9_]*", recovery["factory"])
            is None
        ):
            raise ValueError("HOST_FAULT_RECOVERY_MANIFEST_INVALID")
        recovery_module, _ = recovery["factory"].split(":")
        recovery_source = repo.joinpath(*recovery_module.split(".")).with_suffix(".py")
        if (
            not recovery_source.is_file()
            or not recovery_source.resolve().is_relative_to(repo / "src/ops")
            or any(
                type(recovery[key]) is not str
                or not Path(recovery[key]).is_absolute()
                or Path(recovery[key]).resolve() != Path(recovery[key])
                for key in ("filegate_state_path", "authority_root")
            )
        ):
            raise ValueError("HOST_FAULT_RECOVERY_SOURCE_UNPROVEN")
    bounds = UnattendedHostBoundsV1(**value["bounds"])
    bounds.validate_v1()
    return value, bounds


def host_service_v1(
    *,
    manifest_path: Path,
    action: str,
    output_path: Path | None = None,
    owner_role: str | None = None,
    owner_seed_path: Path | None = None,
):
    """Canonical CLI adapter. Preparing a plist never loads a macOS service."""
    import importlib
    import plistlib

    value, bounds = load_host_service_manifest_v1(manifest_path)
    recovery = value.get("fault_recovery")
    recovery_env = (
        {
            "PEAK_KILL_SWITCH_STATE_PATH": recovery["filegate_state_path"],
            "PEAK_FILEGATE_AUTHORITY_ROOT": recovery["authority_root"],
        }
        if recovery is not None
        else {}
    )
    if action in {"owner-poll", "owner-run"}:
        from src.ops.managed_fault_recovery_v1 import run_standing_managed_owner_publisher_v1

        if recovery is None or recovery["factory"] != (
            "src.ops.managed_fault_recovery_v1:build_standing_managed_fault_recovery_v1"
        ):
            raise ValueError("HOST_FAULT_RECOVERY_OWNER_CONFIG_UNPROVEN")
        if any(os.environ.get(key, expected) != expected for key, expected in recovery_env.items()):
            raise ValueError("HOST_FAULT_RECOVERY_ENVIRONMENT_CHANGED")
        os.environ.update(recovery_env)
        return {
            "ok": True,
            "result": run_standing_managed_owner_publisher_v1(
                state_root=Path(value["state_root"]),
                bounds=bounds,
                runtime_config=recovery["config"],
                owner=owner_role,
                seed_path=owner_seed_path,
                once=action == "owner-poll",
            ),
            "service_activated": False,
            "external_effect_authorized": False,
        }
    if owner_role is not None or owner_seed_path is not None:
        raise ValueError("HOST_FAULT_RECOVERY_OWNER_ACTION_REQUIRED")
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
        if recovery_env:
            payload["EnvironmentVariables"] = recovery_env
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

    fault_recovery = None
    if recovery is not None:
        if any(os.environ.get(key, expected) != expected for key, expected in recovery_env.items()):
            raise ValueError("HOST_FAULT_RECOVERY_ENVIRONMENT_CHANGED")
        os.environ.update(recovery_env)
        module, symbol = recovery["factory"].split(":")
        factory = getattr(importlib.import_module(module), symbol)
        fault_recovery = factory(
            state_root=Path(value["state_root"]),
            runtime_config=recovery["config"],
        )

    result = run_unattended_n1_host_v1(
        bounds=bounds,
        state_root=Path(value["state_root"]),
        request_factory=request_factory,
        fault_recovery=fault_recovery,
    )
    if (
        fault_recovery is not None
        and result["status"] != "STOPPED"
        and _filegate_revision(fault_recovery.writer.state_path) is None
    ):
        root = Path(value["state_root"])
        fault_recovery.run_v1(
            stop_requested=(root / "STOP").exists,
            publish_observation=lambda observed: _write(
                root / "stopped_fault_observation_v1.json", observed
            ),
            allow_release=False,
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
