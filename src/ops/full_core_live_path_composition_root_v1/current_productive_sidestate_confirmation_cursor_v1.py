"""CURRENT_PRODUCTIVE one-shot SideState/confirmation cursor persist/restore.

Joins the already-closed §11.2.1.C–H SideState persist authority and
Cap-6.2 ScopeConfirmation / CanonicalScopeSnapshot contracts into the
CURRENT_PRODUCTIVE one-shot host. Does not redesign Master-V2, Double Play,
confirmation thresholds, Bull/Bear, or entry/exit rules.

Missing cursor defaults to Cap-6.2 NEUTRAL_OBSERVE. Invalid SideState
fails closed like Cap-7.2. Instrument/lineage/schema mismatch refuses
restore and never leaks foreign state. Restore never invents ARMED/ENTER.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_CONFIRMATION_EPOCHS,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    canonical_scope_snapshot_from_dict,
    canonical_scope_snapshot_to_dict,
    runtime_scope_state_from_dict,
    runtime_scope_state_to_dict,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.models_v1 import (
    CanonicalConfirmationStateV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.sidestate_restore_v1 import (
    SideStateRestoreError,
    parse_persisted_side_state_v1,
)
from trading.master_v2.canonical_scope_initialization_v1 import CanonicalScopeSnapshotV1
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
)
from trading.master_v2.double_play_state import RuntimeScopeState, SideState

CURSOR_SCHEMA_NAME = "current_productive_sidestate_confirmation_cursor.v1"
CURSOR_SCHEMA_VERSION = "v1"
CURSOR_LINEAGE_ID = "CURRENT_PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_LINEAGE_V1"
CURSOR_FILENAME = "current_productive_sidestate_confirmation_cursor_v1.json"
CURSOR_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_sidestate_confirmation_cursor_v1"
)

RESTORE_MISSING = "missing"
RESTORE_RESTORED = "restored"
RESTORE_REFUSED_MISMATCH = "refused_mismatch"
RESTORE_REFUSED_STALE = "refused_stale"
RESTORE_FAIL_CLOSED_CORRUPT = "fail_closed_corrupt"
RESTORE_FAIL_CLOSED_INVALID_SIDESTATE = "fail_closed_invalid_sidestate"
RESTORE_NOT_APPLICABLE_OCCUPIED = "not_applicable_occupied"

ACTIVE_FLAT_INCOMPATIBLE_SIDESTATES = frozenset(
    {
        SideState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE,
        SideState.LONG_BLOCKED,
        SideState.SHORT_BLOCKED,
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    }
)


class CurrentProductiveCursorError(ValueError):
    """Fail-closed CURRENT_PRODUCTIVE cursor persist/restore violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


class CursorRestoreDispositionV1(str, Enum):
    MISSING = RESTORE_MISSING
    RESTORED = RESTORE_RESTORED
    REFUSED_MISMATCH = RESTORE_REFUSED_MISMATCH
    REFUSED_STALE = RESTORE_REFUSED_STALE
    FAIL_CLOSED_CORRUPT = RESTORE_FAIL_CLOSED_CORRUPT
    FAIL_CLOSED_INVALID_SIDESTATE = RESTORE_FAIL_CLOSED_INVALID_SIDESTATE
    NOT_APPLICABLE_OCCUPIED = RESTORE_NOT_APPLICABLE_OCCUPIED


@dataclass(frozen=True)
class CurrentProductiveSideStateConfirmationCursorV1:
    schema_name: str
    schema_version: str
    lineage_id: str
    instrument_id: str
    venue_native_id: str
    trading_epoch: int
    last_evaluated_trading_epoch: int
    now_tick: int
    side_state: SideState
    confirmation_epochs: int
    scope_confirmation: ScopeConfirmationStateV1
    existing_scope: Optional[CanonicalScopeSnapshotV1]
    runtime_scope_state: Optional[RuntimeScopeState]
    cap61_confirmation_state: Optional[CanonicalConfirmationStateV1]

    def to_dict(self) -> dict[str, Any]:
        kind = self.scope_confirmation.candidate_kind
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "lineage_id": self.lineage_id,
            "instrument_id": self.instrument_id,
            "venue_native_id": self.venue_native_id,
            "trading_epoch": int(self.trading_epoch),
            "last_evaluated_trading_epoch": int(self.last_evaluated_trading_epoch),
            "now_tick": int(self.now_tick),
            "side_state": self.side_state.value,
            "confirmation_epochs": int(self.confirmation_epochs),
            "scope_confirmation": {
                "candidate_kind": None if kind is None else str(kind.value),
                "candidate_count": int(self.scope_confirmation.candidate_count),
                "last_evaluated_trading_epoch": int(
                    self.scope_confirmation.last_evaluated_trading_epoch
                ),
            },
            "existing_scope": (
                None
                if self.existing_scope is None
                else canonical_scope_snapshot_to_dict(self.existing_scope)
            ),
            "runtime_scope_state": (
                None
                if self.runtime_scope_state is None
                else runtime_scope_state_to_dict(self.runtime_scope_state)
            ),
            "cap61_confirmation_state": (
                None
                if self.cap61_confirmation_state is None
                else self.cap61_confirmation_state.to_dict()
            ),
        }


