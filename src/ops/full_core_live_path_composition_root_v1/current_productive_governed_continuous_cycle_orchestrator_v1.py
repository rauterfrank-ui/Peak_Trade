"""CURRENT_PRODUCTIVE governed continuous-cycle sequencer.

PRIMARY_SEMANTIC_IDENTITY=governed_continuous_cycle_orchestrator_v1
HISTORICAL_COMPATIBILITY_LABEL=EH.S6 / S6 (navigation/tests only)

SEQUENCING AUTHORITY ONLY. Instantiates fresh S5 five-token cycle
authorizations under one bounded continuous Owner-GO. Does not duplicate
the S5 trading path. Does not compose, infer, mint, or execute POST.
Direct V5 remains forbidden. Network GET remains unauthorized.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import tempfile
import time
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    PendingDecisionContextV1,
)

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Protocol, Sequence

if TYPE_CHECKING:
    from .current_productive_post_position_close_v1 import CurrentPostPositionCloseContextV1

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_text,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    ProcessIdentityMismatchError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    capture_process_identity,
    read_local_boot_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT as S5_AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST as S5_AUTONOMY_CAN_POST,
    DISPOSITION_FAIL_CLOSED as S5_DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD as S5_DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT as S5_DISPOSITION_PRE_EXTERNAL_EFFECT,
    EG_OWNER_GO,
    GET_OWNER_GO,
    LEDGER_FILENAME as S5_LEDGER_FILENAME,
    OWNER_GO as S5_PERSIST_GO,
    RUNTIME_OWNER_GO as S5_RUNTIME_OWNER_GO,
    S5_V5_EXECUTE_NETWORK,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
    CurrentProductiveGovernedCycleOrchestratorError,
    CurrentProductiveGovernedCycleResultV1,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    OCCUPANCY_OWNER_GO,
    cursor_last_accepted_c1_venue_event_time_v1,
    load_current_productive_c1_cursor_or_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
    DISPOSITION_EMITTED,
    OWNER_GO as EH_SEAM_OWNER_GO,
    evaluate_current_productive_c1_observation_against_cursor_floor_v1,
    map_injected_candles_payload_to_current_productive_c1_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_get_budget_contract_v1 import (
    compute_max_canonical_continuous_poll_iterations_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_continuous_observation_budget_v1 import (
    ABSOLUTE_MAX_CYCLES_PER_RUN,
    ABSOLUTE_MAX_RUN_DURATION_SECONDS,
    HARD_CAP_MAX_CYCLES_PER_RUN,
    HARD_CAP_MAX_RUN_DURATION_SECONDS,
    PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
    PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    bounded_retry_policy_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    record_runtime_notice_v1,
)

PRIMARY_SEMANTIC_IDENTITY = "governed_continuous_cycle_orchestrator_v1"
HISTORICAL_COMPATIBILITY_LABEL = "EH.S6"
OWNER_GO = "OWNER_GO_EH_S6_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_OFFLINE_BIND_V1"
OWNER_GO_SCOPE = "S6_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_OFFLINE_BIND_ONLY"
OWNER_GO_STATUS = "CONSUMED"
RUNTIME_OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_V1"
RUNTIME_OWNER_GO_SCOPE = (
    "BOUNDED_REPEATED_INSTANTIATION_OF_EXISTING_S5_FIVE_TOKEN_CYCLE_AUTHORIZATION_ONLY"
)
RUNTIME_OWNER_GO_STATUS = "DEFINED_NOT_CONSUMED"
THIS_SLICE = "11.2.1.EH.S6_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_OFFLINE_BIND"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_SEAM_V1"
FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY = "BOUNDED_CONTINUOUS_SEQUENCING_TO_PRE_EXTERNAL_EFFECT_ONLY"
AUTONOMY_CAN_CHANGE_TRADING_LOGIC = False
AUTONOMY_CAN_RESELECT_DOWNSTREAM = False
AUTONOMY_CAN_MINT_PERMIT = False
AUTONOMY_CAN_POST = False
AUTONOMY_CAN_FORCE_ENTER = False
S6_V5_EXECUTE_NETWORK = False
CONTINUOUS_RUN_AUTHORIZED = False
CONTINUOUS_RUN_EXECUTED = False
S6_CONTINUOUS_RUNTIME_EXECUTED = False
PERSIST_GO_IS_RUNTIME_LICENSE = False
POST_COMPOSED_INTO_CONTINUOUS_GO = False
LEDGER_FILENAME = "governed_continuous_cycle_run_ledger_v1.json"
LOCK_NAME = "governed_continuous_cycle_run_exclusion.lock"
LOCK_AUTHORIZATION_ID = "CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_EXCLUSION_V1"
DISPOSITION_PRESENT = "PRESENT"
DISPOSITION_FAIL_CLOSED = "FAIL_CLOSED"
DISPOSITION_HOLD_CONTINUE = "HOLD_CONTINUE_CLOSED"
DISPOSITION_PRE_EXTERNAL_EFFECT = "PRE_EXTERNAL_EFFECT"
DISPOSITION_MAX_CYCLES = "MAX_CYCLES_BOUND_STOP"
DISPOSITION_MAX_DURATION = "MAX_DURATION_BOUND_STOP"
DISPOSITION_STALL = "STALL_BOUND_STOP"
DISPOSITION_CANCELLED = "CANCELLED_STOP"
STATE_IDLE = "IDLE"
STATE_IN_PROGRESS = "IN_PROGRESS"
STATE_WAITING_FOR_NEXT_C1 = "WAITING_FOR_NEXT_C1"
STATE_COMPLETED = "COMPLETED"
STATE_FAILED_STOP = "FAILED_STOP"
STATE_CANCELLED = "CANCELLED_STOP"
REASON_OWNER_GO_MISMATCH = "OWNER_GO_MISMATCH"
REASON_PERSIST_GO_NOT_RUNTIME_LICENSE = "PERSIST_GO_NOT_RUNTIME_LICENSE"
REASON_S5_GO_IS_NOT_CONTINUOUS_GO = "S5_CYCLE_GO_IS_NOT_CONTINUOUS_GO"
REASON_POST_GO_IN_CONTINUOUS_AUTHORIZATION = "POST_GO_IN_CONTINUOUS_AUTHORIZATION"
REASON_NETWORK_NOT_AUTHORIZED = "NETWORK_NOT_AUTHORIZED_THIS_SLICE"
REASON_INJECTED_SOURCE_REQUIRED = "INJECTED_OBSERVATION_SOURCE_REQUIRED_OFFLINE"
REASON_REPLAY = "CONTINUOUS_RUN_AUTHORIZATION_REPLAY"
REASON_PARTIAL_NOT_RESUMABLE = "PARTIAL_CONTINUOUS_RUN_NOT_RESUMABLE"
REASON_CONCURRENT_RUN = "CONCURRENT_CONTINUOUS_RUN"
REASON_STALE_OR_EQUAL_C1 = "STALE_OR_EQUAL_C1_REJECTED"
REASON_CONSUME_INSTANCE_REUSE = "CONSUMED_S5_INSTANCE_REUSE_FORBIDDEN"
REASON_UNBOUNDED_OR_INVALID_BOUND = "UNBOUNDED_OR_INVALID_SAFETY_BOUND"
REASON_EXCEEDS_HARD_CAP = "SAFETY_BOUND_EXCEEDS_VALIDATION_HARD_CAP"
REASON_BUSY_LOOP_FORBIDDEN = "BUSY_LOOP_FORBIDDEN"
REASON_HANG_GUARD = "ANTI_HANG_POLL_GUARD"
REASON_CURSOR_ADVANCE_FAILED = "CURSOR_MONOTONICITY_PERSIST_FAILED"
REASON_DIRECT_V5_PIN_DRIFT = "DIRECT_V5_PIN_DRIFT"
REASON_SEND_PIN_DRIFT = "SEND_AUTHORITY_DRIFT"
REASON_S5_INVOKE_COUNT_DRIFT = "S5_INVOKE_COUNT_NOT_ONE_PER_ACCEPTED_C1"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
DEFAULT_MAX_CYCLES_PER_RUN = 2
DEFAULT_MAX_RUN_DURATION_SECONDS = 90.0
# Productive policy defaults and absolute validation ceiling: observation budget module.
DEFAULT_WAIT_INTERVAL_SECONDS = 1.0
HARD_CAP_WAIT_INTERVAL_SECONDS = 15.0
DEFAULT_MAX_WAIT_FOR_NEXT_C1_SECONDS = 30.0
HARD_CAP_MAX_WAIT_FOR_NEXT_C1_SECONDS = 60.0
DEFAULT_STALL_SECONDS = 30.0
HARD_CAP_STALL_SECONDS = 60.0
MIN_POSITIVE_SECONDS = 0.001
BOUNDS_CLASS = "VALIDATION_DEFAULTS_NOT_PRODUCTIVE_POLICY"
REASON_MANAGED_FILEGATE_ACTIVE_UNPROVEN = "S6_MANAGED_FILEGATE_ACTIVE_UNPROVEN"
REASON_MANAGED_FILEGATE_REVISION_CHANGED = "S6_MANAGED_FILEGATE_REVISION_CHANGED"

S5CycleRunnerV1 = Callable[..., CurrentProductiveGovernedCycleResultV1]
TimeFnV1 = Callable[[], float]
SleepFnV1 = Callable[[float], None]
CancelFnV1 = Callable[[], bool]
IterationAuthorityGateV1 = Callable[[int], None]


class CurrentProductiveGovernedContinuousCycleOrchestratorError(ValueError):
    """Fail-closed continuous-cycle sequencing violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


