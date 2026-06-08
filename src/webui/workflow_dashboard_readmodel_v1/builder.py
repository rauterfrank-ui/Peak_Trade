"""Assemble workflow_dashboard_readmodel.v1 from archive evidence."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from .pipeline_builder import build_workflow_pipeline_aggregate_v1
from .types import (
    READMODEL_ID,
    SCHEMA_VERSION,
    EvidenceCardV1,
    EvidenceExplorerEntryV1,
    KillSwitchRecoveryCardV1,
    MissingTruthCardV1,
    NextGoCardV1,
    OrdersFillsPnlCardV1,
    SafetyCardV1,
    WorkflowDashboardReadModelV1,
)

_FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"
T2_NEXT_GO_FALLBACK = "GO_T3_LONGER_TESTNET_STAGE_READY_PACKAGE_NO_RUN_V1"

_PRODUCER_FOLLOWUP = "Producer persistence contract (Slice 2) — no dashboard substitution."


def _now_iso() -> str:
    fixed = os.environ.get(_FIXED_GEN_ENV)
    if fixed:
        return fixed
    return datetime.now(tz=timezone.utc).isoformat()


def _missing_truth(panel_key: str, truth_status: str, message: str) -> MissingTruthCardV1:
    return MissingTruthCardV1(
        panel_key=panel_key,
        truth_status=truth_status,
        message=message,
        producer_followup=_PRODUCER_FOLLOWUP,
    )


def build_workflow_dashboard_readmodel_v1(archive_root: Path) -> WorkflowDashboardReadModelV1:
    """Materialize display-only workflow dashboard from durable archive."""

    root = archive_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("archive_root_not_directory")

    errors: list[str] = []
    load_status = "ready"

    pipeline, pipeline_errors = build_workflow_pipeline_aggregate_v1(root)
    errors.extend(pipeline_errors)

    safety = SafetyCardV1(
        LIVE_AUTHORIZED=False,
        READY_FOR_OPERATOR_ARMING=False,
        PREFLIGHT_LIFT=False,
        GAP7=False,
        evidence_not_approval=True,
        current_mode_label="Research / Paper / Shadow / Testnet — Live blocked",
    )

    universe_missing = _missing_truth(
        "universe",
        "UNIVERSE_SOURCE_NOT_PERSISTED",
        "No governed universe snapshot (~50 futures) is persisted for this workflow view.",
    )
    top20_missing = _missing_truth(
        "top20",
        "TOP20_RANKING_NOT_PERSISTED",
        "No Top-20 ranking snapshot is persisted for this workflow view.",
    )
    selected_future_missing = _missing_truth(
        "selected_future",
        "SELECTED_FUTURE_NOT_PERSISTED",
        "No selected-future decision artifact is linked to pipeline runs.",
    )
    future_detail_missing = _missing_truth(
        "future_detail",
        "FUTURE_DETAIL_NOT_AVAILABLE",
        "Future detail requires a persisted selection and market snapshot — not available.",
    )

    max_real = 0
    real_total = 0
    live_total = 0
    fills_total = 0
    fills_known = True
    paper_count = 0
    shadow_count = 0
    testnet_count = 0

    evidence_entries: list[EvidenceExplorerEntryV1] = []
    killswitch_entries: list[tuple[str, str | None]] = []

    t2_next_go = T2_NEXT_GO_FALLBACK

    for stage in pipeline.stages:
        if stage.bundle_basename is None:
            evidence_entries.append(
                EvidenceExplorerEntryV1(
                    stage_key=stage.stage_key,
                    bundle_basename=None,
                    manifest_verify_rc=None,
                    post_run_review_status=None,
                    closeout_status=None,
                    primary_evidence_captured=None,
                )
            )
            continue

        if stage.mode_label == "paper":
            paper_count += 1
        elif stage.mode_label == "shadow":
            shadow_count += 1
        elif stage.mode_label in ("testnet", "staging_only"):
            testnet_count += 1

        real_total += stage.real_orders_executed
        if stage.fills_count is not None:
            fills_total += stage.fills_count
        else:
            fills_known = False

        evidence_entries.append(
            EvidenceExplorerEntryV1(
                stage_key=stage.stage_key,
                bundle_basename=stage.bundle_basename,
                manifest_verify_rc=stage.manifest_verify_rc,
                post_run_review_status=stage.post_run_review_status,
                closeout_status=stage.closeout_status,
                primary_evidence_captured=stage.evidence_status == "captured",
            )
        )
        killswitch_entries.append((stage.stage_key, stage.killswitch_summary))

        if stage.stage_key == "T2" and stage.bundle_basename:
            bundle_ml_path = root / "runs" / stage.bundle_basename / "machine_lines.env"
            if bundle_ml_path.is_file():
                for line in bundle_ml_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("SELECTED_NEXT_GO_TOKEN="):
                        t2_next_go = line.split("=", 1)[1].strip().strip('"')
                        break

    orders_fills = OrdersFillsPnlCardV1(
        max_real_orders=max_real,
        real_orders_executed=real_total,
        live_orders_executed=live_total if live_total else None,
        fills_count_total=fills_total if fills_known else None,
        paper_runs_count=paper_count,
        shadow_runs_count=shadow_count,
        testnet_runs_count=testnet_count,
        pnl_status="NOT_PERSISTED",
        pnl_value=None,
    )

    evidence_card = EvidenceCardV1(
        archive_root_basename=root.name,
        entries=tuple(evidence_entries),
    )

    killswitch_card = KillSwitchRecoveryCardV1(entries=tuple(killswitch_entries))

    next_go = NextGoCardV1(
        selected_next_go_token=t2_next_go,
        execute_requires_operator_go=True,
        display_note="Execute requires explicit operator GO — no auto-go from dashboard.",
    )

    if errors:
        load_status = "ready_with_warnings"

    return WorkflowDashboardReadModelV1(
        schema_version=SCHEMA_VERSION,
        readmodel_id=READMODEL_ID,
        generated_at_utc=_now_iso(),
        source_kind="offline_archive_aggregate",
        source_label=root.name,
        stale=True,
        stale_reason="archive_snapshot",
        non_authorizing=True,
        load_status=load_status,
        load_errors=tuple(errors),
        safety=safety,
        universe_missing=universe_missing,
        top20_missing=top20_missing,
        selected_future_missing=selected_future_missing,
        future_detail_missing=future_detail_missing,
        pipeline=pipeline,
        orders_fills_pnl=orders_fills,
        evidence_explorer=evidence_card,
        killswitch_recovery=killswitch_card,
        next_go=next_go,
    )
