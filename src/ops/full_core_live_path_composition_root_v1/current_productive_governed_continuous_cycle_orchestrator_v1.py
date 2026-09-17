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
import time
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
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
HARD_CAP_MAX_CYCLES_PER_RUN = 4
DEFAULT_MAX_RUN_DURATION_SECONDS = 90.0
HARD_CAP_MAX_RUN_DURATION_SECONDS = 180.0
DEFAULT_WAIT_INTERVAL_SECONDS = 1.0
HARD_CAP_WAIT_INTERVAL_SECONDS = 15.0
DEFAULT_MAX_WAIT_FOR_NEXT_C1_SECONDS = 30.0
HARD_CAP_MAX_WAIT_FOR_NEXT_C1_SECONDS = 60.0
DEFAULT_STALL_SECONDS = 30.0
HARD_CAP_STALL_SECONDS = 60.0
MIN_POSITIVE_SECONDS = 0.001
BOUNDS_CLASS = "VALIDATION_DEFAULTS_NOT_PRODUCTIVE_POLICY"

S5CycleRunnerV1 = Callable[..., CurrentProductiveGovernedCycleResultV1]
TimeFnV1 = Callable[[], float]
SleepFnV1 = Callable[[float], None]
CancelFnV1 = Callable[[], bool]


class CurrentProductiveGovernedContinuousCycleOrchestratorError(ValueError):
    """Fail-closed continuous-cycle sequencing violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


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
    extra: dict[str, str] = field(default_factory=dict)


def _token(value: bool) -> str:
    return TRUE_TOKEN if value else FALSE_TOKEN


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


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
        hard_cap=HARD_CAP_MAX_CYCLES_PER_RUN,
    )
    _require_positive_seconds(
        name="MAX_RUN_DURATION_SECONDS",
        value=authorization.max_run_duration_seconds,
        hard_cap=HARD_CAP_MAX_RUN_DURATION_SECONDS,
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
        "max_cycles_per_run_hard_cap": str(HARD_CAP_MAX_CYCLES_PER_RUN),
        "max_run_duration_seconds_default": str(DEFAULT_MAX_RUN_DURATION_SECONDS),
        "max_run_duration_seconds_hard_cap": str(HARD_CAP_MAX_RUN_DURATION_SECONDS),
        "bounds_class": BOUNDS_CLASS,
        "post_count": "0",
    }


def _advance_persisted_c1_cursor_floor_v1(
    *,
    cursor_store_root: Path,
    venue_event_time: float,
) -> None:
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
        if incoming <= previous:
            raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
                REASON_STALE_OR_EQUAL_C1, "cursor_advance"
            )
        identity["venue_event_time"] = incoming
    except CurrentProductiveGovernedContinuousCycleOrchestratorError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CurrentProductiveGovernedContinuousCycleOrchestratorError(
            REASON_CURSOR_ADVANCE_FAILED, "cursor_shape"
        ) from exc
    path = Path(cursor_store_root) / CURSOR_FILENAME
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


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

    lock = AuthorizationLifecycleLockV1(
        lock_path=Path(lock_root) / LOCK_NAME,
        authorization_id=LOCK_AUTHORIZATION_ID,
        owner="current_productive_governed_continuous_cycle_orchestrator_v1",
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
    max_poll_iterations = (
        int(
            float(authorization.max_run_duration_seconds)
            / float(authorization.wait_interval_seconds)
        )
        + int(authorization.max_cycles_per_run)
        + 8
    )
    runner = s5_runner or run_current_productive_governed_cycle_v1
    disposition = DISPOSITION_FAIL_CLOSED
    reason_code = ""
    terminal_class = ""
    first_blocker = ""
    next_owner = ""
    ledger_state = STATE_FAILED_STOP

    def _write_ledger(*, state: str, extra: Mapping[str, Any] | None = None) -> None:
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
            "POST_COUNT": "0",
            "PERMIT_CREATED": FALSE_TOKEN,
            "EXTERNAL_EFFECT_COUNT": "0",
        }
        if extra:
            payload.update(dict(extra))
        _persist_json(path=Path(evidence_root) / LEDGER_FILENAME, payload=payload)
        trans_path = Path(evidence_root) / "transitions.jsonl"
        with trans_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")

    def _elapsed() -> float:
        return float(clock()) - started_at

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
        _write_ledger(state=state, extra={"reason_code": result_reason})
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
        )

    try:
        _write_ledger(state=STATE_IN_PROGRESS)
        while True:
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
                    owner_next="Max run duration bound stopped the sequencer. POST unauthorized.",
                )
            if float(clock()) - last_progress_at >= float(authorization.stall_seconds):
                return _stop(
                    result_disposition=DISPOSITION_STALL,
                    result_reason="STALL",
                    result_terminal="STALL_BOUND",
                    state=STATE_COMPLETED,
                    blocker="STALL",
                    owner_next="Stall/anti-hang bound stopped the sequencer. POST unauthorized.",
                )
            if records and (
                float(clock()) - last_progress_at
                >= float(authorization.max_wait_for_next_c1_seconds)
            ):
                return _stop(
                    result_disposition=DISPOSITION_STALL,
                    result_reason="MAX_WAIT_FOR_NEXT_C1",
                    result_terminal="WAIT_BOUND",
                    state=STATE_COMPLETED,
                    blocker="MAX_WAIT_FOR_NEXT_C1",
                    owner_next="Max wait for next fresh C1 stopped the sequencer. POST unauthorized.",
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
            observation = observation_source.poll()
            if observation is None:
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
            if c1_time <= float(last_accepted):
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=REASON_STALE_OR_EQUAL_C1,
                    result_terminal="STALE_C1",
                    state=STATE_FAILED_STOP,
                    blocker=REASON_STALE_OR_EQUAL_C1,
                    owner_next="Stale or equal C1 was rejected. S5 was not invoked. Do not resume.",
                )
            freshness = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
                owner_go=EH_SEAM_OWNER_GO,
                cursor_store_root=Path(cursor_store_root),
                observation=c1_obs,
            )
            if freshness.disposition != DISPOSITION_EMITTED:
                return _stop(
                    result_disposition=DISPOSITION_FAIL_CLOSED,
                    result_reason=freshness.reason_code or REASON_STALE_OR_EQUAL_C1,
                    result_terminal="STALE_C1",
                    state=STATE_FAILED_STOP,
                    blocker=freshness.reason_code or REASON_STALE_OR_EQUAL_C1,
                    owner_next="C1 failed cursor freshness. S5 was not invoked. Do not resume.",
                )
            cycle_index = len(records) + 1
            consume_id = mint_s5_cycle_consume_instance_id_v1(
                run_id=run_id,
                cycle_index=cycle_index,
                c1_venue_event_time=c1_time,
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
            auth_record = {
                "cycle_index": cycle_index,
                "cycle_instance_id": consume_id,
                "consume_instance_id": consume_id,
                "evidence_root": str(cycle_root),
                "c1_venue_event_time": c1_time,
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
            try:
                s5_result = runner(
                    authorization=s5_auth,
                    origin_main_sha=origin_main_sha,
                    cursor_store_root=Path(cursor_store_root),
                    lock_root=cycle_lock,
                    evidence_root=cycle_root / "s5",
                    candles_payload=observation.candles_payload,
                    occupancy_payloads=observation.occupancy_payloads,
                    execute_network=False,
                    perform_get=False,
                    eg_cycle_dispatch=eg_cycle_dispatch,
                    t2_cycle_dispatch=t2_cycle_dispatch,
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
            last_accepted = c1_time
            last_progress_at = float(clock())
            _advance_persisted_c1_cursor_floor_v1(
                cursor_store_root=Path(cursor_store_root),
                venue_event_time=c1_time,
            )
            if s5_result.disposition == S5_DISPOSITION_PRE_EXTERNAL_EFFECT:
                return _stop(
                    result_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
                    result_reason=s5_result.reason_code or POST_NEXT_OWNER_GO,
                    result_terminal="PRE_EXTERNAL_EFFECT",
                    state=STATE_COMPLETED,
                    blocker=s5_result.first_genuine_blocker or POST_NEXT_OWNER_GO,
                    owner_next=(
                        "ENTER stopped at PRE_EXTERNAL_EFFECT. Continuous GO does not compose "
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
            if s5_result.disposition != S5_DISPOSITION_HOLD:
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
            _write_ledger(
                state=STATE_WAITING_FOR_NEXT_C1,
                extra={"reason_code": "HOLD_WAIT_NEXT_FRESH_C1"},
            )
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
) -> CurrentProductiveGovernedContinuousCycleRunResultV1:
    consumed = "CONSUMED_THIS_RUN_ONLY" if s5_invoke_count > 0 else "DEFINED_NOT_CONSUMED"
    return CurrentProductiveGovernedContinuousCycleRunResultV1(
        disposition=disposition,
        reason_code=reason_code,
        terminal_class=terminal_class,
        continuous_go_status_after=consumed,
        cycles_completed=cycles_completed,
        s5_invoke_count=s5_invoke_count,
        accepted_c1_count=cycles_completed,
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
