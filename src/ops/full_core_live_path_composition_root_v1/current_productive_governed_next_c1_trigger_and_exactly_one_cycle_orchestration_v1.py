"""CURRENT_PRODUCTIVE next-C1 trigger and exactly-one cycle orchestration.

ORCHESTRATION AUTHORITY ONLY. Reuses the existing V5 N=1 cycle host.
Does not invent trading decisions, reselect Cap-2.3/2.4, mint a permit,
POST, poll, daemonize, or automatically retry after ambiguous failure.

Dedup boundary is the persisted cursor last-accepted venue_event_time.
Single-cycle exclusion reuses AuthorizationLifecycleLockV1 O_CREAT|O_EXCL.
Cap-2.3 universe lock is not cycle exclusion.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_LINEAGE_ID,
    CURSOR_SCHEMA_NAME,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    UrllibEeaPublicUniverseGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    OWNER_GO as V5_OWNER_GO,
    execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_V1"
)
RUNTIME_TRIGGER_OWNER_GO = "OWNER_GO_S4A_EG_EXACTLY_ONE_RUNTIME_TRIGGER_V1"
RUNTIME_TRIGGER_OWNER_GO_SCOPE = "EXACTLY_ONE_EG_DISPATCH_ONLY"
RUNTIME_TRIGGER_OWNER_GO_STATUS = "DEFINED_NOT_CONSUMED"
PRODUCTIVE_ACQUISITION_PRODUCER = "acquire_eea_universe_inventory_v1"
PRODUCTIVE_ACQUISITION_TRANSPORT_CLASS = "UrllibEeaPublicUniverseGetTransportV1"
THIS_SLICE = (
    "11.2.1.EG.FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_"
    "EXACTLY_ONE_CYCLE_ORCHESTRATION"
)
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_SEAM_V1"
OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1"
)
FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY = "NEXT_C1_TRIGGER_AND_SINGLE_CYCLE_ORCHESTRATION_ONLY"
AUTONOMY_CAN_CHANGE_TRADING_LOGIC = False
AUTONOMY_CAN_RESELECT_DOWNSTREAM = False
AUTONOMY_CAN_MINT_PERMIT = False
AUTONOMY_CAN_POST = False
CYCLE_EXCLUSION_LOCK_NAME = "current_productive_cycle_exclusion.lock"
CYCLE_EXCLUSION_AUTHORIZATION_ID = "CURRENT_PRODUCTIVE_EXACTLY_ONE_CYCLE_V1"
REQUIRED_BAR = "1m"
STATE_IDLE = "IDLE"
STATE_NEW_C1_ACCEPTED = "NEW_C1_ACCEPTED"
STATE_CYCLE_IN_PROGRESS = "CYCLE_IN_PROGRESS"
STATE_CYCLE_COMPLETED = "CYCLE_COMPLETED"
STATE_FAILED_STOP = "FAILED_STOP"
DISPOSITION_DISPATCHED = "DISPATCHED"
DISPOSITION_NO_DISPATCH = "NO_DISPATCH"
DISPOSITION_FAILED_STOP = "FAILED_STOP"
REASON_DUPLICATE_C1 = "DUPLICATE_C1"
REASON_STALE_C1 = "STALE_C1"
REASON_UNFINALIZED_C1 = "UNFINALIZED_C1"
REASON_CONCURRENT_CYCLE = "CONCURRENT_CYCLE"
REASON_CURSOR_MISSING = "CURSOR_MISSING"
REASON_CURSOR_INVALID = "CURSOR_INVALID"
REASON_LINEAGE_MISMATCH = "LINEAGE_MISMATCH"
REASON_CYCLE_EXCEPTION = "CYCLE_EXCEPTION"
REASON_OWNER_GO_MISMATCH = "OWNER_GO_MISMATCH"
REASON_PERSIST_GO_NOT_TRIGGER_LICENSE = "PERSIST_GO_NOT_TRIGGER_LICENSE"
REASON_DISPATCHED = "DISPATCHED"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

CycleDispatchV1 = Callable[..., Any]


class CurrentProductiveGovernedNextC1OrchestrationError(ValueError):
    """Fail-closed next-C1 orchestration violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class CurrentProductiveC1ObservationV1:
    venue_event_time: float
    confirm: str
    native_id: str
    bar: str = REQUIRED_BAR
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CurrentProductiveNextC1OrchestrationResultV1:
    state: str
    disposition: str
    reason_code: str
    dispatch_count: int
    accepted_c1_venue_event_time: str
    cursor_c1_venue_event_time: str
    lock_path: str
    lock_released: str
    permit_created: str
    post_count: str
    transitions: tuple[str, ...]
    cycle_result: object | None = None
    authority_boundary: str = FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY
    extra: dict[str, str] = field(default_factory=dict)


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cursor_last_accepted_c1_venue_event_time_v1(cursor: Mapping[str, Any]) -> float:
    try:
        cap61 = cursor["cap61_confirmation_state"]
        if not isinstance(cap61, Mapping):
            raise CurrentProductiveGovernedNextC1OrchestrationError(REASON_CURSOR_INVALID)
        observation = cap61["observation_acceptance_state"]
        if not isinstance(observation, Mapping):
            raise CurrentProductiveGovernedNextC1OrchestrationError(REASON_CURSOR_INVALID)
        identity = observation["last_accepted_observation_identity"]
        if not isinstance(identity, Mapping):
            raise CurrentProductiveGovernedNextC1OrchestrationError(REASON_CURSOR_INVALID)
        return float(identity["venue_event_time"])
    except CurrentProductiveGovernedNextC1OrchestrationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CurrentProductiveGovernedNextC1OrchestrationError(REASON_CURSOR_INVALID) from exc