@dataclass(frozen=True)
class CurrentProductiveCursorRestoreResultV1:
    disposition: CursorRestoreDispositionV1
    cursor: Optional[CurrentProductiveSideStateConfirmationCursorV1]
    reason_code: str
    fail_closed: bool


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _text(value: object) -> str:
    return str(value or "").strip()


def _parse_candidate_kind(raw: object) -> Optional[ScopeCandidateKind]:
    if raw is None:
        return None
    if isinstance(raw, ScopeCandidateKind):
        return raw
    text = _text(raw)
    if not text:
        return None
    try:
        return ScopeCandidateKind(text)
    except ValueError as exc:
        raise CurrentProductiveCursorError("CURSOR_CONFIRMATION_KIND_INVALID", text) from exc


def _parse_int(raw: object, *, field: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise CurrentProductiveCursorError("CURSOR_FIELD_UNPARSEABLE", field)
    return int(raw)


def parse_current_productive_sidestate_confirmation_cursor_v1(
    payload: Mapping[str, Any],
) -> CurrentProductiveSideStateConfirmationCursorV1:
    if not isinstance(payload, Mapping):
        raise CurrentProductiveCursorError("CURSOR_PAYLOAD_NOT_OBJECT")
    schema_name = _text(payload.get("schema_name"))
    schema_version = _text(payload.get("schema_version"))
    lineage_id = _text(payload.get("lineage_id"))
    instrument_id = _text(payload.get("instrument_id"))
    venue_native_id = _text(payload.get("venue_native_id"))
    if not instrument_id or not venue_native_id:
        raise CurrentProductiveCursorError("CURSOR_INSTRUMENT_BINDING_MISSING")
    confirmation_raw = payload.get("scope_confirmation")
    if not isinstance(confirmation_raw, Mapping):
        raise CurrentProductiveCursorError("CURSOR_CONFIRMATION_MISSING")
    try:
        side_state = parse_persisted_side_state_v1(payload.get("side_state"))
    except SideStateRestoreError as exc:
        raise CurrentProductiveCursorError(
            RESTORE_FAIL_CLOSED_INVALID_SIDESTATE, exc.detail
        ) from exc
    trading_epoch = _parse_int(payload.get("trading_epoch"), field="trading_epoch")
    last_evaluated = _parse_int(
        payload.get("last_evaluated_trading_epoch"), field="last_evaluated_trading_epoch"
    )
    now_tick = _parse_int(payload.get("now_tick"), field="now_tick")
    confirmation_epochs = _parse_int(
        payload.get("confirmation_epochs"), field="confirmation_epochs"
    )
    candidate_count = _parse_int(
        confirmation_raw.get("candidate_count"), field="scope_confirmation.candidate_count"
    )
    confirmation_last = _parse_int(
        confirmation_raw.get("last_evaluated_trading_epoch"),
        field="scope_confirmation.last_evaluated_trading_epoch",
    )
    if candidate_count < 0:
        raise CurrentProductiveCursorError("CURSOR_CONFIRMATION_COUNT_INVALID")
    existing_raw = payload.get("existing_scope")
    existing_scope = None
    if existing_raw is not None:
        if not isinstance(existing_raw, Mapping):
            raise CurrentProductiveCursorError("CURSOR_EXISTING_SCOPE_UNPARSEABLE")
        try:
            existing_scope = canonical_scope_snapshot_from_dict(existing_raw)
        except (TypeError, ValueError, KeyError) as exc:
            raise CurrentProductiveCursorError("CURSOR_EXISTING_SCOPE_UNPARSEABLE") from exc
    runtime_raw = payload.get("runtime_scope_state")
    runtime_scope = None
    if runtime_raw is not None:
        if not isinstance(runtime_raw, Mapping):
            raise CurrentProductiveCursorError("CURSOR_RUNTIME_SCOPE_UNPARSEABLE")
        try:
            runtime_scope = runtime_scope_state_from_dict(runtime_raw)
        except (TypeError, ValueError) as exc:
            raise CurrentProductiveCursorError("CURSOR_RUNTIME_SCOPE_UNPARSEABLE") from exc
    cap61_raw = payload.get("cap61_confirmation_state")
    cap61_state = None
    if cap61_raw is not None:
        if not isinstance(cap61_raw, Mapping):
            raise CurrentProductiveCursorError("CURSOR_CAP61_UNPARSEABLE")
        try:
            cap61_state = CanonicalConfirmationStateV1.from_dict(cap61_raw)
        except (TypeError, ValueError, KeyError) as exc:
            raise CurrentProductiveCursorError("CURSOR_CAP61_UNPARSEABLE") from exc
    return CurrentProductiveSideStateConfirmationCursorV1(
        schema_name=schema_name,
        schema_version=schema_version,
        lineage_id=lineage_id,
        instrument_id=instrument_id,
        venue_native_id=venue_native_id,
        trading_epoch=trading_epoch,
        last_evaluated_trading_epoch=last_evaluated,
        now_tick=now_tick,
        side_state=side_state,
        confirmation_epochs=confirmation_epochs,
        scope_confirmation=ScopeConfirmationStateV1(
            candidate_kind=_parse_candidate_kind(confirmation_raw.get("candidate_kind")),
            candidate_count=candidate_count,
            last_evaluated_trading_epoch=confirmation_last,
        ),
        existing_scope=existing_scope,
        runtime_scope_state=runtime_scope,
        cap61_confirmation_state=cap61_state,
    )


def build_current_productive_sidestate_confirmation_cursor_v1(
    *,
    instrument_id: str,
    venue_native_id: str,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
    now_tick: int,
    side_state: SideState,
    scope_confirmation: ScopeConfirmationStateV1,
    existing_scope: Optional[CanonicalScopeSnapshotV1],
    runtime_scope_state: Optional[RuntimeScopeState],
    cap61_confirmation_state: Optional[CanonicalConfirmationStateV1] = None,
    confirmation_epochs: int = int(CANONICAL_CONFIRMATION_EPOCHS),
) -> CurrentProductiveSideStateConfirmationCursorV1:
    bound_instrument = _text(instrument_id)
    bound_native = _text(venue_native_id)
    if not bound_instrument or not bound_native:
        raise CurrentProductiveCursorError("CURSOR_INSTRUMENT_BINDING_MISSING")
    if existing_scope is not None and _text(existing_scope.instrument_id) != bound_instrument:
        raise CurrentProductiveCursorError("CURSOR_SCOPE_INSTRUMENT_MISMATCH")
    if (
        cap61_confirmation_state is not None
        and _text(cap61_confirmation_state.instrument_id) != bound_instrument
    ):
        raise CurrentProductiveCursorError("CURSOR_CAP61_INSTRUMENT_MISMATCH")
    return CurrentProductiveSideStateConfirmationCursorV1(
        schema_name=CURSOR_SCHEMA_NAME,
        schema_version=CURSOR_SCHEMA_VERSION,
        lineage_id=CURSOR_LINEAGE_ID,
        instrument_id=bound_instrument,
        venue_native_id=bound_native,
        trading_epoch=int(trading_epoch),
        last_evaluated_trading_epoch=int(last_evaluated_trading_epoch),
        now_tick=int(now_tick),
        side_state=side_state,
        confirmation_epochs=int(confirmation_epochs),
        scope_confirmation=scope_confirmation,
        existing_scope=existing_scope,
        runtime_scope_state=runtime_scope_state,
        cap61_confirmation_state=cap61_confirmation_state,
    )


def _mismatch_result(reason: str) -> CurrentProductiveCursorRestoreResultV1:
    return CurrentProductiveCursorRestoreResultV1(
        disposition=CursorRestoreDispositionV1.REFUSED_MISMATCH,
        cursor=None,
        reason_code=reason,
        fail_closed=False,
    )


def _stale_result(reason: str) -> CurrentProductiveCursorRestoreResultV1:
    return CurrentProductiveCursorRestoreResultV1(
        disposition=CursorRestoreDispositionV1.REFUSED_STALE,
        cursor=None,
        reason_code=reason,
        fail_closed=False,
    )


def restore_current_productive_sidestate_confirmation_cursor_v1(
    payload: Mapping[str, Any] | CurrentProductiveSideStateConfirmationCursorV1 | None,
    *,
    expected_instrument_id: str,
    expected_venue_native_id: str,
    expected_lineage_id: str = CURSOR_LINEAGE_ID,
    venue_flat: bool,
) -> CurrentProductiveCursorRestoreResultV1:
    if payload is None:
        return CurrentProductiveCursorRestoreResultV1(
            disposition=CursorRestoreDispositionV1.MISSING,
            cursor=None,
            reason_code="CURSOR_MISSING",
            fail_closed=False,
        )
    if venue_flat is not True:
        return CurrentProductiveCursorRestoreResultV1(
            disposition=CursorRestoreDispositionV1.NOT_APPLICABLE_OCCUPIED,
            cursor=None,
            reason_code="CURSOR_NOT_APPLICABLE_OCCUPIED",
            fail_closed=False,
        )
    try:
        if isinstance(payload, CurrentProductiveSideStateConfirmationCursorV1):
            cursor = payload
        elif isinstance(payload, Mapping):
            cursor = parse_current_productive_sidestate_confirmation_cursor_v1(payload)
        else:
            raise CurrentProductiveCursorError("CURSOR_PAYLOAD_NOT_OBJECT")
    except CurrentProductiveCursorError as exc:
        if exc.reason_code == RESTORE_FAIL_CLOSED_INVALID_SIDESTATE:
            return CurrentProductiveCursorRestoreResultV1(
                disposition=CursorRestoreDispositionV1.FAIL_CLOSED_INVALID_SIDESTATE,
                cursor=None,
                reason_code=exc.reason_code,
                fail_closed=True,
            )
        return CurrentProductiveCursorRestoreResultV1(
            disposition=CursorRestoreDispositionV1.FAIL_CLOSED_CORRUPT,
            cursor=None,
            reason_code=exc.reason_code,
            fail_closed=True,
        )
    expected_instrument = _text(expected_instrument_id)
    expected_native = _text(expected_venue_native_id)
    if cursor.schema_name != CURSOR_SCHEMA_NAME or cursor.schema_version != CURSOR_SCHEMA_VERSION:
        return _mismatch_result("CURSOR_SCHEMA_MISMATCH")
    if cursor.lineage_id != expected_lineage_id:
        return _mismatch_result("CURSOR_LINEAGE_MISMATCH")
    if cursor.instrument_id != expected_instrument:
        return _mismatch_result("CURSOR_INSTRUMENT_MISMATCH")
    if cursor.venue_native_id != expected_native:
        return _mismatch_result("CURSOR_VENUE_NATIVE_MISMATCH")
    if int(cursor.confirmation_epochs) != int(CANONICAL_CONFIRMATION_EPOCHS):
        return _mismatch_result("CURSOR_CONFIRMATION_EPOCHS_MISMATCH")
    if cursor.existing_scope is not None:
        if _text(cursor.existing_scope.instrument_id) != expected_instrument:
            return _mismatch_result("CURSOR_SCOPE_INSTRUMENT_MISMATCH")
    if cursor.cap61_confirmation_state is not None:
        if _text(cursor.cap61_confirmation_state.instrument_id) != expected_instrument:
            return _mismatch_result("CURSOR_CAP61_INSTRUMENT_MISMATCH")
    if cursor.side_state in ACTIVE_FLAT_INCOMPATIBLE_SIDESTATES:
        return _stale_result("CURSOR_ACTIVE_SIDESTATE_WHILE_FLAT")
    if cursor.trading_epoch < 1 or cursor.last_evaluated_trading_epoch < 0:
        return _stale_result("CURSOR_EPOCH_STALE")
    if cursor.last_evaluated_trading_epoch >= cursor.trading_epoch:
        return _stale_result("CURSOR_EPOCH_STALE")
    if cursor.now_tick < 1:
        return _stale_result("CURSOR_NOW_TICK_STALE")
    confirmation_last = int(cursor.scope_confirmation.last_evaluated_trading_epoch)
    if confirmation_last > int(cursor.last_evaluated_trading_epoch):
        return _stale_result("CURSOR_CONFIRMATION_EPOCH_STALE")
    if confirmation_last < 0:
        return _stale_result("CURSOR_CONFIRMATION_EPOCH_STALE")
    return CurrentProductiveCursorRestoreResultV1(
        disposition=CursorRestoreDispositionV1.RESTORED,
        cursor=cursor,
        reason_code="CURSOR_RESTORED",
        fail_closed=False,
    )


def persist_current_productive_sidestate_confirmation_cursor_v1(
    cursor: CurrentProductiveSideStateConfirmationCursorV1,
    *,
    store_root: Path,
) -> Path:
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CURSOR_FILENAME
    payload = cursor.to_dict()
    path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    return path


def load_current_productive_sidestate_confirmation_cursor_v1(
    store_root: Path,
) -> Mapping[str, Any] | None:
    path = Path(store_root) / CURSOR_FILENAME
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurrentProductiveCursorError("CURSOR_FILE_CORRUPT", path.name) from exc
    if not isinstance(loaded, Mapping):
        raise CurrentProductiveCursorError("CURSOR_PAYLOAD_NOT_OBJECT")
    return loaded