class ManagedFilegateRevisionChangedV1(CurrentProductiveGovernedContinuousCycleOrchestratorError):
    """Yield the attempt to the stopped host observer when Safety changes."""


@dataclass(frozen=True)
class CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    continuous_owner_go: str
    native_id: str
    bar: str
    expected_cursor_floor: float
    max_cycles_per_run: int
    max_run_duration_seconds: float
    wait_interval_seconds: float
    max_wait_for_next_c1_seconds: float
    stall_seconds: float


@dataclass(frozen=True)
class InjectedContinuousObservationV1:
    candles_payload: Mapping[str, Any]
    occupancy_payloads: Mapping[str, Any]
    mark_price_payload: Mapping[str, Any] | None = None
    index_tickers_payload: Mapping[str, Any] | None = None
    mark_acquired_at_utc: str = ""


class ContinuousObservationSourceV1(Protocol):
    def poll(self) -> InjectedContinuousObservationV1 | None:
        """Return one injected observation or None when no C1 is available."""


@dataclass(frozen=True)
class ContinuousCycleRecordV1:
    cycle_index: int
    cycle_instance_id: str
    consume_instance_id: str
    evidence_root: str
    c1_venue_event_time: float
    s5_disposition: str
    s5_reason_code: str
    sequencing_owner_go: str
    get_owner_go: str
    eg_owner_go: str
    occupancy_owner_go: str
    t2_owner_go: str
    pending_decision_context: PendingDecisionContextV1 | None = None
    final_order_envelope: FinalOrderEnvelopeV1 | None = None
    envelope_created: bool = False
    envelope_identity: str = ""
    canonical_order_intent: Any | None = None
    position_management_execution_handoff: Any | None = None
    # Original producer reference only; not owner recovery or submit admission.
    portfolio_reservation_id: str = ""
    execution_plan_context: Any | None = None
    mark_venue_event_time: float | None = None
    mark_evidence_root: str = ""
    position_close_post_context: CurrentPostPositionCloseContextV1 | None = field(
        default=None, repr=False, compare=False
    )


@dataclass(frozen=True)
class CurrentProductiveGovernedContinuousCycleRunResultV1:
    disposition: str
    reason_code: str
    terminal_class: str
    continuous_go_status_after: str
    cycles_completed: int
    s5_invoke_count: int
    accepted_c1_count: int
    consume_instance_ids: tuple[str, ...]
    cycle_records: tuple[ContinuousCycleRecordV1, ...]
    last_accepted_c1: float | None
    cursor_floor_before: float | None
    cursor_floor_after: float | None
    permit_created: bool
    post_count: int
    external_effect_count: int
    first_genuine_blocker: str
    next_required_owner_decision: str
    lock_released: str
    ledger_state: str
    sequencer_elapsed_monotonic_seconds: float = 0.0
    extra: dict[str, str] = field(default_factory=dict)


def _token(value: bool) -> str:
    return TRUE_TOKEN if value else FALSE_TOKEN


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json_text(payload)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp.unlink(missing_ok=True)


def _binding_digest(
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
) -> str:
    material = "|".join(
        [
            authorization.continuous_owner_go,
            authorization.native_id,
            authorization.bar,
            str(float(authorization.expected_cursor_floor)),
            str(int(authorization.max_cycles_per_run)),
            str(float(authorization.max_run_duration_seconds)),
        ]
    )
    return sha256(material.encode("utf-8")).hexdigest()


def mint_continuous_run_id_v1(
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
) -> str:
    return _binding_digest(authorization)[:16]


def mint_s5_cycle_consume_instance_id_v1(
    *,
    run_id: str,
    cycle_index: int,
    c1_venue_event_time: float,
) -> str:
    material = f"{run_id}|{int(cycle_index)}|{float(c1_venue_event_time)}"
    return sha256(material.encode("utf-8")).hexdigest()


def _load_ledger(evidence_root: Path) -> dict[str, Any]:
    path = Path(evidence_root) / LEDGER_FILENAME
    if not path.is_file():
        return {"state": STATE_IDLE}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {"state": STATE_FAILED_STOP, "reason_code": "LEDGER_INVALID"}
    if not isinstance(payload, dict):
        return {"state": STATE_FAILED_STOP, "reason_code": "LEDGER_INVALID"}
    return payload


def _dead_owner_wait_checkpoint_proven_v1(
    receipt: Mapping[str, Any], *, cursor_store_root: Path, native_id: str
) -> bool:
    """Reclaim exclusion only between completed cycles, never an uncertain S5."""
    return (
        read_dead_owner_wait_ledger_v1(
            receipt, cursor_store_root=cursor_store_root, native_id=native_id
        )
        is not None
    )


def read_dead_owner_wait_ledger_v1(
    receipt: Mapping[str, Any],
    *,
    cursor_store_root: Path,
    native_id: str,
    lock_path: Path | None = None,
    filegate_path: Path | None = None,
    repository_sha: str | None = None,
    require_independent: bool = False,
    retired: bool = False,
) -> dict | None:
    """Verify the original WAIT after process death or independently recorded retirement."""
    from src.ops.managed_filegate_v1 import (
        configured_filegate_writer_v1,
        managed_filegate_configured_v1,
    )

    try:
        context = receipt["recovery_context"]
        root = Path(context["evidence_root"])
        if not root.is_absolute() or root.resolve() != root:
            return None
        if context["cursor_store_root"] != str(Path(cursor_store_root).resolve()):
            return None
        ledger_path = root / LEDGER_FILENAME
        if ledger_path.resolve() != ledger_path:
            return None
        ledger_raw = ledger_path.read_bytes()
        ledger = json.loads(ledger_raw)
        if ledger.get("occupied_mark_only") is True:
            # The C1 checkpoint does not attest the occupied Scope snapshot.
            return None
        if (
            retired
            or require_independent
            or (filegate_path is not None and managed_filegate_configured_v1(filegate_path))
        ):
            if filegate_path is None or lock_path is None:
                return None
            writer = configured_filegate_writer_v1(filegate_path)
            anchor = None if writer is None else writer.read_host_checkpoint_v1(lock_path=lock_path)
            if retired and (lock_path.exists() or lock_path.is_symlink()):
                return None
            lock_raw = (
                anchor["retired_lock_receipt"].encode()
                if retired and isinstance(anchor, dict)
                else lock_path.read_bytes()
            )
            if (
                not isinstance(anchor, dict)
                or json.loads(lock_raw) != receipt
                or anchor.get("lock_sha256") != sha256(lock_raw).hexdigest()
                or anchor.get("repository_sha") != repository_sha
            ):
                return None
            if sha256(ledger_raw).hexdigest() != anchor["ledger_sha256"]:
                successor = anchor["wait_ledger"]
                if (
                    sha256(ledger_raw).hexdigest() != anchor["prior_ledger_sha256"]
                    or ledger["state"] != STATE_IN_PROGRESS
                    or ledger["reason_code"] != "S5_CYCLE_STARTING"
                    or sha256(canonical_json_text(successor).encode()).hexdigest()
                    != anchor["ledger_sha256"]
                    or successor["s5_invoke_count"] != ledger["s5_invoke_count"] + 1
                    or successor["consumed_instance_ids"][:-1] != ledger["consumed_instance_ids"]
                    or successor["last_accepted_c1"] <= ledger["last_accepted_c1"]
                ):
                    return None
                cycle_id = mint_s5_cycle_consume_instance_id_v1(
                    run_id=ledger["run_id"],
                    cycle_index=successor["s5_invoke_count"],
                    c1_venue_event_time=successor["last_accepted_c1"],
                )
                s5_path = root / "cycles" / cycle_id / "s5" / S5_LEDGER_FILENAME
                if (
                    cycle_id != successor["consumed_instance_ids"][-1]
                    or s5_path.resolve() != s5_path
                ):
                    return None
                s5_digest = sha256(s5_path.read_bytes()).hexdigest()
                if s5_digest != anchor["s5_ledger_sha256"]:
                    terminal = anchor["s5_terminal_ledger"]
                    if (
                        s5_digest != anchor["prior_s5_ledger_sha256"]
                        or sha256(canonical_json_text(terminal).encode()).hexdigest()
                        != anchor["s5_ledger_sha256"]
                    ):
                        return None
                ledger = successor
            if anchor.get("cursor_sha256") != ledger["checkpoint_cursor_sha256"]:
                return None
        consumed = ledger.get("consumed_instance_ids")
        if (
            ledger.get("state") == STATE_WAITING_FOR_NEXT_C1
            and ledger.get("binding_digest") == context["binding_digest"]
            and ledger.get("native_id") == native_id
            and ledger.get("continuous_owner_go") == RUNTIME_OWNER_GO
            and ledger.get("POST_COUNT") == "0"
            and ledger.get("PERMIT_CREATED") == FALSE_TOKEN
            and ledger.get("EXTERNAL_EFFECT_COUNT") == "0"
            and isinstance(consumed, list)
            and type(ledger.get("s5_invoke_count")) is int
            and ledger["s5_invoke_count"] == len(consumed)
            and len(set(consumed)) == len(consumed)
            and ledger.get("checkpoint_cursor_sha256")
            == sha256((Path(cursor_store_root) / CURSOR_FILENAME).read_bytes()).hexdigest()
        ):
            return ledger
    except (
        AttributeError,
        IndexError,
        OSError,
        KeyError,
        OverflowError,
        TypeError,
        ValueError,
        sqlite3.Error,
    ):
        pass
    return None