def _load_cursor_or_reason(cursor_store_root: Path) -> tuple[Mapping[str, Any] | None, str]:
    try:
        loaded = load_current_productive_sidestate_confirmation_cursor_v1(cursor_store_root)
    except Exception:
        return None, REASON_CURSOR_INVALID
    if loaded is None:
        return None, REASON_CURSOR_MISSING
    if not isinstance(loaded, Mapping):
        return None, REASON_CURSOR_INVALID
    if str(loaded.get("schema_name") or "") != CURSOR_SCHEMA_NAME:
        return None, REASON_CURSOR_INVALID
    return loaded, ""


def load_current_productive_c1_cursor_or_reason_v1(
    cursor_store_root: Path,
) -> tuple[Mapping[str, Any] | None, str]:
    return _load_cursor_or_reason(cursor_store_root)


def evaluate_current_productive_c1_reject_reason_v1(
    *,
    observation: CurrentProductiveC1ObservationV1,
    cursor: Mapping[str, Any],
) -> str:
    return _c1_reject_reason(observation=observation, cursor=cursor)


def _c1_reject_reason(
    *,
    observation: CurrentProductiveC1ObservationV1,
    cursor: Mapping[str, Any],
) -> str:
    if str(observation.bar or "").strip() != REQUIRED_BAR:
        return REASON_UNFINALIZED_C1
    if str(observation.confirm or "").strip() != "1":
        return REASON_UNFINALIZED_C1
    if str(cursor.get("lineage_id") or "") != CURSOR_LINEAGE_ID:
        return REASON_LINEAGE_MISMATCH
    if str(cursor.get("venue_native_id") or "").strip() != str(observation.native_id).strip():
        return REASON_LINEAGE_MISMATCH
    try:
        cursor_c1 = cursor_last_accepted_c1_venue_event_time_v1(cursor)
        incoming = float(observation.venue_event_time)
    except CurrentProductiveGovernedNextC1OrchestrationError as exc:
        return exc.reason_code
    except (TypeError, ValueError):
        return REASON_UNFINALIZED_C1
    if incoming == cursor_c1:
        return REASON_DUPLICATE_C1
    if incoming < cursor_c1:
        return REASON_STALE_C1
    if incoming > cursor_c1:
        return ""
    return REASON_UNFINALIZED_C1


def _inject_productive_acquisition_join(kwargs: dict[str, Any]) -> dict[str, Any]:
    kwargs["execute_network"] = False
    if kwargs.get("acquisition_transport") is None and kwargs.get("acquisition_result") is None:
        kwargs["acquisition_transport"] = UrllibEeaPublicUniverseGetTransportV1()
    return kwargs


def _default_v5_dispatch(**kwargs: Any) -> Any:
    kwargs.setdefault("owner_go", V5_OWNER_GO)
    kwargs = _inject_productive_acquisition_join(kwargs)
    return execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        **kwargs
    )


