"""Partial durable writes must surface in terminal accounting on integrity failure."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveBridgeSessionPartialFailureV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    deterministic_productive_mark_path_v1,
    run_productive_bridge_accumulation_session_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    append_max_age_research_evidence_ledger_record_v1,
    build_max_age_research_evidence_join_v1,
    build_ratified_max_age_research_design_contract_v1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "51a3625b3666bc905b89ba9a8ad1bcfe84494430"
SEED_SAMPLE_COUNT = 62
CAMPAIGN = "cv_maxage_productive_evidence_campaign_v1_partial_acct"
SESSION = f"{CAMPAIGN}_s01_x"
_T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _scoped_orphan_join() -> object:
    ref = _T0 + timedelta(seconds=400)
    as_of = ref - timedelta(seconds=30.0)
    return build_max_age_research_evidence_join_v1(
        session_id=SESSION,
        cycle_id="cycle_extra_scoped_orphan",
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
            "session_id": SESSION,
            "cycle_id": "cycle_extra_scoped_orphan",
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


def test_integrity_failure_after_append_carries_durable_counts(tmp_path: Path) -> None:
    prod = tmp_path / "prod.jsonl"
    join = tmp_path / "join.jsonl"
    q = tmp_path / "q.jsonl"
    persist = tmp_path / "persist.json"
    run_productive_bridge_accumulation_session_v1(
        session_id=SESSION,
        campaign_id=CAMPAIGN,
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=SEED_SAMPLE_COUNT),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    append_max_age_research_evidence_ledger_record_v1(
        ledger_path=join,
        record=_scoped_orphan_join(),
    )
    prereg = build_ratified_max_age_research_design_contract_v1().preregistration_digest
    with pytest.raises(ProductiveBridgeSessionPartialFailureV1) as exc_info:
        run_productive_bridge_accumulation_session_v1(
            session_id=SESSION,
            campaign_id=CAMPAIGN,
            repository_sha=REPO_SHA,
            samples=deterministic_productive_mark_path_v1(count=SEED_SAMPLE_COUNT + 1),
            repo_root=ROOT,
            productive_ledger_path=prod,
            join_ledger_path=join,
            quarantine_ledger_path=q,
            typed_volatility_persistence_path=persist,
            retained_estimate_lifecycle_carrier_path=tmp_path / "carrier.json",
            retained_estimate_carrier_mode="WRITE_ONCE_S01",
            early_session_id=SESSION,
            late_session_id=f"{CAMPAIGN}_s02_y",
            preregistration_digest=prereg,
        )
    err = exc_info.value
    assert err.cycles_executed == SEED_SAMPLE_COUNT + 1
    assert err.records_appended >= 1
    assert err.partial_report.get("retained_estimate_carrier_write_status") == "NOT_REACHED"
    assert not (tmp_path / "carrier.json").exists()
