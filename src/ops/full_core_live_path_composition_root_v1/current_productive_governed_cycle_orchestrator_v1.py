"""CURRENT_PRODUCTIVE governed one-cycle orchestrator.

ORCHESTRATION AUTHORITY ONLY. Sequences existing subordinate one-shots.
Does not substitute, alias, infer, or collapse GET/EG/occupancy/T2/POST.
Remainder identity is not a consume license. Direct V5 remains forbidden.
Does not mint a permit, POST, poll, daemonize, or automatically retry.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_governed_cycle_occupancy_bind_v1 import (
    bind_k1_credential_capability_for_governed_cycle_occupancy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    CYCLE_EXCLUSION_AUTHORIZATION_ID,
    CYCLE_EXCLUSION_LOCK_NAME,
    OCCUPANCY_OWNER_GO,
    OWNER_GO as EG_PERSIST_GO,
    RUNTIME_TRIGGER_OWNER_GO,
    CurrentProductiveC1ObservationV1,
    CurrentProductiveGovernedNextC1OrchestrationError,
    trigger_current_productive_next_c1_and_exactly_one_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
    DISPOSITION_EMITTED,
    DISPOSITION_PRESENT,
    OWNER_GO as EH_SEAM_OWNER_GO,
    S4A_EG_RUNTIME_TRIGGER_OWNER_GO,
    S4A_FRESH_C1_GET_OWNER_GO,
    S4A_V5_EXECUTE_NETWORK,
    T2_OWNER_GO,
    bind_s4a_eg_runtime_trigger_authority_v1,
    bind_s4a_fresh_c1_get_runtime_authority_v1,
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
    NON_EXECUTABLE_NEXT_OWNER_GO,
    POST_NEXT_OWNER_GO,
    PREVIOUS_C1_VENUE_EVENT_TIME,
    _classify_occupancy_v1,
    _evaluate_c1_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = "OWNER_GO_EH_S5_GOVERNED_CYCLE_ORCHESTRATOR_OFFLINE_BIND_V1"
OWNER_GO_SCOPE = "S5_GOVERNED_CYCLE_ORCHESTRATOR_OFFLINE_BIND_ONLY"
OWNER_GO_STATUS = "CONSUMED"
RUNTIME_OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1"
RUNTIME_OWNER_GO_SCOPE = "ONE_CURRENT_PRODUCTIVE_CYCLE_TO_PRE_EXTERNAL_EFFECT_ONLY"
RUNTIME_OWNER_GO_STATUS = "DEFINED_NOT_CONSUMED"
THIS_SLICE = "11.2.1.EH.S5_GOVERNED_CYCLE_ORCHESTRATOR_OFFLINE_BIND"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_SEAM_V1"
FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY = "ONE_CYCLE_ORCHESTRATION_TO_PRE_EXTERNAL_EFFECT_ONLY"
AUTONOMY_CAN_CHANGE_TRADING_LOGIC = False
AUTONOMY_CAN_RESELECT_DOWNSTREAM = False
AUTONOMY_CAN_MINT_PERMIT = False
AUTONOMY_CAN_POST = False
S5_V5_EXECUTE_NETWORK = False
GET_OWNER_GO = S4A_FRESH_C1_GET_OWNER_GO
EG_OWNER_GO = S4A_EG_RUNTIME_TRIGGER_OWNER_GO
T2_RUNTIME_OWNER_GO = T2_OWNER_GO
REMAINDER_OWNER_GO = NON_EXECUTABLE_NEXT_OWNER_GO
LEDGER_FILENAME = "governed_cycle_orchestrator_ledger_v1.json"
DISPOSITION_COMPLETED = "COMPLETED"
DISPOSITION_FAIL_CLOSED = "FAIL_CLOSED"
DISPOSITION_HOLD = "HOLD_CLOSED"
DISPOSITION_PRE_EXTERNAL_EFFECT = "PRE_EXTERNAL_EFFECT"
STATE_IDLE = "IDLE"
STATE_IN_PROGRESS = "IN_PROGRESS"
STATE_COMPLETED = "COMPLETED"
STATE_FAILED_STOP = "FAILED_STOP"
REASON_OWNER_GO_MISMATCH = "OWNER_GO_MISMATCH"
REASON_PERSIST_GO_NOT_RUNTIME_LICENSE = "PERSIST_GO_NOT_RUNTIME_LICENSE"
REASON_REMAINDER_IS_NOT_CONSUME_LICENSE = "REMAINDER_IS_NOT_CONSUME_LICENSE"
REASON_GO_IDENTITY_COLLAPSE = "GO_IDENTITY_COLLAPSE"
REASON_SUBORDINATE_GO_MISMATCH = "SUBORDINATE_GO_MISMATCH"
REASON_POST_GO_IN_CYCLE_AUTHORIZATION = "POST_GO_IN_CYCLE_AUTHORIZATION"
REASON_NETWORK_NOT_AUTHORIZED = "NETWORK_NOT_AUTHORIZED_THIS_SLICE"
REASON_INJECTED_C1_REQUIRED = "INJECTED_C1_REQUIRED_OFFLINE"
REASON_REPLAY = "CYCLE_AUTHORIZATION_REPLAY"
REASON_PARTIAL_NOT_RESUMABLE = "PARTIAL_CYCLE_NOT_RESUMABLE"
REASON_CONCURRENT_CYCLE = "CONCURRENT_CYCLE"
REASON_DIRECT_V5_PIN_DRIFT = "DIRECT_V5_PIN_DRIFT"
REASON_SEND_PIN_DRIFT = "SEND_AUTHORITY_DRIFT"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
CONSUMED_THIS_CYCLE_ONLY = "CONSUMED_THIS_CYCLE_ONLY"
DEFINED_NOT_CONSUMED = "DEFINED_NOT_CONSUMED"

CycleDispatchV1 = Callable[..., Any]


class CurrentProductiveGovernedCycleOrchestratorError(ValueError):
    """Fail-closed governed-cycle orchestration violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class CurrentProductiveGovernedCycleAuthorizationV1:
    cycle_owner_go: str
    get_owner_go: str
    eg_owner_go: str
    occupancy_owner_go: str
    t2_owner_go: str
    native_id: str
    bar: str
    expected_cursor_floor: float


