"""GHV intelligence lineage forensic observability v1 (refs only; AUTHORITY=NONE).

Appends read-only lineage slots for productive cycles when a GHV forensic session is active.
Does not consume lineage values for trading, learning, or optimization decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.governance.ghv_intelligence_lineage_completeness_v1 import (
    derive_realized_economic_completeness_v1,
    derive_structural_outcome_completeness_v1,
)
from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
    LineageSlotStatusV1,
)
from src.governance.ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1 import (
    prove_ghv_reference_artifacts_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION,
    GoldenHappyVectorForensicObservabilityError,
    active_forensic_observability_session_v1,
    geometry_evidence_refs_for_cycle_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

SCHEMA_VERSION = "ghv_intelligence_lineage_forensic_observability.v2"
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


def _ghv_reference_bundle_v1() -> dict[str, str]:
    proof = prove_ghv_reference_artifacts_v1()
    return {
        "ghv_reference_digest": str(proof.get("manifest_digest") or ""),
        "ghv_reference_root": str(proof.get("ghv_reference_root") or ""),
        "ghv_artifacts_ok": str(proof.get("artifacts_ok")),
    }


def build_intelligence_lineage_observability_record_v1(
    *,
    cycle_id: str,
    instrument_id: str,
    venue_native_id: str,
    ddo_capture_summary: Mapping[str, Any] | None,
    ddo_offline_export_handoff: Mapping[str, Any] | None,
    replay: IntegratedOfflineReplayResultV1,
    lane_state_root: Path | None = None,
    pre_external_reached: bool | None = None,
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
    session = active_forensic_observability_session_v1()
    geometry_ref = ""
    geometry_digest = ""
    if session is not None:
        geo = geometry_evidence_refs_for_cycle_v1(session, cycle_id)
        geometry_ref = str(geo.get("geometry_evidence_ref") or "")
        geometry_digest = str(geo.get("geometry_evidence_digest") or "")

    pending_ref = ""
    pending_status = LineageSlotStatusV1.NOT_REACHED
    if lane_state_root is not None and decision_ref:
        pending = load_pending_outcome_by_decision_ref_v1(lane_state_root, decision_ref)
        if pending is not None:
            pending_ref = pending.pending_outcome_id
            pending_status = LineageSlotStatusV1.PRESENT
            if not geometry_ref:
                geometry_ref = str(pending.geometry_evidence_ref or "")
                geometry_digest = str(pending.geometry_evidence_digest or "")

    dpo_ref = ""
    dpo_status = LineageSlotStatusV1.NOT_REACHED
    outcome = str(getattr(getattr(replay, "evidence", None), "decision_outcome", "") or "")
    if outcome.lower() in {"enter_long", "enter_short"}:
        dpo_status = LineageSlotStatusV1.INSUFFICIENT_EVIDENCE

    ghv_bundle = _ghv_reference_bundle_v1()
    learning_evidence_stub: dict[str, Any] = {}
    if handoff_ok and ddo_offline_export_handoff:
        learning_evidence_stub = {
            "decision_event_ref": decision_ref,
            "actual_outcome_ref": "",
            "source_learning_state_record_ref": str(
                ddo_offline_export_handoff.get("learning_state_record_ref") or ""
            ),
            "outcome_semantic_class": "OBSERVED_PRODUCTIVE_PRE_EXTERNAL",
            "outcome_evidence_provenance": {"fill_source_type": "NO_FILL"},
        }

    pre_ext = pre_external_reached
    if pre_ext is None:
        pre_ext = outcome.lower() in {"enter_long", "enter_short"}

    return {
        "schema_version": SCHEMA_VERSION,
        "ghv_authority": GHV_AUTHORITY,
        "owner": OWNER,
        "productive_cycle_id": cycle_id,
        "selected_instrument": instrument_id,
        "venue_native_id": venue_native_id,
        "ghv_reference_ref": _slot(
            ghv_bundle.get("ghv_reference_root"),
            (
                LineageSlotStatusV1.PRESENT
                if bool(ghv_bundle.get("ghv_artifacts_ok"))
                else LineageSlotStatusV1.INSUFFICIENT_EVIDENCE
            ),
        ),
        "ghv_reference_digest": ghv_bundle.get("ghv_reference_digest") or "",
        "instrument_ref": _slot(instrument_id, LineageSlotStatusV1.PRESENT),
        "geometry_evidence_ref": _slot(
            geometry_ref,
            LineageSlotStatusV1.PRESENT if geometry_ref else LineageSlotStatusV1.NOT_REACHED,
        ),
        "geometry_evidence_digest": geometry_digest,
        "scope_ref": _slot(
            cycle_id,
            LineageSlotStatusV1.PRESENT if geometry_ref else LineageSlotStatusV1.NOT_REACHED,
        ),
        "cap61_ref": _slot(None, LineageSlotStatusV1.NOT_APPLICABLE),
        "sidestate_ref": _slot(None, LineageSlotStatusV1.HISTORICAL_REF_NOT_PRESENT),
        "mv2_ref": _slot(cycle_id, LineageSlotStatusV1.PRESENT),
        "double_play_ref": _slot(None, LineageSlotStatusV1.NOT_APPLICABLE),
        "entry_decision_ref": _slot(
            outcome,
            (
                LineageSlotStatusV1.PRESENT
                if outcome.lower() in {"enter_long", "enter_short", "observe", "no_action"}
                else LineageSlotStatusV1.NOT_REACHED
            ),
        ),
        "decision_event_ref": _slot(
            decision_ref,
            LineageSlotStatusV1.PRESENT if decision_ref else LineageSlotStatusV1.NOT_REACHED,
        ),
        "dpo_ref": _slot(dpo_ref, dpo_status),
        "pending_outcome_ref": _slot(pending_ref, pending_status),
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
        "pre_external_ref": _slot(
            "PRE_EXTERNAL_EFFECT" if pre_ext else "",
            (LineageSlotStatusV1.PRESENT if pre_ext else LineageSlotStatusV1.NOT_REACHED),
        ),
        "structural_outcome_completeness": derive_structural_outcome_completeness_v1(
            learning_evidence_stub
        ),
        "realized_economic_completeness": derive_realized_economic_completeness_v1(
            learning_evidence_stub
        ),
        "replay_decision_outcome": outcome,
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
    lane_state_root: Path | None = None,
    pre_external_reached: bool | None = None,
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
        lane_state_root=lane_state_root,
        pre_external_reached=pre_external_reached,
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
