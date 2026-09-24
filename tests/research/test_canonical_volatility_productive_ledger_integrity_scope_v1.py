"""Scoped join/productive integrity matrix (campaign/session binding)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    _filter_records_to_integrity_scope_v1,
    assert_ledger_integrity_matrix_v1,
    deterministic_productive_mark_path_v1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    load_research_evidence_records_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    append_max_age_research_evidence_ledger_record_v1,
    build_max_age_research_evidence_join_v1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "51a3625b3666bc905b89ba9a8ad1bcfe84494430"
SEED_SAMPLE_COUNT = 62
CURRENT_CAMPAIGN = "cv_maxage_productive_evidence_campaign_v1_current_scope"
CURRENT_S01 = f"{CURRENT_CAMPAIGN}_s01_abc"
HIST_CAMPAIGN = "cv_maxage_productive_evidence_campaign_v1_1a638769c1dcb066"
HIST_S01 = f"{HIST_CAMPAIGN}_s01_c3fcb04c41ae"
_T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        tmp_path / "prod.jsonl",
        tmp_path / "join.jsonl",
        tmp_path / "q.jsonl",
        tmp_path / "persist.json",
    )


def _build_join_v1(
    *,
    session_id: str,
    cycle_id: str,
    event_offset_seconds: int = 100,
) -> object:
    ref = _T0 + timedelta(seconds=event_offset_seconds)
    as_of = ref - timedelta(seconds=30.0)
    return build_max_age_research_evidence_join_v1(
        session_id=session_id,
        cycle_id=cycle_id,
        instrument_id="ETH-USD_UM_XPERP-310404",
        regime_id="trending",
        max_age_policy_evidence={
            "estimate_as_of_event_time": as_of.isoformat().replace("+00:00", "Z"),
            "reference_event_time": ref.isoformat().replace("+00:00", "Z"),
            "computed_age_seconds": 30.0,
            "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
            "threshold_status": "UNRESOLVED_MAX_AGE",
            "presence_status": "PRESENT",
            "clock_trust_status": "TRUSTED",
            "data_integrity_status": "TRUSTED",
            "reuse_status": "FRESHLY_PRODUCED",
            "restart_status": "NOT_APPLICABLE",
            "source_digest": "abc123",
            "decision": "AGE_COMPUTED",
            "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
            "enforcement_applied": False,
            "numeric_threshold_selected": False,
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": "ETH-USD_UM_XPERP-310404",
            "regime_id": "trending",
        },
        producer_outcome="PRODUCED",
        reuse_status="FRESHLY_PRODUCED",
        restart_status="NOT_APPLICABLE",
        restart_without_estimate=False,
        estimate_present=True,
        observation_count=60,
        source_digest="abc123",
        trading_epoch=1,
        cycle_index=0,
        alpha_scope_entry_authority_allowed=True,
        decision_outcome="HOLD",
        selected_side="none",
        economic_metrics={"net_pnl_after_fees_and_slippage": 0.0, "trade_count": 0},
    )


def _seed_current_session(tmp_path: Path) -> tuple[Path, Path]:
    prod, join, q, persist = _paths(tmp_path)
    run_productive_bridge_accumulation_session_v1(
        session_id=CURRENT_S01,
        campaign_id=CURRENT_CAMPAIGN,
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=SEED_SAMPLE_COUNT),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    assert join.exists() and join.stat().st_size > 0
    return prod, join


def _append_historical_orphan_join(join_path: Path) -> None:
    orphan = _build_join_v1(
        session_id=HIST_S01,
        cycle_id="cycle_orphan_hist",
        event_offset_seconds=200,
    )
    append_max_age_research_evidence_ledger_record_v1(ledger_path=join_path, record=orphan)


def test_scoped_integrity_passes_with_historical_orphan_joins(tmp_path: Path) -> None:
    prod, join = _seed_current_session(tmp_path)
    _append_historical_orphan_join(join)
    with pytest.raises(ProductiveEvidenceAccumulationError, match="extra_join_records"):
        assert_ledger_integrity_matrix_v1(productive_ledger_path=prod, join_ledger_path=join)
    scoped = assert_ledger_integrity_matrix_v1(
        productive_ledger_path=prod,
        join_ledger_path=join,
        integrity_scope_campaign_id=CURRENT_CAMPAIGN,
        integrity_scope_session_ids=(CURRENT_S01,),
    )
    assert scoped["integrity_scope_applied"] is True
    assert scoped["productive_count"] >= 1
    assert scoped["join_count_total_ledger"] > scoped["join_count"]


def test_scoped_integrity_missing_current_join_fails(tmp_path: Path) -> None:
    prod, join = _seed_current_session(tmp_path)
    join.write_text("", encoding="utf-8")
    with pytest.raises(ProductiveEvidenceAccumulationError, match="missing_join_records"):
        assert_ledger_integrity_matrix_v1(
            productive_ledger_path=prod,
            join_ledger_path=join,
            integrity_scope_campaign_id=CURRENT_CAMPAIGN,
            integrity_scope_session_ids=(CURRENT_S01,),
        )


def test_scoped_integrity_extra_current_join_fails(tmp_path: Path) -> None:
    prod, join = _seed_current_session(tmp_path)
    extra = _build_join_v1(
        session_id=CURRENT_S01,
        cycle_id="cycle_extra_not_in_productive",
        event_offset_seconds=300,
    )
    append_max_age_research_evidence_ledger_record_v1(ledger_path=join, record=extra)
    with pytest.raises(ProductiveEvidenceAccumulationError, match="extra_join_records"):
        assert_ledger_integrity_matrix_v1(
            productive_ledger_path=prod,
            join_ledger_path=join,
            integrity_scope_campaign_id=CURRENT_CAMPAIGN,
            integrity_scope_session_ids=(CURRENT_S01,),
        )


def test_scoped_integrity_duplicate_current_join_fails(tmp_path: Path) -> None:
    prod, join = _seed_current_session(tmp_path)
    joins = load_research_evidence_records_v1(join)
    scoped = [j for j in joins if j.session_id == CURRENT_S01]
    assert len(scoped) >= 1
    duplicate_pair = scoped[0:1] + scoped[0:1]
    productive = valid_productive_records_from_ledger_v1(prod)
    with pytest.raises(
        ProductiveEvidenceAccumulationError, match="duplicate_join_records_in_scope"
    ):
        _filter_records_to_integrity_scope_v1(
            productive,
            duplicate_pair,
            campaign_id=CURRENT_CAMPAIGN,
            authorized_session_ids=(CURRENT_S01,),
        )


def test_scoped_integrity_wrong_campaign_binding_fails(tmp_path: Path) -> None:
    prod, join = _seed_current_session(tmp_path)
    with pytest.raises(
        ProductiveEvidenceAccumulationError,
        match="integrity_scope_productive_campaign_mismatch",
    ):
        assert_ledger_integrity_matrix_v1(
            productive_ledger_path=prod,
            join_ledger_path=join,
            integrity_scope_campaign_id="wrong_campaign_id",
            integrity_scope_session_ids=(CURRENT_S01,),
        )


def test_historical_joins_cannot_satisfy_current_scope_completeness(tmp_path: Path) -> None:
    prod, join, _q, _persist = _paths(tmp_path)
    prod.write_text("", encoding="utf-8")
    _append_historical_orphan_join(join)
    scoped = assert_ledger_integrity_matrix_v1(
        productive_ledger_path=prod,
        join_ledger_path=join,
        integrity_scope_campaign_id=CURRENT_CAMPAIGN,
        integrity_scope_session_ids=(CURRENT_S01,),
    )
    assert scoped["productive_count"] == 0
    assert scoped["join_count"] == 0
    assert scoped["join_count_total_ledger"] >= 1