@dataclass(frozen=True)
class CurrentProductiveGovernedCycleResultV1:
    disposition: str
    reason_code: str
    terminal_class: str
    cycle_go_status_after: str
    get_consumed: bool
    eg_consumed: bool
    occupancy_consumed: bool
    t2_consumed: bool
    get_consume_count: int
    eg_dispatch_count: int
    occupancy_disposition: str
    t2_consume_count: int
    runtime_cycle_count: int
    c1_used: str
    occupancy_used: str
    decision_result: str
    decision_execution_eligible: str
    master_v2_decision: str
    venue_plan_status: str
    envelope_created: bool
    envelope_identity: str
    permit_created: bool
    post_count: int
    external_effect_count: int
    cursor_floor_before: float | None
    cursor_floor_after: float | None
    cursor_persisted: bool
    first_genuine_blocker: str
    blocker_class: str
    next_required_owner_decision: str
    lock_released: str
    ledger_state: str
    transitions: tuple[str, ...]
    extra: dict[str, str] = field(default_factory=dict)


def _token(value: bool) -> str:
    return TRUE_TOKEN if value else FALSE_TOKEN


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _binding_digest(authorization: CurrentProductiveGovernedCycleAuthorizationV1) -> str:
    material = "|".join(
        [
            authorization.cycle_owner_go,
            authorization.native_id,
            authorization.bar,
            str(float(authorization.expected_cursor_floor)),
        ]
    )
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
        raise CurrentProductiveGovernedCycleOrchestratorError("MAX_POSITIONS_DRIFT")
    if STEP_29Q_PLAN_ONLY != "PLAN_ONLY":
        raise CurrentProductiveGovernedCycleOrchestratorError("STEP_29Q_DRIFT")
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_SEND_PIN_DRIFT)
    if AUTONOMY_CAN_MINT_PERMIT is True or AUTONOMY_CAN_POST is True:
        raise CurrentProductiveGovernedCycleOrchestratorError("AUTONOMY_SEND_DRIFT")
    if DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT != "FORBIDDEN":
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_DIRECT_V5_PIN_DRIFT)
    if S4A_V5_EXECUTE_NETWORK is True or S5_V5_EXECUTE_NETWORK is True:
        raise CurrentProductiveGovernedCycleOrchestratorError("V5_EXECUTE_NETWORK_PIN_DRIFT")