def _no_dispatch_result(
    *,
    reason_code: str,
    cursor_c1: str = "",
    lock_path: str = "",
    lock_released: bool = True,
    transitions: tuple[str, ...] = (STATE_IDLE,),
) -> CurrentProductiveNextC1OrchestrationResultV1:
    return CurrentProductiveNextC1OrchestrationResultV1(
        state=STATE_IDLE,
        disposition=DISPOSITION_NO_DISPATCH,
        reason_code=reason_code,
        dispatch_count=0,
        accepted_c1_venue_event_time="",
        cursor_c1_venue_event_time=cursor_c1,
        lock_path=lock_path,
        lock_released=_token(lock_released),
        permit_created=FALSE_TOKEN,
        post_count="0",
        transitions=transitions,
        cycle_result=None,
    )


def trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    observation: CurrentProductiveC1ObservationV1,
    cursor_store_root: Path,
    lock_root: Path,
    evidence_root: Path | None = None,
    cycle_dispatch: CycleDispatchV1 | None = None,
    v5_kwargs: Mapping[str, Any] | None = None,
) -> CurrentProductiveNextC1OrchestrationResultV1:
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveGovernedNextC1OrchestrationError("MAX_POSITIONS_DRIFT")
    if STEP_29Q_PLAN_ONLY != "PLAN_ONLY":
        raise CurrentProductiveGovernedNextC1OrchestrationError("STEP_29Q_DRIFT")
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise CurrentProductiveGovernedNextC1OrchestrationError("SEND_AUTHORITY_DRIFT")
    if AUTONOMY_CAN_MINT_PERMIT is True or AUTONOMY_CAN_POST is True:
        raise CurrentProductiveGovernedNextC1OrchestrationError("AUTONOMY_SEND_DRIFT")
    if owner_go == OWNER_GO:
        raise CurrentProductiveGovernedNextC1OrchestrationError(
            REASON_PERSIST_GO_NOT_TRIGGER_LICENSE
        )
    if owner_go != RUNTIME_TRIGGER_OWNER_GO:
        raise CurrentProductiveGovernedNextC1OrchestrationError(REASON_OWNER_GO_MISMATCH)

    lock = AuthorizationLifecycleLockV1(
        lock_path=Path(lock_root) / CYCLE_EXCLUSION_LOCK_NAME,
        authorization_id=CYCLE_EXCLUSION_AUTHORIZATION_ID,
        owner=OWNER,
    )
    try:
        lock.acquire()
    except LifecycleLockError:
        return _no_dispatch_result(
            reason_code=REASON_CONCURRENT_CYCLE,
            lock_path=str(lock.lock_path),
            lock_released=False,
        )

    transitions = [STATE_IDLE]
    cursor_c1_text = ""
    try:
        cursor, cursor_reason = _load_cursor_or_reason(Path(cursor_store_root))
        if cursor is None:
            lock.release()
            return _no_dispatch_result(
                reason_code=cursor_reason,
                lock_path=str(lock.lock_path),
                lock_released=True,
            )
        try:
            cursor_c1_text = str(cursor_last_accepted_c1_venue_event_time_v1(cursor))
        except CurrentProductiveGovernedNextC1OrchestrationError as exc:
            lock.release()
            return _no_dispatch_result(
                reason_code=exc.reason_code,
                lock_path=str(lock.lock_path),
                lock_released=True,
            )
        reject = _c1_reject_reason(observation=observation, cursor=cursor)
        if reject:
            lock.release()
            return _no_dispatch_result(
                reason_code=reject,
                cursor_c1=cursor_c1_text,
                lock_path=str(lock.lock_path),
                lock_released=True,
            )

        transitions.append(STATE_NEW_C1_ACCEPTED)
        transitions.append(STATE_CYCLE_IN_PROGRESS)
        dispatch = cycle_dispatch if cycle_dispatch is not None else _default_v5_dispatch
        kwargs: dict[str, Any] = {
            "owner_go": V5_OWNER_GO,
            "origin_main_sha": origin_main_sha,
            "incoming_cursor": cursor,
            "cursor_store_root": Path(cursor_store_root),
            "execute_network": False,
        }
        if observation.payload is not None:
            kwargs["c1_gate_payload"] = dict(observation.payload)
        if evidence_root is not None:
            kwargs["evidence_root"] = Path(evidence_root) / "cycle"
        if v5_kwargs:
            kwargs.update(dict(v5_kwargs))
        kwargs = _inject_productive_acquisition_join(kwargs)
        cycle_result = dispatch(**kwargs)
        transitions.append(STATE_CYCLE_COMPLETED)
        transitions.append(STATE_IDLE)
        permit_created = FALSE_TOKEN
        post_count = "0"
        if cycle_result is not None:
            permit_created = str(
                getattr(cycle_result, "permit_created", FALSE_TOKEN) or FALSE_TOKEN
            )
            post_count = str(getattr(cycle_result, "post_count", "0") or "0")
        if permit_created.lower() == TRUE_TOKEN or post_count not in {"", "0"}:
            raise CurrentProductiveGovernedNextC1OrchestrationError("ORCHESTRATOR_SEND_LEAK")
        result = CurrentProductiveNextC1OrchestrationResultV1(
            state=STATE_IDLE,
            disposition=DISPOSITION_DISPATCHED,
            reason_code=REASON_DISPATCHED,
            dispatch_count=1,
            accepted_c1_venue_event_time=str(float(observation.venue_event_time)),
            cursor_c1_venue_event_time=cursor_c1_text,
            lock_path=str(lock.lock_path),
            lock_released=TRUE_TOKEN,
            permit_created=FALSE_TOKEN,
            post_count="0",
            transitions=tuple(transitions),
            cycle_result=cycle_result,
        )
        if evidence_root is not None:
            _persist_json(
                path=Path(evidence_root) / "orchestration_v1.json",
                payload={
                    "THIS_SLICE": THIS_SLICE,
                    "OWNER_GO": OWNER_GO,
                    "JOIN_SEAM_ID": JOIN_SEAM_ID,
                    "FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY": (
                        FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY
                    ),
                    "AUTONOMY_CAN_CHANGE_TRADING_LOGIC": _token(AUTONOMY_CAN_CHANGE_TRADING_LOGIC),
                    "AUTONOMY_CAN_RESELECT_DOWNSTREAM": _token(AUTONOMY_CAN_RESELECT_DOWNSTREAM),
                    "AUTONOMY_CAN_MINT_PERMIT": FALSE_TOKEN,
                    "AUTONOMY_CAN_POST": FALSE_TOKEN,
                    "STATE": result.state,
                    "DISPOSITION": result.disposition,
                    "REASON_CODE": result.reason_code,
                    "DISPATCH_COUNT": str(result.dispatch_count),
                    "PERMIT_CREATED": FALSE_TOKEN,
                    "POST_COUNT": "0",
                    "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
                    "CURSOR_FILE": CURSOR_FILENAME,
                    "LOCK_RELEASED": result.lock_released,
                },
            )
        lock.release()
        return result
    except CurrentProductiveGovernedNextC1OrchestrationError:
        raise
    except Exception:
        if evidence_root is not None:
            _persist_json(
                path=Path(evidence_root) / "orchestration_failed_stop_v1.json",
                payload={
                    "STATE": STATE_FAILED_STOP,
                    "DISPOSITION": DISPOSITION_FAILED_STOP,
                    "REASON_CODE": REASON_CYCLE_EXCEPTION,
                    "DISPATCH_COUNT": "1",
                    "NO_AUTOMATIC_RETRY": TRUE_TOKEN,
                    "LOCK_RELEASED": FALSE_TOKEN,
                    "PERMIT_CREATED": FALSE_TOKEN,
                    "POST_COUNT": "0",
                },
            )
        return CurrentProductiveNextC1OrchestrationResultV1(
            state=STATE_FAILED_STOP,
            disposition=DISPOSITION_FAILED_STOP,
            reason_code=REASON_CYCLE_EXCEPTION,
            dispatch_count=1,
            accepted_c1_venue_event_time=str(float(observation.venue_event_time)),
            cursor_c1_venue_event_time=cursor_c1_text,
            lock_path=str(lock.lock_path),
            lock_released=FALSE_TOKEN,
            permit_created=FALSE_TOKEN,
            post_count="0",
            transitions=tuple(transitions + [STATE_FAILED_STOP]),
            cycle_result=None,
        )