def _assert_standing_pins() -> None:
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("MAX_POSITIONS_DRIFT")
    if STEP_29Q_PLAN_ONLY != "PLAN_ONLY":
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("STEP_29Q_DRIFT")
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(REASON_SEND_PIN_DRIFT)
    if AUTONOMY_CAN_MINT_PERMIT is True or AUTONOMY_CAN_POST is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("AUTONOMY_SEND_DRIFT")
    if AUTONOMY_CAN_FORCE_ENTER is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("AUTO_ENTER_DRIFT")
    if DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT != "FORBIDDEN":
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(REASON_DIRECT_V5_PIN_DRIFT)
    if S5_V5_EXECUTE_NETWORK is True or S6_V5_EXECUTE_NETWORK is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            "V5_EXECUTE_NETWORK_PIN_DRIFT"
        )
    if S5_AUTONOMY_CAN_MINT_PERMIT is True or S5_AUTONOMY_CAN_POST is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("S5_SEND_PIN_DRIFT")
    if POST_COMPOSED_INTO_CONTINUOUS_GO is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("POST_COMPOSE_PIN_DRIFT")
    if CONTINUOUS_RUN_AUTHORIZED is True or CONTINUOUS_RUN_EXECUTED is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            "CONTINUOUS_RUNTIME_PIN_DRIFT"
        )


def _require_positive_int(*, name: str, value: int, hard_cap: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, name
        )
    if value > hard_cap:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_EXCEEDS_HARD_CAP, name
        )


def _require_positive_seconds(*, name: str, value: float, hard_cap: float) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, name
        ) from exc
    if not math.isfinite(numeric):
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, name
        )
    if numeric <= 0 or numeric < MIN_POSITIVE_SECONDS:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, name
        )
    if numeric > hard_cap:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_EXCEEDS_HARD_CAP, name
        )


def _validate_authorization(
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
) -> None:
    if authorization.continuous_owner_go == OWNER_GO:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_PERSIST_GO_NOT_RUNTIME_LICENSE
        )
    if authorization.continuous_owner_go == S5_PERSIST_GO:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_PERSIST_GO_NOT_RUNTIME_LICENSE
        )
    if authorization.continuous_owner_go == S5_RUNTIME_OWNER_GO:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_S5_GO_IS_NOT_CONTINUOUS_GO
        )
    if authorization.continuous_owner_go == POST_NEXT_OWNER_GO:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_POST_GO_IN_CONTINUOUS_AUTHORIZATION
        )
    if authorization.continuous_owner_go != RUNTIME_OWNER_GO:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(REASON_OWNER_GO_MISMATCH)
    if authorization.bar != "1m":
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("BAR_MISMATCH")
    if not str(authorization.native_id or "").strip():
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError("NATIVE_ID_MISSING")
    _require_positive_int(
        name="MAX_CYCLES_PER_RUN",
        value=authorization.max_cycles_per_run,
        hard_cap=ABSOLUTE_MAX_CYCLES_PER_RUN,
    )
    _require_positive_seconds(
        name="MAX_RUN_DURATION_SECONDS",
        value=authorization.max_run_duration_seconds,
        hard_cap=ABSOLUTE_MAX_RUN_DURATION_SECONDS,
    )
    _require_positive_seconds(
        name="WAIT_INTERVAL_SECONDS",
        value=authorization.wait_interval_seconds,
        hard_cap=HARD_CAP_WAIT_INTERVAL_SECONDS,
    )
    _require_positive_seconds(
        name="MAX_WAIT_FOR_NEXT_C1_SECONDS",
        value=authorization.max_wait_for_next_c1_seconds,
        hard_cap=HARD_CAP_MAX_WAIT_FOR_NEXT_C1_SECONDS,
    )
    _require_positive_seconds(
        name="STALL_SECONDS",
        value=authorization.stall_seconds,
        hard_cap=HARD_CAP_STALL_SECONDS,
    )
    if float(authorization.wait_interval_seconds) <= 0:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(REASON_BUSY_LOOP_FORBIDDEN)


def bind_s6_governed_continuous_cycle_orchestrator_offline_v1(
    *,
    owner_go: str,
) -> dict[str, str]:
    if owner_go != OWNER_GO:
        return {
            "disposition": DISPOSITION_FAIL_CLOSED,
            "reason_code": REASON_OWNER_GO_MISMATCH,
        }
    return {
        "disposition": DISPOSITION_PRESENT,
        "reason_code": "",
        "owner_go": OWNER_GO,
        "owner_go_scope": OWNER_GO_SCOPE,
        "runtime_owner_go": RUNTIME_OWNER_GO,
        "runtime_owner_go_scope": RUNTIME_OWNER_GO_SCOPE,
        "runtime_owner_go_status": RUNTIME_OWNER_GO_STATUS,
        "persist_go_is_runtime_license": FALSE_TOKEN,
        "post_composed_into_continuous_go": FALSE_TOKEN,
        "s5_runtime_owner_go": S5_RUNTIME_OWNER_GO,
        "direct_v5": DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
        "continuous_run_authorized": FALSE_TOKEN,
        "continuous_run_executed": FALSE_TOKEN,
        "max_cycles_per_run_default": str(DEFAULT_MAX_CYCLES_PER_RUN),
        "max_cycles_per_run_hard_cap": str(ABSOLUTE_MAX_CYCLES_PER_RUN),
        "max_run_duration_seconds_default": str(DEFAULT_MAX_RUN_DURATION_SECONDS),
        "max_run_duration_seconds_hard_cap": str(ABSOLUTE_MAX_RUN_DURATION_SECONDS),
        "productive_policy_max_cycles_per_run": str(PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN),
        "productive_policy_max_run_duration_seconds": str(
            PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS
        ),
        "bounds_class": BOUNDS_CLASS,
        "post_count": "0",
    }