def _validate_authorization(
    authorization: CurrentProductiveGovernedCycleAuthorizationV1,
) -> None:
    if authorization.cycle_owner_go == OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_PERSIST_GO_NOT_RUNTIME_LICENSE)
    if authorization.cycle_owner_go == REMAINDER_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(
            REASON_REMAINDER_IS_NOT_CONSUME_LICENSE
        )
    if authorization.cycle_owner_go == POST_NEXT_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_POST_GO_IN_CYCLE_AUTHORIZATION)
    if authorization.cycle_owner_go != RUNTIME_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_OWNER_GO_MISMATCH)
    tokens = (
        authorization.cycle_owner_go,
        authorization.get_owner_go,
        authorization.eg_owner_go,
        authorization.occupancy_owner_go,
        authorization.t2_owner_go,
    )
    if len(set(tokens)) != 5:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_GO_IDENTITY_COLLAPSE)
    if authorization.get_owner_go != GET_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_SUBORDINATE_GO_MISMATCH)
    if (
        authorization.eg_owner_go != EG_OWNER_GO
        or authorization.eg_owner_go != RUNTIME_TRIGGER_OWNER_GO
    ):
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_SUBORDINATE_GO_MISMATCH)
    if authorization.occupancy_owner_go != OCCUPANCY_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_SUBORDINATE_GO_MISMATCH)
    if authorization.t2_owner_go != T2_RUNTIME_OWNER_GO:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_SUBORDINATE_GO_MISMATCH)
    if POST_NEXT_OWNER_GO in tokens or EG_PERSIST_GO in tokens:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_GO_IDENTITY_COLLAPSE)
    if authorization.bar != "1m":
        raise CurrentProductiveGovernedCycleOrchestratorError("BAR_MISMATCH")
    if not str(authorization.native_id or "").strip():
        raise CurrentProductiveGovernedCycleOrchestratorError("NATIVE_ID_MISSING")


def bind_s5_governed_cycle_orchestrator_offline_v1(
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
        "remainder_is_consume_license": FALSE_TOKEN,
        "direct_v5": DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
        "post_count": "0",
    }


