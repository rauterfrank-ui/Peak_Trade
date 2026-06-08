"""Datentypen für workflow_dashboard_readmodel.v1 (display-only, stdlib)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "workflow_dashboard_readmodel.v1"
READMODEL_ID = "workflow_dashboard_readmodel.v1"
PIPELINE_READMODEL_ID = "workflow_pipeline_aggregate.v1"


@dataclass(frozen=True)
class SafetyCardV1:
    LIVE_AUTHORIZED: bool
    READY_FOR_OPERATOR_ARMING: bool
    PREFLIGHT_LIFT: bool
    GAP7: bool
    evidence_not_approval: bool
    current_mode_label: str


@dataclass(frozen=True)
class MissingTruthCardV1:
    panel_key: str
    truth_status: str
    message: str
    producer_followup: str


@dataclass(frozen=True)
class RunStageCardV1:
    stage_key: str
    stage_label: str
    bundle_basename: str | None
    verdict: str
    reclassification: str | None
    utc_start: str | None
    utc_end: str | None
    duration_actual_seconds: float | int | None
    duration_cap_seconds: int | None
    hard_stop_enforced: bool | None
    job_accepted: bool | None
    real_orders_executed: int
    fills_count: int | None
    manifest_verify_rc: str | None
    post_run_review_status: str | None
    closeout_status: str | None
    operator: str | None
    execute_go_token: str | None
    mode_label: str | None
    heartbeat_count: int | None
    evidence_status: str
    killswitch_summary: str | None


@dataclass(frozen=True)
class WorkflowPipelineAggregateV1:
    readmodel_id: str
    stage_count: int
    stages: tuple[RunStageCardV1, ...]


@dataclass(frozen=True)
class OrdersFillsPnlCardV1:
    max_real_orders: int
    real_orders_executed: int
    live_orders_executed: int | None
    fills_count_total: int | None
    paper_runs_count: int
    shadow_runs_count: int
    testnet_runs_count: int
    pnl_status: str
    pnl_value: None


@dataclass(frozen=True)
class EvidenceExplorerEntryV1:
    stage_key: str
    bundle_basename: str | None
    manifest_verify_rc: str | None
    post_run_review_status: str | None
    closeout_status: str | None
    primary_evidence_captured: bool | None


@dataclass(frozen=True)
class EvidenceCardV1:
    archive_root_basename: str
    entries: tuple[EvidenceExplorerEntryV1, ...]


@dataclass(frozen=True)
class KillSwitchRecoveryCardV1:
    entries: tuple[tuple[str, str | None], ...]


@dataclass(frozen=True)
class NextGoCardV1:
    selected_next_go_token: str
    execute_requires_operator_go: bool
    display_note: str


@dataclass(frozen=True)
class UniverseSelectionRowDisplayV1:
    row_id: str
    symbol: str
    rank: int
    exchange: str | None = None
    display_score: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class SelectedFutureDisplayV1:
    row_id: str
    symbol: str
    rank: int
    truth_status: str
    selection_reason: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class MarketSnapshotDisplayV1:
    truth_status: str
    source_kind: str | None = None
    snapshot_id: str | None = None
    exchange: str | None = None
    captured_at: str | None = None


@dataclass(frozen=True)
class UniverseSelectionDashboardSliceV1:
    loaded: bool
    load_errors: tuple[str, ...]
    source_run_id: str | None = None
    source_stage: str | None = None
    generated_at: str | None = None
    universe: tuple[UniverseSelectionRowDisplayV1, ...] = ()
    ranking: tuple[UniverseSelectionRowDisplayV1, ...] = ()
    selected_future: SelectedFutureDisplayV1 | None = None
    market_snapshot: MarketSnapshotDisplayV1 | None = None
    evidence_links: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowDashboardReadModelV1:
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
    safety: SafetyCardV1
    universe_missing: MissingTruthCardV1
    top20_missing: MissingTruthCardV1
    selected_future_missing: MissingTruthCardV1
    future_detail_missing: MissingTruthCardV1
    universe_selection: UniverseSelectionDashboardSliceV1
    pipeline: WorkflowPipelineAggregateV1
    orders_fills_pnl: OrdersFillsPnlCardV1
    evidence_explorer: EvidenceCardV1
    killswitch_recovery: KillSwitchRecoveryCardV1
    next_go: NextGoCardV1


def to_json_dict(model: WorkflowDashboardReadModelV1) -> dict[str, Any]:
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
        "safety": {
            "LIVE_AUTHORIZED": model.safety.LIVE_AUTHORIZED,
            "READY_FOR_OPERATOR_ARMING": model.safety.READY_FOR_OPERATOR_ARMING,
            "PREFLIGHT_LIFT": model.safety.PREFLIGHT_LIFT,
            "GAP7": model.safety.GAP7,
            "evidence_not_approval": model.safety.evidence_not_approval,
            "current_mode_label": model.safety.current_mode_label,
        },
        "universe_missing": {
            "panel_key": model.universe_missing.panel_key,
            "truth_status": model.universe_missing.truth_status,
            "message": model.universe_missing.message,
            "producer_followup": model.universe_missing.producer_followup,
        },
        "top20_missing": {
            "panel_key": model.top20_missing.panel_key,
            "truth_status": model.top20_missing.truth_status,
            "message": model.top20_missing.message,
            "producer_followup": model.top20_missing.producer_followup,
        },
        "selected_future_missing": {
            "panel_key": model.selected_future_missing.panel_key,
            "truth_status": model.selected_future_missing.truth_status,
            "message": model.selected_future_missing.message,
            "producer_followup": model.selected_future_missing.producer_followup,
        },
        "future_detail_missing": {
            "panel_key": model.future_detail_missing.panel_key,
            "truth_status": model.future_detail_missing.truth_status,
            "message": model.future_detail_missing.message,
            "producer_followup": model.future_detail_missing.producer_followup,
        },
        "universe_selection": {
            "loaded": model.universe_selection.loaded,
            "load_errors": list(model.universe_selection.load_errors),
            "source_run_id": model.universe_selection.source_run_id,
            "source_stage": model.universe_selection.source_stage,
            "generated_at": model.universe_selection.generated_at,
            "universe": [
                {
                    "row_id": row.row_id,
                    "symbol": row.symbol,
                    "rank": row.rank,
                    "exchange": row.exchange,
                    "display_score": row.display_score,
                    "notes": row.notes,
                }
                for row in model.universe_selection.universe
            ],
            "ranking": [
                {
                    "row_id": row.row_id,
                    "symbol": row.symbol,
                    "rank": row.rank,
                    "exchange": row.exchange,
                    "display_score": row.display_score,
                    "notes": row.notes,
                }
                for row in model.universe_selection.ranking
            ],
            "selected_future": (
                None
                if model.universe_selection.selected_future is None
                else {
                    "row_id": model.universe_selection.selected_future.row_id,
                    "symbol": model.universe_selection.selected_future.symbol,
                    "rank": model.universe_selection.selected_future.rank,
                    "truth_status": model.universe_selection.selected_future.truth_status,
                    "selection_reason": model.universe_selection.selected_future.selection_reason,
                    "notes": model.universe_selection.selected_future.notes,
                }
            ),
            "market_snapshot": (
                None
                if model.universe_selection.market_snapshot is None
                else {
                    "truth_status": model.universe_selection.market_snapshot.truth_status,
                    "source_kind": model.universe_selection.market_snapshot.source_kind,
                    "snapshot_id": model.universe_selection.market_snapshot.snapshot_id,
                    "exchange": model.universe_selection.market_snapshot.exchange,
                    "captured_at": model.universe_selection.market_snapshot.captured_at,
                }
            ),
            "evidence_links": list(model.universe_selection.evidence_links),
        },
        "pipeline": {
            "readmodel_id": model.pipeline.readmodel_id,
            "stage_count": model.pipeline.stage_count,
            "stages": [
                {
                    "stage_key": s.stage_key,
                    "stage_label": s.stage_label,
                    "bundle_basename": s.bundle_basename,
                    "verdict": s.verdict,
                    "reclassification": s.reclassification,
                    "utc_start": s.utc_start,
                    "utc_end": s.utc_end,
                    "duration_actual_seconds": s.duration_actual_seconds,
                    "duration_cap_seconds": s.duration_cap_seconds,
                    "hard_stop_enforced": s.hard_stop_enforced,
                    "job_accepted": s.job_accepted,
                    "real_orders_executed": s.real_orders_executed,
                    "fills_count": s.fills_count,
                    "manifest_verify_rc": s.manifest_verify_rc,
                    "post_run_review_status": s.post_run_review_status,
                    "closeout_status": s.closeout_status,
                    "operator": s.operator,
                    "execute_go_token": s.execute_go_token,
                    "mode_label": s.mode_label,
                    "heartbeat_count": s.heartbeat_count,
                    "evidence_status": s.evidence_status,
                    "killswitch_summary": s.killswitch_summary,
                }
                for s in model.pipeline.stages
            ],
        },
        "orders_fills_pnl": {
            "max_real_orders": model.orders_fills_pnl.max_real_orders,
            "real_orders_executed": model.orders_fills_pnl.real_orders_executed,
            "live_orders_executed": model.orders_fills_pnl.live_orders_executed,
            "fills_count_total": model.orders_fills_pnl.fills_count_total,
            "paper_runs_count": model.orders_fills_pnl.paper_runs_count,
            "shadow_runs_count": model.orders_fills_pnl.shadow_runs_count,
            "testnet_runs_count": model.orders_fills_pnl.testnet_runs_count,
            "pnl_status": model.orders_fills_pnl.pnl_status,
            "pnl_value": model.orders_fills_pnl.pnl_value,
        },
        "evidence_explorer": {
            "archive_root_basename": model.evidence_explorer.archive_root_basename,
            "entries": [
                {
                    "stage_key": e.stage_key,
                    "bundle_basename": e.bundle_basename,
                    "manifest_verify_rc": e.manifest_verify_rc,
                    "post_run_review_status": e.post_run_review_status,
                    "closeout_status": e.closeout_status,
                    "primary_evidence_captured": e.primary_evidence_captured,
                }
                for e in model.evidence_explorer.entries
            ],
        },
        "killswitch_recovery": {
            "entries": [
                {"stage_key": k, "summary": s} for k, s in model.killswitch_recovery.entries
            ],
        },
        "next_go": {
            "selected_next_go_token": model.next_go.selected_next_go_token,
            "execute_requires_operator_go": model.next_go.execute_requires_operator_go,
            "display_note": model.next_go.display_note,
        },
    }
