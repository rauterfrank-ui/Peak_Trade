"""Golden Happy Vector forensic observability (signal strength + entry state).

Observation-only. Does not change trading decisions, thresholds, or state transitions.
Default disabled; explicit enable for bounded forensic productive runs.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    cursor_last_accepted_c1_venue_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_SCHEMA_NAME,
    CURSOR_SCHEMA_VERSION,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

RECONCILIATION_NO_PERSISTED_CURSOR = "NO_PERSISTED_CURSOR"
RECONCILIATION_SAME_INSTRUMENT_CONTINUATION = "SAME_INSTRUMENT_CONTINUATION"
RECONCILIATION_SELECTION_ROTATION_FRESH_LANE = "SELECTION_ROTATION_FRESH_LANE"
from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationProgressStateV1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalAssessmentConfirmationIntegrationResultV1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentPolicyV1

OWNER = (
    "full_core_live_path_composition_root_v1."
    "productive_golden_happy_vector_forensic_observability_v1"
)

DIRECTIONAL_SIGNAL_OBSERVABILITY_SCHEMA_VERSION = "directional_signal_observability.v1"
ENTRY_STATE_SNAPSHOT_SCHEMA_VERSION = "continuous_run_entry_state_snapshot.v1"

DIRECTIONAL_SIGNAL_LEDGER_FILENAME = "directional_signal_observability_v1.jsonl"
ENTRY_STATE_SNAPSHOT_FILENAME = "continuous_run_entry_state_snapshot_v1.json"

OBSERVABILITY_DEFAULT_ENABLED = False
OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION = False
ENTRY_STATE_SNAPSHOT_FAILURE_POLICY = "FAIL_CLOSED_BEFORE_FIRST_OBSERVATION"

MISSING_BY_DESIGN_AFTER_ROTATION = "MISSING_BY_DESIGN_AFTER_ROTATION"
EXPECTED_BUT_NOT_AVAILABLE = "EXPECTED_BUT_NOT_AVAILABLE"

_session_var: ContextVar[Optional["GoldenHappyVectorForensicObservabilitySessionV1"]] = (
    ContextVar("golden_happy_vector_forensic_observability_session_v1", default=None)
)


class GoldenHappyVectorForensicObservabilityError(RuntimeError):
    """Fail-closed observability persistence violation."""


@dataclass
class GoldenHappyVectorForensicObservabilitySessionV1:
    enabled: bool
    product_evidence_root: Path
    run_id: str
    continuous_run_id: str
    repository_sha: str = ""
    cycle_index: int | None = None
    cycle_instance_id: str = ""
    c1_venue_event_time: float | None = None
    _entry_snapshot_written: bool = field(default=False, repr=False)

    def with_cycle_from_s5_evidence_root_v1(self, *, s5_evidence_root: Path) -> None:
        auth_path = Path(s5_evidence_root).parent / "s5_cycle_authorization_v1.json"
        if not auth_path.is_file():
            return
        try:
            payload = json.loads(auth_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.cycle_index = int(payload.get("cycle_index") or 0) or None
        self.cycle_instance_id = str(payload.get("cycle_instance_id") or "")
        raw_time = payload.get("c1_venue_event_time")
        if raw_time is not None:
            try:
                self.c1_venue_event_time = float(raw_time)
            except (TypeError, ValueError):
                self.c1_venue_event_time = None


def bind_golden_happy_vector_forensic_observability_session_v1(
    session: GoldenHappyVectorForensicObservabilitySessionV1 | None,
) -> Token:
    return _session_var.set(session)


def reset_golden_happy_vector_forensic_observability_session_v1(token: Token) -> None:
    _session_var.reset(token)


def active_forensic_observability_session_v1() -> GoldenHappyVectorForensicObservabilitySessionV1 | None:
    session = _session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _atomic_write_json_v1(*, path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".obs_", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise GoldenHappyVectorForensicObservabilityError(str(exc)) from exc


def _append_jsonl_v1(*, path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _threshold_flags_from_assessment_signal_v1(
    *,
    signal_strength: float,
    policy: DirectionalAssessmentPolicyV1,
) -> tuple[bool, bool]:
    strength = float(signal_strength)
    candidate_met = strength >= float(policy.candidate_signal_threshold)
    confirmation_met = strength >= float(policy.confirmation_signal_threshold)
    return candidate_met, confirmation_met


def _confirmation_state_dict_v1(state: ConfirmationProgressStateV1) -> dict[str, Any]:
    return state.to_dict()


def build_directional_signal_observability_record_v1(
    *,
    session: GoldenHappyVectorForensicObservabilitySessionV1,
    c3_result: DirectionalAssessmentConfirmationIntegrationResultV1,
    policy: DirectionalAssessmentPolicyV1,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    instrument_id: str,
    side: str,
) -> dict[str, Any]:
    assessment = c3_result.assessment
    strength = float(assessment.signal_strength)
    candidate_met, confirmation_met = _threshold_flags_from_assessment_signal_v1(
        signal_strength=strength,
        policy=policy,
    )
    obs_id = observation_acceptance_result.observation_identity
    classification = str(observation_acceptance_result.classification.value)
    reason_codes = list(assessment.reason_codes) + [c3_result.reason_code.value]
    return {
        "schema_version": DIRECTIONAL_SIGNAL_OBSERVABILITY_SCHEMA_VERSION,
        "capture_timestamp": _utc_now_iso_v1(),
        "run_id": session.run_id,
        "continuous_run_id": session.continuous_run_id,
        "repository_sha": session.repository_sha,
        "cycle_index": session.cycle_index,
        "cycle_instance_id": session.cycle_instance_id,
        "c1_venue_event_time": session.c1_venue_event_time,
        "instrument_id": instrument_id,
        "canonical_instrument_id": instrument_id,
        "venue_instrument_id": str(
            observation_acceptance_result.state_before.bound_instrument_key.venue_instrument_id
        ),
        "observation_classification": classification,
        "observation_reason_code": str(observation_acceptance_result.reason_code),
        "strategy_advance_allowed": bool(observation_acceptance_result.strategy_advance_allowed),
        "market_observation_epoch": int(
            observation_acceptance_result.state_after.market_observation_epoch.value
        ),
        "observation_identity_digest": (
            None if obs_id is None else str(getattr(obs_id, "semantic_digest", "") or "")
        ),
        "signal_strength": strength,
        "candidate_signal_threshold": float(policy.candidate_signal_threshold),
        "confirmation_signal_threshold": float(policy.confirmation_signal_threshold),
        "confirmation_epochs": int(policy.confirmation_epochs),
        "assessment_signal": c3_result.assessment_signal.value,
        "direction_side": side,
        "assessment_status": assessment.status.value,
        "candidate_threshold_met": candidate_met,
        "confirmation_threshold_met": confirmation_met,
        "confirmation_state_before": _confirmation_state_dict_v1(
            c3_result.confirmation_progress_before
        ),
        "confirmation_state_after": _confirmation_state_dict_v1(
            c3_result.confirmation_progress_after
        ),
        "distinct_confirmation_count_before": int(
            c3_result.confirmation_progress_before.distinct_confirmation_observation_count
        ),
        "distinct_confirmation_count_after": int(
            c3_result.confirmation_progress_after.distinct_confirmation_observation_count
        ),
        "confirmation_advanced": bool(c3_result.confirmation_advanced),
        "state_changed": bool(c3_result.state_changed),
        "fail_closed": bool(c3_result.fail_closed),
        "reason_codes": reason_codes,
        "owner": OWNER,
    }


def append_directional_signal_observability_v1(
    *,
    c3_result: DirectionalAssessmentConfirmationIntegrationResultV1,
    policy: DirectionalAssessmentPolicyV1,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    instrument_id: str,
    side: str,
) -> dict[str, Any] | None:
    session = active_forensic_observability_session_v1()
    if session is None:
        return None
    record = build_directional_signal_observability_record_v1(
        session=session,
        c3_result=c3_result,
        policy=policy,
        observation_acceptance_result=observation_acceptance_result,
        instrument_id=instrument_id,
        side=side,
    )
    path = session.product_evidence_root / DIRECTIONAL_SIGNAL_LEDGER_FILENAME
    try:
        _append_jsonl_v1(path=path, record=record)
    except OSError as exc:
        if OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION:
            raise GoldenHappyVectorForensicObservabilityError(str(exc)) from exc
        record = {**record, "capture_error": str(exc), "capture_ok": False}
    else:
        record = {**record, "capture_ok": True}
    return record


def _cursor_carrier_section_v1(
    *,
    cursor_store_root: Path,
    reconciliation: Any,
) -> dict[str, Any]:
    if reconciliation.action == RECONCILIATION_SELECTION_ROTATION_FRESH_LANE:
        return {
            "present": False,
            "reason": MISSING_BY_DESIGN_AFTER_ROTATION,
        }
    active = cursor_store_root / CURSOR_FILENAME
    if not active.is_file():
        if reconciliation.action == RECONCILIATION_NO_PERSISTED_CURSOR:
            return {"present": False, "reason": MISSING_BY_DESIGN_AFTER_ROTATION}
        return {"present": False, "reason": EXPECTED_BUT_NOT_AVAILABLE}
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(cursor_store_root)
    if loaded is None:
        return {"present": False, "reason": EXPECTED_BUT_NOT_AVAILABLE}
    return {
        "present": True,
        "reason": "",
        "cursor_schema_name": CURSOR_SCHEMA_NAME,
        "cursor_schema_version": CURSOR_SCHEMA_VERSION,
        "payload": loaded,
    }


def build_continuous_run_entry_state_snapshot_v1(
    *,
    session: GoldenHappyVectorForensicObservabilitySessionV1,
    bound: BoundInstrumentV1,
    reconciliation: Any,
    cursor_store_root: Path,
    expected_cursor_floor: float,
    selection_id: str = "",
    binding_epoch: str = "",
    cap24_reselection_performed: bool = False,
) -> dict[str, Any]:
    carrier = _cursor_carrier_section_v1(
        cursor_store_root=cursor_store_root,
        reconciliation=reconciliation,
    )
    last_accepted: float | None = None
    if carrier.get("present") is True:
        payload = carrier.get("payload") or {}
        if isinstance(payload, Mapping):
            try:
                last_accepted = float(cursor_last_accepted_c1_venue_event_time_v1(payload))
            except (TypeError, ValueError):
                last_accepted = None
    return {
        "schema_version": ENTRY_STATE_SNAPSHOT_SCHEMA_VERSION,
        "capture_timestamp": _utc_now_iso_v1(),
        "run_id": session.run_id,
        "continuous_run_id": session.continuous_run_id,
        "repository_sha": session.repository_sha,
        "selected_canonical_instrument": str(bound.instrument_id or ""),
        "selected_native_instrument": str(bound.venue_native_id or ""),
        "selection_id": selection_id,
        "binding_epoch": binding_epoch,
        "cap24_reselection_performed": bool(cap24_reselection_performed),
        "universe_snapshot_id": str(bound.universe_snapshot_id or ""),
        "ranking_snapshot_id": str(bound.ranking_snapshot_id or ""),
        "ranking_integrity_digest": str(bound.ranking_integrity_digest or ""),
        "rotation_reconciliation": {
            "action": reconciliation.action,
            "previous_native_instrument": reconciliation.persisted_native_id,
            "current_native_instrument": reconciliation.selected_native_id,
            "rotation_performed": (
                reconciliation.action == RECONCILIATION_SELECTION_ROTATION_FRESH_LANE
            ),
            "archived_cursor_path": reconciliation.archived_cursor_path or None,
            "same_instrument_continuation": (
                reconciliation.action == RECONCILIATION_SAME_INSTRUMENT_CONTINUATION
            ),
        },
        "expected_cursor_floor": float(expected_cursor_floor),
        "last_accepted_c1_venue_event_time_unix": last_accepted,
        "entry_confirmation_and_sidestate_carrier": carrier,
        "owner": OWNER,
    }


def persist_continuous_run_entry_state_snapshot_v1(
    *,
    session: GoldenHappyVectorForensicObservabilitySessionV1,
    bound: BoundInstrumentV1,
    reconciliation: Any,
    cursor_store_root: Path,
    expected_cursor_floor: float,
    selection_id: str = "",
    binding_epoch: str = "",
    cap24_reselection_performed: bool = False,
) -> Path:
    if session._entry_snapshot_written:
        raise GoldenHappyVectorForensicObservabilityError("ENTRY_STATE_SNAPSHOT_DUPLICATE_FORBIDDEN")
    path = session.product_evidence_root / ENTRY_STATE_SNAPSHOT_FILENAME
    payload = build_continuous_run_entry_state_snapshot_v1(
        session=session,
        bound=bound,
        reconciliation=reconciliation,
        cursor_store_root=cursor_store_root,
        expected_cursor_floor=expected_cursor_floor,
        selection_id=selection_id,
        binding_epoch=binding_epoch,
        cap24_reselection_performed=cap24_reselection_performed,
    )
    _atomic_write_json_v1(path=path, payload=payload)
    session._entry_snapshot_written = True
    return path


__all__ = [
    "DIRECTIONAL_SIGNAL_LEDGER_FILENAME",
    "DIRECTIONAL_SIGNAL_OBSERVABILITY_SCHEMA_VERSION",
    "ENTRY_STATE_SNAPSHOT_FAILURE_POLICY",
    "ENTRY_STATE_SNAPSHOT_FILENAME",
    "ENTRY_STATE_SNAPSHOT_SCHEMA_VERSION",
    "EXPECTED_BUT_NOT_AVAILABLE",
    "GoldenHappyVectorForensicObservabilityError",
    "GoldenHappyVectorForensicObservabilitySessionV1",
    "MISSING_BY_DESIGN_AFTER_ROTATION",
    "OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION",
    "OBSERVABILITY_DEFAULT_ENABLED",
    "OWNER",
    "active_forensic_observability_session_v1",
    "append_directional_signal_observability_v1",
    "bind_golden_happy_vector_forensic_observability_session_v1",
    "build_continuous_run_entry_state_snapshot_v1",
    "build_directional_signal_observability_record_v1",
    "persist_continuous_run_entry_state_snapshot_v1",
    "reset_golden_happy_vector_forensic_observability_session_v1",
]