def run_current_productive_governed_cycle_v1(
    *,
    authorization: CurrentProductiveGovernedCycleAuthorizationV1,
    origin_main_sha: str,
    cursor_store_root: Path,
    lock_root: Path,
    evidence_root: Path,
    candles_payload: Mapping[str, Any] | None = None,
    occupancy_payloads: Mapping[str, Any] | None = None,
    execute_network: bool = False,
    perform_get: bool = False,
    eg_cycle_dispatch: CycleDispatchV1 | None = None,
    t2_cycle_dispatch: CycleDispatchV1 | None = None,
) -> CurrentProductiveGovernedCycleResultV1:
    _assert_standing_pins()
    _validate_authorization(authorization)
    if execute_network is True or perform_get is True:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_NETWORK_NOT_AUTHORIZED)
    if candles_payload is None:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_INJECTED_C1_REQUIRED)

    get_auth = bind_s4a_fresh_c1_get_runtime_authority_v1(
        owner_go=authorization.get_owner_go,
        cursor_store_root=Path(cursor_store_root),
    )
    if get_auth.disposition != DISPOSITION_PRESENT:
        raise CurrentProductiveGovernedCycleOrchestratorError(
            get_auth.reason_code or REASON_SUBORDINATE_GO_MISMATCH
        )
    eg_auth = bind_s4a_eg_runtime_trigger_authority_v1(owner_go=authorization.eg_owner_go)
    if eg_auth.disposition != DISPOSITION_PRESENT:
        raise CurrentProductiveGovernedCycleOrchestratorError(
            eg_auth.reason_code or REASON_SUBORDINATE_GO_MISMATCH
        )

    Path(evidence_root).mkdir(parents=True, exist_ok=True)
    Path(lock_root).mkdir(parents=True, exist_ok=True)
    ledger = _load_ledger(Path(evidence_root))
    digest = _binding_digest(authorization)
    prior_state = str(ledger.get("state") or STATE_IDLE)
    if prior_state == STATE_IN_PROGRESS:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_PARTIAL_NOT_RESUMABLE)
    if prior_state == STATE_FAILED_STOP:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_PARTIAL_NOT_RESUMABLE)
    if prior_state == STATE_COMPLETED and str(ledger.get("binding_digest") or "") == digest:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_REPLAY)
    if prior_state == STATE_COMPLETED:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_REPLAY)

    lock = AuthorizationLifecycleLockV1(
        lock_path=Path(lock_root) / CYCLE_EXCLUSION_LOCK_NAME,
        authorization_id=CYCLE_EXCLUSION_AUTHORIZATION_ID,
        owner="current_productive_governed_cycle_orchestrator_v1",
    )
    try:
        lock.acquire()
    except LifecycleLockError as exc:
        raise CurrentProductiveGovernedCycleOrchestratorError(REASON_CONCURRENT_CYCLE) from exc

    transitions = [STATE_IDLE, STATE_IN_PROGRESS]
    get_consumed = False
    eg_consumed = False
    occupancy_consumed = False
    t2_consumed = False
    occupancy_disposition = "NOT_REACHED"
    occupancy_used = ""
    k1_ledger_extra: dict[str, str] = {}
    decision_result = "NOT_REACHED"
    eligible = FALSE_TOKEN
    master_v2_decision = ""
    venue_plan_status = ""
    envelope_id = ""
    envelope_digest = ""
    permit_created = False
    post_count = 0
    runtime_cycle_count = 0
    t2_consume_count = 0
    eg_dispatch_count = 0
    cursor_floor_before: float | None = None
    c1_used = ""
    first_blocker = ""
    blocker_class = ""
    terminal_class = ""
    disposition = DISPOSITION_FAIL_CLOSED
    reason_code = ""
    next_owner = ""

    def _write_ledger(*, state: str, extra: Mapping[str, Any] | None = None) -> None:
        payload = {
            "state": state,
            "binding_digest": digest,
            "cycle_owner_go": authorization.cycle_owner_go,
            "get_consumed": get_consumed,
            "eg_consumed": eg_consumed,
            "occupancy_consumed": occupancy_consumed,
            "t2_consumed": t2_consumed,
            "native_id": authorization.native_id,
            "expected_cursor_floor": authorization.expected_cursor_floor,
            "CURSOR_FILE": CURSOR_FILENAME,
            "POST_COUNT": "0",
            "PERMIT_CREATED": FALSE_TOKEN,
        }
        payload.update(k1_ledger_extra)
        if extra:
            payload.update(dict(extra))
        _persist_json(path=Path(evidence_root) / LEDGER_FILENAME, payload=payload)
        trans_path = Path(evidence_root) / "transitions.jsonl"
        with trans_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")

    (Path(evidence_root) / "eg_lock").mkdir(parents=True, exist_ok=True)
    try:
        _write_ledger(state=STATE_IN_PROGRESS)
        mapped = map_injected_candles_payload_to_current_productive_c1_observation_v1(
            owner_go=EH_SEAM_OWNER_GO,
            candles_payload=candles_payload,
            native_id=authorization.native_id,
        )
        get_consumed = True
        if mapped.disposition != DISPOSITION_EMITTED or mapped.observation is None:
            first_blocker = mapped.reason_code or "C1_UNFINALIZED"
            blocker_class = "MARKET_STATE_REQUIRED"
            terminal_class = "FRESHNESS_FAILURE"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class=terminal_class,
                get_consumed=get_consumed,
                eg_consumed=False,
                occupancy_consumed=False,
                t2_consumed=False,
                get_consume_count=1,
                first_genuine_blocker=first_blocker,
                blocker_class=blocker_class,
                next_required_owner_decision=(
                    "Fresh finalized C1 is required. Cycle stopped before EG/occupancy/T2. "
                    "Do not silently resume this partial cycle."
                ),
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                cursor_floor_before=authorization.expected_cursor_floor,
            )
        observation = mapped.observation
        if (
            observation.native_id != authorization.native_id
            or observation.bar != authorization.bar
            or str(observation.confirm) != "1"
        ):
            first_blocker = "BOUND_C1_IDENTITY_MISMATCH"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="C1_MISMATCH",
                get_consumed=True,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="Fail-closed C1 identity mismatch. Do not resume.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=_c1_text(observation),
                cursor_floor_before=authorization.expected_cursor_floor,
            )
        freshness = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
            owner_go=EH_SEAM_OWNER_GO,
            cursor_store_root=Path(cursor_store_root),
            observation=observation,
        )
        cursor_floor_before = freshness.floor_venue_event_time
        if float(cursor_floor_before or 0) != float(authorization.expected_cursor_floor):
            first_blocker = "CURSOR_FLOOR_BINDING_MISMATCH"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="CURSOR_BINDING_FAILURE",
                get_consumed=True,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="Persisted cursor floor did not match authorization.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=_c1_text(observation),
                cursor_floor_before=cursor_floor_before,
            )
        c1_used = _c1_text(observation)
        if freshness.disposition != DISPOSITION_EMITTED:
            first_blocker = freshness.reason_code or "C1_NOT_FRESH_VS_CURSOR"
            blocker_class = "MARKET_STATE_REQUIRED"
            terminal_class = "FRESHNESS_FAILURE"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class=terminal_class,
                get_consumed=True,
                first_genuine_blocker=first_blocker,
                blocker_class=blocker_class,
                next_required_owner_decision=(
                    "C1 is not newer than persisted cursor. EG/occupancy/T2 not consumed. "
                    "Do not silently resume this partial cycle."
                ),
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        gate = _evaluate_c1_gate_v1(payload=dict(observation.payload or {}))
        if str(gate.get("CONDITION_GATE") or "") != "SATISFIED":
            first_blocker = "T2_GATE_NOT_SATISFIED"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="T2_GATE_FAILURE",
                get_consumed=True,
                first_genuine_blocker=first_blocker,
                blocker_class="AUTHORITY_REQUIRED",
                next_required_owner_decision=(
                    f"Bound C1 must have venue_event_time > {PREVIOUS_C1_VENUE_EVENT_TIME}."
                ),
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )

        try:
            eg_result = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
                owner_go=authorization.eg_owner_go,
                origin_main_sha=origin_main_sha,
                observation=CurrentProductiveC1ObservationV1(
                    venue_event_time=observation.venue_event_time,
                    confirm=observation.confirm,
                    native_id=observation.native_id,
                    bar=observation.bar,
                    payload=observation.payload,
                ),
                cursor_store_root=Path(cursor_store_root),
                lock_root=Path(evidence_root) / "eg_lock",
                evidence_root=Path(evidence_root) / "eg",
                cycle_dispatch=eg_cycle_dispatch or _reject_default_v5_as_t2_substitute,
            )
        except (
            CurrentProductiveGovernedNextC1OrchestrationError,
            CurrentProductiveGovernedCycleOrchestratorError,
        ) as exc:
            first_blocker = exc.reason_code
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="EG_FAILURE",
                get_consumed=True,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="EG failed closed. Do not resume this partial cycle.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        eg_consumed = True
        eg_dispatch_count = int(eg_result.dispatch_count)
        if eg_dispatch_count != 1:
            first_blocker = f"EG_DISPATCH_COUNT_NOT_1:{eg_result.reason_code}"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="EG_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="EG did not dispatch exactly once. Do not resume.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )

        k1_bind = bind_k1_credential_capability_for_governed_cycle_occupancy_v1()
        if k1_bind.material_loaded != FALSE_TOKEN:
            first_blocker = "K1_CREDENTIAL_MATERIAL_LOADED_FORBIDDEN"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="K1_BIND_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision=(
                    "K1 occupancy bind must not load credential material. Do not resume."
                ),
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        k1_ledger_extra.update(
            {
                "K1_CREDENTIAL_BIND": k1_bind.disposition,
                "K1_RESOLVE_FAIL_CLOSED": k1_bind.resolve_fail_closed,
                "K1_MATERIAL_LOADED": k1_bind.material_loaded,
                "K1_SEND_HANDLE_JOINED": k1_bind.send_handle_joined,
                "K1_V5_JOINED": k1_bind.v5_joined,
                "K1_PERMIT_CREATED": k1_bind.permit_created,
                "K1_POST_COUNT": k1_bind.post_count,
            }
        )
        _write_ledger(state=STATE_IN_PROGRESS)

        if occupancy_payloads is None:
            first_blocker = "OCCUPANCY_PAYLOADS_REQUIRED_OFFLINE"
            reason_code = first_blocker
            occupancy_consumed = False
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="OCCUPANCY_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                first_genuine_blocker=first_blocker,
                blocker_class="IMPLEMENTATION_REQUIRED",
                next_required_owner_decision="Offline occupancy payloads were not injected.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        occupancy_facts = _classify_occupancy_v1(
            positions_payload=occupancy_payloads.get("POSITIONS"),
            pending_payload=occupancy_payloads.get("PENDING"),
            config_payload=occupancy_payloads.get("CONFIG"),
            positions_error=str(occupancy_payloads.get("POSITIONS_ERROR") or ""),
            pending_error=str(occupancy_payloads.get("PENDING_ERROR") or ""),
            config_error=str(occupancy_payloads.get("CONFIG_ERROR") or ""),
        )
        occupancy_consumed = True
        occupancy_disposition = str(occupancy_facts.get("OCCUPANCY_STATUS") or "UNKNOWN")
        occupancy_used = occupancy_disposition
        pending_status = str(occupancy_facts.get("PENDING_ORDERS_STATUS") or "")
        if occupancy_disposition not in {"OCCUPANCY_ABSENT"} or pending_status not in {
            "NONE_OBSERVED",
            "",
        }:
            first_blocker = (
                occupancy_disposition
                if occupancy_disposition != "OCCUPANCY_ABSENT"
                else pending_status
            )
            blocker_class = (
                "MARKET_STATE_REQUIRED"
                if occupancy_disposition in {"OCCUPANCY_PRESENT", "UNKNOWN"}
                or pending_status == "PENDING_ORDERS_PRESENT"
                else "UNKNOWN_OR_CONFLICTING"
            )
            terminal_class = "OCCUPANCY_FAILURE"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class=terminal_class,
                get_consumed=True,
                eg_consumed=True,
                occupancy_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                occupancy_disposition=occupancy_disposition,
                occupancy_used=occupancy_used,
                first_genuine_blocker=first_blocker,
                blocker_class=blocker_class,
                next_required_owner_decision=(
                    "Occupancy/pending is not absent. T2 not consumed. Do not resume."
                ),
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )

        t2_dispatch = t2_cycle_dispatch or _reject_default_v5_as_direct_entrypoint
        try:
            t2_result = t2_dispatch(
                owner_go=authorization.t2_owner_go,
                origin_main_sha=origin_main_sha,
                observation=observation,
                occupancy_status=occupancy_disposition,
            )
        except CurrentProductiveGovernedCycleOrchestratorError as exc:
            first_blocker = exc.reason_code
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": first_blocker})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=first_blocker,
                terminal_class="T2_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                occupancy_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                occupancy_disposition=occupancy_disposition,
                occupancy_used=occupancy_used,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="T2/V5 N=1 failed closed. Do not resume this partial cycle.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        except Exception:
            first_blocker = "T2_CYCLE_EXCEPTION"
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": first_blocker})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=first_blocker,
                terminal_class="T2_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                occupancy_consumed=True,
                eg_dispatch_count=eg_dispatch_count,
                occupancy_disposition=occupancy_disposition,
                occupancy_used=occupancy_used,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="T2/V5 N=1 failed closed. Do not resume this partial cycle.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )
        t2_consumed = True
        t2_consume_count = 1
        runtime_cycle_count = int(str(getattr(t2_result, "runtime_cycle_count", "1") or "1"))
        decision_result = str(getattr(t2_result, "decision_result", "") or "")
        eligible = str(
            getattr(t2_result, "decision_execution_eligible", FALSE_TOKEN) or FALSE_TOKEN
        )
        master_v2_decision = str(getattr(t2_result, "master_v2_decision", "") or "")
        venue_plan_status = str(getattr(t2_result, "venue_plan_status", "") or "")
        envelope_id = str(getattr(t2_result, "final_envelope_id", "") or "")
        envelope_digest = str(getattr(t2_result, "final_envelope_digest", "") or "")
        permit_created = str(getattr(t2_result, "permit_created", FALSE_TOKEN)).lower() == "true"
        post_count = int(str(getattr(t2_result, "post_count", "0") or "0"))
        first_blocker = str(getattr(t2_result, "first_real_blocker", "") or "")
        if permit_created or post_count != 0:
            first_blocker = "EXTERNAL_EFFECT_OR_POST_LEAK"
            reason_code = first_blocker
            _write_ledger(state=STATE_FAILED_STOP, extra={"reason_code": reason_code})
            return _result(
                disposition=DISPOSITION_FAIL_CLOSED,
                reason_code=reason_code,
                terminal_class="T2_FAILURE",
                get_consumed=True,
                eg_consumed=True,
                occupancy_consumed=True,
                t2_consumed=True,
                get_consume_count=1,
                eg_dispatch_count=eg_dispatch_count,
                occupancy_disposition=occupancy_disposition,
                occupancy_used=occupancy_used,
                t2_consume_count=1,
                first_genuine_blocker=first_blocker,
                blocker_class="UNKNOWN_OR_CONFLICTING",
                next_required_owner_decision="POST/permit leak is forbidden. Do not resume.",
                lock_released=_token(True),
                ledger_state=STATE_FAILED_STOP,
                transitions=tuple(transitions + [STATE_FAILED_STOP]),
                c1_used=c1_used,
                cursor_floor_before=cursor_floor_before,
            )

        transitions.append(STATE_COMPLETED)
        if decision_result == "EXECUTABLE_VENUE_PLAN_BOUND" and eligible.lower() == "true":
            disposition = DISPOSITION_PRE_EXTERNAL_EFFECT
            terminal_class = "PRE_EXTERNAL_EFFECT"
            blocker_class = "PRE_EXTERNAL_EFFECT"
            first_blocker = first_blocker or POST_NEXT_OWNER_GO
            reason_code = first_blocker
            next_owner = (
                f"Authorize or withhold {POST_NEXT_OWNER_GO} for one envelope-bound "
                "single-use permit/POST. Cycle GO does not compose POST."
            )
        else:
            disposition = DISPOSITION_HOLD
            terminal_class = "MARKET_STATE_REQUIRED"
            blocker_class = "MARKET_STATE_REQUIRED"
            first_blocker = first_blocker or "HOLD"
            reason_code = first_blocker
            next_owner = (
                "HOLD/non-executable is a valid terminal trading outcome. Do not force ENTER. "
                f"Remainder {REMAINDER_OWNER_GO} is not a consume license. POST unauthorized."
            )
        _write_ledger(
            state=STATE_COMPLETED,
            extra={
                "reason_code": reason_code,
                "terminal_class": terminal_class,
                "decision_result": decision_result,
            },
        )
        return _result(
            disposition=disposition,
            reason_code=reason_code,
            terminal_class=terminal_class,
            get_consumed=True,
            eg_consumed=True,
            occupancy_consumed=True,
            t2_consumed=True,
            get_consume_count=1,
            eg_dispatch_count=eg_dispatch_count,
            occupancy_disposition=occupancy_disposition,
            occupancy_used=occupancy_used,
            t2_consume_count=t2_consume_count,
            runtime_cycle_count=runtime_cycle_count,
            c1_used=c1_used,
            decision_result=decision_result,
            decision_execution_eligible=eligible,
            master_v2_decision=master_v2_decision,
            venue_plan_status=venue_plan_status,
            envelope_created=bool(envelope_id),
            envelope_identity=(
                f"envelope_id={envelope_id};digest={envelope_digest}" if envelope_id else ""
            ),
            first_genuine_blocker=first_blocker,
            blocker_class=blocker_class,
            next_required_owner_decision=next_owner,
            lock_released=_token(True),
            ledger_state=STATE_COMPLETED,
            transitions=tuple(transitions + [STATE_IDLE]),
            cursor_floor_before=cursor_floor_before,
            cursor_floor_after=cursor_floor_before,
        )
    finally:
        lock.release()


