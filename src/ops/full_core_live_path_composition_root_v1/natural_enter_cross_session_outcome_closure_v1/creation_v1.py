"""Create durable pending outcomes after genuine Natural Enter + PRE_EXTERNAL."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    NaturalEnterReportingResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    DEFAULT_N_BARS_REQUIRED,
    EVENT_CREATED,
    STATUS_PENDING,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.id_v1 import (
    pending_outcome_id_from_decision_event_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
    pending_outcome_has_closed_outcome_in_ddo_ledger_v1,
    persist_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.types_v1 import (
    NaturalEnterPendingOutcomeRecordV1,
)


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class NaturalEnterPendingCreationResultV1:
    created: bool
    skipped: bool
    reason: str
    pending_outcome_id: str | None = None
    record: NaturalEnterPendingOutcomeRecordV1 | None = None


def _is_genuine_natural_enter_report_v1(
    reporting: NaturalEnterReportingResultV1,
    *,
    synthetic_enter_observed: bool,
) -> bool:
    if synthetic_enter_observed:
        return False
    if not reporting.natural_pre_external_reached:
        return False
    if not reporting.natural_enter_observed:
        return False
    dpo = reporting.dpo
    if not dpo.get("decision_event_ref") or not dpo.get("dpo_ref"):
        return False
    outcome = str(dpo.get("decision_outcome") or "").lower()
    return outcome in {"enter_long", "enter_short"}


def maybe_create_natural_enter_pending_outcome_v1(
    *,
    lane_state_root: Path,
    reporting: NaturalEnterReportingResultV1,
    run_id: str,
    evidence_root: Path,
    canonical_instrument_id: str,
    native_id: str,
    decision_timestamp_unix: float,
    decision_reference_price: float,
    market_context_ref: str = "",
    decision_id: str = "",
    synthetic_enter_observed: bool = False,
    n_bars_required: int = DEFAULT_N_BARS_REQUIRED,
) -> NaturalEnterPendingCreationResultV1:
    if not _is_genuine_natural_enter_report_v1(
        reporting, synthetic_enter_observed=synthetic_enter_observed
    ):
        return NaturalEnterPendingCreationResultV1(
            created=False,
            skipped=True,
            reason="NOT_GENUINE_NATURAL_ENTER",
        )
    decision_event_ref = str(reporting.dpo.get("decision_event_ref") or "")
    ddo_path = lane_state_root / "LANE_1/ddo_learning_capture_v1.jsonl"
    if pending_outcome_has_closed_outcome_in_ddo_ledger_v1(ddo_path, decision_event_ref):
        return NaturalEnterPendingCreationResultV1(
            created=False,
            skipped=True,
            reason="OUTCOME_ALREADY_CLOSED_IN_DDO",
        )
    existing = load_pending_outcome_by_decision_ref_v1(lane_state_root, decision_event_ref)
    if existing is not None:
        return NaturalEnterPendingCreationResultV1(
            created=False,
            skipped=True,
            reason="PENDING_ALREADY_EXISTS",
            pending_outcome_id=existing.pending_outcome_id,
            record=existing,
        )
    pending_id = pending_outcome_id_from_decision_event_ref_v1(decision_event_ref)
    side = str(reporting.enter_side or reporting.dpo.get("selected_side") or "").upper()
    cycle_id = str(reporting.dpo.get("cycle_id") or "")
    session_part = cycle_id.rsplit(":cycle:", 1)[0] if ":cycle:" in cycle_id else cycle_id
    correlation_id = f"ddo.corr.{session_part}" if session_part else ""
    now = _utc_now_iso_v1()
    record = NaturalEnterPendingOutcomeRecordV1(
        schema_version="natural_enter_pending_outcome.v1",
        pending_outcome_id=pending_id,
        decision_event_ref=decision_event_ref,
        dpo_ref=str(reporting.dpo.get("dpo_ref") or ""),
        decision_id=str(decision_id or ""),
        correlation_id=correlation_id[:128],
        cycle_id=cycle_id,
        source_run_id=str(run_id),
        source_session_id=cycle_id.rsplit(":cycle:", 1)[0] if ":cycle:" in cycle_id else cycle_id,
        source_evidence_root=str(evidence_root),
        canonical_instrument_id=str(canonical_instrument_id),
        native_id=str(native_id),
        side=side,
        decision_timestamp_unix=float(decision_timestamp_unix),
        decision_reference_price=float(decision_reference_price),
        market_context_ref=str(market_context_ref or ""),
        n_bars_required=int(n_bars_required),
        bars_observed=0,
        finalized_bar_identities=(),
        status=STATUS_PENDING,
        created_at_utc=now,
        updated_at_utc=now,
    )
    persist_record_v1(
        lane_state_root,
        event_type=EVENT_CREATED,
        record=record,
        detail={
            "reason": "HORIZON_INCOMPLETE_AT_PRE_EXTERNAL",
            "synthetic_enter_observed": synthetic_enter_observed,
        },
    )
    return NaturalEnterPendingCreationResultV1(
        created=True,
        skipped=False,
        reason="CREATED",
        pending_outcome_id=pending_id,
        record=record,
    )


def extract_decision_context_from_report_v1(
    report: Mapping[str, Any],
    *,
    default_decision_ts_unix: float,
    default_price: float,
    canonical_instrument_id: str,
) -> tuple[float, float, str]:
    summaries = report.get("S5_CYCLE_SUMMARIES") or []
    ts = default_decision_ts_unix
    if summaries:
        last = summaries[-1]
        if isinstance(last, dict) and last.get("c1_venue_event_time") is not None:
            ts = float(last["c1_venue_event_time"])
    price = default_price
    dpo = report.get("DPO")
    if isinstance(dpo, dict):
        pass
    return ts, price, str(canonical_instrument_id)
