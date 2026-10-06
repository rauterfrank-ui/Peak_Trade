"""GHV intelligence lineage forensic observability v1 (refs only; AUTHORITY=NONE).

Appends read-only lineage slots for productive cycles when a GHV forensic session is active.
Does not consume lineage values for trading, learning, or optimization decisions.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
    LineageSlotStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION,
    GoldenHappyVectorForensicObservabilityError,
    active_forensic_observability_session_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

SCHEMA_VERSION = "ghv_intelligence_lineage_forensic_observability.v1"
LEDGER_FILENAME = "ghv_intelligence_lineage_trace_v1.jsonl"
OWNER = "full_core_live_path_composition_root_v1.ghv_intelligence_lineage_forensic_observability_v1"
GHV_AUTHORITY = "NONE"


def _append_jsonl_v1(*, path: Any, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _slot(ref: str | None, status: LineageSlotStatusV1) -> dict[str, str]:
    return {"status": status.value, "ref": ref or ""}


def build_intelligence_lineage_observability_record_v1(
    *,
    cycle_id: str,
    instrument_id: str,
    venue_native_id: str,
    ddo_capture_summary: Mapping[str, Any] | None,
    ddo_offline_export_handoff: Mapping[str, Any] | None,
    replay: IntegratedOfflineReplayResultV1,
) -> dict[str, Any]:
    """Build refs-only intelligence lineage snapshot for one productive cycle."""
    decision_ref = ""
    if ddo_offline_export_handoff:
        decision_ref = str(ddo_offline_export_handoff.get("decision_event_ref") or "")
    elif ddo_capture_summary:
        ids = ddo_capture_summary.get("record_ids") or ()
        if ids:
            decision_ref = str(ids[-1])
    handoff_ok = bool(ddo_offline_export_handoff and ddo_offline_export_handoff.get("ok"))
    return {
        "schema_version": SCHEMA_VERSION,
        "ghv_authority": GHV_AUTHORITY,
        "owner": OWNER,
        "productive_cycle_id": cycle_id,
        "selected_instrument": instrument_id,
        "venue_native_id": venue_native_id,
        "decision_event_ref": _slot(
            decision_ref,
            LineageSlotStatusV1.PRESENT if decision_ref else LineageSlotStatusV1.NOT_REACHED,
        ),
        "dpo_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "pending_outcome_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "outcome_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "learning_state_ref": _slot(
            str((ddo_offline_export_handoff or {}).get("learning_state_record_ref") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if handoff_ok
                and (ddo_offline_export_handoff or {}).get("learning_state_record_ref")
                else LineageSlotStatusV1.NOT_REACHED
            ),
        ),
        "learning_evidence_ref": _slot(
            str((ddo_offline_export_handoff or {}).get("learning_evidence_record_id") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if handoff_ok
                and (ddo_offline_export_handoff or {}).get("learning_evidence_record_id")
                else LineageSlotStatusV1.NOT_REACHED
            ),
        ),
        "optimization_input_ref": _slot(
            str((ddo_offline_export_handoff or {}).get("optimization_ack_status") or ""),
            status=(LineageSlotStatusV1.PRESENT if handoff_ok else LineageSlotStatusV1.NOT_REACHED),
        ),
        "experiment_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "robustness_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "champion_challenger_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "meta_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "mi_ref": _slot(None, LineageSlotStatusV1.INTENTIONALLY_DISCONNECTED),
        "gvef_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "proposal_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "m10_ref": _slot(None, LineageSlotStatusV1.NOT_REACHED),
        "replay_decision_outcome": str(
            getattr(getattr(replay, "evidence", None), "decision_outcome", "") or ""
        ),
        "ddo_capture_ok": bool((ddo_capture_summary or {}).get("ok")),
        "decision_unchanged": True,
        "capture_failure_changes_decision": False,
    }


def append_intelligence_lineage_observability_from_productive_cycle_v1(
    *,
    cycle_id: str,
    instrument_id: str,
    venue_native_id: str,
    ddo_capture_summary: Mapping[str, Any] | None,
    ddo_offline_export_handoff: Mapping[str, Any] | None,
    replay: IntegratedOfflineReplayResultV1,
) -> dict[str, Any] | None:
    session = active_forensic_observability_session_v1()
    if session is None:
        return None
    record = build_intelligence_lineage_observability_record_v1(
        cycle_id=cycle_id,
        instrument_id=instrument_id,
        venue_native_id=venue_native_id,
        ddo_capture_summary=ddo_capture_summary,
        ddo_offline_export_handoff=ddo_offline_export_handoff,
        replay=replay,
    )
    path = session.product_evidence_root / LEDGER_FILENAME
    try:
        _append_jsonl_v1(path=path, record=record)
    except OSError as exc:
        if OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION:
            raise GoldenHappyVectorForensicObservabilityError(str(exc)) from exc
        record = {**record, "capture_error": str(exc), "capture_ok": False}
    else:
        record = {**record, "capture_ok": True}
    return record


__all__ = [
    "GHV_AUTHORITY",
    "LEDGER_FILENAME",
    "SCHEMA_VERSION",
    "append_intelligence_lineage_observability_from_productive_cycle_v1",
    "build_intelligence_lineage_observability_record_v1",
]