def _reject_default_v5_as_t2_substitute(**_kwargs: Any) -> Any:
    return type("EgHostStub", (), {"permit_created": FALSE_TOKEN, "post_count": "0"})()


def _reject_default_v5_as_direct_entrypoint(**_kwargs: Any) -> Any:
    raise CurrentProductiveGovernedCycleOrchestratorError(
        "T2_CYCLE_DISPATCH_REQUIRED_OFFLINE_NO_DIRECT_V5"
    )


def _c1_text(observation: CurrentProductiveC1ObservationV1) -> str:
    return (
        f"native_id={observation.native_id};bar={observation.bar};"
        f"confirm={observation.confirm};venue_event_time={float(observation.venue_event_time)}"
    )


def _result(
    *,
    disposition: str,
    reason_code: str,
    terminal_class: str,
    get_consumed: bool = False,
    eg_consumed: bool = False,
    occupancy_consumed: bool = False,
    t2_consumed: bool = False,
    get_consume_count: int = 0,
    eg_dispatch_count: int = 0,
    occupancy_disposition: str = "NOT_REACHED",
    occupancy_used: str = "",
    t2_consume_count: int = 0,
    runtime_cycle_count: int = 0,
    c1_used: str = "",
    decision_result: str = "NOT_REACHED",
    decision_execution_eligible: str = FALSE_TOKEN,
    master_v2_decision: str = "",
    venue_plan_status: str = "",
    envelope_created: bool = False,
    envelope_identity: str = "",
    first_genuine_blocker: str = "",
    blocker_class: str = "",
    next_required_owner_decision: str = "",
    lock_released: str = TRUE_TOKEN,
    ledger_state: str = STATE_FAILED_STOP,
    transitions: tuple[str, ...] = (),
    cursor_floor_before: float | None = None,
    cursor_floor_after: float | None = None,
) -> CurrentProductiveGovernedCycleResultV1:
    return CurrentProductiveGovernedCycleResultV1(
        disposition=disposition,
        reason_code=reason_code,
        terminal_class=terminal_class,
        cycle_go_status_after=CONSUMED_THIS_CYCLE_ONLY
        if t2_consumed
        else DEFINED_NOT_CONSUMED
        if not get_consumed
        else CONSUMED_THIS_CYCLE_ONLY,
        get_consumed=get_consumed,
        eg_consumed=eg_consumed,
        occupancy_consumed=occupancy_consumed,
        t2_consumed=t2_consumed,
        get_consume_count=get_consume_count if get_consumed else 0,
        eg_dispatch_count=eg_dispatch_count,
        occupancy_disposition=occupancy_disposition,
        t2_consume_count=t2_consume_count,
        runtime_cycle_count=runtime_cycle_count,
        c1_used=c1_used,
        occupancy_used=occupancy_used,
        decision_result=decision_result,
        decision_execution_eligible=decision_execution_eligible,
        master_v2_decision=master_v2_decision,
        venue_plan_status=venue_plan_status,
        envelope_created=envelope_created,
        envelope_identity=envelope_identity,
        permit_created=False,
        post_count=0,
        external_effect_count=0,
        cursor_floor_before=cursor_floor_before,
        cursor_floor_after=cursor_floor_after
        if cursor_floor_after is not None
        else cursor_floor_before,
        cursor_persisted=False,
        first_genuine_blocker=first_genuine_blocker,
        blocker_class=blocker_class,
        next_required_owner_decision=next_required_owner_decision,
        lock_released=lock_released,
        ledger_state=ledger_state,
        transitions=transitions,
        extra={
            "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
            "DIRECT_V5": DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
            "REMAINDER_IS_CONSUME_LICENSE": FALSE_TOKEN,
        },
    )