def _advance_persisted_c1_cursor_floor_v1(
    *,
    cursor_store_root: Path,
    venue_event_time: float,
) -> None:
    """Reconcile S6 sequencing floor after a successful S5 cycle.

    Durable sidestate cursor commits are owned by S7
    (``persist_occupied_lane_mv2_dp_decision_state_cursor_v1`` via
    ``compose_occupied_lane_mv2_dp_durable_cycle_v1``). Stub or non-persisting
    T2 paths leave the floor unchanged; S6 then performs the minimal
    ``venue_event_time`` bump. When the durable owner already committed the
    accepted C1 epoch (``incoming == previous``), this is a no-op reconcile —
    not duplicate-input acceptance (freshness gates run before S5).
    """
    cursor, reason = load_current_productive_c1_cursor_or_reason_v1(cursor_store_root)
    if cursor is None:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_CURSOR_ADVANCE_FAILED, reason or "CURSOR_MISSING"
        )
    try:
        payload = json.loads(json.dumps(dict(cursor)))
        identity = payload["cap61_confirmation_state"]["observation_acceptance_state"][
            "last_accepted_observation_identity"
        ]
        if not isinstance(identity, dict):
            raise TypeError("last_accepted_observation_identity")
        previous = float(identity["venue_event_time"])
        incoming = float(venue_event_time)
        if incoming < previous:
            raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
                REASON_STALE_OR_EQUAL_C1, "cursor_advance"
            )
        if incoming == previous:
            return
        identity["venue_event_time"] = incoming
    except CurrentProductiveGovernedContinuousCycleOrchestratorError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_CURSOR_ADVANCE_FAILED, "cursor_shape"
        ) from exc
    _persist_json(path=Path(cursor_store_root) / CURSOR_FILENAME, payload=payload)


def _mint_s5_authorization(
    *,
    native_id: str,
    bar: str,
    expected_cursor_floor: float,
) -> CurrentProductiveGovernedCycleAuthorizationV1:
    return CurrentProductiveGovernedCycleAuthorizationV1(
        cycle_owner_go=S5_RUNTIME_OWNER_GO,
        get_owner_go=GET_OWNER_GO,
        eg_owner_go=EG_OWNER_GO,
        occupancy_owner_go=OCCUPANCY_OWNER_GO,
        t2_owner_go=T2_RUNTIME_OWNER_GO,
        native_id=native_id,
        bar=bar,
        expected_cursor_floor=expected_cursor_floor,
    )


def _completed_s5_hold_digest(path: Path, *, result, native_id: str, prior_floor: float):
    if (
        result.terminal_class != "MARKET_STATE_REQUIRED"
        or result.envelope_created
        or result.extra.get("PORTFOLIO_RESERVATION_ID")
        or getattr(result, "position_management_execution_handoff", None) is not None
        or getattr(result, "canonical_order_intent", None) is not None
        or path.resolve() != path
    ):
        return None
    try:
        raw = path.read_bytes()
        original = json.loads(raw)
    except (OSError, ValueError):
        return None
    if (
        isinstance(original, dict)
        and original.get("state") == "COMPLETED"
        and original.get("terminal_class") == result.terminal_class
        and original.get("reason_code") == result.reason_code
        and original.get("native_id") == native_id
        and original.get("cycle_owner_go") == S5_RUNTIME_OWNER_GO
        and original.get("expected_cursor_floor") == prior_floor
        and original.get("t2_consumed") is True
        and original.get("portfolio_reservation_id") == ""
        and original.get("POST_COUNT") == "0"
        and original.get("PERMIT_CREATED") == FALSE_TOKEN
    ):
        return sha256(raw).hexdigest()
    return None


def _new_occupied_mark_time_v1(
    *,
    observation: InjectedContinuousObservationV1,
    native_id: str,
    cursor_store_root: Path,
    observed_unix: float,
) -> float | None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )

    if observation.mark_price_payload is None:
        return None
    try:
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=observation.mark_price_payload,
            venue_native_id=native_id,
            index_from_index_tickers=observation.index_tickers_payload,
            mark_acquired_at_utc=observation.mark_acquired_at_utc,
        )
        event_time = provenance.require_current_mark_clock_v1(observed_unix=observed_unix)
    except ValueError:
        return None
    prior = read_occupied_scope_mark_snapshot_v1(cursor_store_root)
    if prior is None:
        return event_time
    mark = prior["mark"]
    if event_time < mark["event_unix"] or (
        event_time == mark["event_unix"] and provenance.mark_px in mark["prices"]
    ):
        return None
    return event_time


