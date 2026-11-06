"""Datentypen für `last_paper_run_panel_readmodel.v0` (display-only, stdlib)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "last_paper_run_panel_readmodel.v0"
READMODEL_ID = "last_paper_run_panel_readmodel.v0"

InstrumentTruthStatus = str  # PERSISTED | NOT_PERSISTED | UNKNOWN


@dataclass(frozen=True)
class LastRunBlockV0:
    run_id: str
    job_name: str
    stage: str
    mode: str
    status: str
    job_accepted: bool | None
    duration_actual_seconds: int | None
    duration_cap_seconds: int | None
    hard_stop_enforced: bool | None
    utc_start: str | None
    utc_end: str | None
    adapter_rc: int | None
    operator: str | None
    execute_go_token: str | None
    repo_head: str | None


@dataclass(frozen=True)
class InstrumentBlockV0:
    instrument_truth_status: InstrumentTruthStatus
    selected_instrument: str | None
    selected_future: str | None
    selected_symbol: str | None
    runtime_fixture_ref: str | None
    source_of_truth_file: str | None
    source_of_truth_field: str | None


@dataclass(frozen=True)
class OrdersFillsBlockV0:
    max_real_orders: int | None
    real_orders_executed: int | None
    live_orders_executed: int | None
    fills_count: int | None
    paper_orders_count: int | None


@dataclass(frozen=True)
class EvidenceBlockV0:
    durable_evidence_root_basename: str
    primary_evidence_captured: bool
    manifest_verify_rc: str | None
    post_run_review_status: str | None
    closeout_status: str | None
    adapter_primary_evidence_basename: str
    paper_archive_basename: str | None


@dataclass(frozen=True)
class SafetyBlockV0:
    LIVE_AUTHORIZED: bool
    READY_FOR_OPERATOR_ARMING: bool
    PREFLIGHT_LIFT: bool
    GAP7: bool
    evidence_not_approval: bool


@dataclass(frozen=True)
class NextTokenBlockV0:
    selected_next_go_token: str | None
    next_stage_requires_operator_go: bool
    next_stage_label: str | None


@dataclass(frozen=True)
class LastPaperRunPanelReadModelV0:
    schema_version: str
    readmodel_id: str
    generated_at_utc: str
    source_kind: str
    source_label: str
    stale: bool
    stale_reason: str
    non_authorizing: bool
    load_status: str
    load_errors: tuple[str, ...]
    last_run: LastRunBlockV0
    instrument: InstrumentBlockV0
    orders_fills: OrdersFillsBlockV0
    evidence: EvidenceBlockV0
    safety: SafetyBlockV0
    next_token: NextTokenBlockV0


def to_json_dict(model: LastPaperRunPanelReadModelV0) -> dict[str, Any]:
    return {
        "schema_version": model.schema_version,
        "readmodel_id": model.readmodel_id,
        "generated_at_utc": model.generated_at_utc,
        "source_kind": model.source_kind,
        "source_label": model.source_label,
        "stale": model.stale,
        "stale_reason": model.stale_reason,
        "non_authorizing": model.non_authorizing,
        "load_status": model.load_status,
        "load_errors": list(model.load_errors),
        "last_run": {
            "run_id": model.last_run.run_id,
            "job_name": model.last_run.job_name,
            "stage": model.last_run.stage,
            "mode": model.last_run.mode,
            "status": model.last_run.status,
            "job_accepted": model.last_run.job_accepted,
            "duration_actual_seconds": model.last_run.duration_actual_seconds,
            "duration_cap_seconds": model.last_run.duration_cap_seconds,
            "hard_stop_enforced": model.last_run.hard_stop_enforced,
            "utc_start": model.last_run.utc_start,
            "utc_end": model.last_run.utc_end,
            "adapter_rc": model.last_run.adapter_rc,
            "operator": model.last_run.operator,
            "execute_go_token": model.last_run.execute_go_token,
            "repo_head": model.last_run.repo_head,
        },
        "instrument": {
            "instrument_truth_status": model.instrument.instrument_truth_status,
            "selected_instrument": model.instrument.selected_instrument,
            "selected_future": model.instrument.selected_future,
            "selected_symbol": model.instrument.selected_symbol,
            "runtime_fixture_ref": model.instrument.runtime_fixture_ref,
            "source_of_truth_file": model.instrument.source_of_truth_file,
            "source_of_truth_field": model.instrument.source_of_truth_field,
        },
        "orders_fills": {
            "max_real_orders": model.orders_fills.max_real_orders,
            "real_orders_executed": model.orders_fills.real_orders_executed,
            "live_orders_executed": model.orders_fills.live_orders_executed,
            "fills_count": model.orders_fills.fills_count,
            "paper_orders_count": model.orders_fills.paper_orders_count,
        },
        "evidence": {
            "durable_evidence_root_basename": model.evidence.durable_evidence_root_basename,
            "primary_evidence_captured": model.evidence.primary_evidence_captured,
            "manifest_verify_rc": model.evidence.manifest_verify_rc,
            "post_run_review_status": model.evidence.post_run_review_status,
            "closeout_status": model.evidence.closeout_status,
            "adapter_primary_evidence_basename": model.evidence.adapter_primary_evidence_basename,
            "paper_archive_basename": model.evidence.paper_archive_basename,
        },
        "safety": {
            "LIVE_AUTHORIZED": model.safety.LIVE_AUTHORIZED,
            "READY_FOR_OPERATOR_ARMING": model.safety.READY_FOR_OPERATOR_ARMING,
            "PREFLIGHT_LIFT": model.safety.PREFLIGHT_LIFT,
            "GAP7": model.safety.GAP7,
            "evidence_not_approval": model.safety.evidence_not_approval,
        },
        "next_token": {
            "selected_next_go_token": model.next_token.selected_next_go_token,
            "next_stage_requires_operator_go": model.next_token.next_stage_requires_operator_go,
            "next_stage_label": model.next_token.next_stage_label,
        },
    }