def run_current_productive_governed_continuous_cycle_run_v1(
    *,
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    origin_main_sha: str,
    cursor_store_root: Path,
    lock_root: Path,
    evidence_root: Path,
    observation_source: ContinuousObservationSourceV1 | None,
    execute_network: bool = False,
    perform_get: bool = False,
    eg_cycle_dispatch: Callable[..., Any] | None = None,
    t2_cycle_dispatch: Callable[..., Any] | None = None,
    s5_runner: S5CycleRunnerV1 | None = None,
    time_fn: TimeFnV1 | None = None,
    sleep_fn: SleepFnV1 | None = None,
    cancel_requested: CancelFnV1 | None = None,
    iteration_authority_gate_v1: IterationAuthorityGateV1 | None = None,
    occupied_mark_only: bool = False,
) -> CurrentProductiveGovernedContinuousCycleRunResultV1:
    _assert_standing_pins()
    _validate_authorization(authorization)
    if execute_network is True or perform_get is True:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_NETWORK_NOT_AUTHORIZED
        )
    if observation_source is None:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_INJECTED_SOURCE_REQUIRED
        )
    if occupied_mark_only and s5_runner is None:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            "OCCUPIED_MARK_RUNNER_REQUIRED"
        )

    Path(evidence_root).mkdir(parents=True, exist_ok=True)
    Path(lock_root).mkdir(parents=True, exist_ok=True)
    ledger = _load_ledger(Path(evidence_root))
    digest = _binding_digest(authorization)
    prior_state = str(ledger.get("state") or STATE_IDLE)
    if prior_state in {STATE_IN_PROGRESS, STATE_WAITING_FOR_NEXT_C1, STATE_FAILED_STOP}:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_PARTIAL_NOT_RESUMABLE
        )
    if prior_state in {STATE_COMPLETED, STATE_CANCELLED}:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(REASON_REPLAY)

    from src.ops.gates.risk_gate import canonical_kill_switch_state_path
    from src.ops.filegate_recovery_authority_v1 import FilegateAuthorityError
    from src.ops.managed_filegate_v1 import (
        configured_filegate_writer_v1,
        managed_filegate_configured_v1,
        read_configured_filegate_v1,
    )

    filegate_path = Path(canonical_kill_switch_state_path())
    managed_filegate = configured_filegate_writer_v1(filegate_path)
    lock_path = Path(lock_root).resolve() / LOCK_NAME
    try:
        process_identity = capture_process_identity(os.getpid()).to_dict()
    except ProcessIdentityMismatchError:
        process_identity = None
    lock = AuthorizationLifecycleLockV1(
        lock_path=lock_path,
        authorization_id=LOCK_AUTHORIZATION_ID,
        owner="current_productive_governed_continuous_cycle_orchestrator_v1",
        recover_dead_local_owner=True,
        recovery_context={
            "evidence_root": str(Path(evidence_root).resolve()),
            "cursor_store_root": str(Path(cursor_store_root).resolve()),
            "binding_digest": digest,
            "process_identity": process_identity,
            "boot_identity": read_local_boot_identity_v1(),
        },
        dead_owner_validator=lambda receipt: (
            read_dead_owner_wait_ledger_v1(
                receipt,
                cursor_store_root=Path(cursor_store_root),
                native_id=authorization.native_id,
                lock_path=lock_path,
                filegate_path=filegate_path,
                repository_sha=origin_main_sha,
            )
            is not None
        ),
    )
    try:
        lock.acquire()
    except LifecycleLockError as exc:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_CONCURRENT_RUN
        ) from exc

    clock = time_fn or time.monotonic
    sleeper = sleep_fn or time.sleep
    started_at = float(clock())
    last_progress_at = started_at
    run_id = mint_continuous_run_id_v1(authorization)
    consumed: list[str] = []
    records: list[ContinuousCycleRecordV1] = []
    last_accepted = float(authorization.expected_cursor_floor)
    cursor_floor_before = last_accepted
    s5_invoke_count = 0
    poll_iterations = 0
    poll_retry_count = 0
    recovery_incident_id = None
    last_fresh_c1_at = started_at
    latest_context_c1 = last_accepted
    max_poll_iterations = compute_max_canonical_continuous_poll_iterations_v1(
        max_run_duration_seconds=authorization.max_run_duration_seconds,
        wait_interval_seconds=authorization.wait_interval_seconds,
        max_cycles_per_run=authorization.max_cycles_per_run,
    )
    runner = s5_runner or run_current_productive_governed_cycle_v1
    # The standard S5 cycle consumes finalized C1 and occupancy. The N1 adapter
    # uses the original Mark/Index bundle to build its own market context.
    runner_accepts_market_bundle = runner is not run_current_productive_governed_cycle_v1
    disposition = DISPOSITION_FAIL_CLOSED
    reason_code = ""
    terminal_class = ""
    first_blocker = ""
    next_owner = ""
    ledger_state = STATE_FAILED_STOP

    managed_release = None

    def _require_managed_release():
        if managed_release is None:
            return
        current = read_configured_filegate_v1(filegate_path) or {}
        if (
            os.environ.get("PEAK_KILL_SWITCH") == "1"
            or current.get("filegate_release_sha256") != managed_release
        ):
            raise ManagedFilegateRevisionChangedV1(REASON_MANAGED_FILEGATE_REVISION_CHANGED)

    ledger_path = Path(evidence_root) / LEDGER_FILENAME

    def _ledger_payload(*, state: str, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "state": state,
            "binding_digest": digest,
            "run_id": run_id,
            "continuous_owner_go": authorization.continuous_owner_go,
            "s5_runtime_owner_go": S5_RUNTIME_OWNER_GO,
            "consumed_instance_ids": list(consumed),
            "s5_invoke_count": s5_invoke_count,
            "last_accepted_c1": last_accepted,
            "native_id": authorization.native_id,
            "expected_cursor_floor": authorization.expected_cursor_floor,
            "max_cycles_per_run": authorization.max_cycles_per_run,
            "max_run_duration_seconds": authorization.max_run_duration_seconds,
            "poll_retry_count": poll_retry_count,
            "POST_COUNT": "0",
            "PERMIT_CREATED": FALSE_TOKEN,
            "EXTERNAL_EFFECT_COUNT": "0",
        }
        if extra:
            payload.update(dict(extra))
        if occupied_mark_only:
            payload["occupied_mark_only"] = True
            payload["occupied_mark_cycles"] = [
                {
                    "consume_instance_id": record.consume_instance_id,
                    "mark_venue_event_time": record.mark_venue_event_time,
                    "s5_evidence_root": record.mark_evidence_root,
                    "envelope_identity": record.envelope_identity,
                }
                for record in records
            ]
        if (
            state == STATE_WAITING_FOR_NEXT_C1
            and (Path(cursor_store_root) / CURSOR_FILENAME).is_file()
        ):
            payload["checkpoint_cursor_sha256"] = sha256(
                (Path(cursor_store_root) / CURSOR_FILENAME).read_bytes()
            ).hexdigest()
        if (
            state == STATE_COMPLETED
            and last_accepted > cursor_floor_before
            and (Path(cursor_store_root) / CURSOR_FILENAME).is_file()
        ):
            payload["completed_cursor_sha256"] = sha256(
                (Path(cursor_store_root) / CURSOR_FILENAME).read_bytes()
            ).hexdigest()
        return payload

    def _seal_wait(payload: dict[str, Any], *, s5_checkpoint: Mapping[str, Any] | None = None):
        lock.assert_held()
        _require_managed_release()
        checkpoint = {
            "lock_sha256": sha256(lock_path.read_bytes()).hexdigest(),
            "ledger_sha256": sha256(canonical_json_text(payload).encode()).hexdigest(),
            "cursor_sha256": payload["checkpoint_cursor_sha256"],
            "repository_sha": origin_main_sha,
        }
        if s5_checkpoint is not None:
            checkpoint.update(
                wait_ledger=payload,
                prior_ledger_sha256=sha256(ledger_path.read_bytes()).hexdigest(),
                **s5_checkpoint,
            )
        try:
            managed_filegate.set_host_checkpoint_v1(
                lock_path=lock_path, checkpoint=checkpoint, expected_release_sha256=managed_release
            )
        except (FilegateAuthorityError, sqlite3.Error):
            _require_managed_release()
            raise

    def _write_ledger(
        *, state: str, extra: Mapping[str, Any] | None = None, completed_hold_sha256=None
    ) -> None:
        payload = _ledger_payload(state=state, extra=extra)
        if managed_filegate is not None and state != STATE_WAITING_FOR_NEXT_C1:
            lock.assert_held()
            managed_filegate.set_host_checkpoint_v1(
                lock_path=lock.lock_path.resolve(), checkpoint=None
            )
        if (
            managed_filegate is not None
            and state == STATE_WAITING_FOR_NEXT_C1
            and not occupied_mark_only
            and "checkpoint_cursor_sha256" in payload
        ):
            _seal_wait(
                payload,
                s5_checkpoint=(
                    {"s5_ledger_sha256": completed_hold_sha256}
                    if completed_hold_sha256 is not None
                    else None
                ),
            )
        _persist_json(path=ledger_path, payload=payload)
        trans_path = Path(evidence_root) / "transitions.jsonl"
        with trans_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")

    def _elapsed() -> float:
        return float(clock()) - started_at

    def _touch_poll_liveness_v1() -> None:
        """Active Fresh-C1 polling (incl. stale wait) is not a sequencer stall."""
        nonlocal last_progress_at
        last_progress_at = float(clock())

    def _stop(
        *,
        result_disposition: str,
        result_reason: str,
        result_terminal: str,
        state: str,
        blocker: str,
        owner_next: str,
    ) -> CurrentProductiveGovernedContinuousCycleRunResultV1:
        nonlocal disposition, reason_code, terminal_class, first_blocker, next_owner, ledger_state
        disposition = result_disposition
        reason_code = result_reason
        terminal_class = result_terminal
        first_blocker = blocker
        next_owner = owner_next
        ledger_state = state
        _write_ledger(
            state=state,
            extra={
                "reason_code": result_reason,
                "first_genuine_blocker": blocker,
                "next_required_owner_decision": owner_next,
            },
        )
        record_runtime_notice_v1(
            evidence_root=Path(evidence_root),
            component="GOVERNED_CONTINUOUS_RUNTIME",
            run_id=run_id,
            reason_code=result_reason,
            action=owner_next,
            owner_action_required=result_disposition != DISPOSITION_CANCELLED,
            notification_kind="FAULT"
            if result_disposition in {DISPOSITION_FAIL_CLOSED, DISPOSITION_STALL}
            else None,
            extra={
                "disposition": result_disposition,
                "poll_retry_count": poll_retry_count,
                "cycles_completed": len(records),
                "automatic_restart_allowed": False,
            },
        )
        return _result(
            disposition=disposition,
            reason_code=reason_code,
            terminal_class=terminal_class,
            cycles_completed=len(records),
            s5_invoke_count=s5_invoke_count,
            consume_instance_ids=tuple(consumed),
            cycle_records=tuple(records),
            last_accepted_c1=last_accepted,
            cursor_floor_before=cursor_floor_before,
            cursor_floor_after=last_accepted,
            first_genuine_blocker=first_blocker,
            next_required_owner_decision=next_owner,
            ledger_state=ledger_state,
            sequencer_elapsed_monotonic_seconds=_elapsed(),
        )

    try:
        if managed_filegate_configured_v1(filegate_path):
            current = read_configured_filegate_v1(filegate_path) or {}
            managed_release = current.get("filegate_release_sha256")
            if current.get("state") != "ACTIVE" or managed_release is None:
                raise ManagedFilegateRevisionChangedV1(REASON_MANAGED_FILEGATE_ACTIVE_UNPROVEN)
            _require_managed_release()
        _write_ledger(state=STATE_IN_PROGRESS)
        while True:
            _require_managed_release()
            if cancel_requested is not None and cancel_requested() is True:
                return _stop(
                    result_disposition=DISPOSITION_CANCELLED,
                    result_reason="CANCELLED",
                    result_terminal="CANCELLATION",
                    state=STATE_CANCELLED,
                    blocker="CANCELLED",
                    owner_next="Cancellation left an auditable terminal ledger. Do not resume.",
                )
            if _elapsed() >= float(authorization.max_run_duration_seconds):
                return _stop(
                    result_disposition=DISPOSITION_MAX_DURATION,
                    result_reason="MAX_RUN_DURATION",
                    result_terminal="MAX_DURATION_BOUND",
                    state=STATE_COMPLETED,
                    blocker="MAX_RUN_DURATION",
                    owner_next="Authorized duration completed. A new run requires fresh bounded authorization and current inputs.",
                )
            if float(clock()) - last_progress_at >= float(authorization.stall_seconds):
                return _stop(
                    result_disposition=DISPOSITION_STALL,
                    result_reason="STALL",
                    result_terminal="STALL_BOUND",
                    state=STATE_COMPLETED,
                    blocker="STALL",
                    owner_next="Inspect the stalled runtime/source and reconcile durable state before a newly authorized run.",
                )
            if float(clock()) - last_fresh_c1_at >= float(
                authorization.max_wait_for_next_c1_seconds
            ):
                return _stop(
                    result_disposition=DISPOSITION_STALL,
                    result_reason="MAX_WAIT_FOR_NEXT_C1",
                    result_terminal="WAIT_BOUND",
                    state=STATE_COMPLETED,
                    blocker="MAX_WAIT_FOR_NEXT_C1",
                    owner_next="Restore fresh C1 supply and reconcile the cursor before a newly authorized run. This run cannot be replayed.",
                )
            poll_iterations += 1
            if poll_iterations > max_poll_iterations:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=REASON_HANG_GUARD,
                    result_terminal="ANTI_HANG",
                    state=STATE_FAILED_STOP,
                    blocker=REASON_HANG_GUARD,
                    owner_next="Anti-hang poll guard fired. Do not resume.",
                )
            try:
                observation = observation_source.poll()
            except (TimeoutError, ConnectionError) as exc:
                if recovery_incident_id is None:
                    fault = record_runtime_notice_v1(
                        evidence_root=Path(evidence_root),
                        component="GOVERNED_CONTINUOUS_RUNTIME",
                        run_id=run_id,
                        reason_code="OBSERVATION_SOURCE_FAULT",
                        action="Automatic bounded fresh-source recovery is in progress.",
                        owner_action_required=False,
                        notification_kind="FAULT",
                        extra={
                            "exception_type": type(exc).__name__,
                            "recovery_scope": "FRESH_C1_DATA_PROCESSING",
                        },
                    )
                    recovery_incident_id = fault["event_id"]
                retry = bounded_retry_policy_v1(
                    attempt=poll_retry_count, automatic_recovery_allowed=True
                )
                if not retry["retry_allowed"]:
                    return _stop(
                        result_disposition=DISPOSITION_FAIL_CLOSED,
                        result_reason="OBSERVATION_POLL_RETRY_EXHAUSTED",
                        result_terminal="SOURCE_UNAVAILABLE",
                        state=STATE_FAILED_STOP,
                        blocker=type(exc).__name__,
                        owner_next="Restore observation source and reconcile the persisted cursor; obtain a fresh authorized run. Do not replay this run.",
                    )
                poll_retry_count += 1
                _write_ledger(
                    state=STATE_WAITING_FOR_NEXT_C1,
                    extra={"reason_code": "OBSERVATION_POLL_RETRY_SCHEDULED"},
                )
                record_runtime_notice_v1(
                    evidence_root=Path(evidence_root),
                    component="GOVERNED_CONTINUOUS_RUNTIME",
                    run_id=run_id,
                    reason_code="OBSERVATION_POLL_RETRY_SCHEDULED",
                    action="Poll the source again within the same bounded authorization.",
                    owner_action_required=False,
                    extra={
                        "poll_retry_count": poll_retry_count,
                        "exception_type": type(exc).__name__,
                    },
                )
                _touch_poll_liveness_v1()
                sleeper(
                    min(
                        float(authorization.wait_interval_seconds),
                        max(0.0, float(authorization.max_run_duration_seconds) - _elapsed()),
                    )
                )
                continue
            if _elapsed() >= float(authorization.max_run_duration_seconds) or float(
                clock()
            ) - last_fresh_c1_at >= float(authorization.max_wait_for_next_c1_seconds):
                continue  # expired bounds are handled before any S5 invocation
            if observation is None:
                _touch_poll_liveness_v1()
                _write_ledger(state=STATE_WAITING_FOR_NEXT_C1)
                sleeper(float(authorization.wait_interval_seconds))
                continue
            mapped = map_injected_candles_payload_to_current_productive_c1_observation_v1(
                owner_go=EH_SEAM_OWNER_GO,
                candles_payload=observation.candles_payload,
                native_id=authorization.native_id,
            )
            if mapped.disposition != DISPOSITION_EMITTED or mapped.observation is None:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=mapped.reason_code or "C1_UNFINALIZED",
                    result_terminal="FRESHNESS_FAILURE",
                    state=STATE_FAILED_STOP,
                    blocker=mapped.reason_code or "C1_UNFINALIZED",
                    owner_next="Unfinalized/unmapped C1 is not an S5 cycle. Do not resume.",
                )
            c1_obs = mapped.observation
            c1_time = float(c1_obs.venue_event_time)
            mark_time = (
                _new_occupied_mark_time_v1(
                    observation=observation,
                    native_id=authorization.native_id,
                    cursor_store_root=Path(cursor_store_root),
                    observed_unix=time.time(),
                )
                if occupied_mark_only and c1_time >= float(latest_context_c1)
                else None
            )
            if occupied_mark_only and mark_time is not None and c1_time > latest_context_c1:
                latest_context_c1 = c1_time
                last_fresh_c1_at = float(clock())
            if (occupied_mark_only and mark_time is None) or (
                not occupied_mark_only and c1_time <= float(last_accepted)
            ):
                _touch_poll_liveness_v1()
                _write_ledger(state=STATE_WAITING_FOR_NEXT_C1)
                sleeper(float(authorization.wait_interval_seconds))
                continue
            freshness = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
                owner_go=EH_SEAM_OWNER_GO,
                cursor_store_root=Path(cursor_store_root),
                observation=c1_obs,
            )
            if not occupied_mark_only and freshness.disposition != DISPOSITION_EMITTED:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=freshness.reason_code or REASON_STALE_OR_EQUAL_C1,
                    result_terminal="STALE_C1",
                    state=STATE_FAILED_STOP,
                    blocker=freshness.reason_code or REASON_STALE_OR_EQUAL_C1,
                    owner_next="C1 failed cursor freshness. S5 was not invoked. Do not resume.",
                )
            cycle_index = len(records) + 1
            if iteration_authority_gate_v1 is not None:
                try:
                    iteration_authority_gate_v1(cycle_index)
                except Exception as exc:
                    _require_managed_release()
                    return _stop(
                        result_disposition=DISPOSITION_FAIL_CLOSED,
                        result_reason="ITERATION_AUTHORITY_GATE_DENIED",
                        result_terminal="AUTHORITY_VIOLATION",
                        state=STATE_FAILED_STOP,
                        blocker=str(exc),
                        owner_next=(
                            "Iteration authority gate denied before S5 cycle. "
                            "Continuous run terminated. Do not resume."
                        ),
                    )
            consume_id = mint_s5_cycle_consume_instance_id_v1(
                run_id=run_id,
                cycle_index=cycle_index,
                c1_venue_event_time=c1_time if mark_time is None else mark_time,
            )
            if consume_id in consumed:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=REASON_CONSUME_INSTANCE_REUSE,
                    result_terminal="AUTHORITY_VIOLATION",
                    state=STATE_FAILED_STOP,
                    blocker=REASON_CONSUME_INSTANCE_REUSE,
                    owner_next="Consumed S5 instance reuse is forbidden. Do not resume.",
                )
            cycle_root = Path(evidence_root) / "cycles" / consume_id
            cycle_lock = Path(evidence_root) / "cycle_locks" / consume_id
            # End the safe wait checkpoint before any per-cycle authorization or
            # S5 effect. A SIGKILL here must not inherit the previous WAIT state.
            _require_managed_release()
            _write_ledger(state=STATE_IN_PROGRESS, extra={"reason_code": "S5_CYCLE_STARTING"})
            auth_record = {
                "cycle_index": cycle_index,
                "cycle_instance_id": consume_id,
                "consume_instance_id": consume_id,
                "evidence_root": str(cycle_root),
                "c1_venue_event_time": c1_time,
                **({"mark_venue_event_time": mark_time} if mark_time is not None else {}),
                "logical_tokens": {
                    "SEQUENCING": S5_RUNTIME_OWNER_GO,
                    "GET": GET_OWNER_GO,
                    "EG": EG_OWNER_GO,
                    "OCCUPANCY": OCCUPANCY_OWNER_GO,
                    "T2": T2_RUNTIME_OWNER_GO,
                },
                "continuous_owner_go": authorization.continuous_owner_go,
                "post_owner_go_composed": FALSE_TOKEN,
            }
            _persist_json(path=cycle_root / "s5_cycle_authorization_v1.json", payload=auth_record)
            s5_auth = _mint_s5_authorization(
                native_id=authorization.native_id,
                bar=authorization.bar,
                expected_cursor_floor=float(last_accepted),
            )
            s5_invoke_count += 1
            if s5_invoke_count != cycle_index:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=REASON_S5_INVOKE_COUNT_DRIFT,
                    result_terminal="AUTHORITY_VIOLATION",
                    state=STATE_FAILED_STOP,
                    blocker=REASON_S5_INVOKE_COUNT_DRIFT,
                    owner_next="S5 invoke cardinality drifted. Do not resume.",
                )

            def _seal_no_effect_hold(path: Path, terminal: Mapping[str, Any]) -> None:
                # Only the already durable original S7 cursor can support this
                # boundary. S6 cannot infer completion from a cursor advance.
                expected_path = cycle_root.resolve() / "s5" / S5_LEDGER_FILENAME
                if path.absolute() != expected_path or path.resolve() != expected_path:
                    return
                prior_s5 = path.read_bytes()
                prior = json.loads(prior_s5)
                if (
                    prior["state"] != "IN_PROGRESS"
                    or prior["binding_digest"] != terminal["binding_digest"]
                    or terminal["native_id"] != authorization.native_id
                    or terminal["expected_cursor_floor"] != last_accepted
                ):
                    return
                cursor_path = Path(cursor_store_root) / CURSOR_FILENAME
                cursor_raw = cursor_path.read_bytes()
                cursor = json.loads(cursor_raw)
                if (
                    cursor.get("venue_native_id") != authorization.native_id
                    or cursor_last_accepted_c1_venue_event_time_v1(cursor) != c1_time
                ):
                    return
                successor = _ledger_payload(
                    state=STATE_WAITING_FOR_NEXT_C1,
                    extra={
                        "reason_code": "HOLD_WAIT_NEXT_FRESH_C1",
                        "consumed_instance_ids": [*consumed, consume_id],
                        "last_accepted_c1": c1_time,
                    },
                )
                if successor.get("checkpoint_cursor_sha256") != sha256(cursor_raw).hexdigest():
                    return
                _seal_wait(
                    successor,
                    s5_checkpoint={
                        "prior_s5_ledger_sha256": sha256(prior_s5).hexdigest(),
                        "s5_ledger_sha256": sha256(
                            canonical_json_text(terminal).encode()
                        ).hexdigest(),
                        "s5_terminal_ledger": terminal,
                    },
                )

            try:
                _require_managed_release()
                s5_result = runner(
                    authorization=s5_auth,
                    origin_main_sha=origin_main_sha,
                    cursor_store_root=Path(cursor_store_root),
                    lock_root=cycle_lock,
                    evidence_root=cycle_root / "s5",
                    candles_payload=observation.candles_payload,
                    occupancy_payloads=observation.occupancy_payloads,
                    **(
                        {"mark_price_payload": observation.mark_price_payload}
                        if runner_accepts_market_bundle
                        and observation.mark_price_payload is not None
                        else {}
                    ),
                    **(
                        {"index_tickers_payload": observation.index_tickers_payload}
                        if runner_accepts_market_bundle
                        and observation.index_tickers_payload is not None
                        else {}
                    ),
                    **(
                        {"mark_acquired_at_utc": observation.mark_acquired_at_utc}
                        if runner_accepts_market_bundle and observation.mark_acquired_at_utc
                        else {}
                    ),
                    execute_network=False,
                    perform_get=False,
                    eg_cycle_dispatch=eg_cycle_dispatch,
                    t2_cycle_dispatch=t2_cycle_dispatch,
                    **(
                        {"seal_no_effect_hold_v1": _seal_no_effect_hold}
                        if managed_filegate is not None
                        and not occupied_mark_only
                        and cycle_index < authorization.max_cycles_per_run
                        else {}
                    ),
                )
            except CurrentProductiveGovernedCycleOrchestratorError as exc:
                consumed.append(consume_id)
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=exc.reason_code,
                    result_terminal="S5_FAILURE",
                    state=STATE_FAILED_STOP,
                    blocker=exc.reason_code,
                    owner_next="S5 failed closed. Continuous run terminated. Do not resume.",
                )
            consumed.append(consume_id)
            records.append(
                ContinuousCycleRecordV1(
                    cycle_index=cycle_index,
                    cycle_instance_id=consume_id,
                    consume_instance_id=consume_id,
                    evidence_root=str(cycle_root),
                    c1_venue_event_time=c1_time,
                    s5_disposition=s5_result.disposition,
                    s5_reason_code=s5_result.reason_code,
                    sequencing_owner_go=S5_RUNTIME_OWNER_GO,
                    get_owner_go=GET_OWNER_GO,
                    eg_owner_go=EG_OWNER_GO,
                    occupancy_owner_go=OCCUPANCY_OWNER_GO,
                    t2_owner_go=T2_RUNTIME_OWNER_GO,
                    pending_decision_context=getattr(s5_result, "pending_decision_context", None),
                    final_order_envelope=s5_result.final_order_envelope,
                    envelope_created=s5_result.envelope_created,
                    canonical_order_intent=getattr(s5_result, "canonical_order_intent", None),
                    position_management_execution_handoff=getattr(
                        s5_result, "position_management_execution_handoff", None
                    ),
                    envelope_identity=s5_result.envelope_identity,
                    portfolio_reservation_id=s5_result.extra.get("PORTFOLIO_RESERVATION_ID", ""),
                    execution_plan_context=getattr(s5_result, "execution_plan_context", None),
                    mark_venue_event_time=mark_time,
                    mark_evidence_root=str(s5_result.extra.get("OCCUPIED_MARK_EVIDENCE_ROOT", "")),
                    position_close_post_context=getattr(
                        s5_result, "position_close_post_context", None
                    ),
                )
            )
            if s5_result.permit_created is True or int(s5_result.post_count) != 0:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason="EXTERNAL_EFFECT_OR_POST_LEAK",
                    result_terminal="POST_BOUNDARY",
                    state=STATE_FAILED_STOP,
                    blocker="EXTERNAL_EFFECT_OR_POST_LEAK",
                    owner_next="POST/permit leak is forbidden in continuous sequencing.",
                )
            if occupied_mark_only and (
                s5_result.extra.get("PORTFOLIO_RESERVATION_ID")
                or (
                    s5_result.disposition == S5_DISPOSITION_PRE_EXTERNAL_EFFECT
                    and s5_result.position_management_execution_handoff is None
                )
            ):
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason="OCCUPIED_MARK_ENTRY_FORBIDDEN",
                    result_terminal="AUTHORITY_VIOLATION",
                    state=STATE_FAILED_STOP,
                    blocker="OCCUPIED_MARK_ENTRY_FORBIDDEN",
                    owner_next="Reconcile the occupied position before a new run.",
                )
            prior_floor = last_accepted
            last_progress_at = float(clock())
            if not occupied_mark_only:
                last_accepted = c1_time
                _advance_persisted_c1_cursor_floor_v1(
                    cursor_store_root=Path(cursor_store_root),
                    venue_event_time=c1_time,
                )
                last_fresh_c1_at = float(clock())
            if (
                not occupied_mark_only
                and recovery_incident_id is not None
                and s5_result.disposition
                in {
                    S5_DISPOSITION_HOLD,
                    S5_DISPOSITION_PRE_EXTERNAL_EFFECT,
                }
            ):
                # Report recovery after real S5 processing and durable cursor
                # advancement, never merely after a GET or a component restart.
                cursor_digest = sha256(
                    (Path(cursor_store_root) / CURSOR_FILENAME).read_bytes()
                ).hexdigest()
                record_runtime_notice_v1(
                    evidence_root=Path(evidence_root),
                    component="GOVERNED_CONTINUOUS_RUNTIME",
                    run_id=run_id,
                    reason_code="RUNTIME_RECOVERY_VERIFIED",
                    action="Fresh C1 processing has resumed under the existing cycle admission.",
                    owner_action_required=False,
                    notification_kind="RECOVERED",
                    extra={
                        "incident_id": recovery_incident_id,
                        "recovery_scope": "FRESH_C1_DATA_PROCESSING",
                        "accepted_c1": c1_time,
                        "cursor_sha256": cursor_digest,
                        "s5_consume_instance_id": consume_id,
                        "s5_disposition": s5_result.disposition,
                        "cycles_completed": len(records),
                        "poll_retry_count": poll_retry_count,
                    },
                )
                recovery_incident_id = None
            if s5_result.disposition == S5_DISPOSITION_PRE_EXTERNAL_EFFECT:
                return _stop(
                    result_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
                    result_reason=s5_result.reason_code or POST_NEXT_OWNER_GO,
                    result_terminal="PRE_EXTERNAL_EFFECT",
                    state=STATE_COMPLETED,
                    blocker=s5_result.first_genuine_blocker or POST_NEXT_OWNER_GO,
                    owner_next=(
                        "Cycle stopped at PRE_EXTERNAL_EFFECT. Continuous GO does not compose "
                        f"{POST_NEXT_OWNER_GO}. No subsequent S5 cycle."
                    ),
                )
            if s5_result.disposition == S5_DISPOSITION_FAIL_CLOSED:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=s5_result.reason_code or "S5_FAIL_CLOSED",
                    result_terminal=s5_result.terminal_class or "S5_FAILURE",
                    state=STATE_FAILED_STOP,
                    blocker=s5_result.first_genuine_blocker or s5_result.reason_code,
                    owner_next="S5 fail-closed terminated the continuous run. Do not resume.",
                )
            occupied_hold = occupied_mark_only and (
                s5_result.disposition == "COMPLETED"
                and s5_result.terminal_class == "POSITION_MANAGEMENT_EVALUATED"
                and s5_result.final_order_envelope is None
            )
            if s5_result.disposition != S5_DISPOSITION_HOLD and not occupied_hold:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=f"UNKNOWN_S5_DISPOSITION:{s5_result.disposition}",
                    result_terminal="UNKNOWN_OR_CONFLICTING",
                    state=STATE_FAILED_STOP,
                    blocker=s5_result.disposition,
                    owner_next="Unknown S5 disposition. Continuous run terminated.",
                )
            if cycle_index >= int(authorization.max_cycles_per_run):
                return _stop(
                    result_disposition=DISPOSITION_MAX_CYCLES,
                    result_reason="MAX_CYCLES_PER_RUN",
                    result_terminal="MAX_CYCLES_BOUND",
                    state=STATE_COMPLETED,
                    blocker="MAX_CYCLES_PER_RUN",
                    owner_next=(
                        "HOLD is terminal for this cycle. Max cycles bound stopped continuation. "
                        "POST unauthorized."
                    ),
                )
            completed_hold = None
            if managed_filegate is not None and not occupied_mark_only:
                completed_hold = _completed_s5_hold_digest(
                    cycle_root.resolve() / "s5" / S5_LEDGER_FILENAME,
                    result=s5_result,
                    native_id=authorization.native_id,
                    prior_floor=prior_floor,
                )
            _write_ledger(
                state=STATE_WAITING_FOR_NEXT_C1,
                extra={"reason_code": "HOLD_WAIT_NEXT_FRESH_C1"},
                completed_hold_sha256=completed_hold,
            )
    except Exception as exc:
        if isinstance(exc, ManagedFilegateRevisionChangedV1) and managed_filegate is not None:
            try:
                lock.assert_held()
                lock_raw = lock_path.read_bytes()
                if (
                    read_dead_owner_wait_ledger_v1(
                        json.loads(lock_raw),
                        cursor_store_root=Path(cursor_store_root),
                        native_id=authorization.native_id,
                        lock_path=lock_path,
                        filegate_path=filegate_path,
                        repository_sha=origin_main_sha,
                        require_independent=True,
                    )
                    is not None
                ):
                    managed_filegate.retire_host_checkpoint_v1(
                        lock_path=lock_path, lock_receipt=lock_raw
                    )
                    retained_wait = True
                else:
                    retained_wait = False
            except (KeyError, LifecycleLockError, OSError, TypeError, ValueError, sqlite3.Error):
                retained_wait = False
            if retained_wait:
                # The host rechecks the new release before opening runtime ports.
                raise
        # An unexpected failure may follow a consumed S5 instance. Preserve the
        # original exception and consumed ledger; never retry the trading cycle.
        try:
            _write_ledger(
                state=STATE_FAILED_STOP,
                extra={
                    "reason_code": "UNEXPECTED_RUNTIME_FAILURE",
                    "exception_type": type(exc).__name__,
                },
            )
            record_runtime_notice_v1(
                evidence_root=Path(evidence_root),
                component="GOVERNED_CONTINUOUS_RUNTIME",
                run_id=run_id,
                reason_code="UNEXPECTED_RUNTIME_FAILURE",
                notification_kind="FAULT",
                action="Inspect owner state and reconcile consumed cycle/cursor evidence before a newly authorized run.",
                owner_action_required=True,
                extra={
                    "exception_type": type(exc).__name__,
                    "s5_invoke_count": s5_invoke_count,
                    "automatic_restart_allowed": False,
                },
            )
        except (FilegateAuthorityError, LifecycleLockError, OSError, sqlite3.Error):
            pass  # notice writer logs persistence failure; retain original error
        raise
    finally:
        lock.release()
    return _stop(
        result_disposition=DISPOSITION_FAIL_CLOSED,
        result_reason="CONTINUOUS_LOOP_EXIT_WITHOUT_TERMINAL",
        result_terminal="UNKNOWN_OR_CONFLICTING",
        state=STATE_FAILED_STOP,
        blocker="CONTINUOUS_LOOP_EXIT_WITHOUT_TERMINAL",
        owner_next="Sequencer exited without a declared terminal. Fail-closed.",
    )


def _result(
    *,
    disposition: str,
    reason_code: str,
    terminal_class: str,
    cycles_completed: int,
    s5_invoke_count: int,
    consume_instance_ids: tuple[str, ...],
    cycle_records: tuple[ContinuousCycleRecordV1, ...],
    last_accepted_c1: float | None,
    cursor_floor_before: float | None,
    cursor_floor_after: float | None,
    first_genuine_blocker: str,
    next_required_owner_decision: str,
    ledger_state: str,
    sequencer_elapsed_monotonic_seconds: float = 0.0,
) -> CurrentProductiveGovernedContinuousCycleRunResultV1:
    consumed = "CONSUMED_THIS_RUN_ONLY" if s5_invoke_count > 0 else "DEFINED_NOT_CONSUMED"
    return CurrentProductiveGovernedContinuousCycleRunResultV1(
        disposition=disposition,
        reason_code=reason_code,
        terminal_class=terminal_class,
        continuous_go_status_after=consumed,
        cycles_completed=cycles_completed,
        s5_invoke_count=s5_invoke_count,
        accepted_c1_count=sum(record.mark_venue_event_time is None for record in cycle_records),
        consume_instance_ids=consume_instance_ids,
        cycle_records=cycle_records,
        last_accepted_c1=last_accepted_c1,
        cursor_floor_before=cursor_floor_before,
        cursor_floor_after=cursor_floor_after,
        permit_created=False,
        post_count=0,
        external_effect_count=0,
        first_genuine_blocker=first_genuine_blocker,
        next_required_owner_decision=next_required_owner_decision,
        lock_released=_token(True),
        ledger_state=ledger_state,
        sequencer_elapsed_monotonic_seconds=float(sequencer_elapsed_monotonic_seconds),
        extra={
            "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
            "DIRECT_V5": DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
            "POST_COMPOSED_INTO_CONTINUOUS_GO": FALSE_TOKEN,
            "BOUNDS_CLASS": BOUNDS_CLASS,
            "S5_REUSED": TRUE_TOKEN,
        },
    )


class ScriptedContinuousObservationSourceV1:
    """Deterministic injected observation source. Not a network GET."""

    def __init__(self, steps: Sequence[InjectedContinuousObservationV1 | None]) -> None:
        self._steps = list(steps)
        self.poll_count = 0

    def poll(self) -> InjectedContinuousObservationV1 | None:
        index = self.poll_count
        self.poll_count += 1
        if index >= len(self._steps):
            return None
        return self._steps[index]
